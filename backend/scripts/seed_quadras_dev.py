"""Cadastra quadras de exemplo para testar o sistema localmente (NÃO usar em produção).

Uso (com os containers no ar):
    docker compose exec backend python -m scripts.seed_quadras_dev
"""

from datetime import time

from app.core.database import SessionLocal
from app.models import Quadra, QuadraFaixaHoraria

QUADRAS_DEV = [
    {
        "nome": "Quadra Central",
        "descricao": "Quadra poliesportiva coberta do centro.",
        "endereco": "Rua Rio Verde, 100",
        "bairro": "Centro",
        "esporte": "Futsal",
        "faixas": [(dia, time(8, 0), time(22, 0)) for dia in range(7)],
    },
    {
        "nome": "Quadra Central",
        "descricao": "Quadra poliesportiva coberta do centro.",
        "endereco": "Rua Rio Verde, 100",
        "bairro": "Centro",
        "esporte": "Basquete",
        "faixas": [(dia, time(8, 0), time(22, 0)) for dia in range(7)],
    },
    {
        "nome": "Arena Popular",
        "descricao": "Quadra de areia do parque municipal.",
        "endereco": "Av. dos Esportes, 500",
        "bairro": "Jardim América",
        "esporte": "Vôlei",
        "faixas": [(dia, time(7, 0), time(21, 0)) for dia in range(5)],
    },
]


def main() -> None:
    with SessionLocal() as db:
        for dados in QUADRAS_DEV:
            existente = (
                db.query(Quadra).filter_by(nome=dados["nome"], esporte=dados["esporte"]).first()
            )
            if existente is not None:
                print(f'Quadra "{dados["nome"]}" ({dados["esporte"]}) ja existe; pulando.')
                continue
            quadra = Quadra(
                nome=dados["nome"],
                descricao=dados["descricao"],
                endereco=dados["endereco"],
                bairro=dados["bairro"],
                esporte=dados["esporte"],
            )
            quadra.faixas_horarias = [
                QuadraFaixaHoraria(dia_semana=dia, hora_inicio=inicio, hora_fim=fim)
                for dia, inicio, fim in dados["faixas"]
            ]
            db.add(quadra)
            print(f'Quadra "{dados["nome"]}" ({dados["esporte"]}) criada.')
        db.commit()


if __name__ == "__main__":
    main()
