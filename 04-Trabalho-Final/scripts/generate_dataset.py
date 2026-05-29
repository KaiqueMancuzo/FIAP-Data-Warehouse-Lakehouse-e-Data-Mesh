#!/usr/bin/env python3
"""
generate_dataset.py — gera os 3 CSVs sinteticos do trabalho final.

O QUE FAZ
=========
Gera (deterministicamente, seed=42) tres arquivos CSV:
  customers.csv     — 10.000 linhas
  orders.csv        — 100.000 linhas
  delta_orders.csv  — 5 linhas (3 inserts + 2 updates)

POR QUE DETERMINISTICO
======================
Todo aluno que rodar o script obtem os MESMOS dados — entao a query final
"top 5 clientes" devolve as MESMAS 5 linhas em qualquer turma. Isso permite
correcao automatica e comparacao entre alunos (compare md5sum com o colega:
se diferir, alguem rodou em ambiente quebrado).

USO
===
    python3 generate_dataset.py <output_dir>

Ex:
    python3 generate_dataset.py /tmp/dataset

REQUISITOS
==========
Python 3.10+. Sem dependencias externas (apenas stdlib).
"""

import argparse
import csv
import hashlib
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes deterministas — ordem importa! Listas (nao set/dict) para
# garantir reprodutibilidade entre execucoes e versoes do Python.
# ---------------------------------------------------------------------------

SEED = 42

N_CUSTOMERS = 10_000
N_ORDERS = 100_000

# 50 nomes proprios brasileiros comuns (lista ordenada — nao mexer)
NOMES = [
    "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela",
    "Henrique", "Isabela", "Joao", "Karina", "Leonardo", "Mariana",
    "Nelson", "Olivia", "Patricia", "Rafael", "Sabrina", "Thiago",
    "Ursula", "Vinicius", "Wagner", "Yasmin", "Adriana", "Beatriz",
    "Caio", "Debora", "Eduardo", "Fernanda", "Gustavo", "Heloisa",
    "Igor", "Juliana", "Kelvin", "Larissa", "Marcelo", "Natalia",
    "Otavio", "Paula", "Renato", "Silvia", "Tatiana", "Ulisses",
    "Vanessa", "Wellington", "Xavier", "Yago", "Zilda", "Andre",
    "Bianca",
]

# 50 sobrenomes brasileiros comuns
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
    "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins",
    "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira",
    "Barbosa", "Rocha", "Dias", "Nunes", "Mendes", "Moreira", "Cardoso",
    "Teixeira", "Correia", "Cavalcanti", "Pinto", "Ramos", "Araujo",
    "Monteiro", "Castro", "Andrade", "Cunha", "Freitas", "Morais",
    "Borges", "Reis", "Macedo", "Tavares", "Marques", "Pires", "Pacheco",
    "Moura", "Coelho", "Sampaio", "Brito", "Aragao",
]

# 27 capitais brasileiras (cidade, UF) — ordem fixa pela UF para estabilidade
CAPITAIS = [
    ("Rio Branco", "AC"),
    ("Maceio", "AL"),
    ("Macapa", "AP"),
    ("Manaus", "AM"),
    ("Salvador", "BA"),
    ("Fortaleza", "CE"),
    ("Brasilia", "DF"),
    ("Vitoria", "ES"),
    ("Goiania", "GO"),
    ("Sao Luis", "MA"),
    ("Cuiaba", "MT"),
    ("Campo Grande", "MS"),
    ("Belo Horizonte", "MG"),
    ("Belem", "PA"),
    ("Joao Pessoa", "PB"),
    ("Curitiba", "PR"),
    ("Recife", "PE"),
    ("Teresina", "PI"),
    ("Rio de Janeiro", "RJ"),
    ("Natal", "RN"),
    ("Porto Alegre", "RS"),
    ("Porto Velho", "RO"),
    ("Boa Vista", "RR"),
    ("Florianopolis", "SC"),
    ("Sao Paulo", "SP"),
    ("Aracaju", "SE"),
    ("Palmas", "TO"),
]

SEGMENTOS = ["VAREJO", "CORPORATIVO", "PME", "GOVERNO", "EDUCACAO"]

CATEGORIAS = [
    "ELETRONICOS", "MODA", "LIVROS", "CASA",
    "ESPORTE", "BELEZA", "ALIMENTOS",
]

