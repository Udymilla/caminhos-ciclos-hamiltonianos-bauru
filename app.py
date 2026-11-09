"""Planejador de visitas escolares: caminhos e ciclos hamiltonianos (Bauru).

Interface: seleção -> execução -> resultados. Fundamentação no README/PDF.
Algoritmos próprios implementados em src/algoritmos.py.
"""
from __future__ import annotations

import hashlib
import json
import math

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.algoritmos import comparar, rota_valida
from src.apresentacao import (
    ROTULOS_MODOS, melhor_resultado, explicar_resultado, comparar_interpretacao,
    nome_algoritmo, status_resultado, tabela_etapas, tabela_resultados,
)
from src.base_fixa import NOME_BASE, LATITUDE_BASE, LONGITUDE_BASE, adicionar_base_fixa
from src.dados import (
    RAIZ, PAGINA_OFICIAL, apenas_escolas_estaduais_bauru, csv_padronizado,
    ler_escolas, baixar_base_2026, matriz_osrm, aplicar_restricoes,
    geocodificar_poucas, geometria_rota_osrm,
)
from src.experimentos import realizar_experimentos
from src.instancias import instancias_offline, pontos_simulados, matriz_cenario, distancia_aproximada
from src.mapas import montar_mapa, figura_esquematica

st.set_page_config(
    page_title="Roteirização de Escolas | Bauru",
    page_icon="📍", layout="wide", initial_sidebar_state="expanded",
)

st.markdown("""<style>
:root {--azul:#244f78;--linha:#e4e9ee;--cinza:#5c6875}
html, body, [class*="css"], [data-testid="stApp"] {font-family: system-ui, -apple-system, 'Segoe UI', Arial, sans-serif}
[data-testid="stAppViewContainer"] {background:#fff}
.block-container {max-width:1470px;padding-top:1.65rem;padding-bottom:3rem}
[data-testid="stSidebar"] {background:#f7f9fb;border-right:1px solid #e5e9ef}
[data-testid="stSidebar"] .block-container {padding-top:1.55rem}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stCaption {font-size: .96rem !important;line-height:1.55}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {font-size: 1rem !important;font-weight:600}
[data-testid="stSidebar"] [role="radiogroup"] label p {font-size: .96rem !important;font-weight:500}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {font-size:.99rem !important}
[data-testid="stSidebar"] div[data-baseweb="select"] {font-size: 1rem}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {height:3.15rem;font-size:1.04rem;font-weight:700;border-radius:8px}
[data-testid="stSidebar"] hr {border-color:#e4e8ed;margin:1.15rem 0}
h1,h2,h3 {letter-spacing:-.024em}
h1 {font-size:2.05rem !important;line-height:1.25 !important}
h2 {font-size:1.42rem !important}
h3 {font-size:1.18rem !important}
[data-testid="stMetric"] {padding:14px 17px;border:1px solid #e5eaf0;border-radius:8px;background:#fff}
[data-testid="stMetricLabel"] p {font-size:.89rem !important}
[data-testid="stMetricValue"] {font-size:1.65rem !important}
[data-testid="stDataFrame"] {border-radius:7px;overflow:hidden}
.headline {border-bottom:1px solid #e5eaf0;padding:0 0 18px;margin:0 0 18px}
.headline .kicker {color:#566a7d;font-size:.77rem;font-weight:700;letter-spacing:.12em;margin-bottom:7px}
.headline h1{color:#172d42;font-weight:750;margin:0}
.headline .sub {color:#586a7c;font-size:1rem;margin-top:8px}
.sidebrand {font-weight:800;color:#183e62;font-size:1.2rem;margin-bottom:1px}
.sidebrand-sub {font-size:.9rem;color:#677789;margin-bottom:19px}
.step {font-size:.76rem;font-weight:800;letter-spacing:.10em;color:#52718f;margin:1.25rem 0 10px}
.base {padding:12px 13px;background:#eef3f8;border:1px solid #dbe5ee;border-radius:8px;margin:8px 0 4px}
.base strong {font-size:.93rem;color:#213f5b}
.base span {display:block;font-size:.86rem;color:#5c7083;margin-top:2px}
.inline-help {padding:12px 16px;border:1px solid #dbe4ec;border-radius:7px;color:#4b5e70;background:#f9fbfd}
[data-testid="stAlert"] {border-radius:7px}
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="headline">
<div class="kicker">ROTEIRIZAÇÃO ESCOLAR · BAURU / SP</div>
<h1>Planejamento de visitas técnicas</h1>
<div class="sub">Caminhos e ciclos hamiltonianos · Escolas estaduais</div>
</div>""", unsafe_allow_html=True)

