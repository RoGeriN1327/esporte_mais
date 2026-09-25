from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '736082b76710'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_usuario = postgresql.ENUM('Ativo', 'Desativado', name='status_usuario', create_type=False)
perfil_administrativo = postgresql.ENUM('Gestor', 'Operador', name='perfil_administrativo', create_type=False)
tipo_usuario = postgresql.ENUM('Pessoa', 'Administrativo', name='tipo_usuario', create_type=False)

def upgrade() -> None:
    bind = op.get_bind()
    status_usuario.create(bind, checkfirst=True)
    perfil_administrativo.create(bind, checkfirst=True)
    tipo_usuario.create(bind, checkfirst=True)

    op.create_table('usuario_pessoa',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('cpf', sa.String(length=11), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('senha', sa.String(length=255), nullable=False),
    sa.Column('status', status_usuario, server_default='Ativo', nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('tentativas_login', sa.Integer(), server_default='0', nullable=False),
    sa.Column('bloqueado_ate', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuario_pessoa')),
    sa.UniqueConstraint('cpf', name=op.f('uq_usuario_pessoa_cpf')),
    sa.UniqueConstraint('email', name=op.f('uq_usuario_pessoa_email'))
    )
    op.create_table('usuario_administrativo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('cpf', sa.String(length=11), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('senha', sa.String(length=255), nullable=False),
    sa.Column('perfil', perfil_administrativo, nullable=False),
    sa.Column('status', status_usuario, server_default='Ativo', nullable=False),
    sa.Column('data_cadastro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('tentativas_login', sa.Integer(), server_default='0', nullable=False),
    sa.Column('bloqueado_ate', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuario_administrativo')),
    sa.UniqueConstraint('cpf', name=op.f('uq_usuario_administrativo_cpf')),
    sa.UniqueConstraint('email', name=op.f('uq_usuario_administrativo_email'))
    )
    op.create_table('refresh_token',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('tipo_usuario', tipo_usuario, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revogado_em', sa.DateTime(timezone=True), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_token')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_refresh_token_token_hash'))
    )
    op.create_index('ix_refresh_token_tipo_usuario_usuario_id', 'refresh_token', ['tipo_usuario', 'usuario_id'], unique=False)
    op.create_table('token_revogado',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jti', sa.String(length=36), nullable=False),
    sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revogado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_token_revogado')),
    sa.UniqueConstraint('jti', name=op.f('uq_token_revogado_jti'))
    )
    op.create_table('token_redefinicao_senha',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('tipo_usuario', tipo_usuario, nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('usado_em', sa.DateTime(timezone=True), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_token_redefinicao_senha')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_token_redefinicao_senha_token_hash'))
    )

def downgrade() -> None:
    op.drop_table('token_redefinicao_senha')
    op.drop_table('token_revogado')
    op.drop_index('ix_refresh_token_tipo_usuario_usuario_id', table_name='refresh_token')
    op.drop_table('refresh_token')
    op.drop_table('usuario_administrativo')
    op.drop_table('usuario_pessoa')

    bind = op.get_bind()
    tipo_usuario.drop(bind, checkfirst=True)
    perfil_administrativo.drop(bind, checkfirst=True)
    status_usuario.drop(bind, checkfirst=True)
