"""${message}

Revision ${up_revision}, created ${create_date}.
Tables hold one JSON document per row: change them with ``from backend.core import migration_ops as ops``
(feature_table, create_document_table, update_documents, rename_table, drop_table). Never import feature models here:
they change later, and a revision must keep working on the data as it was.
"""

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
