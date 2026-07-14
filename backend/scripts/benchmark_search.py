"""Reproducible benchmark for the global declarative search (`systemSearch`).

Seeds `system.task` and `system.message` with a configurable number of records
owned by a single dedicated benchmark user, then fires concurrent TEXT-mode
searches through `SystemSearchService.search` (the same code path used by the
topbar) and reports latency percentiles against the design SLO (p95 < 300ms
at 100,000 records/model, 10 concurrent clients).

Usage (from backend/, with the venv active):

    python scripts/benchmark_search.py seed --records-per-model 100000
    python scripts/benchmark_search.py run --concurrency 10 --requests 60
    python scripts/benchmark_search.py cleanup

`seed` is idempotent-ish: it always wipes previously seeded benchmark data for
the benchmark user before inserting fresh rows, so re-running `seed` does not
accumulate duplicates. `cleanup` removes the benchmark user and all of its
tasks/messages.

`run` drives `SystemSearchService.search` in-process, in the same single
Python process/event loop as the benchmark script itself — it does not
measure how a real multi-worker deployment spreads concurrent requests across
processes. `run-http` fills that gap: it fires the same query mix as real
`systemSearch` GraphQL requests (mode=TEXT, same code path) over HTTP against
an already-running server, so concurrent clients are actually served by
however many worker processes that server was started with. Start the server
separately first, e.g.:

    uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4

then:

    python scripts/benchmark_search.py run-http --base-url http://127.0.0.1:8000 \
        --concurrency 10 --requests 60
"""

import argparse
import asyncio
import random
import statistics
import sys
import time
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import httpx  # noqa: E402
from sqlalchemy import delete, insert, select  # noqa: E402

from app.core.database.session import db  # noqa: E402
from app.core.security.jwt_manager import JWTManager  # noqa: E402
from app.domains.system.models.system_colors import SystemColor  # noqa: E402
from app.domains.system.models.system_message import (  # noqa: E402
    MessageStatus,
    SystemMessage,
)
from app.domains.system.models.system_search_audit import (  # noqa: E402
    SystemSearchAudit,
)
from app.domains.system.models.system_task import (  # noqa: E402
    SystemTask,
    TaskPriority,
    TaskStatus,
)
from app.domains.system.service.system_search_service import (  # noqa: E402
    SystemSearchService,
)
from app.domains.users.models.user_user import UserUser  # noqa: E402

BENCHMARK_EMAIL = "search-benchmark@local.test"
BATCH_SIZE = 5000
NEEDLE_TASK_TITLE_ES = "Renovar contrato zeta-vector-77321-unico"
NEEDLE_MESSAGE_SUBJECT_ES = "Aprobar presupuesto zeta-vector-77321-unico"

# A handful of common phrases so some query terms hit a large fraction of rows
# (the realistic "stress" case) while the numbered suffix keeps rows unique.
TASK_PHRASES = [
    ("Revisar presupuesto", "Review budget"),
    ("Enviar reporte semanal", "Send weekly report"),
    ("Actualizar documentacion", "Update documentation"),
    ("Contactar cliente", "Contact client"),
    ("Preparar presentacion", "Prepare presentation"),
    ("Corregir defecto", "Fix defect"),
    ("Planificar sprint", "Plan sprint"),
    ("Auditar accesos", "Audit access"),
]
MESSAGE_PHRASES = [
    ("Seguimiento de proyecto", "Project follow-up"),
    ("Confirmacion de reunion", "Meeting confirmation"),
    ("Actualizacion de estado", "Status update"),
    ("Solicitud de aprobacion", "Approval request"),
    ("Recordatorio de pago", "Payment reminder"),
    ("Notificacion de incidente", "Incident notification"),
    ("Cambio de horario", "Schedule change"),
    ("Cierre de ticket", "Ticket closure"),
]

COMMON_QUERY_ES = TASK_PHRASES[0][0]
COMMON_QUERY_MESSAGE_ES = MESSAGE_PHRASES[0][0]
QUERY_SET = [
    ("common_task_word", "revisar"),
    ("common_message_word", "seguimiento"),
    ("needle_exact", "zeta-vector-77321-unico"),
    ("no_match", "xyzxyzxyz-no-existe-en-ningun-registro"),
]


