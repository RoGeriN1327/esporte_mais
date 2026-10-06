"""Limite de requisições por IP (slowapi).

Em produção a API fica atrás da Cloudflare + proxy do Render. O X-Forwarded-For
não serve para identificar o cliente: o proxy do Render não descarta o valor
enviado pelo próprio cliente, só acrescenta o dele, então um atacante trocaria de
"IP" a cada requisição e nunca seria limitado. O CF-Connecting-IP é sempre
reescrito pela Cloudflare com o IP real de quem conectou. Fora da Cloudflare
(desenvolvimento, testes) o cabeçalho não existe e vale o IP da conexão.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

CABECALHO_IP_CLOUDFLARE = "cf-connecting-ip"


def ip_do_cliente(request: Request) -> str:
    return request.headers.get(CABECALHO_IP_CLOUDFLARE) or get_remote_address(request)


limiter = Limiter(key_func=ip_do_cliente)
