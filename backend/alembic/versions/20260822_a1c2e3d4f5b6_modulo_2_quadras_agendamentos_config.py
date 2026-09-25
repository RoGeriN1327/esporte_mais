from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1c2e3d4f5b6'
down_revision: Union[str, None] = '736082b76710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_quadra = postgresql.ENUM('Ativa', 'Desativada', name='status_quadra', create_type=False)
status_agendamento = postgresql.ENUM(
    'Confirmado', 'Cancelado', 'Concluído', 'Renovado',
    name='status_agendamento', create_type=False,
)

def upgrade() -> None:
    bind = op.get_bind()
    status_quadra.create(bind, checkfirst=True)
    status_agendamento.create(bind, checkfirst=True)

    op.create_table('quadra',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('descricao', sa.Text(), nullable=False),
    sa.Column('endereco', sa.String(length=255), nullable=False),
    sa.Column('bairro', sa.String(length=100), nullable=False),
    sa.Column('esporte', sa.String(length=50), nullable=False),
    sa.Column('status', status_quadra, server_default='Ativa', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quadra'))
    )

    op.create_table('quadra_faixa_horaria',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_quadra', sa.Integer(), nullable=False),
    sa.Column('dia_semana', sa.SmallInteger(), nullable=False),
    sa.Column('hora_inicio', sa.Time(), nullable=False),
    sa.Column('hora_fim', sa.Time(), nullable=False),
    sa.CheckConstraint('dia_semana BETWEEN 0 AND 6', name=op.f('ck_quadra_faixa_horaria_dia_semana_valido')),
    sa.CheckConstraint('hora_fim > hora_inicio', name=op.f('ck_quadra_faixa_horaria_horas_validas')),
    sa.ForeignKeyConstraint(['id_quadra'], ['quadra.id'], name=op.f('fk_quadra_faixa_horaria_id_quadra_quadra'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quadra_faixa_horaria'))
    )
    op.create_index('ix_quadra_faixa_horaria_id_quadra', 'quadra_faixa_horaria', ['id_quadra'], unique=False)

    op.create_table('agendamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_usuario', sa.Integer(), nullable=False),
    sa.Column('id_quadra', sa.Integer(), nullable=False),
    sa.Column('id_admin_responsavel', sa.Integer(), nullable=True),
    sa.Column('data_hora_inicio', sa.DateTime(timezone=True), nullable=False),
    sa.Column('data_hora_fim', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', status_agendamento, server_default='Confirmado', nullable=False),
    sa.Column('data_criacao', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['id_usuario'], ['usuario_pessoa.id'], name=op.f('fk_agendamento_id_usuario_usuario_pessoa')),
    sa.ForeignKeyConstraint(['id_quadra'], ['quadra.id'], name=op.f('fk_agendamento_id_quadra_quadra')),
    sa.ForeignKeyConstraint(['id_admin_responsavel'], ['usuario_administrativo.id'], name=op.f('fk_agendamento_id_admin_responsavel_usuario_administrativo')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_agendamento'))
    )
    op.create_index('ix_agendamento_id_usuario', 'agendamento', ['id_usuario'], unique=False)
    op.create_index('ix_agendamento_id_quadra_inicio', 'agendamento', ['id_quadra', 'data_hora_inicio'], unique=False)
    op.create_index(
        'uq_agendamento_quadra_horario_confirmado', 'agendamento',
        ['id_quadra', 'data_hora_inicio'], unique=True,
        postgresql_where=sa.text("status = 'Confirmado'"),
    )
    op.create_index(
        'uq_agendamento_usuario_confirmado', 'agendamento',
        ['id_usuario'], unique=True,
        postgresql_where=sa.text("status = 'Confirmado'"),
    )

    op.create_table('configuracao',
    sa.Column('chave', sa.String(length=64), nullable=False),
    sa.Column('valor', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('chave', name=op.f('pk_configuracao'))
    )

    op.execute(
        "INSERT INTO configuracao (chave, valor) "
        "VALUES ('cancelamento_antecedencia_minima_horas', '2')"
    )

def downgrade() -> None:
    op.drop_table('configuracao')
    op.drop_index('uq_agendamento_usuario_confirmado', table_name='agendamento')
    op.drop_index('uq_agendamento_quadra_horario_confirmado', table_name='agendamento')
    op.drop_index('ix_agendamento_id_quadra_inicio', table_name='agendamento')
    op.drop_index('ix_agendamento_id_usuario', table_name='agendamento')
    op.drop_table('agendamento')
    op.drop_index('ix_quadra_faixa_horaria_id_quadra', table_name='quadra_faixa_horaria')
    op.drop_table('quadra_faixa_horaria')
    op.drop_table('quadra')

    bind = op.get_bind()
    status_agendamento.drop(bind, checkfirst=True)
    status_quadra.drop(bind, checkfirst=True)
