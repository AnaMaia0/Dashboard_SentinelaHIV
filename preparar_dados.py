import json
import os
import sys
from datetime import datetime

# ── Caminhos ──────────────────────────────────────────────────────────────────
DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(DIR, "data.json")
OUTPUT_FILE = os.path.join(DIR, "data.js")


def carregar_dados(caminho: str) -> dict:
    """Carrega e valida o arquivo JSON de entrada."""
    if not os.path.exists(caminho):
        print(f"[ERRO] Arquivo não encontrado: {caminho}")
        sys.exit(1)

    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    # Validações mínimas de integridade
    campos_obrigatorios = ["meta", "serie_temporal", "municipios",
                           "perfil_demografico", "categoria_exposicao", "kpis"]
    ausentes = [c for c in campos_obrigatorios if c not in dados]
    if ausentes:
        print(f"[ERRO] Campos obrigatórios ausentes em data.json: {ausentes}")
        sys.exit(1)

    n_anos = len(dados["serie_temporal"]["anos"])
    for municipio, serie in dados["municipios"].items():
        if len(serie) != n_anos:
            print(f"[AVISO] Município '{municipio}' tem {len(serie)} valores "
                  f"mas a série temporal tem {n_anos} anos.")

    return dados


def calcular_totais_municipios(dados: dict) -> dict:
    """Calcula o total acumulado por município e sua participação percentual."""
    total_geral = dados["kpis"]["total_notificacoes"]
    totais = {}
    for municipio, serie in dados["municipios"].items():
        total = sum(serie)
        totais[municipio] = {
            "total": total,
            "participacao_pct": round(total / total_geral * 100, 1)
        }
    # Ordena por total decrescente
    return dict(sorted(totais.items(), key=lambda x: x[1]["total"], reverse=True))


def gerar_sumario(dados: dict) -> dict:
    """Gera um dicionário de sumário para log e validação."""
    serie = dados["serie_temporal"]["notificacoes"]
    anos  = dados["serie_temporal"]["anos"]
    totais_muni = calcular_totais_municipios(dados)

    return {
        "total_notificacoes":    sum(serie),
        "periodo":               f"{min(anos)}–{max(anos)}",
        "municipios":            len(dados["municipios"]),
        "pico_ano":              anos[serie.index(max(serie))],
        "pico_valor":            max(serie),
        "menor_ano":             anos[serie.index(min(serie))],
        "menor_valor":           min(serie),
        "municipio_1":           list(totais_muni.keys())[0],
        "municipio_1_total":     list(totais_muni.values())[0]["total"],
        "municipio_1_pct":       list(totais_muni.values())[0]["participacao_pct"],
    }


def empacotar_js(dados: dict, caminho_saida: str) -> None:
    """Serializa os dados como variável JavaScript e salva em data.js."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cabecalho = f"""\
/*
 * data.js — SentinelaHIV | Baixo Amazonas (2016–2025)
 * Gerado automaticamente por preparar_dados.py em {timestamp}
 *
 * NÃO EDITE MANUALMENTE — edite data.json e execute preparar_dados.py.
 *
 * Fonte: SINAN / DATASUS — Ministério da Saúde
 * Aviso: dados representativos para fins de demonstração acadêmica.
 */

"""

    corpo = "window.SENTINELA_DATA = " + json.dumps(dados, ensure_ascii=False, indent=2) + ";\n"

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(cabecalho + corpo)


def main():
    print("=" * 60)
    print("SentinelaHIV — preparar_dados.py")
    print("=" * 60)

    print(f"\n[1/3] Carregando dados de '{INPUT_FILE}'...")
    dados = carregar_dados(INPUT_FILE)
    print(f"      OK — {dados['kpis']['total_notificacoes']} notificações | "
          f"{len(dados['municipios'])} municípios | "
          f"{len(dados['serie_temporal']['anos'])} anos")

    print("\n[2/3] Validando e calculando totais municipais...")
    sumario = gerar_sumario(dados)
    print(f"      Total consolidado : {sumario['total_notificacoes']}")
    print(f"      Período           : {sumario['periodo']}")
    print(f"      Pico da série     : {sumario['pico_valor']} notificações em {sumario['pico_ano']}")
    print(f"      Mínimo da série   : {sumario['menor_valor']} notificações em {sumario['menor_ano']}")
    print(f"      Maior carga       : {sumario['municipio_1']} "
          f"({sumario['municipio_1_total']} casos / {sumario['municipio_1_pct']}%)")

    print(f"\n[3/3] Empacotando para '{OUTPUT_FILE}'...")
    empacotar_js(dados, OUTPUT_FILE)
    tamanho_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"      OK — {tamanho_kb:.1f} KB gerados")

    print("\n✓ Concluído. Mantenha index.html e data.js na mesma pasta")
    print("  e abra index.html no navegador para visualizar o painel.\n")


if __name__ == "__main__":
    main()