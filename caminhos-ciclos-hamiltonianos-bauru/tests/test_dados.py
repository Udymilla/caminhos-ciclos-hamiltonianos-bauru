import io
import math
import json
import pandas as pd
import pytest
from src.dados import ler_escolas, filtrar_municipios, aplicar_restricoes, matriz_osrm, _geolocalizacao
from src.instancias import pontos_simulados, matriz_cenario, instancias_offline
from src.algoritmos import exato, heuristico, rota_valida


def test_csv_simples():
    s="nome;latitude;longitude;municipio\nEE A;-22,32;-49,06;Bauru\nEE B;-22,34;-49,07;Agudos\n"
    # Decimal com virgula sem aspas em arquivo com separador ponto-e-virgula.
    df,m=ler_escolas(s.encode("utf-8"),"exemplo.csv")
    assert len(df)==2 and m["com_coordenadas"]==2
    assert math.isclose(df.iloc[0]["latitude"],-22.32)
    assert len(filtrar_municipios(df,["Bauru"]))==1


def test_csv_alias_inep():
    s="NO_ENTIDADE,NU_LATITUDE,NU_LONGITUDE,NO_MUNICIPIO\nEscola 1,-22.33,-49.05,Bauru\n"
    df,m=ler_escolas(s.encode(),"inep.csv")
    assert df.iloc[0].nome=="Escola 1"


def test_geolocalizacao_wkt():
    assert _geolocalizacao("POINT (-49.070 -22.320)")==(-22.32,-49.07)
    assert _geolocalizacao("-22.32, -49.07")==(-22.32,-49.07)


def test_sem_coordenada_preservada():
    s="nome,latitude,longitude\nA,-22.32,-49.02\nB,,\n"
    df,m=ler_escolas(s.encode(),"a.csv")
    assert m["sem_coordenadas"]==1 and len(df)==2


def test_sinteticos_tem_instancias_distintas():
    conf=instancias_offline()
    assert len(conf)>=5
    for c in conf.values():
        d=matriz_cenario(pontos_simulados(c["n"]),c["cenario"])
        assert len(d)==c["n"]


def test_osrm_simetrizacao_e_cache(monkeypatch,tmp_path):
    df=pontos_simulados(3)
    chamadas=[]
    class Resposta:
        def raise_for_status(self): pass
        def json(self):
            return {"code":"Ok","distances":[[0,1000,2500],[1200,0,900],[2000,1000,0]]}
    def get(*args,**kwargs):
        chamadas.append(1)
        return Resposta()
    monkeypatch.setattr("src.dados.requests.get",get)
    m,dir,orig=matriz_osrm(df,pasta_cache=tmp_path)
    assert m[0][1]==m[1][0]==1.1
    assert m[0][2]==2.25
    assert dir[0][1]==1 and dir[1][0]==1.2
    matriz_osrm(df,pasta_cache=tmp_path)
    assert len(chamadas)==1


def test_osrm_unreachable_pair(monkeypatch,tmp_path):
    class R:
        def raise_for_status(self): pass
        def json(self): return {"code":"Ok","distances":[[0,1000,2000],[None,0,3000],[2000,3000,0]]}
    monkeypatch.setattr("src.dados.requests.get",lambda *a,**k:R())
    m,_,_=matriz_osrm(pontos_simulados(3),pasta_cache=tmp_path)
    assert math.isinf(m[0][1]) and math.isinf(m[1][0])


def test_simulated_sample_true_cycle():
    d=matriz_cenario(pontos_simulados(5))
    e=exato(d,"minimo",2)
    assert e["otimo_comprovado"] and rota_valida(e["rota"],d,"minimo")


def test_heuristic_instance_large_valid():
    d=matriz_cenario(pontos_simulados(16))
    r=heuristico(d,"minimo")
    assert rota_valida(r["rota"],d,"minimo")


def test_invalid_coordinates():
    s="nome,latitude,longitude\nA,123.45,-49.0\nB,-22.3,-49.0\n"
    df,m=ler_escolas(s.encode(),"a.csv")
    assert m["sem_coordenadas"]==1


def test_filtro_municipio_nao_diretoria():
    from src.dados import apenas_escolas_estaduais_bauru
    csv_texto = ("Nome Escola,Diretoria,Municipio,latitude,longitude,Rede\\n"
                 "EE BAURU,BAURU,BAURU,-22.3,-49.0,Estadual\\n"
                 "EE AGUDOS,BAURU,AGUDOS,-22.3,-49.0,Estadual\\n")
    # Usar quebras reais nos registros, nao os caracteres barra-n.
    escolas, _ = ler_escolas(csv_texto.replace('\\n','\n').encode(), "s.csv")
    somente, rel = apenas_escolas_estaduais_bauru(escolas)
    assert somente.nome.tolist() == ["EE BAURU"]
    assert rel["removidas"] == 1


def test_inep_sem_coordenadas_e_municipio_codificado():
    from src.dados import apenas_escolas_estaduais_bauru
    raw = "NO_ENTIDADE,CO_ENTIDADE,CO_MUNICIPIO,TP_DEPENDENCIA,TP_SITUACAO_FUNCIONAMENTO\nE E Bauru,35000001,3506003,2,1\nE Municipal,35000002,3506003,3,1\nE Fechada,35000003,3506003,2,2\nE Agudos,35000004,3500000,2,1\n"
    escolas, _ = ler_escolas(raw.encode(), "inep.csv")
    filtradas, info = apenas_escolas_estaduais_bauru(escolas)
    assert len(filtradas) == 1
    assert filtradas.iloc[0].nome == "E E Bauru"
    assert filtradas.iloc[0].codigo_inep == "35000001"
    assert filtradas.iloc[0].latitude != filtradas.iloc[0].latitude # nan


def test_cruzamento_por_codigo_sem_duplicar():
    from src.dados import cruzar_seduc_inep
    seduc, _ = ler_escolas("nome,municipio,latitude,longitude,codigo_inep\nEE A,Bauru,-22.3,-49.0,35000001\nEE B,Bauru,-22.4,-49.1,35000002\n".encode(), "s.csv")
    inep, _ = ler_escolas("no_entidade,co_municipio,co_entidade,tp_dependencia\nEE A,3506003,35000001,2\n".encode(), "i.csv")
    combinado, rel = cruzar_seduc_inep(seduc, inep)
    assert len(combinado) == 2
    assert rel["coincidencias_codigo_inep"] == 1
    assert combinado.validado_inep.tolist() == [True, False]


def test_arquivo_sem_municipio_nao_e_aceito_para_recorte():
    from src.dados import apenas_escolas_estaduais_bauru
    frame, _ = ler_escolas(b"nome,latitude,longitude,diretoria\nEE A,-22.3,-49.0,Bauru\n", "s.csv")
    with pytest.raises(ValueError, match="MUNICIPIO"):
        apenas_escolas_estaduais_bauru(frame)
