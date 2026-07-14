"""require user type when creating users

Revision ID: 8c25f91d6a44
Revises: d4c1a7e93b20
"""

from alembic import op

revision = "8c25f91d6a44"
down_revision = "d4c1a7e93b20"
branch_labels = None
depends_on = None


def _update(required: bool, readonly: bool):
    op.execute(f"""
        UPDATE system_model_fields AS field
        SET required = {str(required).lower()}, readonly = {str(readonly).lower()}
        FROM system_models AS model
        WHERE field.model_id = model.id
          AND model.name = 'user.user'
          AND field.name = 'user_type'
    """)
    op.execute(f"""
        UPDATE system_model_schemas AS schema
        SET view = (
            SELECT jsonb_agg(
                CASE WHEN element->>'name' = 'user_type'
                    THEN jsonb_set(element, '{{form,required}}', '{str(required).lower()}'::jsonb, true)
                    ELSE element
                END
            )
            FROM jsonb_array_elements(schema.view) AS element
        )
        FROM system_models AS model
        WHERE schema.model_id = model.id
          AND model.name = 'user.user'
          AND jsonb_typeof(schema.view) = 'array'
    """)


def upgrade():
    _update(required=True, readonly=False)


def downgrade():
    _update(required=False, readonly=True)
