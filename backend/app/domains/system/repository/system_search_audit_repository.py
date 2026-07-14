from datetime import datetime

from sqlalchemy import delete

from app.core.database.session import db
from app.domains.system.models.system_search_audit import SystemSearchAudit


class SystemSearchAuditRepository:
    @staticmethod
    async def create_and_purge(
        audit: SystemSearchAudit, *, older_than: datetime
    ) -> SystemSearchAudit:
        async with db.session() as session:
            await session.execute(
                delete(SystemSearchAudit).where(
                    SystemSearchAudit.created_at < older_than
                )
            )
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            return audit