MODOS = {
    "Caminho hamiltoniano": "caminho",
    "Ciclo hamiltoniano": "ciclo",
    "Ciclo hamiltoniano mínimo": "minimo",
}
TIPOS_FONTE = ("Escolas oficiais de Bauru", "Cenários de teste", "Importar CSV / XLSX")
TIPOS_ALGO = ("Comparar os dois", "Somente backtracking", "Somente heurística")


def _registro(config, df, matriz, resultados, origem_matriz, matriz_dirigida=None):
    return {"chave": config, "pontos": df.to_dict("records"), "matriz": matriz,
            "resultados": resultados, "origem_matriz": origem_matriz,
            "dir_matriz": matriz_dirigida}


@st.cache_data(show_spinner=False)
def _ler_bytes(conteudo: bytes, nome: str):
    return ler_escolas(conteudo, nome)


def _mapa(df, matriz, rota=None, *, origem="", arestas=False, ruas=False, chave="mapa"):
    geometria = km_ruas = nome_cache = None
    if rota and ruas and origem.startswith("OSRM"):
        try:
            with st.spinner("Carregando percurso pelas ruas..."):
                geometria, km_ruas, nome_cache = geometria_rota_osrm(df, rota)
        except Exception as exc:
            st.warning(f"A geometria das ruas não ficou disponível ({exc}). O mapa mostrará somente as ligações ilustrativas.")
    mapa = montar_mapa(df, matriz, rota, geometria, bool(geometria), arestas)
    try:
        st_folium(mapa, height=510 if rota else 445, width=940,
                  returned_objects=[], key=chave)
    except Exception as exc:
        st.warning(f"Mapa interativo indisponível ({exc}). Exibindo a visualização alternativa.")
        st.components.v1.html(mapa._repr_html_(), height=520)
    if geometria is not None and km_ruas is not None:
        st.caption(f"Percurso rodoviário efetivo (OSRM): {km_ruas:.2f} km · {nome_cache}. "
                   "Pode diferir do custo médio de ida/volta do grafo não direcionado.")
    elif rota:
        st.caption("O traçado está em linha reta apenas para visualização. Ele não representa o percurso pelas ruas.")


