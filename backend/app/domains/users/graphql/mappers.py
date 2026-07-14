from app.domains.users.graphql.types import UserLogType


def user_log_to_type(log):
    return UserLogType(
        uuid=log.uuid,
        status=log.status,
        start_date=log.start_date,
        last_seen_at=log.last_seen_at,
        end_date=log.end_date,
        duration=log.duration,
        created_at=log.created_at,
    )
