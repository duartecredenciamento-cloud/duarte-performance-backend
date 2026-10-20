"""Baseline de compatibilidade: valida schema existente sem alterações.

Esta revisão intencionalmente não executa DDL. O banco anexado e o banco
Railway não foram identificados como o mesmo schema SQLAlchemy; nenhuma
migração automática segura pode ser inferida a partir deles.
"""
revision = '20261020_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
