from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import RefreshToken, TipoUsuario, TokenRedefinicaoSenha, TokenRevogado


class TokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def criar_refresh(
        self, *, token_hash: str, tipo_usuario: TipoUsuario, usuario_id: int, expira_em: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            token_hash=token_hash,
            tipo_usuario=tipo_usuario,
            usuario_id=usuario_id,
            expira_em=expira_em,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def obter_refresh_por_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    def revogar_refresh(self, token: RefreshToken) -> None:
        token.revogado_em = datetime.now(UTC)
        self.db.flush()

    def revogar_todos_refresh_do_usuario(self, tipo_usuario: TipoUsuario, usuario_id: int) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.tipo_usuario == tipo_usuario,
                RefreshToken.usuario_id == usuario_id,
                RefreshToken.revogado_em.is_(None),
            )
            .values(revogado_em=datetime.now(UTC))
        )

    def adicionar_jti_na_denylist(self, jti: str, expira_em: datetime) -> None:
        """Invalida um access token antes de ele expirar (usado no logout)."""
        if not self.jti_esta_revogado(jti):
            self.db.add(TokenRevogado(jti=jti, expira_em=expira_em))
            self.db.flush()

    def jti_esta_revogado(self, jti: str) -> bool:
        return self.db.scalar(select(TokenRevogado.id).where(TokenRevogado.jti == jti)) is not None

    def criar_token_redefinicao(
        self, *, token_hash: str, tipo_usuario: TipoUsuario, usuario_id: int, expira_em: datetime
    ) -> TokenRedefinicaoSenha:
        token = TokenRedefinicaoSenha(
            token_hash=token_hash,
            tipo_usuario=tipo_usuario,
            usuario_id=usuario_id,
            expira_em=expira_em,
        )
        self.db.add(token)
        self.db.flush()
        return token

    def obter_token_redefinicao_por_hash(self, token_hash: str) -> TokenRedefinicaoSenha | None:
        return self.db.scalar(
            select(TokenRedefinicaoSenha).where(TokenRedefinicaoSenha.token_hash == token_hash)
        )

    def marcar_token_redefinicao_usado(self, token: TokenRedefinicaoSenha) -> None:
        token.usado_em = datetime.now(UTC)
        self.db.flush()