async def _get_or_create_benchmark_user() -> int:
    async with db.session() as session:
        result = await session.execute(
            select(UserUser.id).where(UserUser.email == BENCHMARK_EMAIL)
        )
        user_id = result.scalar_one_or_none()
        if user_id is not None:
            return user_id
        user = UserUser(
            email=BENCHMARK_EMAIL,
            name="Search Benchmark",
            password="benchmark-only-not-a-real-login",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id


def _task_row(index: int, user_id: int, phrase_pool) -> dict:
    if index == 0:
        title_es, title_en = NEEDLE_TASK_TITLE_ES, "Renew contract zeta-vector-77321-unique"
    else:
        phrase_es, phrase_en = random.choice(phrase_pool)
        title_es = f"{phrase_es} #{index}"
        title_en = f"{phrase_en} #{index}"
    return {
        "uuid": uuid.uuid4(),
        "status": random.choice(list(TaskStatus)).value,
        "color": random.choice(list(SystemColor)).value,
        "title": {"es_MX": title_es, "en_US": title_en},
        "priority": random.choice(list(TaskPriority)).value,
        "user_id": user_id,
        "create_by": user_id,
    }


def _message_row(index: int, user_id: int, phrase_pool) -> dict:
    if index == 0:
        subject_es = NEEDLE_MESSAGE_SUBJECT_ES
        subject_en = "Approve budget zeta-vector-77321-unique"
    else:
        phrase_es, phrase_en = random.choice(phrase_pool)
        subject_es = f"{phrase_es} #{index}"
        subject_en = f"{phrase_en} #{index}"
    return {
        "uuid": uuid.uuid4(),
        "status": random.choice(list(MessageStatus)).value,
        "subject": {"es_MX": subject_es, "en_US": subject_en},
        "from_user_id": user_id,
        "create_by": user_id,
    }


async def cleanup(user_id: int | None = None) -> None:
    async with db.session() as session:
        if user_id is None:
            result = await session.execute(
                select(UserUser.id).where(UserUser.email == BENCHMARK_EMAIL)
            )
            user_id = result.scalar_one_or_none()
        if user_id is None:
            print("No benchmark data found.")
            return
        await session.execute(delete(SystemTask).where(SystemTask.user_id == user_id))
        await session.execute(
            delete(SystemMessage).where(SystemMessage.from_user_id == user_id)
        )
        await session.execute(
            delete(SystemSearchAudit).where(SystemSearchAudit.user_id == user_id)
        )
        await session.execute(delete(UserUser).where(UserUser.id == user_id))
        await session.commit()
    print(f"Removed benchmark user {user_id} and its tasks/messages.")


async def seed(records_per_model: int) -> int:
    user_id = await _get_or_create_benchmark_user()
    print(f"Benchmark user id={user_id} ({BENCHMARK_EMAIL})")

    async with db.session() as session:
        await session.execute(delete(SystemTask).where(SystemTask.user_id == user_id))
        await session.execute(
            delete(SystemMessage).where(SystemMessage.from_user_id == user_id)
        )
        await session.commit()

    for label, model_table, row_builder, phrase_pool in (
        ("system.task", SystemTask.__table__, _task_row, TASK_PHRASES),
        ("system.message", SystemMessage.__table__, _message_row, MESSAGE_PHRASES),
    ):
        started = time.monotonic()
        inserted = 0
        async with db.session() as session:
            for start in range(0, records_per_model, BATCH_SIZE):
                batch_len = min(BATCH_SIZE, records_per_model - start)
                rows = [
                    row_builder(start + i, user_id, phrase_pool)
                    for i in range(batch_len)
                ]
                await session.execute(insert(model_table), rows)
                inserted += batch_len
                print(f"  {label}: {inserted}/{records_per_model}", end="\r")
            await session.commit()
        elapsed = time.monotonic() - started
        print(f"\n{label}: inserted {inserted} rows in {elapsed:.1f}s")

    return user_id


async def _timed_search(query: str, user_id: int) -> tuple[float, str]:
    started = time.monotonic()
    try:
        results = await SystemSearchService.search(query, user_id, lang="es", limit=20)
        elapsed = time.monotonic() - started
        return elapsed, f"ok:{len(results)}"
    except TimeoutError:
        elapsed = time.monotonic() - started
        return elapsed, "timeout"
    except Exception as exc:  # noqa: BLE001 - benchmark must keep going
        elapsed = time.monotonic() - started
        return elapsed, f"error:{type(exc).__name__}:{exc}"


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


async def run(concurrency: int, requests: int, user_id: int) -> None:
    semaphore = asyncio.Semaphore(concurrency)
    plan = [QUERY_SET[i % len(QUERY_SET)] for i in range(requests)]

    async def worker(label: str, query: str):
        async with semaphore:
            elapsed, outcome = await _timed_search(query, user_id)
            return label, query, elapsed, outcome

    started = time.monotonic()
    results = await asyncio.gather(*(worker(label, q) for label, q in plan))
    total_elapsed = time.monotonic() - started

    by_label: dict[str, list[float]] = {}
    outcomes: dict[str, int] = {}
    for label, _query, elapsed, outcome in results:
        by_label.setdefault(label, []).append(elapsed)
        kind = outcome.split(":", 1)[0]
        outcomes[kind] = outcomes.get(kind, 0) + 1

    all_latencies = [elapsed for _label, _q, elapsed, _o in results]

    print(f"\n=== Benchmark: concurrency={concurrency} requests={requests} ===")
    print(f"Wall time: {total_elapsed:.2f}s  |  throughput: {requests / total_elapsed:.2f} req/s")
    print(f"Outcomes: {outcomes}")
    print(
        f"\nAll queries combined: "
        f"p50={_percentile(all_latencies, 50) * 1000:.0f}ms "
        f"p95={_percentile(all_latencies, 95) * 1000:.0f}ms "
        f"p99={_percentile(all_latencies, 99) * 1000:.0f}ms "
        f"max={max(all_latencies) * 1000:.0f}ms "
        f"mean={statistics.mean(all_latencies) * 1000:.0f}ms"
    )
    print("\nBy query type:")
    for label, values in by_label.items():
        print(
            f"  {label:20s} n={len(values):3d}  "
            f"p50={_percentile(values, 50) * 1000:8.0f}ms  "
            f"p95={_percentile(values, 95) * 1000:8.0f}ms  "
            f"max={max(values) * 1000:8.0f}ms"
        )

    slo_ms = 300
    p95_ms = _percentile(all_latencies, 95) * 1000
    verdict = "PASS" if p95_ms < slo_ms else "FAIL"
    print(f"\nSLO check: p95 < {slo_ms}ms -> {verdict} (measured {p95_ms:.0f}ms)")


SYSTEM_SEARCH_GRAPHQL = """
query SystemSearch($query: String!, $lang: String!, $limit: Int!) {
  systemSearch(input: {query: $query, lang: $lang, limit: $limit, mode: TEXT}) {
    status
    results { uuid }
    errors { code message }
  }
}
"""


async def _mint_access_token(user_id: int) -> str:
    async with db.session() as session:
        result = await session.execute(
            select(UserUser.email).where(UserUser.id == user_id)
        )
        email = result.scalar_one()
    return JWTManager.generate_access_token({"sub": email})


async def _timed_http_search(
    client: httpx.AsyncClient, headers: dict, query: str
) -> tuple[float, str]:
    started = time.monotonic()
    try:
        response = await client.post(
            "/graphql",
            json={
                "query": SYSTEM_SEARCH_GRAPHQL,
                "variables": {"query": query, "lang": "es", "limit": 20},
            },
            headers=headers,
        )
        elapsed = time.monotonic() - started
        payload = response.json()
        if response.status_code != 200 or payload.get("errors"):
            return elapsed, f"error:HTTP{response.status_code}:{payload.get('errors')}"
        status = payload["data"]["systemSearch"]["status"]
        count = len(payload["data"]["systemSearch"]["results"])
        return elapsed, f"ok:{status}:{count}"
    except Exception as exc:  # noqa: BLE001 - benchmark must keep going
        elapsed = time.monotonic() - started
        return elapsed, f"error:{type(exc).__name__}:{exc}"


async def run_http(
    base_url: str, concurrency: int, requests: int, user_id: int
) -> None:
    token = await _mint_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    semaphore = asyncio.Semaphore(concurrency)
    plan = [QUERY_SET[i % len(QUERY_SET)] for i in range(requests)]

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:

        async def worker(label: str, query: str):
            async with semaphore:
                elapsed, outcome = await _timed_http_search(client, headers, query)
                return label, query, elapsed, outcome

        started = time.monotonic()
        results = await asyncio.gather(*(worker(label, q) for label, q in plan))
        total_elapsed = time.monotonic() - started

    by_label: dict[str, list[float]] = {}
    outcomes: dict[str, int] = {}
    for label, _query, elapsed, outcome in results:
        by_label.setdefault(label, []).append(elapsed)
        kind = outcome.split(":", 1)[0]
        outcomes[kind] = outcomes.get(kind, 0) + 1
        if kind == "error":
            print(f"  {label}: {outcome}")

    all_latencies = [elapsed for _label, _q, elapsed, _o in results]

    print(f"\n=== HTTP benchmark: {base_url} concurrency={concurrency} requests={requests} ===")
    print(f"Wall time: {total_elapsed:.2f}s  |  throughput: {requests / total_elapsed:.2f} req/s")
    print(f"Outcomes: {outcomes}")
    print(
        f"\nAll queries combined: "
        f"p50={_percentile(all_latencies, 50) * 1000:.0f}ms "
        f"p95={_percentile(all_latencies, 95) * 1000:.0f}ms "
        f"p99={_percentile(all_latencies, 99) * 1000:.0f}ms "
        f"max={max(all_latencies) * 1000:.0f}ms "
        f"mean={statistics.mean(all_latencies) * 1000:.0f}ms"
    )
    print("\nBy query type:")
    for label, values in by_label.items():
        print(
            f"  {label:20s} n={len(values):3d}  "
            f"p50={_percentile(values, 50) * 1000:8.0f}ms  "
            f"p95={_percentile(values, 95) * 1000:8.0f}ms  "
            f"max={max(values) * 1000:8.0f}ms"
        )

    slo_ms = 300
    p95_ms = _percentile(all_latencies, 95) * 1000
    verdict = "PASS" if p95_ms < slo_ms else "FAIL"
    print(f"\nSLO check: p95 < {slo_ms}ms -> {verdict} (measured {p95_ms:.0f}ms)")


async def _resolve_user_id() -> int:
    async with db.session() as session:
        result = await session.execute(
            select(UserUser.id).where(UserUser.email == BENCHMARK_EMAIL)
        )
        user_id = result.scalar_one_or_none()
    if user_id is None:
        raise SystemExit(
            "No benchmark user found. Run `python scripts/benchmark_search.py seed` first."
        )
    return user_id


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Seed benchmark data")
    seed_parser.add_argument("--records-per-model", type=int, default=100_000)

    run_parser = subparsers.add_parser("run", help="Run the concurrent load test")
    run_parser.add_argument("--concurrency", type=int, default=10)
    run_parser.add_argument("--requests", type=int, default=60)

    run_http_parser = subparsers.add_parser(
        "run-http",
        help="Run the concurrent load test over HTTP against a running server",
    )
    run_http_parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    run_http_parser.add_argument("--concurrency", type=int, default=10)
    run_http_parser.add_argument("--requests", type=int, default=60)

    subparsers.add_parser("cleanup", help="Delete benchmark user, tasks, and messages")

    args = parser.parse_args()

    try:
        if args.command == "seed":
            await seed(args.records_per_model)
        elif args.command == "run":
            user_id = await _resolve_user_id()
            await run(args.concurrency, args.requests, user_id)
        elif args.command == "run-http":
            user_id = await _resolve_user_id()
            await run_http(args.base_url, args.concurrency, args.requests, user_id)
        elif args.command == "cleanup":
            await cleanup()
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
