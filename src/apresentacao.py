"""Textos e tabelas do resultado, separados da interface Streamlit.

Não apresenta uma heurística como prova de inexistência ou de otimalidade.
Os testes desta camada podem ser executados sem interface gráfica.
"""
from __future__ import annotations

import math
import pandas as pd

ROTULOS_MODOS = {
    "caminho": "Caminho hamiltoniano",
    "ciclo": "Ciclo hamiltoniano",
    "minimo": "Ciclo hamiltoniano mínimo",
}


def nome_algoritmo(chave: str) -> str:
    return "Backtracking com poda" if chave == "Exato" else "Vizinho mais próximo (2-opt opcional)"


def status_resultado(r: dict) -> str:
    if r["otimo_comprovado"]:
        return "Ótimo comprovado"
    if r["ausencia_comprovada"]:
        return "Inexistência comprovada"
    if r["rota"] and r["metodo"] == "Exato" and r["modo"] != "minimo":
        return "Existência comprovada"
    if r["rota"] and r["timeout"]:
        return "Solução válida; busca interrompida"
    if r["rota"]:
        return "Solução válida"
    if r["timeout"]:
        return "Busca inconclusiva"
    return "Não encontrou solução"


def explicar_resultado(r: dict, total_pontos: int) -> str:
    """Explicação gerada SOMENTE a partir de dados realmente computados."""
    modo = r["modo"]
    caminho = modo == "caminho"
    trecho = "visita todos os vértices uma única vez a partir da base" if caminho else (
        "visita todos os vértices uma única vez e retorna à base"
    )
    nome = nome_algoritmo(r["metodo"])
    motivo = (r.get("aviso") or "").strip()
    if r["rota"]:
        texto = (f"O {nome} encontrou uma solução válida com {total_pontos} vértices: "
                 f"o percurso {trecho}. Distância no grafo: {r['km']:.2f} km; "
                 f"tempo do algoritmo: {r['tempo_ms']:.2f} ms.")
        if r["otimo_comprovado"]:
            return texto + " A busca exata terminou e comprovou que não existe outro ciclo de menor custo neste grafo."
        if r["metodo"] == "Heuristica":
            return texto + " É um percurso obtido por heurística; não há garantia de que seja o de menor custo."
        if r["timeout"]:
            return texto + " O tempo limite foi atingido; a busca não comprovou que este custo é ótimo."
        if modo == "minimo":
            return texto + " O menor custo não foi comprovado."
        return texto + " A existência do caminho/ciclo está comprovada, mas não foi pesquisado o menor custo."
    if r["ausencia_comprovada"]:
        retorno = (f"A busca exata foi concluída e comprovou que não existe "
                   f"{ROTULOS_MODOS[modo].lower()} com as ligações e restrições atuais.")
        return f"{retorno} Diagnóstico: {motivo}" if motivo else retorno
    if r["timeout"]:
        return (f"O {nome} atingiu o tempo limite sem encontrar uma solução. O resultado é "
                "inconclusivo: não é possível afirmar que um caminho/ciclo hamiltoniano não exista.")
    texto = (f"O {nome} não encontrou uma solução para as ligações e restrições selecionadas. "
             "Isso não comprova a inexistência de caminho/ciclo hamiltoniano, pois a busca heurística não é exaustiva.")
    return f"{texto} Detalhe: {motivo}" if motivo else texto


def comparar_interpretacao(resultados: dict, modo: str) -> str:
    if "Exato" not in resultados or "Heuristica" not in resultados:
        return "A comparação entre os algoritmos aparece quando ambos são executados."
    e, h = resultados["Exato"], resultados["Heuristica"]
    if e["km"] is None and h["km"] is None:
        if e["ausencia_comprovada"]:
            return "A busca exata comprovou a inexistência de solução. A heurística também não encontrou uma rota."
        return "Nenhum método encontrou uma rota; sem conclusão exata, a inexistência não pode ser afirmada."
    if e["km"] is None or h["km"] is None:
        if e["km"] is not None:
            return ("A busca exata encontrou uma solução válida, mas a heurística não. "
                    "O insucesso da heurística não comprova que um percurso inexista.")
        return ("A heurística encontrou uma solução válida, enquanto a busca exata não apresentou rota. "
                "Se o backtracking parou por tempo, a busca ficou inconclusiva; a heurística não garante ótimo.")
    variacao = h["km"] - e["km"]
    percentual = 100 * variacao / e["km"] if e["km"] else 0.0
    rapidez = ("heurística" if h["tempo_ms"] < e["tempo_ms"] else
               "exata" if e["tempo_ms"] < h["tempo_ms"] else "ambas, com tempo semelhante")
    texto = (f"Custo do backtracking: {e['km']:.2f} km. "
             f"Custo da heurística: {h['km']:.2f} km. "
             f"Diferença (heurística − exato): {variacao:+.2f} km ({percentual:+.2f}%). "
             f"Nesta execução, a busca mais rápida foi a {rapidez}.")
    if modo == "minimo" and e["otimo_comprovado"]:
        return texto + " O custo do backtracking é ótimo comprovado, portanto a diferença representa o desvio da heurística em relação ao ótimo."
    return texto + " Não se pode interpretar essa diferença como desvio do ótimo sem uma prova de otimalidade."


def tabela_etapas(df: pd.DataFrame, rota: list[int], matriz) -> pd.DataFrame:
    registros = []
    for pos, vertice in enumerate(rota):
        proximo = rota[pos + 1] if pos < len(rota) - 1 else None
        registros.append({
            "Etapa": pos + 1,
            "Vértice": int(vertice),
            "Local": str(df.iloc[vertice]["nome"]),
            "Próximo trecho (km)": round(float(matriz[vertice][proximo]), 2) if proximo is not None else None,
        })
    return pd.DataFrame(registros)


def melhor_resultado(resultados: dict):
    validos = [(k, r) for k, r in resultados.items() if r.get("rota") and r.get("km") is not None]
    return min(validos, key=lambda par: par[1]["km"]) if validos else (None, None)


def tabela_resultados(resultados: dict) -> pd.DataFrame:
    return pd.DataFrame([{
        "Algoritmo": nome_algoritmo(k),
        "Distância (km)": round(r["km"], 2) if r["km"] is not None else None,
        "Tempo (ms)": round(r["tempo_ms"], 2),
        "Situação": status_resultado(r),
        "Nós explorados": r["nos"] if k == "Exato" else None,
        "Podas": r["podas"] if k == "Exato" else None,
    } for k, r in resultados.items()])