# Faixa de datas para os pedidos (inclusive nos dois extremos).
# 2023-01-01 ate 2024-12-31 = 731 dias.
ORDER_DATE_START_ORDINAL = 738521  # date(2023, 1, 1).toordinal()
ORDER_DATE_END_ORDINAL = 739251    # date(2024, 12, 31).toordinal()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def md5_of_file(path: Path) -> str:
    """MD5 hexdigest de um arquivo, lido em chunks (defensivo, mesmo que
    nossos CSVs caibam tranquilamente em memoria)."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ordinal_to_iso(ordinal: int) -> str:
    """Converte um ordinal (date.toordinal()) para 'YYYY-MM-DD' sem usar
    objetos date — implementacao estavel entre versoes Python."""
    from datetime import date  # import local: usado so aqui
    return date.fromordinal(ordinal).isoformat()


# ---------------------------------------------------------------------------
# Geracao dos datasets
# ---------------------------------------------------------------------------

def gerar_customers(rng: random.Random) -> list[dict]:
    """Gera 10.000 clientes deterministicamente.

    Cada customer_id segue o formato C00001 .. C10000 (sequencial, nao
    aleatorio — facilita debug e a query do trabalho final).

    A coluna birth_year (INT, 1950..2005) existe por dois motivos:
      1. Garante que a 1a linha do CSV (cabecalho) tem coluna numerica,
         o que faz o Glue Crawler detectar header automaticamente sem
         precisar de classifier customizado.
      2. Enriquece a query executiva (idade media do top 5).
    A ordem de chamadas rng.choice(...) NAO mudou; o randint do
    birth_year e adicionado depois do sobrenome para nao quebrar o
    pareto (que depende do customer_id permanecer C00001..C10000)."""
    customers = []
    for i in range(1, N_CUSTOMERS + 1):
        cidade, uf = rng.choice(CAPITAIS)
        # ATENCAO: a ordem dos rng.* importa para reprodutibilidade.
        # Mantemos cidade/uf primeiro (mesma posicao da v1), depois
        # nome/sobrenome/birth_year/segmento. birth_year e gerado
        # APOS sobrenome para que o ano nao "consuma" o estado do rng
        # antes do cidade/uf — preservando pareto.
        nome = rng.choice(NOMES)
        sobrenome = rng.choice(SOBRENOMES)
        birth_year = rng.randint(1950, 2005)
        segmento = rng.choice(SEGMENTOS)
        customers.append({
            "customer_id": f"C{i:05d}",
            "nome": nome,
            "sobrenome": sobrenome,
            "birth_year": birth_year,
            "cidade": cidade,
            "estado": uf,
            "segmento": segmento,
        })
    return customers


def construir_pesos_pareto(rng: random.Random) -> list[float]:
    """Distribui 'peso de compra' entre os 10.000 clientes seguindo curva
    Pareto (alpha=1.16 — regra 80/20 classica). Resultado: ~20% dos
    clientes concentram ~80% dos pedidos. Garante que existem clientes
    'top 5' claramente distintos para a query final.

    Os pesos sao bruto-aleatorios e DEPOIS ordenados por customer_id
    (ou seja, NAO ordenados por peso) — caso contrario o C00001 seria
    sempre o maior comprador, o que daria spoiler do resultado da query.
    """
    pesos = [rng.paretovariate(1.16) for _ in range(N_CUSTOMERS)]
    return pesos


def gerar_orders(rng: random.Random, pesos_clientes: list[float]) -> list[dict]:
    """Gera 100.000 pedidos. Distribuicao de customer_id segue a curva
    Pareto pre-computada — o random.choices ja retorna proporcional ao
    peso, sem necessidade de normalizar."""
    customer_ids = [f"C{i:05d}" for i in range(1, N_CUSTOMERS + 1)]

    # Sorteia todos os customer_ids de uma vez (mais rapido e
    # deterministicamente consistente com o estado do rng).
    sorteados = rng.choices(customer_ids, weights=pesos_clientes, k=N_ORDERS)

    orders = []
    for i in range(1, N_ORDERS + 1):
        cust_id = sorteados[i - 1]
        # Datas: ordinal aleatorio entre os dois limites (inclusivos)
        date_ord = rng.randint(ORDER_DATE_START_ORDINAL, ORDER_DATE_END_ORDINAL)
        order_date = ordinal_to_iso(date_ord)

        quantity = rng.randint(1, 10)
        unit_price = round(rng.uniform(10.00, 1000.00), 2)
        discount = round(rng.uniform(0.00, 0.30), 2)
        freight = round(rng.uniform(5.00, 50.00), 2)

        orders.append({
            "order_id": f"O{i:06d}",
            "customer_id": cust_id,
            "order_date": order_date,
            "product_category": rng.choice(CATEGORIAS),
            "quantity": quantity,
            "unit_price": f"{unit_price:.2f}",
            "discount": f"{discount:.2f}",
            "freight": f"{freight:.2f}",
        })
    return orders


def gerar_delta(orders: list[dict]) -> list[dict]:
    """Gera 5 deltas hardcoded:
      - 3 INSERTs: O100001, O100002, O100003 (ids inexistentes em orders.csv)
      - 2 UPDATEs: usa os order_ids dos 2 PRIMEIROS pedidos de orders.csv,
        com discount aumentado representando ajuste pos-fechamento.

    Totalmente deterministico — nao usa rng. O aluno enxerga este arquivo
    como 'os 5 deltas que vieram do fim do dia'.
    """
    o1 = orders[0]  # primeiro pedido (sera atualizado)
    o2 = orders[1]  # segundo pedido (sera atualizado)

    deltas = [
        # 3 INSERTs — order_ids 100.001 / 002 / 003 (nao existem em orders.csv)
        {
            "order_id": "O100001",
            "customer_id": "C00001",
            "order_date": "2024-12-31",
            "product_category": "ELETRONICOS",
            "quantity": "5",
            "unit_price": "899.90",
            "discount": "0.10",
            "freight": "29.90",
        },
        {
            "order_id": "O100002",
            "customer_id": "C00042",
            "order_date": "2024-12-31",
            "product_category": "MODA",
            "quantity": "3",
            "unit_price": "149.00",
            "discount": "0.05",
            "freight": "15.00",
        },
        {
            "order_id": "O100003",
            "customer_id": "C09999",
            "order_date": "2024-12-31",
            "product_category": "LIVROS",
            "quantity": "2",
            "unit_price": "59.90",
            "discount": "0.00",
            "freight": "12.00",
        },
        # 2 UPDATEs — mesmos order_ids do orders.csv, mas com discount alterado
        {
            "order_id": o1["order_id"],
            "customer_id": o1["customer_id"],
            "order_date": o1["order_date"],
            "product_category": o1["product_category"],
            "quantity": str(o1["quantity"]),
            "unit_price": o1["unit_price"],
            "discount": "0.50",  # ajuste de pos-fechamento
            "freight": o1["freight"],
        },
        {
            "order_id": o2["order_id"],
            "customer_id": o2["customer_id"],
            "order_date": o2["order_date"],
            "product_category": o2["product_category"],
            "quantity": str(o2["quantity"]),
            "unit_price": o2["unit_price"],
            "discount": "0.45",
            "freight": o2["freight"],
        },
    ]
    return deltas


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def escrever_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Escreve CSV utf-8 com cabecalho. Newline='' evita linhas em branco
    extras no Windows; o csv module cuida do line terminator."""
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera os 3 CSVs sinteticos do trabalho final (deterministicos, seed=42).",
    )
    parser.add_argument(
        "output_dir",
        help="Diretorio onde os CSVs serao gravados (sera criado se nao existir).",
    )
    args = parser.parse_args()

    print("[1/5] Validando argumentos e diretorio de saida...")
    out_dir = Path(args.output_dir)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(
            f"ERRO: diretorio {out_dir} nao existe e nao foi possivel criar ({e}).",
            file=sys.stderr,
        )
        return 1
    if not out_dir.is_dir():
        print(f"ERRO: {out_dir} existe mas nao e um diretorio.", file=sys.stderr)
        return 1

    customers_path = out_dir / "customers.csv"
    orders_path = out_dir / "orders.csv"
    delta_path = out_dir / "delta_orders.csv"

    # rng UNICO para todo o processo — cada chamada consome do mesmo
    # estado, mantendo a sequencia reprodutivel.
    rng = random.Random(SEED)

    print(f"[2/5] Gerando customers.csv ({N_CUSTOMERS} linhas, seed={SEED})...")
    customers = gerar_customers(rng)
    escrever_csv(
        customers_path,
        ["customer_id", "nome", "sobrenome", "birth_year", "cidade", "estado", "segmento"],
        customers,
    )

    print(f"[3/5] Gerando orders.csv ({N_ORDERS} linhas, seed={SEED})...")
    pesos = construir_pesos_pareto(rng)
    orders = gerar_orders(rng, pesos)
    escrever_csv(
        orders_path,
        [
            "order_id", "customer_id", "order_date", "product_category",
            "quantity", "unit_price", "discount", "freight",
        ],
        orders,
    )

    print("[4/5] Gerando delta_orders.csv (5 linhas hardcoded)...")
    deltas = gerar_delta(orders)
    escrever_csv(
        delta_path,
        [
            "order_id", "customer_id", "order_date", "product_category",
            "quantity", "unit_price", "discount", "freight",
        ],
        deltas,
    )

    print("[5/5] Calculando md5sum dos arquivos para validar reprodutibilidade...")
    md5_customers = md5_of_file(customers_path)
    md5_orders = md5_of_file(orders_path)
    md5_delta = md5_of_file(delta_path)

    print()
    print(f"OK. Arquivos gerados em {out_dir}:")
    print(f"  customers.csv      ({N_CUSTOMERS} linhas, md5: {md5_customers})")
    print(f"  orders.csv         ({N_ORDERS} linhas, md5: {md5_orders})")
    print(f"  delta_orders.csv   (5 linhas, md5: {md5_delta})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
