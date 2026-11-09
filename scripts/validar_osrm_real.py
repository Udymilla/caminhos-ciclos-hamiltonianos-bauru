"""Experimento rodoviario REPRODUZIVEL, sem simulacao ou fallback silencioso.

Execute no Windows com internet: validar_distancias_windows.bat
O programa faz chamadas HTTP reais ao OSRM e somente registra 'real' se houver
HTTP 2xx, code='Ok' e matriz integra. Em caso de falha, termina com erro,
sem fabricar distancias. Saidas em data/resultados_osrm/.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from src.base_fixa import adicionar_base_fixa, LATITUDE_BASE, LONGITUDE_BASE
from src.algoritmos import comparar, rota_valida
from src.dados import matriz_osrm, geometria_rota_osrm, chave_cache

RESULTS = ROOT / 'data' / 'resultados_osrm'


def distancia_haversine(lat1,lon1,lat2,lon2):
    a1,a2=math.radians(float(lat1)),math.radians(float(lat2))
    dl=math.radians(float(lon2)-float(lon1))
    da=a2-a1
    x=math.sin(da/2)**2+math.cos(a1)*math.cos(a2)*math.sin(dl/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(x)))


def selecionar_amostra(escolas:pd.DataFrame, quantidade=11) -> pd.DataFrame:
    """Escolas comuns com coord. consistentes, distribuídas espacialmente.

    Selecao gulosa deterministica: escola mais distante do conjunto ja escolhido.
    A amostra maior contem as menores, para comparabilidade dos experimentos.
    """
    candidatas=escolas[
      escolas['validado_inep'].astype(str).eq('SIM')
      & escolas['alerta_coordenadas'].fillna('').astype(str).eq('')
      & escolas['latitude'].notna() & escolas['longitude'].notna()
    ].copy()
    especiais=r'CDP|PENIT|SOCIOEDUC|SOCIO EDUC|CLASSE HOSPITALAR|CEL JTO|EPF JTO|CENTRO ATEND'
    candidatas=candidatas[~candidatas.nome.str.contains(especiais,case=False,na=False,regex=True)]
    candidatas=candidatas.sort_values(['codigo_inep','nome']).reset_index(drop=True)
    if len(candidatas)<quantidade:
        raise ValueError(f'Apenas {len(candidatas)} escolas elegiveis; esperadas {quantidade}.')
    escolhidas=[]
    pontos=[(LATITUDE_BASE,LONGITUDE_BASE)]
    for _ in range(quantidade):
        indices=[i for i in range(len(candidatas)) if i not in escolhidas]
        melhor=max(indices,key=lambda i: (
             min(distancia_haversine(*p,candidatas.iloc[i].latitude,candidatas.iloc[i].longitude) for p in pontos),
             -i))
        escolhidas.append(melhor)
        pontos.append((float(candidatas.iloc[melhor].latitude),float(candidatas.iloc[melhor].longitude)))
    return candidatas.iloc[escolhidas].copy().reset_index(drop=True)


def _seguro_json(x):
    if isinstance(x, dict):return {k:_seguro_json(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)):return [_seguro_json(z) for z in x]
    if isinstance(x,float) and not math.isfinite(x):return None
    return x


def _csv_matriz(df,matriz,path):
    nomes=['BASE']+[f"{x.codigo_inep} - {x.nome[:32]}" for x in df.iloc[1:].itertuples()]
    pd.DataFrame(matriz,index=nomes,columns=nomes).to_csv(path,encoding='utf-8-sig',float_format='%.6f')


def _gerar_mapa(df,rota,linha,arquivo):
    import folium
    centro=[float(df.iloc[0].latitude),float(df.iloc[0].longitude)]
    mapa=folium.Map(location=centro,zoom_start=12,tiles='OpenStreetMap')
    for i,escola in enumerate(df.itertuples()):
        folium.Marker([float(escola.latitude),float(escola.longitude)],
            popup=f"{i} - {str(escola.nome)}", tooltip=str(i)+' '+str(escola.nome),
            icon=folium.Icon(color='red' if i==0 else 'blue')).add_to(mapa)
    if linha:
        folium.PolyLine(linha,weight=5,opacity=0.8,tooltip='Rota efetiva OSRM').add_to(mapa)
    else:
        folium.PolyLine([[float(df.iloc[i].latitude),float(df.iloc[i].longitude)] for i in rota],
                        weight=3,dash_array='8,8',tooltip='SEQUENCIA ENTRE PONTOS - NAO E RUA').add_to(mapa)
    mapa.save(str(arquivo))


def _gerar_relatorio_pdf(instancias, auditoria, destino):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if not Path(fontfile).is_file():
        try:
            import matplotlib
            fontfile=str(Path(matplotlib.get_data_path())/'fonts'/'ttf'/'DejaVuSans.ttf')
        except Exception:
            fontfile='' 
    if Path(fontfile).is_file():
        pdfmetrics.registerFont(TTFont('DejaVuSans',fontfile))
        fonte='DejaVuSans'
    else:
        fonte='Helvetica'
    estilos=getSampleStyleSheet()
    estilos.add(ParagraphStyle(name='TituloCustom',fontName=fonte,fontSize=16,leading=21,spaceAfter=16))
    estilos.add(ParagraphStyle(name='SubCustom',fontName=fonte,fontSize=10.5,leading=16,spaceBefore=12,spaceAfter=6))
    estilos.add(ParagraphStyle(name='BodyCustom',fontName=fonte,fontSize=8.7,leading=14,spaceAfter=7))
    doc=SimpleDocTemplate(str(destino),pagesize=(21*cm,29.7*cm),rightMargin=2*cm,leftMargin=2*cm,topMargin=2*cm,bottomMargin=2*cm)
    parts=[Paragraph('Validação rodoviária — OSRM / Bauru',estilos['TituloCustom']),
           Paragraph('Documento de evidências criado por consultas REAIS via HTTPS ao servidor público OSRM; sem estimativas offline.',estilos['BodyCustom']),
           Paragraph(f"Data da geração: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}. Base fixa: Rua Campos Salles, 9-43, Vila Falcão, Bauru. Coordenadas: {LATITUDE_BASE}, {LONGITUDE_BASE}.",estilos['BodyCustom']),
           Paragraph(f"Auditoria de cadastros: {auditoria['total_seduc']} registros SEDUC; {auditoria['codigo_inep_cruzado']} com código INEP correspondente; {auditoria['divergentes_gt_200_m']} divergências geográficas &gt;200 m (excluídas dos experimentos).",estilos['BodyCustom'])]
    for rec in instancias:
        n=rec['vertices']
        parts.append(Paragraph(f'Instância com {n} vértices ({n-1} escolas + base)',estilos['SubCustom']))
        parts.append(Paragraph(f"Consulta UTC: {rec['consulta_utc']}. Origem: {rec['origem_matriz']}. Encaixe máximo na rede viária: {rec['encaixe_maximo_m']} m.",estilos['BodyCustom']))
        tabelinha=[['Algoritmo','Distância (km)','Tempo (ms)','Ótimo comprovado','Rota válida']]
        for alg in ('Exato','Heuristica'):
            x=rec['resultados'][alg]
            tabelinha.append([alg,f"{x['km']:.3f}" if x['km'] is not None else '—',f"{x['tempo_ms']:.3f}", 'Sim' if x['otimo_comprovado'] else 'Não', 'Sim' if x['rota_valida'] else 'Não'])
        table=Table(tabelinha,colWidths=[2.6*cm,2.6*cm,2.5*cm,4*cm,3.4*cm],repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6EAF1')),('FONTNAME',(0,0),(-1,-1),fonte),('FONTSIZE',(0,0),(-1,-1),7.5),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),0.5,colors.grey)]))
        parts.append(table)
        melhor=rec.get('melhor_rota_escolas',[])
        if melhor:
            parts.append(Paragraph('Sequência da rota: '+' → '.join(str(t) for t in melhor),estilos['BodyCustom']))
        if rec.get('distancia_rodoviaria_efetiva_km') is not None:
            parts.append(Paragraph(f"Distância efetiva desenhada pelo serviço route: {rec['distancia_rodoviaria_efetiva_km']:.3f} km; a função objetivo usa a matriz não direcionada simetrizada.",estilos['BodyCustom']))
        else:
            parts.append(Paragraph('Geometria de rua não confirmada: verificar log. A distância da matriz é real, mas a rota desenhada não foi validada.',estilos['BodyCustom']))
    parts.append(Paragraph('Interpretação e limitações',estilos['SubCustom']))
    parts.append(Paragraph('O serviço OSRM otimiza o tempo estimado de viagem e devolve a distância correspondente; esta não equivale necessariamente à menor distância viária entre dois pontos. O custo hamiltoniano foi construído a partir da média ida/volta, para manter o grafo não direcionado. A geometria efetiva pode diferir. Não contempla trânsito em tempo real, acesso ao portão ou estacionamento.',estilos['BodyCustom']))
    parts.append(Paragraph('Fontes: https://project-osrm.org/docs/ ; https://debauru.educacao.sp.gov.br/ ; bases de escolas SEDUC SP (08/2026) e INEP fornecidas pelo grupo.',estilos['BodyCustom']))
    doc.build(parts)


def executar(*,origem_dados:Path|None=None,saida:Path|None=None,limite_exato=4.0):
    saida=Path(saida or RESULTS)
    saida.mkdir(parents=True,exist_ok=True)
    csv=Path(origem_dados or ROOT/'data'/'escolas_bauru_consolidadas.csv')
    escolas=pd.read_csv(csv,dtype={'codigo_inep':str})
    amostra=selecionar_amostra(escolas)
    amostra.to_csv(saida/'amostra_escolas_osrm.csv',index=False,encoding='utf-8-sig')
    auditoria=json.loads((ROOT/'data'/'resultado_auditoria_geografica.json').read_text(encoding='utf-8'))
    registros=[]
    for total_vertices in (5,8,12):
        df=adicionar_base_fixa(amostra.iloc[:total_vertices-1].copy())
        print(f'Consultando OSRM AO VIVO: {total_vertices} vertices, {total_vertices-1} escolas...',flush=True)
        matriz,dirigida,origem=matriz_osrm(df,forcar=True)
        if not origem.startswith('API OSRM'):
            raise RuntimeError('Consulta não foi obtida da API ao vivo. Recusado marcar resultado como REAL.')
        arquivo_cache=ROOT/'data'/'cache'/f'matriz_{chave_cache(df)}.json'
        comprovante=json.loads(arquivo_cache.read_text(encoding='utf-8'))
        if not comprovante.get('consulta_utc') or not comprovante.get('sha256_resposta_osrm'):
            raise RuntimeError('Faltou evidencia da consulta OSRM no cache.')
        _csv_matriz(df,matriz,saida/f'matriz_osrm_{total_vertices}_vertices.csv')
        _csv_matriz(df,dirigida,saida/f'matriz_direcional_{total_vertices}_vertices.csv')
        rs=comparar(matriz,'minimo',limite_segundos=float(limite_exato),usar_exato=True,usar_heuristico=True)
        result={alg:dict(r,rota_valida=bool(rota_valida(r['rota'],matriz,'minimo'))) for alg,r in rs.items()}
        disponiveis=[(alg,r) for alg,r in result.items() if r['rota_valida']]
        melhor=min(disponiveis,key=lambda z:z[1]['km']) if disponiveis else None
        linha=[];km_rua=None;status_geo='sem solucao valida'
        if melhor:
            try:
                linha,km_rua,status_geo=geometria_rota_osrm(df,melhor[1]['rota'])
            except Exception as exc:
                status_geo=f'NAO VALIDADA: {type(exc).__name__}: {exc}'
                print('AVISO:',status_geo)
            _gerar_mapa(df,melhor[1]['rota'],linha,saida/f'mapa_osrm_{total_vertices}_vertices.html')
        resumo={
          'vertices':total_vertices,'escolas':total_vertices-1,'origem_matriz':origem,
          'consulta_utc':comprovante['consulta_utc'],
          'sha256_resposta_osrm':comprovante['sha256_resposta_osrm'],
          'encaixe_maximo_m':comprovante.get('distancia_maxima_encaixe_m'),
          'coordenadas':[{'codigo_inep':str(z.codigo_inep),'nome':z.nome,'latitude':float(z.latitude),'longitude':float(z.longitude)} for z in df.iloc[1:].itertuples()],
          'resultados':result,'melhor_algoritmo':melhor[0] if melhor else None,
          'melhor_rota_escolas':[str(df.iloc[i].nome) for i in melhor[1]['rota']] if melhor else [],
          'melhor_custo_simetrico_km':melhor[1]['km'] if melhor else None,
          'distancia_rodoviaria_efetiva_km':km_rua,'origem_geometria':status_geo,
          'rota_rodoviaria_confirmada':bool(linha and km_rua is not None),
          'cache_comprovante':str(arquivo_cache.relative_to(ROOT)).replace('\\','/')}
        (saida/f'resultado_osrm_{total_vertices}_vertices.json').write_text(json.dumps(_seguro_json(resumo),ensure_ascii=False,indent=2),encoding='utf-8')
        registros.append(resumo)
    resumo={'fonte':'OSRM REAL — API HTTPS sem estimativa','data_geracao_utc':datetime.now(timezone.utc).isoformat(),'auditoria_escolas':auditoria,'instancias':registros}
    (saida/'evidencia_osrm_real.json').write_text(json.dumps(_seguro_json(resumo),ensure_ascii=False,indent=2),encoding='utf-8')
    linhas=[]
    for r in registros:
        for a,z in r['resultados'].items():
            linhas.append({'vertices':r['vertices'],'algoritmo':a,'distancia_km':z['km'],'tempo_ms':z['tempo_ms'],
                          'rota_valida':z['rota_valida'],'otimo_comprovado':z['otimo_comprovado'],'timeout':z['timeout'],
                          'nos':z['nos'],'podas':z['podas'],'consulta_utc':r['consulta_utc']})
    pd.DataFrame(linhas).to_csv(saida/'comparacao_algoritmos_osrm_real.csv',index=False,encoding='utf-8-sig')
    _gerar_relatorio_pdf(registros,auditoria,saida/'ANEXO_VALIDACAO_OSRM_REAL.pdf')
    # A prova da consulta real e anexada ao relatorio tecnico gerado neste pacote.
    # Assim nao e necessario combinar PDFs manualmente no Windows.
    from pypdf import PdfReader, PdfWriter
    documento_base=ROOT/'docs'/'RELATORIO_TECNICO_HAMILTONIANOS_BAURU_V7_AUDITORIA.pdf'
    if documento_base.exists():
        final=PdfWriter()
        final.append(str(documento_base))
        final.append(str(saida/'ANEXO_VALIDACAO_OSRM_REAL.pdf'))
        with (saida/'RELATORIO_FINAL_COM_VALIDACAO_OSRM.pdf').open('wb') as arquivo:
            final.write(arquivo)
    print('\nVALIDACAO CONCLUIDA: arquivos em',saida)
    print('PDF de evidências:',saida/'ANEXO_VALIDACAO_OSRM_REAL.pdf')
    return resumo


def main():
    ap=argparse.ArgumentParser(description='Valida 3 instancias OSRM AO VIVO e gera anexos. Sem fallback simulado.')
    ap.add_argument('--limite-exato',type=float,default=4.0)
    args=ap.parse_args()
    try:
        executar(limite_exato=args.limite_exato)
    except Exception as exc:
        RESULTS.mkdir(parents=True,exist_ok=True)
        log=(f"{datetime.now(timezone.utc).isoformat()} - ERRO: {type(exc).__name__}: {exc}\n"+traceback.format_exc())
        (RESULTS/'ERRO_CONSULTA_OSRM.txt').write_text(log,encoding='utf-8')
        print('\nERRO: não foi possível validar acesso real ao OSRM. Não foram produzidas distâncias falsas.\n'+log)
        sys.exit(2)

if __name__=='__main__': main()
