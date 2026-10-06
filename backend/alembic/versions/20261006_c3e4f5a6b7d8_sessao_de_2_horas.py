"""Sessão de 2 horas: encerra as sessões abertas com a regra antiga (7 dias).

Os refresh tokens emitidos antes desta versão valiam 7 dias e a renovação
herda o prazo do token renovado, então essas sessões continuariam longas.
Revogá-las obriga um novo login, que já segue a regra de 2 horas.

Revision ID: c3e4f5a6b7d8
Revises: b2d3e4f5a6c7
Create Date: 2026-10-06
"""

from typing import Sequence, Union

from alembic import op

revision: str = 'c3e4f5a6b7d8'
down_revision: Union[str, None] = 'b2d3e4f5a6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE refresh_token SET revogado_em = now() WHERE revogado_em IS NULL")


def downgrade() -> None:
    # Sessões revogadas não são restauradas.
    pass
