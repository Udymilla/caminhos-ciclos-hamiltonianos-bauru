"""Algoritmos PROPRIOS para caminhos e ciclos hamiltonianos.

Grafo simples, nao direcionado, ponderado, com matriz NxN; infinito significa
aresta ausente. O vertice de partida e 0. Nao usa biblioteca de algoritmos.
"""
from __future__ import annotations
import math
import time
from typing import Sequence

Matriz = Sequence[Sequence[float]]
MODOS = ("caminho", "ciclo", "minimo")


def verificar_matriz(matriz: Matriz) -> None:
    n = len(matriz)
    if n == 0:
        raise ValueError("A matriz deve ter pelo menos um vertice.")
    if any(len(row) != n for row in matriz):
        raise ValueError("A matriz de distancias deve ser quadrada.")
    for i in range(n):
        if not math.isclose(float(matriz[i][i]), 0.0, abs_tol=1e-9):
            raise ValueError("A diagonal da matriz deve ser zero.")
        for j in range(i + 1, n):
            a, b = float(matriz[i][j]), float(matriz[j][i])
            if math.isnan(a) or math.isnan(b) or a < 0 or b < 0:
                raise ValueError("Distancias devem ser nao negativas e nao NaN.")
            if math.isfinite(a) != math.isfinite(b) or (math.isfinite(a) and not math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-7)):
                raise ValueError("Para grafo nao direcionado a matriz deve ser simetrica.")


def custo_rota(rota: Sequence[int], matriz: Matriz) -> float:
    return sum(matriz[a][b] for a, b in zip(rota, rota[1:]))


def rota_valida(rota: Sequence[int], matriz: Matriz, modo: str) -> bool:
    n = len(matriz)
    if modo not in MODOS or not rota or rota[0] != 0:
        return False
    if modo == "caminho":
        if len(rota) != n or sorted(rota) != list(range(n)):
            return False
    else:
        if n < 3 or len(rota) != n + 1 or rota[-1] != 0 or sorted(rota[:-1]) != list(range(n)):
            return False
    return all(math.isfinite(matriz[a][b]) for a, b in zip(rota, rota[1:]))


def restricoes_impossiveis(matriz: Matriz, modo: str) -> str | None:
    """Verificacoes NECESSARIAS (nao suficientes) que nao descartam solucoes."""
    n = len(matriz)
    if modo != "caminho" and n < 3:
        return "Ciclo hamiltoniano simples exige pelo menos 3 vertices."
    if modo == "caminho" and n == 1:
        return None
    graus = [sum(1 for j in range(n) if i != j and math.isfinite(matriz[i][j])) for i in range(n)]
    if modo == "caminho" and any(g == 0 for g in graus):
        return "Existe vertice isolado, impedindo caminho hamiltoniano."
    if modo != "caminho" and any(g < 2 for g in graus):
        return "Existe vertice com grau menor que 2, impedindo ciclo hamiltoniano."
    descobertos, fila = {0}, [0]
    while fila:
        atual = fila.pop()
        for v in range(n):
            if v not in descobertos and math.isfinite(matriz[atual][v]):
                descobertos.add(v)
                fila.append(v)
    if len(descobertos) < n:
        return "O grafo nao e conexo, impedindo a visita a todos os vertices."
    return None


def _resultado(modo: str, metodo: str, rota: list[int], matriz: Matriz, inicio: float,
               *, completo: bool, timeout: bool = False, nos: int = 0, podas: int = 0,
               aviso: str = "") -> dict:
    existe = bool(rota)
    return {
        "modo": modo, "metodo": metodo, "rota": rota,
        "km": round(float(custo_rota(rota, matriz)), 6) if existe else None,
        "tempo_ms": round((time.perf_counter() - inicio) * 1000, 4),
        "encontrou": existe, "concluido": completo, "timeout": timeout,
        "otimo_comprovado": modo == "minimo" and completo and existe and metodo == "Exato",
        "ausencia_comprovada": completo and not existe and metodo == "Exato",
        "nos": nos, "podas": podas, "aviso": aviso,
    }


