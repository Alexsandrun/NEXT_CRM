"""0002_contacts

Revision ID: 0002_contacts
Revises: 0001_init
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_contacts"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("contact_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_contacts_tenant_id", "contacts", ["tenant_id"])
    op.create_index("ix_contacts_tenant_created", "contacts", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_contacts_tenant_created", table_name="contacts")
    op.drop_index("ix_contacts_tenant_id", table_name="contacts")
    op.drop_table("contacts")
