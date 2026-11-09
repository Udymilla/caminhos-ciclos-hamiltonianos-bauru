import math
import pytest
from src.algoritmos import exato, heuristico, custo_rota, rota_valida, restricoes_impossiveis, comparar, verificar_matriz
from src.dados import aplicar_restricoes

QUADRADO = [[0,1,2,1],[1,0,1,2],[2,1,0,1],[1,2,1,0]]


def caminho_corridor(n):
    return [[0 if i==j else (1 if abs(i-j)==1 else math.inf) for j in range(n)] for i in range(n)]


def test_exato_ciclo_minimo_comprova_otimo():
    r=exato(QUADRADO,"minimo",2)
    assert r["otimo_comprovado"] and r["km"] == 4
    assert rota_valida(r["rota"], QUADRADO, "minimo")


def test_exato_ciclo_detecta():
    r=exato(QUADRADO,"ciclo",1)
    assert r["encontrou"] and r["concluido"]
    assert rota_valida(r["rota"], QUADRADO, "ciclo")


def test_exato_caminho_detecta():
    r=exato(caminho_corridor(5),"caminho",1)
    assert r["rota"] == [0,1,2,3,4]


def test_caminho_corridor_sem_ciclo():
    d=caminho_corridor(7)
    assert exato(d,"ciclo",1)["ausencia_comprovada"]
    assert exato(d,"minimo",1)["ausencia_comprovada"]
    assert rota_valida(exato(d,"caminho",1)["rota"],d,"caminho")


def test_grafo_desconexo_sem_caminho():
    d=caminho_corridor(5)
    d[3][4]=d[4][3]=math.inf
    assert exato(d,"caminho",1)["ausencia_comprovada"]


def test_grafo_sem_ciclo_mas_grau_minimo_dois():
    # dois triangulos que so dividem o vertice 0 (ponto de articulacao)
    n=5; d=[[0 if i==j else math.inf for j in range(n)] for i in range(n)]
    for i,j in [(0,1),(1,2),(2,0),(0,3),(3,4),(4,0)]:
        d[i][j]=d[j][i]=1
    assert restricoes_impossiveis(d,"ciclo") is None
    assert exato(d,"ciclo",2)["ausencia_comprovada"]


def test_heuristica_valida_quadrado():
    r=heuristico(QUADRADO,"minimo")
    assert r["encontrou"] and rota_valida(r["rota"],QUADRADO,"minimo")
    assert not r["otimo_comprovado"]


def test_heuristica_pode_falhar_quando_existe():
    n=5; d=[[0 if i==j else math.inf for j in range(n)] for i in range(n)]
    for i,j,w in [(0,1,.5),(1,2,1),(2,3,1),(3,4,1),(0,2,4),(1,4,3)]:
        d[i][j]=d[j][i]=w
    assert not heuristico(d,"ciclo")["encontrou"]
    assert rota_valida(exato(d,"ciclo",2)["rota"],d,"ciclo")


def test_2opt_nao_piora():
    a=heuristico(QUADRADO,"minimo",False)
    b=heuristico(QUADRADO,"minimo",True)
    assert b["km"] <= a["km"]


def test_limite_restricoes_remove_arestas_simetrico():
    d=aplicar_restricoes(QUADRADO,1.2)
    assert math.isinf(d[0][2]) and math.isinf(d[2][0])
    assert exato(d,"minimo",1)["km"] == 4


def test_bloqueio_manual():
    d=aplicar_restricoes(QUADRADO,None,[(0,1),(0,3)])
    assert exato(d,"ciclo",1)["ausencia_comprovada"]


def test_rota_invalida_nao_aceita_repeticao():
    assert not rota_valida([0,1,1,3,0],QUADRADO,"ciclo")
    assert not rota_valida([0,1,2,0],QUADRADO,"caminho")


def test_matriz_assimetrica_rejeitada():
    with pytest.raises(ValueError,match="simetrica"):
        verificar_matriz([[0,1,2],[3,0,1],[2,1,0]])


def test_diagonal_negativa_rejeitada():
    with pytest.raises(ValueError):
        verificar_matriz([[1,2],[2,0]])


def test_ciclo_com_dois_vertices_inesistente():
    assert exato([[0,1],[1,0]],"ciclo",1)["ausencia_comprovada"]


def test_caminho_unico_vertice():
    assert exato([[0]],"caminho",1)["rota"] == [0]
    assert rota_valida([0],[[0]],"caminho")


def test_verificacao_parametros_invalidos():
    with pytest.raises(ValueError):
        exato(QUADRADO,"invalido",1)
    with pytest.raises(ValueError):
        exato(QUADRADO,"minimo",0)


def test_comparacao_ambos():
    r=comparar(QUADRADO,"minimo")
    assert set(r)=={"Exato","Heuristica"}
    assert r["Exato"]["km"] <= r["Heuristica"]["km"]


def test_custo_rota_manual():
    assert custo_rota([0,1,2,3,0],QUADRADO)==4