def _validar_e_ler_escolas(fonte: str):
    """Retorna (df_escolas, origem, meta). Não adiciona a base aqui."""
    if fonte == "Cenários de teste":
        nome = st.selectbox("Conjunto de teste", list(instancias_offline()), key="instancia")
        cfg = instancias_offline()[nome]
        st.caption(f"{cfg['n']} vértices · dados simulados, não são escolas reais")
        return pontos_simulados(cfg["n"]), cfg["cenario"], {"simulado": True}

    if fonte == "Escolas oficiais de Bauru":
        caminhos = [
            RAIZ / "data" / "escolas_bauru_consolidadas.csv",
            RAIZ / "data" / "escolas_bauru_seduc_2026.csv",
            RAIZ / "data" / "escolas_sp_2026.xlsx",
        ]
        arquivo = next((f for f in caminhos if f.is_file()), None)
        if arquivo is None:
            st.error("A base escolar não foi encontrada em data/. Consulte o README.")
            return None, "", {}
        try:
            base, meta = _ler_bytes(arquivo.read_bytes(), arquivo.name)
        except Exception as exc:
            st.error(f"Erro ao carregar cadastro local: {exc}")
            return None, "", {}
    else:
        enviado = st.file_uploader("Arquivo de escolas", type=["csv", "xlsx", "xls"], key="arquivo_escolas")
        if enviado is None:
            st.caption("Selecione um arquivo de escolas de Bauru.")
            return None, "", {}
        try:
            base, meta = _ler_bytes(enviado.getvalue(), enviado.name)
        except Exception as exc:
            st.error(f"Arquivo não reconhecido: {exc}")
            return None, "", {}

    try:
        base, recorte = apenas_escolas_estaduais_bauru(base)
    except ValueError as exc:
        st.error(f"Não foi possível filtrar apenas as escolas estaduais de Bauru: {exc}")
        return None, "", {}

    # O recorte deve usar MUNICÍPIO = Bauru, nunca apenas a diretoria regional.
    base = base.reset_index(drop=True)
    if "validado_inep" in base:
        with st.expander("Filtros do cadastro", expanded=False):
            confirmadas = base["validado_inep"].astype(str).str.upper().isin(["SIM", "TRUE", "1"])
            apenas_confirmadas = st.checkbox("Somente registros conferidos pelo INEP", key="confirmadas")
            st.caption(f"{int(confirmadas.sum())} registros conferidos nas duas fontes.")
        if apenas_confirmadas:
            base = base.loc[confirmadas].copy()

    alertas = 0
    if "alerta_coordenadas" in base:
        alertas = int(base["alerta_coordenadas"].astype(str).eq("CONFERIR_COORDENADAS").sum())
    sem = base[base.latitude.isna() | base.longitude.isna()]
    if not sem.empty:
        with st.expander(f"Coordenadas pendentes ({len(sem)})", expanded=False):
            st.caption("Pesquisar até 5 registros pelo Nominatim; confira manualmente as coordenadas antes de utilizar.")
            consulta = st.multiselect("Escolas", sem["nome"].astype(str).tolist(), max_selections=5,
                                     key="escolas_geocodificar")
            email = st.text_input("E-mail de identificação (opcional)", key="email_geo")
            if st.button("Buscar coordenadas", disabled=not consulta):
                indices = base.index[base["nome"].isin(consulta)].tolist()
                corrigida, mensagens = geocodificar_poucas(base, indices, email)
                st.session_state["geo_base"] = corrigida
                for mensagem in mensagens:
                    st.write(mensagem)
        salvo = st.session_state.get("geo_base")
        if salvo is not None and set(salvo["id"]).issuperset(set(base["id"])):
            base = base.drop(columns=["latitude", "longitude"]).merge(
                salvo[["id", "latitude", "longitude"]], on="id", how="left")
    base = base.dropna(subset=["latitude", "longitude"]).copy().reset_index(drop=True)
    if base.empty:
        st.warning("Nenhuma escola de Bauru com coordenadas válidas.")
        return None, "", {}

    base["etiqueta_ui"] = base["nome"].astype(str) + "  ·  " + base["id"].astype(str)
    default = base["etiqueta_ui"].tolist()[:min(6, len(base))]
    selecionadas = st.multiselect(
        "Escolas para visitar", base["etiqueta_ui"].tolist(), default=default,
        max_selections=24, placeholder="Digite para localizar uma escola...", key=f"escolas_{fonte}",
    )
    base = base[base["etiqueta_ui"].isin(selecionadas)].copy().reset_index(drop=True)
    st.caption(f"{len(selecionadas)} de {recorte['estaduais_ativas_bauru']} escolas selecionadas · limite: 24")
    if alertas:
        st.caption(f"Atenção: {alertas} coordenada(s) da base precisam de conferência.")
    with st.expander("Dados e arquivos", expanded=False):
        st.caption("Rede estadual · município de Bauru · base SEDUC 2026 conferida com INEP.")
        st.markdown(f"[Consultar fonte oficial]({PAGINA_OFICIAL})")
        st.download_button("Exportar cadastro filtrado (.csv)", data=csv_padronizado(base),
                           file_name="escolas_estaduais_bauru.csv", mime="text/csv", width="stretch")
        if fonte == "Escolas oficiais de Bauru" and st.button("Baixar atualização SEDUC 2026"):
            try:
                with st.spinner("Consultando base oficial..."):
                    baixar_base_2026(RAIZ / "data" / "escolas_sp_2026.xlsx")
                st.success("Arquivo baixado. Use o conversor de dados para atualizar o cadastro consolidado.")
            except Exception as exc:
                st.error(f"Não foi possível baixar o arquivo: {exc}")
    return base, "escolas_reais", {"simulado": False, "alertas": alertas}


