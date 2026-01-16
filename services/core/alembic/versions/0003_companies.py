"""0003_companies

Revision ID: 0003_companies
Revises: 0002_contacts
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_companies"
down_revision = "0002_contacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("company_id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("domain", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_companies_tenant_id", "companies", ["tenant_id"])
    op.create_index("ix_companies_tenant_created", "companies", ["tenant_id", "created_at"])

    # add company_id -> contacts
    op.add_column("contacts", sa.Column("company_id", sa.String(length=64), nullable=True))
    op.create_index("ix_contacts_tenant_company", "contacts", ["tenant_id", "company_id"])

    op.create_foreign_key(
        "fk_contacts_company_id",
        "contacts",
        "companies",
        ["company_id"],
        ["company_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_contacts_company_id", "contacts", type_="foreignkey")
    op.drop_index("ix_contacts_tenant_company", table_name="contacts")
    op.drop_column("contacts", "company_id")

    op.drop_index("ix_companies_tenant_created", table_name="companies")
    op.drop_index("ix_companies_tenant_id", table_name="companies")
    op.drop_table("companies")