def heuristico(matriz: Matriz, modo: str = "minimo", dois_opt: bool = True) -> dict:
    """Vizinho mais proximo da base, seguido de 2-opt, quando ha rota.

    Nao ter encontrado rota NAO comprova que nao existe caminho/ciclo.
    Nao assegura otimalidade, mesmo quando um ciclo e encontrado.
    """
    inicio = time.perf_counter()
    verificar_matriz(matriz)
    if modo not in MODOS:
        raise ValueError("Modo invalido.")
    n = len(matriz)
    impossivel = restricoes_impossiveis(matriz, modo)
    if impossivel:
        return _resultado(modo, "Heuristica", [], matriz, inicio, completo=False, aviso=impossivel)
    if n == 1:
        return _resultado(modo, "Heuristica", [0], matriz, inicio, completo=False)
    rota, faltam = [0], set(range(1, n))
    while faltam:
        candidatos = [v for v in faltam if math.isfinite(matriz[rota[-1]][v])]
        if not candidatos:
            return _resultado(modo, "Heuristica", [], matriz, inicio, completo=False,
                              aviso="Vizinho mais proximo ficou sem proximo vertice valido.")
        proximo = min(candidatos, key=lambda v: (matriz[rota[-1]][v], v))
        rota.append(proximo)
        faltam.remove(proximo)
    if modo != "caminho":
        if not math.isfinite(matriz[rota[-1]][0]):
            return _resultado(modo, "Heuristica", [], matriz, inicio, completo=False,
                              aviso="Vizinho mais proximo nao conseguiu retornar a base.")
        rota.append(0)
    if dois_opt:
        # Primeiro melhoramento estrito; recomeca ate nao haver mais melhoras.
        atual = custo_rota(rota, matriz)
        limite_fim = len(rota) - 1 if modo != "caminho" else len(rota)
        houve = True
        while houve:
            houve = False
            for i in range(1, len(rota) - 1):
                for j in range(i + 1, limite_fim):
                    candidata = rota[:i] + rota[i:j + 1][::-1] + rota[j + 1:]
                    if rota_valida(candidata, matriz, modo):
                        custo = custo_rota(candidata, matriz)
                        if custo + 1e-10 < atual:
                            rota, atual, houve = candidata, custo, True
                            break
                if houve:
                    break
    return _resultado(modo, "Heuristica", rota, matriz, inicio, completo=False,
                      aviso="Solucao heuristica: nao ha garantia de otimalidade.")


def exato(matriz: Matriz, modo: str = "minimo", limite_segundos: float = 5.0) -> dict:
    """DFS/backtracking com poda de custo para minimo e limite de tempo.

    Caminho/ciclo: encerra ao encontrar 1 testemunho, demonstrando existencia.
    Minimo: enumera possibilidades com poda e certifica otimo apenas se completa.
    Timeout + rota: rota valida, mas otimalidade nao certificada.
    Timeout + sem rota: inconclusivo sobre a existencia.
    """
    inicio = time.perf_counter()
    verificar_matriz(matriz)
    if modo not in MODOS or limite_segundos <= 0:
        raise ValueError("Modo ou limite de tempo invalido.")
    n = len(matriz)
    motivo = restricoes_impossiveis(matriz, modo)
    if motivo:
        return _resultado(modo, "Exato", [], matriz, inicio, completo=True, aviso=motivo)
    if n == 1:
        return _resultado(modo, "Exato", [0], matriz, inicio, completo=True, nos=1)

    # Construcao inicial via heuristica como teto superior, APENAS na otimizacao.
    inicial = heuristico(matriz, "minimo") if modo == "minimo" else None
    melhor_rota = list(inicial["rota"]) if inicial and inicial["rota"] else []
    melhor_custo = custo_rota(melhor_rota, matriz) if melhor_rota else math.inf
    nos, podas, expirou, parou_por_existencia = 0, 0, False, False
    vizinhos = [sorted((j for j in range(1, n) if i != j and math.isfinite(matriz[i][j])),
                      key=lambda j: (matriz[i][j], j)) for i in range(n)]
    todos = (1 << n) - 1

    def dfs(atual: int, mascara: int, rota: list[int], acumulado: float):
        nonlocal melhor_rota, melhor_custo, nos, podas, expirou, parou_por_existencia
        if expirou or parou_por_existencia:
            return
        nos += 1
        if time.perf_counter() - inicio >= limite_segundos:
            expirou = True
            return
        if modo == "minimo" and acumulado >= melhor_custo - 1e-10:
            podas += 1
            return
        if mascara == todos:
            if modo == "caminho":
                melhor_rota, parou_por_existencia = list(rota), True
            else:
                if math.isfinite(matriz[atual][0]):
                    custo = acumulado + matriz[atual][0]
                    if modo == "ciclo":
                        melhor_rota, parou_por_existencia = rota + [0], True
                    elif custo < melhor_custo - 1e-10:
                        melhor_custo, melhor_rota = custo, rota + [0]
            return
        for prox in vizinhos[atual]:
            if not mascara & (1 << prox):
                dfs(prox, mascara | (1 << prox), rota + [prox], acumulado + matriz[atual][prox])
                if expirou or parou_por_existencia:
                    break

    dfs(0, 1, [0], 0.0)
    completo = not expirou  # Encontrar testemunho ja comprova a EXISTENCIA.
    aviso = "Tempo limite atingido; resultado nao conclusivo quanto a otimalidade/ausencia." if expirou else ""
    return _resultado(modo, "Exato", melhor_rota, matriz, inicio,
                      completo=completo, timeout=expirou, nos=nos, podas=podas, aviso=aviso)


def comparar(matriz: Matriz, modo: str, limite_segundos: float = 5.0,
             usar_exato: bool = True, usar_heuristico: bool = True, dois_opt: bool = True) -> dict[str, dict]:
    if not usar_exato and not usar_heuristico:
        raise ValueError("Escolha pelo menos um algoritmo.")
    resultados = {}
    if usar_exato:
        resultados["Exato"] = exato(matriz, modo, limite_segundos)
    if usar_heuristico:
        resultados["Heuristica"] = heuristico(matriz, modo, dois_opt)
    return resultados