with st.sidebar:
    st.markdown('<div class="sidebrand">Configurar percurso</div>'
                '<div class="sidebrand-sub">Defina os pontos e execute a busca.</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="step">01 / ESCOLAS</div>', unsafe_allow_html=True)
    fonte = st.selectbox("Origem dos dados", TIPOS_FONTE, key="fonte_escolas")
    df, cenario, metadados = _validar_e_ler_escolas(fonte)
    if fonte != "Cenários de teste":
        st.markdown(f'<div class="base"><strong>Ponto de partida fixo</strong>'
                    f'<span>{NOME_BASE}</span>'
                    f'<span>{LATITUDE_BASE:.6f}, {LONGITUDE_BASE:.6f}</span></div>',
                    unsafe_allow_html=True)
        if df is not None and not df.empty:
            try:
                df = adicionar_base_fixa(df)
            except ValueError as exc:
                st.error(str(exc))
                df = None

    st.divider()
    st.markdown('<div class="step">02 / ROTEIRIZAÇÃO</div>', unsafe_allow_html=True)
    modo_label = st.selectbox("Tipo de percurso", list(MODOS), index=2, key="modo")
    modo = MODOS[modo_label]
    algoritmo = st.selectbox("Método de busca", TIPOS_ALGO, key="algoritmo")
    com_heuristica = algoritmo != "Somente backtracking"
    com_exato = algoritmo != "Somente heurística"

    st.divider()
    st.markdown('<div class="step">03 / DISTÂNCIAS</div>', unsafe_allow_html=True)
    if fonte == "Cenários de teste":
        opcoes_distancia = ("Simulada (cenário de teste)", "Por ruas (OSRM)")
    else:
        opcoes_distancia = ("Por ruas (OSRM)", "Estimativa offline")
    tipo_distancia = st.selectbox("Cálculo das distâncias", opcoes_distancia, key="tipo_distancia")
    if tipo_distancia != "Por ruas (OSRM)":
        st.caption("Distâncias estimadas/simuladas: não correspondem ao percurso real pelas ruas.")
    else:
        st.caption("Distâncias rodoviárias; exige conexão na primeira consulta. As matrizes são salvas em cache.")
    with st.expander("Configurações avançadas", expanded=False):
        opt2 = st.checkbox("Melhorar heurística com 2-opt", value=True, disabled=not com_heuristica,
                           key="opt2")
        tempo_limite = st.slider("Tempo limite do backtracking (s)", 1, 30, 5,
                                 disabled=not com_exato, key="tempo_limite")
        limitar = st.checkbox("Limitar quilômetros por trecho", key="limitar_trecho")
        teto = st.number_input("Máximo por trecho (km)", min_value=0.1, max_value=5000.0,
                               value=5.0, step=0.5, disabled=not limitar, key="teto_km") if limitar else None
        bloqueios = []
        if df is not None and 2 <= len(df) <= 10:
            opcoes_arestas = {f"{i} — {j}": (i, j)
                               for i in range(len(df)) for j in range(i+1, len(df))}
            excluir = st.multiselect("Ligações proibidas", list(opcoes_arestas),
                                     key="arestas_proibidas")
            bloqueios = [opcoes_arestas[x] for x in excluir]
        else:
            st.caption("Exclusão manual de ligações disponível para até 10 vértices.")
    disponivel = df is not None and len(df) >= (2 if modo == "caminho" else 3)
    if df is None or len(df) < (2 if modo == "caminho" else 3):
        st.caption("Selecione escolas suficientes para o tipo de percurso escolhido.")
    calcular = st.button("Executar roteirização", type="primary", width="stretch", disabled=not disponivel)

