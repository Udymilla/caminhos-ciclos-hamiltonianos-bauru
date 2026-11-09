import json
from pathlib import Path
import pandas as pd
import pytest
from scripts.validar_osrm_real import selecionar_amostra, executar, distancia_haversine
from src.dados import matriz_osrm
from src.instancias import pontos_simulados

ROOT=Path(__file__).resolve().parents[1]


def test_amostra_exclui_registros_especiais_e_divergentes():
    csv=ROOT/'data/escolas_bauru_consolidadas.csv'
    escolas=pd.read_csv(csv,dtype={'codigo_inep':str})
    amostra=selecionar_amostra(escolas,11)
    assert len(amostra)==11
    assert amostra.codigo_inep.is_unique
    assert set(amostra.validado_inep)=={'SIM'}
    assert amostra.alerta_coordenadas.isna().all()
    assert amostra.municipio.eq('Bauru').all()
    assert 'PENIT' not in ' '.join(amostra.nome).upper()
    assert amostra.codigo_inep.tolist()==selecionar_amostra(escolas,11).codigo_inep.tolist()


def test_auditoria_nao_declara_coordenadas_individuais_completas():
    a=json.loads((ROOT/'data/resultado_auditoria_geografica.json').read_text())
    assert a['total_seduc']==62
    assert a['ate_200_m']==54
    assert a['divergentes_gt_200_m']==2
    assert a['codigo_inep_cruzado']==57
    assert a['so_seduc']==5


def test_distancia_base_entre_localizacao_coerente():
    assert distancia_haversine(-22.325573,-49.091570,-22.325573,-49.091570)==0


def test_cache_registra_proveniencia_api_osrm(monkeypatch,tmp_path):
    class R:
        content=b'{"code":"Ok", "distances": [[0, 1200], [1400, 0]]}'
        def raise_for_status(self): pass
        def json(self):return {'code':'Ok','distances':[[0,1200],[1400,0]],
                   'sources':[{'distance':8},{'distance':13}],
                   'destinations':[{'distance':8},{'distance':13}]}
    monkeypatch.setattr('src.dados.requests.get',lambda *a,**kw:R())
    m,d,orig=matriz_osrm(pontos_simulados(2),pasta_cache=tmp_path)
    v=json.loads(next(tmp_path.glob('matriz_*.json')).read_text())
    assert orig.startswith('API OSRM')
    assert v['distancia_maxima_encaixe_m']==13
    assert v['consulta_utc'].endswith('+00:00')
    assert len(v['sha256_resposta_osrm'])==64
    assert m[0][1]==pytest.approx(1.3)


def test_conexao_indisponivel_nao_gera_falsas_distancias(monkeypatch,tmp_path):
    import scripts.validar_osrm_real as validator
    def falhou(*args,**kw): raise ConnectionError('Serviço externo indisponível')
    monkeypatch.setattr(validator,'matriz_osrm',falhou)
    with pytest.raises(ConnectionError):
        executar(saida=tmp_path)
    assert not (tmp_path/'evidencia_osrm_real.json').exists()
    assert not (tmp_path/'ANEXO_VALIDACAO_OSRM_REAL.pdf').exists()
