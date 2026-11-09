"""Comparacao independente com enumeracao exaustiva (oraculo) em grafos pequenos."""
import itertools
import math
import random
from src.algoritmos import exato, heuristico, rota_valida


def oraculo(m, modo):
    n=len(m)
    melhor=math.inf; rota=[]
    for perm in itertools.permutations(range(1,n)):
        p=[0,*perm]
        if modo != "caminho": p.append(0)
        if all(math.isfinite(m[a][b]) for a,b in zip(p,p[1:])):
            valor=sum(m[a][b] for a,b in zip(p,p[1:]))
            if valor < melhor:
                melhor,rota=valor,p
    return melhor,rota


def test_exato_contra_oraculo_enumeracao_independente():
    rng=random.Random(20261028)
    for n in (3,4,5,6,7):
        for _ in range(4):
            m=[[0.0]*n for _ in range(n)]
            for i in range(n):
                for j in range(i+1,n):
                    m[i][j]=m[j][i]=rng.randint(1,20) if rng.random() < .72 else math.inf
            for modo in ("caminho","ciclo","minimo"):
                melhor,rota=oraculo(m,modo)
                r=exato(m,modo,2)
                assert r["concluido"],(n,modo)
                assert bool(r["rota"]) == bool(rota)
                if r["rota"]:
                    assert rota_valida(r["rota"],m,modo)
                    if modo=="minimo": assert abs(r["km"]-melhor) < 1e-6
                elif modo!="caminho" or n>=3:
                    assert r["ausencia_comprovada"]


def test_heuristica_nunca_devolve_rota_invalida_random():
    rng=random.Random(42)
    for n in (4,5,6,8):
        for _ in range(6):
            m=[[0.0]*n for _ in range(n)]
            for i in range(n):
                for j in range(i+1,n):
                    m[i][j]=m[j][i]=rng.randint(1,40) if rng.random()<.7 else math.inf
            for modo in ("caminho","ciclo","minimo"):
                r=heuristico(m,modo)
                assert not r["rota"] or rota_valida(r["rota"],m,modo)