# Uma navegação real evita uma aba de resultados "vazia" após qualquer rerun.
if "visao" not in st.session_state:
    st.session_state["visao"] = "Visão geral"
config = None
if df is not None and not df.empty:
    df = df.reset_index(drop=True)
    config = hashlib.sha256(json.dumps({
        "pontos": df[["nome", "latitude", "longitude"]].to_dict("records"),
        "modo": modo, "algoritmo": algoritmo, "peso": tipo_distancia,
        "teto": teto, "cenario": cenario, "bloqueios": bloqueios,
        "2opt": bool(opt2), "tempo_limite": tempo_limite,
    }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

if calcular and df is not None:
    st.session_state.pop("erro_roteirizacao", None)
    try:
        with st.spinner("Obtendo distâncias entre os pontos..."):
            dirigida = None
            if tipo_distancia == "Por ruas (OSRM)":
                matriz_bruta, dirigida, info_distancia = matriz_osrm(df)
                origem_matriz = "OSRM — " + info_distancia
            elif fonte == "Cenários de teste":
                matriz_bruta = matriz_cenario(df, cenario)
                origem_matriz = "SIMULADA (NÃO RODOVIÁRIA)"
            else:
                matriz_bruta = distancia_aproximada(df)
                origem_matriz = "ESTIMADA (NÃO RODOVIÁRIA)"
            matriz = aplicar_restricoes(matriz_bruta, teto, bloqueios)
        with st.spinner("Executando os algoritmos hamiltonianos..."):
            resultados = comparar(
                matriz, modo, tempo_limite, usar_exato=com_exato,
                usar_heuristico=com_heuristica, dois_opt=opt2,
            )
        for resultado in resultados.values():
            if resultado["rota"] and not rota_valida(resultado["rota"], matriz, modo):
                raise RuntimeError("O algoritmo retornou uma rota inválida.")
        st.session_state["resultado_hamiltoniano"] = _registro(
            config, df, matriz, resultados, origem_matriz, dirigida,
        )
        st.session_state["visao"] = "Resultados e rota"
    except Exception as exc:
        st.session_state["erro_roteirizacao"] = str(exc)
        st.session_state["visao"] = "Resultados e rota"

navegacao = st.radio(
    "Navegação", ("Visão geral", "Resultados e rota", "Experimentos"),
    key="visao", horizontal=True, label_visibility="collapsed",
)
st.divider()


def _visao_geral():
    st.subheader("Escolas selecionadas")
    if df is None or df.empty:
        st.info("Escolha a fonte e as escolas na barra lateral para começar.")
        return
    col1, col2, col3 = st.columns(3)
    col1.metric("Escolas", len(df) if fonte == "Cenários de teste" else len(df)-1)
    col2.metric("Vértices do grafo", len(df))
    col3.metric("Percurso", ROTULOS_MODOS[modo])
    st.markdown("### Localização dos pontos")
    zeros = [[0.0] * len(df) for _ in range(len(df))]
    _mapa(df, zeros, chave="mapa_pontos")
    st.markdown("### Relação de pontos")
    tabela = df.copy()
    tabela.insert(0, "Vértice", range(len(tabela)))
    if fonte != "Cenários de teste":
        tabela.insert(1, "Tipo", ["Ponto base"] + ["Escola"] * (len(tabela)-1))
    colunas = [c for c in ("Vértice", "Tipo", "nome", "endereco", "municipio") if c in tabela]
    tabela = tabela[colunas].rename(columns={"nome": "Local", "endereco": "Endereço", "municipio": "Município"})
    st.dataframe(tabela, hide_index=True, width="stretch")
    if fonte == "Cenários de teste":
        st.caption("Cenário simulado para análise dos algoritmos. Os pontos não são escolas reais.")
    else:
        st.caption("O vértice 0 é a Unidade Regional de Ensino de Bauru. Confira as coordenadas antes de utilizar o roteiro em campo.")
    st.markdown('''<div class="inline-help">Defina as opções na lateral e selecione <b>Executar roteirização</b>. O sistema abrirá a rota calculada na tela de resultados.</div>''', unsafe_allow_html=True)


def _visao_resultados():
    st.subheader("Resultados e rota")
    erro = st.session_state.get("erro_roteirizacao")
    if erro:
        st.error(f"A última execução não foi concluída: {erro}")
    res = st.session_state.get("resultado_hamiltoniano")
    if not res:
        st.markdown('''<div class="inline-help">Ainda não há resultados calculados. Selecione as escolas e o tipo de percurso na lateral e clique em <b>Executar roteirização</b>.</div>''', unsafe_allow_html=True)
        if df is not None and not df.empty:
            st.markdown("### Pontos preparados para o cálculo")
            zeros = [[0.0] * len(df) for _ in range(len(df))]
            _mapa(df, zeros, chave="mapa_sem_calculo")
        return
    if res["chave"] != config:
        st.warning("Os campos da lateral foram alterados desde a última execução. Abaixo está o **último resultado calculado**; clique em Executar roteirização para atualizar.")
    pontos = pd.DataFrame(res["pontos"])
    matriz = res["matriz"]
    resultados = res["resultados"]
    modo_salvo = next(iter(resultados.values()))["modo"]
    algoritmo_melhor, melhor = melhor_resultado(resultados)
    c1, c2, c3 = st.columns(3)
    c1.metric("Menor distância encontrada", f"{melhor['km']:.2f} km" if melhor else "Sem rota")
    c2.metric("Pontos da execução", len(pontos))
    c3.metric("Soluções válidas", sum(bool(r["rota"]) for r in resultados.values()))
    st.caption(f"{ROTULOS_MODOS[modo_salvo]} · pesos: {res['origem_matriz']}")

    st.markdown("### Comparação dos algoritmos")
    st.dataframe(tabela_resultados(resultados), hide_index=True, width="stretch")
    if len(resultados) == 2:
        st.markdown("**Leitura da comparação**")
        st.write(comparar_interpretacao(resultados, modo_salvo))

    st.markdown("### Interpretação do resultado")
    for chave, r in resultados.items():
        st.markdown(f"**{nome_algoritmo(chave)} — {status_resultado(r)}**")
        st.write(explicar_resultado(r, len(pontos)))

    validos = {chave: r for chave, r in resultados.items() if r["rota"]}
    if validos:
        st.markdown("### Percurso no mapa")
        ctrl_rota, ctrl_ruas, ctrl_arestas = st.columns([2.2, 1, 1], gap="medium")
        with ctrl_rota:
            selecionado = st.selectbox("Exibir rota calculada por", list(validos),
                                      format_func=nome_algoritmo, key="algoritmo_rota")
        with ctrl_ruas:
            mostrar_ruas = st.checkbox("Traçar pelas ruas (OSRM)", value=True,
                                      disabled=not res["origem_matriz"].startswith("OSRM"),
                                      key="mapa_ruas")
        with ctrl_arestas:
            mostrar_arestas = st.checkbox("Mostrar outras ligações", value=False,
                                         key="mapa_arestas")
        if mostrar_arestas and len(pontos) > 12:
            st.caption("Para exibir todas as ligações, selecione até 12 vértices.")
        r = validos[selecionado]
        _mapa(pontos, matriz, r["rota"], origem=res["origem_matriz"],
              ruas=mostrar_ruas, arestas=mostrar_arestas,
              chave=f"mapa_rota_{res['chave'][:8]}_{selecionado}")
        st.markdown("### Ordem de visita")
        st.dataframe(tabela_etapas(pontos, r["rota"], matriz), hide_index=True, width="stretch")
        if modo_salvo != "caminho":
            st.caption("A repetição do vértice 0 ao final fecha o ciclo; não representa uma segunda visita à base como escola.")
    else:
        st.markdown("### Grafo analisado")
        st.write("Nenhuma rota foi obtida nesta execução. O mapa abaixo mostra os vértices e as ligações permitidas.")
        _mapa(pontos, matriz, arestas=True, chave=f"mapa_sem_rota_{res['chave'][:8]}")

    with st.expander("Detalhes técnicos da execução"):
        st.caption("Matriz de adjacência ponderada (∞ = ligação inexistente ou proibida).")
        valores = [[round(float(x), 2) if math.isfinite(x) else "∞" for x in linha]
                   for linha in matriz]
        st.dataframe(pd.DataFrame(valores, columns=[str(i) for i in range(len(matriz))]),
                     hide_index=True, width="stretch")
        fig = figura_esquematica(pontos, matriz, melhor["rota"] if melhor else None)
        st.pyplot(fig, width="stretch")
        plt.close(fig)
        st.caption("Em OSRM, os pesos do grafo não direcionado são simetrizados pela média de ida e volta. Não representam trânsito em tempo real.")
    exportado = {
        "projeto": "Caminhos e Ciclos Hamiltonianos - Bauru",
        "modo": modo_salvo, "origem": res["origem_matriz"], "pontos": res["pontos"],
        "matriz_km": [[round(float(x), 6) if math.isfinite(x) else None for x in linha]
                       for linha in matriz],
        "resultados": resultados,
    }
    st.download_button("Exportar resultado (.json)",
                       data=json.dumps(exportado, ensure_ascii=False, indent=2, default=str),
                       file_name="resultado_hamiltoniano.json", mime="application/json")


def _visao_experimentos():
    st.subheader("Experimentos comparativos")
    st.write("Compare o tempo de execução e a distância calculada em instâncias simuladas de diferentes tamanhos.")
    if st.button("Executar experimentos", type="primary"):
        with st.spinner("Executando bateria de testes..."):
            st.session_state["experimentos"] = realizar_experimentos(min(3, tempo_limite))
    exp = st.session_state.get("experimentos")
    if exp is None:
        st.info("Execute os experimentos para visualizar os resultados e os gráficos.")
        return
    st.dataframe(exp, hide_index=True, width="stretch")
    completos = exp[(exp.cenario == "completo") & (exp.problema == "minimo")]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tempo de execução**")
        fig, ax = plt.subplots(figsize=(7, 4))
        for metodo in ("Exato", "Heuristica"):
            subset = completos[completos.algoritmo == metodo]
            ax.plot(subset.pontos, subset.tempo_ms, marker="o",
                    label=nome_algoritmo(metodo))
        ax.set_xlabel("Número de vértices")
        ax.set_ylabel("Tempo (ms)")
        ax.set_yscale("symlog", linthresh=1)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
        fig.tight_layout()
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    with c2:
        st.markdown("**Distância da solução**")
        fig, ax = plt.subplots(figsize=(7, 4))
        for metodo in ("Exato", "Heuristica"):
            subset = completos[completos.algoritmo == metodo]
            ax.plot(subset.pontos, subset.distancia_km, marker="o",
                    label=nome_algoritmo(metodo))
        ax.set_xlabel("Número de vértices")
        ax.set_ylabel("Distância simulada (km)")
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
        fig.tight_layout()
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    st.caption("Conjuntos simulados: os valores não representam rotas rodoviárias. Busca exata interrompida por tempo não garante mínimo.")
    st.download_button("Exportar experimentos (.csv)", exp.to_csv(index=False).encode("utf-8-sig"),
                       file_name="experimentos_hamiltonianos.csv", mime="text/csv")


if navegacao == "Visão geral":
    _visao_geral()
elif navegacao == "Resultados e rota":
    _visao_resultados()
else:
    _visao_experimentos()
