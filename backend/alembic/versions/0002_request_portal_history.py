"""Track portal-scoped deals and inactive request history.

Revision ID: 0002_request_history
Revises: 0001_bootstrap
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_request_history"
down_revision = "0001_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("procurement_requests")}
    if "bitrix_portal_url" not in columns:
        op.add_column("procurement_requests", sa.Column("bitrix_portal_url", sa.String(length=255), nullable=True))
        op.execute(sa.text("UPDATE procurement_requests SET bitrix_portal_url = 'legacy' WHERE bitrix_portal_url IS NULL"))
        if dialect == "sqlite":
            with op.batch_alter_table("procurement_requests") as batch_op:
                batch_op.alter_column("bitrix_portal_url", nullable=False, server_default="legacy")
        else:
            op.alter_column("procurement_requests", "bitrix_portal_url", nullable=False, server_default="legacy")
    if "is_active" not in columns:
        op.add_column(
            "procurement_requests",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    inspector = sa.inspect(op.get_bind())
    for index in inspector.get_indexes("procurement_requests"):
        if index.get("unique") and index.get("column_names") == ["bitrix_deal_id"]:
            op.drop_index(index["name"], table_name="procurement_requests")

    constraints = sa.inspect(op.get_bind()).get_unique_constraints("procurement_requests")
    for constraint in constraints:
        if constraint.get("column_names") == ["bitrix_deal_id"] and constraint.get("name"):
            if dialect == "sqlite":
                with op.batch_alter_table("procurement_requests") as batch_op:
                    batch_op.drop_constraint(constraint["name"], type_="unique")
            else:
                op.drop_constraint(constraint["name"], "procurement_requests", type_="unique")

    constraints = sa.inspect(op.get_bind()).get_unique_constraints("procurement_requests")
    has_portal_constraint = any(
        set(constraint.get("column_names") or []) == {"bitrix_portal_url", "bitrix_deal_id"}
        for constraint in constraints
    )
    if not has_portal_constraint:
        if dialect == "sqlite":
            with op.batch_alter_table("procurement_requests") as batch_op:
                batch_op.create_unique_constraint(
                    "uq_portal_bitrix_deal",
                    ["bitrix_portal_url", "bitrix_deal_id"],
                )
        else:
            op.create_unique_constraint(
                "uq_portal_bitrix_deal",
                "procurement_requests",
                ["bitrix_portal_url", "bitrix_deal_id"],
            )

    active_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("procurement_requests")}
    if "ix_procurement_requests_is_active" not in active_indexes:
        op.create_index("ix_procurement_requests_is_active", "procurement_requests", ["is_active"])

    ensure_unique_constraint(
        "request_factories",
        "uq_request_factory",
        ["procurement_request_id", "factory_id"],
    )
    ensure_unique_constraint(
        "factory_order_numbers",
        "uq_request_factory_order_number",
        ["request_factory_id", "order_number"],
    )


def ensure_unique_constraint(table_name: str, name: str, columns: list[str]) -> None:
    inspector = sa.inspect(op.get_bind())
    constraints = inspector.get_unique_constraints(table_name)
    if any(set(constraint.get("column_names") or []) == set(columns) for constraint in constraints):
        return
    quoted_columns = ", ".join(columns)
    duplicate = op.get_bind().execute(sa.text(
        f"SELECT 1 FROM {table_name} GROUP BY {quoted_columns} HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError(f"Resolve duplicate records in {table_name} before applying {name}")
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.create_unique_constraint(name, columns)
    else:
        op.create_unique_constraint(name, table_name, columns)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    for table_name, constraint_name in [
        ("factory_order_numbers", "uq_request_factory_order_number"),
        ("request_factories", "uq_request_factory"),
    ]:
        constraints = sa.inspect(op.get_bind()).get_unique_constraints(table_name)
        if any(constraint.get("name") == constraint_name for constraint in constraints):
            if dialect == "sqlite":
                with op.batch_alter_table(table_name) as batch_op:
                    batch_op.drop_constraint(constraint_name, type_="unique")
            else:
                op.drop_constraint(constraint_name, table_name, type_="unique")

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("procurement_requests")}
    if "ix_procurement_requests_is_active" in indexes:
        op.drop_index("ix_procurement_requests_is_active", table_name="procurement_requests")
    if dialect == "sqlite":
        with op.batch_alter_table("procurement_requests") as batch_op:
            batch_op.drop_constraint("uq_portal_bitrix_deal", type_="unique")
            batch_op.drop_column("is_active")
            batch_op.drop_column("bitrix_portal_url")
    else:
        op.drop_constraint("uq_portal_bitrix_deal", "procurement_requests", type_="unique")
        op.drop_column("procurement_requests", "is_active")
        op.drop_column("procurement_requests", "bitrix_portal_url")
