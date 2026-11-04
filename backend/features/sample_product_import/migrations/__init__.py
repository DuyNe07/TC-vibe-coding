"""Database migrations of feature "sample_product_import" (Alembic chain, own version table).

Create a table or change stored data: python scripts/migrate.py new sample_product_import "what changes"
then fill upgrade() / downgrade() with backend.core.migration_ops (create_document_table, update_documents...).
python scripts/migrate.py applies them; run.ps1 and the Docker image run it before the app starts.
"""
