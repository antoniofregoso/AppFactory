#!/usr/bin/env python3
"""Audit AppFactory domain metadata, views, and access-control JSON."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


FIELD_TYPES = {
    "string", "string_i18n", "integer", "decimal", "monetary", "percentage",
    "date", "datetime", "boolean", "color", "image", "text", "password",
    "selection", "status_badge", "html", "json", "many2one",
    "many2one_avatar", "one2many", "one2many_kanban", "one2many_list",
    "one2many_followers", "many2many", "many2many_pills",
}
RELATION_TYPES = {
    "many2one", "many2one_avatar", "one2many", "one2many_kanban",
    "one2many_list", "many2many", "many2many_pills",
}
FORM_PLACEMENTS = {"header", "leftColumn", "rightColumn", "footer", "tab"}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc


def source_file(data_dir: Path, plural: str, singular: str) -> Path:
    plural_path = data_dir / plural
    return plural_path if plural_path.exists() else data_dir / singular


def duplicate_values(values):
    seen = set()
    return sorted({value for value in values if value in seen or seen.add(value)})


def audit_models(models, errors):
    names = [model.get("name") for model in models]
    for name in duplicate_values(names):
        errors.append(f"duplicate model: {name}")
    for model in models:
        model_name = model.get("name")
        if not model_name or "." not in model_name:
            errors.append(f"invalid logical model name: {model_name!r}")
        fields = model.get("fields") or []
        field_names = [field.get("name") for field in fields]
        for name in duplicate_values(field_names):
            errors.append(f"{model_name}: duplicate field {name}")
        for field in fields:
            field_name = field.get("name")
            field_type = field.get("type")
            if field_type not in FIELD_TYPES:
                errors.append(f"{model_name}.{field_name}: unsupported type {field_type!r}")
            if field_name in {"description", "mission"} and field_type != "html":
                errors.append(f"{model_name}.{field_name}: rich description must use html")
            if field_type in RELATION_TYPES and not field.get("model"):
                errors.append(f"{model_name}.{field_name}: relation is missing model")


def audit_schemas(models, schemas, errors):
    fields_by_model = {
        model["name"]: {field["name"]: field for field in model.get("fields") or []}
        for model in models if model.get("name")
    }
    default_models = {
        schema.get("model") for schema in schemas
        if schema.get("name") == "default" and schema.get("use") == "view"
    }
    for model_name in fields_by_model:
        if model_name not in default_models:
            errors.append(f"{model_name}: missing default/view schema")

    for schema in schemas:
        model_name = schema.get("model")
        if model_name not in fields_by_model:
            errors.append(f"schema references unknown model {model_name!r}")
            continue
        if schema.get("use") != "view":
            continue
        view = schema.get("view")
        if not isinstance(view, list):
            errors.append(f"{model_name}/{schema.get('name')}: view must be a list")
            continue
        known_fields = fields_by_model[model_name]
        title_fields = []
        kanban_title_fields = []
        list_columns = []
        calendar_markers = {"title": 0, "startDate": 0, "endDate": 0}
        has_calendar = False
        for item in view:
            name = item.get("name")
            if name not in known_fields and name not in {"uuid", "followers"}:
                errors.append(f"{model_name}: view references unknown field {name!r}")
            if item.get("type") not in FIELD_TYPES:
                errors.append(f"{model_name}.{name}: view has unsupported type {item.get('type')!r}")
            form = item.get("form")
            if form is not None:
                placements = FORM_PLACEMENTS & set(form)
                if not placements:
                    errors.append(f"{model_name}.{name}: form field has no placement")
                if form.get("header") == "title":
                    title_fields.append(name)
                for position_name in ("leftColumn", "rightColumn", "tab"):
                    if position_name in form and (
                        not isinstance(form[position_name], (int, float))
                        or form[position_name] < 0
                    ):
                        errors.append(
                            f"{model_name}.{name}: form.{position_name} must be a non-negative number"
                        )
                metadata_help = known_fields.get(name, {}).get("help")
                if metadata_help is not None and form.get("help") != metadata_help:
                    errors.append(f"{model_name}.{name}: form.help differs from model help")
                if name in {"description", "mission"} and item.get("type") == "html" and form.get("tab") != 0:
                    errors.append(f"{model_name}.{name}: rich description must use form.tab 0")
            if item.get("kanban", {}).get("header") == "title":
                kanban_title_fields.append(name)
            if "list" in item:
                column = item["list"].get("column")
                if not isinstance(column, (int, float)):
                    errors.append(f"{model_name}.{name}: list column must be numeric")
                else:
                    list_columns.append(column)
            calendar = item.get("calendar")
            if calendar:
                has_calendar = True
                for marker in calendar_markers:
                    if calendar.get(marker) is True:
                        calendar_markers[marker] += 1
        if len(title_fields) != 1:
            errors.append(f"{model_name}: form requires exactly one title, found {title_fields}")
        if len(kanban_title_fields) != 1:
            errors.append(
                f"{model_name}: kanban requires exactly one title, found {kanban_title_fields}"
            )
        for column in duplicate_values(list_columns):
            errors.append(f"{model_name}: duplicate list column {column}")
        if has_calendar:
            if calendar_markers["title"] != 1 or calendar_markers["startDate"] != 1:
                errors.append(
                    f"{model_name}: calendar needs exactly one title and startDate; "
                    f"found {calendar_markers}"
                )


def audit_access(source, errors):
    permissions = source.get("permissions") or []
    roles = source.get("roles") or []
    permission_codes = [item.get("code") for item in permissions]
    role_codes = [item.get("code") for item in roles]
    for code in duplicate_values(permission_codes):
        errors.append(f"duplicate permission: {code}")
    for code in duplicate_values(role_codes):
        errors.append(f"duplicate role: {code}")
    known_permissions = set(permission_codes)
    known_roles = set(role_codes)
    for role in roles:
        missing = set(role.get("permissions") or []) - known_permissions
        if missing:
            errors.append(f"role {role.get('code')} references unknown permissions: {sorted(missing)}")
    for assignment in source.get("assignments") or []:
        if assignment.get("role") not in known_roles:
            errors.append(f"assignment references unknown role: {assignment.get('role')}")


def _literal_keys_by_name(path: Path) -> dict[str, set[str]]:
    """Map every top-level `NAME = {...}` / `NAME = {"k": v, ...}` assignment in a
    module to its string keys/elements, resolving `*OTHER_NAME` set spreads against
    assignments already seen earlier in the same file."""
    resolved: dict[str, set[str]] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return resolved
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        value = node.value
        keys: set[str] | None = None
        if isinstance(value, ast.Dict):
            keys = {
                key.value for key in value.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            }
        elif isinstance(value, ast.Set):
            keys = set()
            for elt in value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    keys.add(elt.value)
                elif isinstance(elt, ast.Starred) and isinstance(elt.value, ast.Name):
                    keys.update(resolved.get(elt.value.id, set()))
        if keys is not None:
            resolved[target.id] = keys
    return resolved


def audit_generic_registration(domain_dir: Path, models, errors, warnings) -> None:
    """Cross-check the domain's models against the Python-side registries the
    'Registration checklist' in domain-architecture.md requires. audit_models/
    audit_schemas only validate JSON; this catches a model that is declared but
    was never wired into generic CRUD, permission enforcement, or fresh setup."""
    domain_name = domain_dir.name
    backend_dir = domain_dir.parents[2] if len(domain_dir.parents) >= 3 else None
    if backend_dir is None or backend_dir.name != "backend":
        return

    repository_path = backend_dir / "app/domains/system/repository/system_model_repository.py"
    service_path = backend_dir / "app/domains/system/service/system_model_service.py"
    setup_path = backend_dir / "scripts/setup_database.py"
    declared_model_names = [model.get("name") for model in models if model.get("name")]

    if repository_path.exists():
        repo_names = _literal_keys_by_name(repository_path)
        model_class_by_name = repo_names.get("MODEL_CLASS_BY_NAME", set())
        for model_name in declared_model_names:
            if model_name not in model_class_by_name:
                errors.append(
                    f"{model_name}: not registered in MODEL_CLASS_BY_NAME "
                    f"({repository_path.name}); generic CRUD cannot find this model"
                )

    if service_path.exists():
        service_names = _literal_keys_by_name(service_path)
        access_controlled = service_names.get("ACCESS_CONTROLLED_MODELS", set())
        read_only = service_names.get("READ_ONLY_MODELS", set())
        has_custom_graphql = (domain_dir / "graphql").is_dir()
        for model_name in declared_model_names:
            if model_name in access_controlled or model_name in read_only:
                continue
            if has_custom_graphql:
                warnings.append(
                    f"{model_name}: not in ACCESS_CONTROLLED_MODELS ({service_path.name}); "
                    f"confirm the domain's custom GraphQL enforces the same "
                    f"'{model_name}.<action>' permission on every query/mutation, "
                    f"since the generic API leaves it unchecked"
                )
            else:
                warnings.append(
                    f"{model_name}: not in ACCESS_CONTROLLED_MODELS ({service_path.name}) and "
                    f"the domain has no custom graphql/ directory; any authenticated user can "
                    f"create/update/delete this model through the generic API with no "
                    f"permission check"
                )

    if setup_path.exists() and domain_name != "system":
        setup_source = setup_path.read_text(encoding="utf-8")
        const_match = re.search(
            r'(\w+_DATA_DIR)\s*=\s*BACKEND_DIR\s*/\s*"app"\s*/\s*"domains"\s*/\s*"'
            + re.escape(domain_name) + r'"\s*/\s*"data"',
            setup_source,
        )
        if const_match is None:
            errors.append(
                f"{domain_name}: no '<NAME>_DATA_DIR' constant for this domain in "
                f"{setup_path.name}; fresh setup cannot load its model/schema JSON"
            )
        else:
            sources_match = re.search(
                r"MODEL_DATA_SOURCES\s*=\s*\((.*?)\n\)", setup_source, re.DOTALL
            )
            block = sources_match.group(1) if sources_match else ""
            if not re.search(rf"\b{re.escape(const_match.group(1))}\b", block):
                errors.append(
                    f"{domain_name}: {const_match.group(1)} is defined but missing from "
                    f"MODEL_DATA_SOURCES in {setup_path.name}; fresh setup cannot load its "
                    f"model/schema JSON"
                )


def _check_bilingual(node, path: str, errors: list[str]) -> None:
    if isinstance(node, dict):
        if "es_MX" in node or "en_US" in node:
            missing = [lang for lang in ("es_MX", "en_US") if not node.get(lang)]
            if missing:
                errors.append(f"{path}: missing/empty {' and '.join(missing)}")
        for key, value in node.items():
            _check_bilingual(value, f"{path}.{key}", errors)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _check_bilingual(item, f"{path}[{index}]", errors)


def audit_bilingual(models, schemas, access, errors) -> None:
    _check_bilingual(models, "models", errors)
    _check_bilingual(schemas, "schemas", errors)
    _check_bilingual(access, "access_control", errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", type=Path, help="Path to backend/app/domains/<domain>")
    args = parser.parse_args()
    domain_dir = args.domain.resolve()
    data_dir = domain_dir / "data"
    models_path = source_file(data_dir, "system_models.json", "system_model.json")
    schemas_path = source_file(data_dir, "system_model_schemas.json", "system_model_schema.json")
    access_path = data_dir / "access_control.json"
    errors: list[str] = []

    try:
        models = load_json(models_path)
        schemas = load_json(schemas_path)
        access = load_json(access_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not isinstance(models, list) or not isinstance(schemas, list) or not isinstance(access, dict):
        print("ERROR: invalid top-level JSON types", file=sys.stderr)
        return 2

    warnings: list[str] = []
    audit_models(models, errors)
    audit_schemas(models, schemas, errors)
    audit_access(access, errors)
    audit_bilingual(models, schemas, access, errors)
    audit_generic_registration(domain_dir, models, errors, warnings)

    if warnings:
        print(f"Domain audit found {len(warnings)} warning(s) to review:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)

    if errors:
        print(f"Domain audit failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Domain audit passed: {domain_dir.name} "
        f"({len(models)} models, {len(schemas)} schemas, "
        f"{len(access.get('roles') or [])} roles)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
