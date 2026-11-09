"""Conferência reproduzível dos CSVs gerados a partir das fontes fornecidas.

Não requer conexão externa; os originais são preservados em data/fontes_originais/.
"""
from pathlib import Path
from src.dados import ler_escolas, apenas_escolas_estaduais_bauru, csv_padronizado

DATA = Path(__file__).resolve().parents[1] / 'data'


def test_seduc_2026_apenas_bauru_rede_estadual():
    df, meta = ler_escolas(DATA / 'escolas_bauru_seduc_2026.csv')
    filtrado, _ = apenas_escolas_estaduais_bauru(df)
    assert len(df) == len(filtrado) == 62
    assert meta['com_coordenadas'] == 62
    assert df.codigo_inep.nunique() == 62


def test_inep_recorte_ativo():
    df, meta = ler_escolas(DATA / 'escolas_bauru_inep_exportacao.csv')
    filtrado, _ = apenas_escolas_estaduais_bauru(df)
    assert len(df) == len(filtrado) == 61
    assert meta['com_coordenadas'] == 60
    assert df.codigo_inep.nunique() == 61


def test_cruzamento_e_alerta_coordenadas():
    df, _ = ler_escolas(DATA / 'escolas_bauru_consolidadas.csv')
    assert len(df) == 62
    assert (df.validado_inep == 'SIM').sum() == 57
    assert (df.alerta_coordenadas == 'CONFERIR_COORDENADAS').sum() == 2
    assert (df.alerta_coordenadas == 'NAO_CONSTA_NO_INEP_EXPORTADO').sum() == 5
    exportado, _ = ler_escolas(csv_padronizado(df), 'export.csv')
    assert len(exportado) == 62 and 'validado_inep' in exportado


def test_aliases_planilha_seduc_e_restricao_inep():
    raw = ('NOMEDEP,MUN,CODESCMEC,NOMESC,CODSIT,DS_LATITUDE,DS_LONGITUDE,ENDESC,NUMESC,BAIESC\n'
           'ESTADUAL - SE,BAURU,35025483,ESCOLA A,1,-22.32,-49.07,RUA A,123,BAIRRO\n'
           'ESTADUAL - SE,AGUDOS,35025484,ESCOLA B,1,-22.33,-49.08,RUA B,122,BAIRRO\n'
           'ESTADUAL - SE,BAURU,35025485,ESCOLA C,2,-22.34,-49.09,RUA C,121,BAIRRO\n')
    df, _ = ler_escolas(raw.encode(), 'seduc.csv')
    filtrado, _ = apenas_escolas_estaduais_bauru(df)
    assert len(filtrado) == 1
    assert filtrado.iloc[0]['codigo_inep'] == '35025483'
    assert 'RUA A' in filtrado.iloc[0]['endereco']
    inep = ('Escola,Município,Dependência Administrativa,Restrição de Atendimento,Latitude,Longitude\n'
            'EE A,Bauru,Estadual,ESCOLA EM FUNCIONAMENTO E SEM RESTRIÇÃO DE ATENDIMENTO,-22.32,-49.07\n'
            'EE B,Bauru,Estadual,ESCOLA PARALISADA,-22.33,-49.08\n')
    df2, _ = ler_escolas(inep.encode(), 'inep.csv')
    filtro2, _ = apenas_escolas_estaduais_bauru(df2)
    assert len(filtro2) == 1 and filtro2.iloc[0]['nome'] == 'EE A'
