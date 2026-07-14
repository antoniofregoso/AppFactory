from typing import Any

from app.core.database.session import db


class SearchQueryRepository:
    @staticmethod
    async def execute(statement: Any) -> list[Any]:
        async with db.session() as session:
            result = await session.execute(statement)
            return list(result.scalars().unique().all())
