from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2d3e4f5a6c7'
down_revision: Union[str, None] = 'a1c2e3d4f5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('notificacao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('destinatario', sa.String(length=255), nullable=False),
    sa.Column('assunto', sa.String(length=255), nullable=False),
    sa.Column('evento', sa.String(length=50), nullable=False),
    sa.Column('sucesso', sa.Boolean(), nullable=False),
    sa.Column('enviado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notificacao'))
    )
    op.create_index('ix_notificacao_destinatario', 'notificacao', ['destinatario'], unique=False)

    op.add_column('agendamento', sa.Column('lembrete_enviado_em', sa.DateTime(timezone=True), nullable=True))

    op.execute(
        "INSERT INTO configuracao (chave, valor) VALUES ('lembrete_antecedencia_horas', '24') "
        "ON CONFLICT (chave) DO NOTHING"
    )

def downgrade() -> None:
    op.execute("DELETE FROM configuracao WHERE chave = 'lembrete_antecedencia_horas'")
    op.drop_column('agendamento', 'lembrete_enviado_em')
    op.drop_index('ix_notificacao_destinatario', table_name='notificacao')
    op.drop_table('notificacao')
