"""Importacao de dados escolares e acesso cauteloso a Nominatim/OSRM.

Os dados disponibilizados pelo governo nao sao baixados ao gerar este ZIP,
pois nao foi possivel obter o arquivo externo neste ambiente. O aplicativo
aceita o arquivo baixado localmente e pode obtê-lo em tempo de execucao.
"""
from __future__ import annotations
import hashlib
import io
import json
import math
from pathlib import Path
import re
import time
import unicodedata
from datetime import datetime, timezone
import requests
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / "data" / "cache"
DATA_URL_2026 = "https://dados.educacao.sp.gov.br/sites/default/files/ENDERECO_ESCOLAS_082026.xlsx"
PAGINA_OFICIAL = "https://dados.educacao.sp.gov.br/dataset/escolas-ativas"
OSRM = "https://router.project-osrm.org"
NOMINATIM = "https://nominatim.openstreetmap.org"
USER_AGENT = "TrabalhoAcademicoGrafosHamiltonianosBauru/2.0 (aplicacao educativa sem fins comerciais)"
CIDADES = ["Bauru"]
CODIGO_IBGE_BAURU = "3506003"


def normalizar(value) -> str:
    txt = unicodedata.normalize("NFKD", str(value))
    txt = "".join(c for c in txt if not unicodedata.combining(c)).lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", txt).strip("_")


def _ler_arquivo(arquivo, nome: str | None = None) -> pd.DataFrame:
    if isinstance(arquivo, (str, Path)):
        caminho = Path(arquivo)
        conteudo = caminho.read_bytes()
        nome = nome or caminho.name
    elif isinstance(arquivo, bytes):
        conteudo = arquivo
    else:
        conteudo = arquivo.read()
        nome = nome or getattr(arquivo, "name", "arquivo.csv")
    if not conteudo:
        raise ValueError("Arquivo vazio")
    if str(nome).lower().endswith((".xlsx", ".xls")):
        # Algumas planilhas oficiais trazem titulos nas primeiras linhas.
        primeiro = None
        for folha in range(3):
            for cabecalho in range(6):
                try:
                    candidato = pd.read_excel(io.BytesIO(conteudo), sheet_name=folha, header=cabecalho)
                except (ValueError, IndexError):
                    break
                chaves = [normalizar(c) for c in candidato.columns]
                if (any(x in chaves for x in ("nome", "nome_escola", "nome_da_escola", "nomesc", "no_entidade"))
                    and any(x in chaves for x in ("latitude", "nu_latitude", "latitude_escola", "geolocalizacao", "longitude", "ds_latitude", "ds_longitude"))):
                    return candidato
                if folha == 0 and cabecalho == 0:
                    primeiro = candidato
        if primeiro is None:
            raise ValueError("Nao foi possivel interpretar a planilha XLSX.")
        return primeiro
    ultimo = None
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        for header in (0, 1, 2, 3, 4):
            try:
                df = pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python", encoding=enc, header=header,
                                 dtype=str, on_bad_lines="skip")
                if len(df.columns) > 1:
                    chaves = [normalizar(c) for c in df.columns]
                    if (any(k in chaves for k in ("latitude", "lat", "latitude_escola", "geolocalizacao", "longitude", "nu_latitude", "ds_latitude", "ds_longitude"))
                        or (any(k in chaves for k in ("nome", "nome_escola", "no_entidade", "no_escola", "nome_da_escola", "nomesc"))
                            and any(k in chaves for k in ("municipio", "no_municipio", "co_municipio", "municipio_escola", "mun")))):
                        return df
                    if ultimo is None:
                        ultimo = df
            except (UnicodeError, pd.errors.ParserError, ValueError, TypeError):
                continue
    if ultimo is None:
        raise ValueError("Nao foi possivel ler o arquivo CSV; verifique delimitador e codificacao.")
    return ultimo


def _encontrar(colunas: list[str], nomes: list[str]):
    for nome in nomes:
        if nome in colunas:
            return nome
    for col in colunas:
        if any(col.startswith(nome + "_") or col.endswith("_" + nome) for nome in nomes):
            return col
    return None


def _coord_num(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype("string").str.strip().str.replace(",", ".", regex=False), errors="coerce")


def _geolocalizacao(texto) -> tuple[float | None, float | None]:
    if pd.isna(texto):
        return None, None
    s = str(texto).strip()
    # POINT (longitude latitude) ou 'latitude, longitude'.
    achados = re.findall(r"-?\d+(?:[.,]\d+)?", s)
    if len(achados) < 2:
        return None, None
    a, b = float(achados[0].replace(",", ".")), float(achados[1].replace(",", "."))
    if s.upper().startswith("POINT"):
        return b, a
    if -34 <= a <= -19 and -55 <= b <= -44:
        return a, b
    if -55 <= a <= -44 and -34 <= b <= -19:
        return b, a
    return None, None


def ler_escolas(arquivo, nome: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Normaliza CSV/XLSX de diversas origens, sem inventar escolas ou coords.

    Retorna dataframe valido e metadados sobre entradas descartadas/incompletas.
    Linhas sem coordenadas permanecem no resultado para geocodificacao opcional.
    """
    df = _ler_arquivo(arquivo, nome)
    df.columns = [normalizar(c) for c in df.columns]
    cols = df.columns.tolist()
    nomes = {
        "nome": ["nome", "nome_escola", "nome_da_escola", "nome_da_unidade", "no_entidade", "no_escola", "nomesc", "nome_da_ue", "escola", "unidade_escolar", "nm_escola", "nom_entidade", "nomesc"],
        "latitude": ["latitude", "latitude_escola", "lat", "nu_latitude", "coordenada_latitude", "latitude_da_escola", "lat_escola", "ds_latitude"],
        "longitude": ["longitude", "longitude_escola", "long", "lon", "lng", "nu_longitude", "coordenada_longitude", "longitude_da_escola", "long_escola", "ds_longitude"],
        "municipio": ["municipio", "nome_municipio", "municipio_escola", "no_municipio", "nm_municipio", "cidade", "municipio_da_escola", "nome_do_municipio", "mun", "nommun", "nome_mun", "municipio_inep", "nm_mun", "co_municipio", "codigo_municipio", "cod_municipio", "codigo_ibge", "co_municipio_ibge", "mun"],
        "endereco": ["endereco", "endereco_escola", "logradouro", "ds_endereco", "endereco_da_escola", "endesc"],
        "codigo_inep": ["codigo_inep", "codigo_inep_escola", "co_entidade", "co_inep", "inep", "cod_inep", "codinep", "cod_escola_inep", "codigo_da_escola_inep", "codescmec"],
        "rede": ["rede", "dependencia_administrativa", "tp_dependencia", "tipo_rede", "rede_ensino", "tipo_dependencia", "nomedep"],
        "situacao": ["tp_situacao_funcionamento", "situacao_funcionamento", "situacao_escola", "codsit", "restricao_de_atendimento"],
    }
    m = {campo: _encontrar(cols, options) for campo, options in nomes.items()}
    if not m["nome"]:
        raise ValueError(f"Coluna de nome nao encontrada. Colunas existentes: {', '.join(cols[:20])}")
    geo_col = _encontrar(cols, ["geolocalizacao", "geolocalizacao_escola", "coordenadas", "coordenada_geografica", "localizacao"])
    # Exportacoes INEP podem nao conter coordenadas; mantemos linhas sem geolocalizacao
    # para cruzamento por codigo INEP com SEDUC e geocodificacao posterior.
    saida = pd.DataFrame(index=df.index)
    for destino in ("nome", "municipio", "endereco", "codigo_inep", "rede", "situacao"):
        saida[destino] = df[m[destino]].astype("string").fillna("").str.strip() if m[destino] else ""
    saida["latitude"] = _coord_num(df[m["latitude"]]) if m["latitude"] else float("nan")
    saida["longitude"] = _coord_num(df[m["longitude"]]) if m["longitude"] else float("nan")
    if geo_col:
        geo = df[geo_col].apply(_geolocalizacao)
        lat = pd.to_numeric(geo.map(lambda p: p[0]), errors="coerce")
        lon = pd.to_numeric(geo.map(lambda p: p[1]), errors="coerce")
        saida["latitude"] = saida["latitude"].fillna(lat)
        saida["longitude"] = saida["longitude"].fillna(lon)
    # A planilha oficial SEDUC separa tipo de via, logradouro, numero e bairro.
    if all(c in cols for c in ("endesc", "numesc", "baiesc")):
        via = df["complend"].fillna("").astype(str).str.strip() if "complend" in cols else pd.Series("", index=df.index)
        log = df["endesc"].fillna("").astype(str).str.strip()
        num = df["numesc"].fillna("").astype(str).str.strip()
        bairro = df["baiesc"].fillna("").astype(str).str.strip()
        via = via.where(via.str.upper().isin(["RUA", "AVENIDA", "PRACA", "TRAVESSA", "QUADRA"]), "")
        saida["endereco"] = (via + " " + log + ", " + num + " - " + bairro + " - Bauru/SP").str.strip()
    # Manter campos de auditoria de fontes cruzadas quando existirem no CSV.
    for extra in ("validado_inep", "fonte_cadastro", "alerta_coordenadas", "distancia_coordenadas_fontes_km"):
        if extra in cols:
            saida[extra] = df[extra].fillna("").astype(str).str.strip()
    saida = saida[saida.nome.str.len() > 0].copy()
    # Excluir coordenadas invalidadas sem descartar escola, para permitir geocodificacao.
    validas = saida.latitude.between(-90, 90) & saida.longitude.between(-180, 180)
    saida.loc[~validas, ["latitude", "longitude"]] = float("nan")
    # CSV com codigo INEP fornece id mais forte que nome.
    saida["id"] = saida.codigo_inep.mask(saida.codigo_inep == "", saida.nome + " - " + saida.municipio)
    saida = saida.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
    saida["origem"] = nome or "arquivo enviado pelo usuario"
    return saida, {"linhas_validas": len(saida), "com_coordenadas": int(saida.latitude.notna().sum()),
                   "sem_coordenadas": int(saida.latitude.isna().sum()), "colunas_detectadas": m,
                   "coluna_geolocalizacao": geo_col}


def filtrar_municipios(df: pd.DataFrame, cidades: list[str]):
    cidades_norm = {normalizar(s) for s in cidades}
    if not cidades_norm:
        return df.iloc[0:0].copy()
    return df[df.municipio.apply(normalizar).isin(cidades_norm)].reset_index(drop=True)



def apenas_escolas_estaduais_bauru(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Filtro rigoroso: MUNICÍPIO de Bauru, nunca 'Diretoria de Bauru'.

    CO_MUNICIPIO == 3506003 (IBGE) e aceito em arquivos INEP.
    TP_DEPENDENCIA: 2 = estadual. Escolas fechadas no Censo (TP_SITUACAO!=1)
    sao excluidas quando esta informacao estiver disponivel.
    """
    if "municipio" not in df or df["municipio"].astype(str).str.strip().eq("").all():
        raise ValueError("Arquivo sem coluna de MUNICIPIO. Nao e seguro filtrar apenas pela diretoria regional de Bauru.")
    cidades = df["municipio"].map(normalizar)
    mascara = cidades.eq("bauru") | df["municipio"].astype(str).str.strip().isin([CODIGO_IBGE_BAURU, CODIGO_IBGE_BAURU+".0"])
    filtrado = df[mascara].copy()
    count_city = len(filtrado)
    if "rede" in filtrado:
        rede = filtrado["rede"].fillna("").astype(str).map(normalizar)
        estadual = rede.isin(["", "2", "estadual", "estadual_se", "rede_estadual", "rede_estadual_se", "estado", "2_0"])
        filtrado = filtrado[estadual].copy()
    count_rede = len(filtrado)
    if "situacao" in filtrado:
        situacao = filtrado["situacao"].fillna("").astype(str).map(normalizar)
        ativa = situacao.isin(["", "1", "ativa", "em_atividade", "em_funcionamento", "escola_em_funcionamento_e_sem_restricao_de_atendimento", "1_0"])
        filtrado = filtrado[ativa].copy()
    filtrado = filtrado.reset_index(drop=True)
    # O codigo IBGE tambem identifica Bauru, mas exportamos o nome para leitura humana.
    filtrado.loc[:, "municipio"] = "Bauru"
    return filtrado, {"total_origem": len(df), "municipio_bauru": count_city,
                      "estaduais_bauru": count_rede, "estaduais_ativas_bauru": len(filtrado),
                      "removidas": len(df)-len(filtrado)}


def csv_padronizado(df: pd.DataFrame) -> bytes:
    """CSV UTF-8 BOM (abre com acentos no Excel), virgula e ponto decimal."""
    colunas = [x for x in ["codigo_inep", "nome", "municipio", "endereco", "latitude", "longitude", "rede", "situacao", "origem", "validado_inep", "alerta_coordenadas", "distancia_coordenadas_fontes_km"] if x in df]
    return df[colunas].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def cruzar_seduc_inep(seduc: pd.DataFrame, inep: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """SEDUC define o cadastro espacial; INEP valida por codigo, sem duplicar registros.

    Somente correspondencia por codigo INEP e considerada confirmacao.
    Nomes nao sao usados como identificadores univocos.
    """
    s, _ = apenas_escolas_estaduais_bauru(seduc)
    i, _ = apenas_escolas_estaduais_bauru(inep)
    s = s.copy()
    codigos = set(i["codigo_inep"].fillna("").astype(str).str.strip().tolist()) - {""}
    s["validado_inep"] = s["codigo_inep"].fillna("").astype(str).str.strip().isin(codigos)
    i_por_codigo = i.set_index("codigo_inep")
    s["distancia_coordenadas_fontes_km"] = ""
    s["alerta_coordenadas"] = ""
    for idx, row in s.iterrows():
        cod = str(row["codigo_inep"]).strip()
        if cod not in codigos:
            s.at[idx, "alerta_coordenadas"] = "NAO_CONSTA_NO_INEP_EXPORTADO"
            continue
        other = i_por_codigo.loc[cod]
        if isinstance(other, pd.DataFrame):
            other = other.iloc[0]
        nums = [row["latitude"], row["longitude"], other["latitude"], other["longitude"]]
        if any(pd.isna(v) for v in nums):
            s.at[idx, "alerta_coordenadas"] = "COORDENADAS_AUSENTES_EM_UMA_FONTE"
            continue
        lat1, lon1, lat2, lon2 = (float(x) for x in nums)
        distancia = 111.195 * math.hypot(lat1-lat2, math.cos(math.radians(lat1))*(lon1-lon2))
        s.at[idx, "distancia_coordenadas_fontes_km"] = round(distancia, 3)
        if distancia > 0.2:
            s.at[idx, "alerta_coordenadas"] = "CONFERIR_COORDENADAS"
    s["origem"] = "SEDUC-SP; INEP quando validado por codigo"
    return s.reset_index(drop=True), {"base_seduc":len(s), "base_inep":len(i),
                                   "coincidencias_codigo_inep":int(s.validado_inep.sum()),
                                   "nao_conferidas":int((~s.validado_inep).sum()),
                                   "coordenadas_divergentes_mais_200m":int((s.alerta_coordenadas == 'CONFERIR_COORDENADAS').sum())}

def baixar_base_2026(destino: str | Path | None = None) -> Path:
    destino = Path(destino or RAIZ / "data" / "escolas_sp_2026.xlsx")
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(DATA_URL_2026, timeout=(12, 90), headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    if not r.content.startswith(b"PK") or len(r.content) < 1000:
        raise ValueError("Download nao retornou um XLSX valido. Use o download manual no portal oficial.")
    destino.write_bytes(r.content)
    return destino


def chave_cache(df: pd.DataFrame, versao: str = "osrm_2") -> str:
    pares = [(round(float(r.latitude), 6), round(float(r.longitude), 6)) for r in df.itertuples()]
    return hashlib.sha256(json.dumps([versao, pares]).encode()).hexdigest()[:20]


def matriz_osrm(df: pd.DataFrame, *, pasta_cache: Path | None = None,
                forcar: bool = False) -> tuple[list[list[float]], list[list[float]], str]:
    """A matriz nao direcionada e MEDIA de i->j e j->i.

    Retorna matriz simetrizada, matriz direcional original e origem cache/API.
    "+inf" = ausencia de via nos dois sentidos.
    """
    n = len(df)
    if n < 2 or n > 25:
        raise ValueError("OSRM publico: selecione entre 2 e 25 pontos por chamada.")
    if df[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Todos os pontos precisam de coordenadas para OSRM.")
    pasta = Path(pasta_cache or CACHE)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"matriz_{chave_cache(df)}.json"
    if arquivo.is_file() and not forcar:
        d = json.loads(arquivo.read_text(encoding="utf-8"))
        return (_reconstruir(d["simetrica"]), _reconstruir(d["direcional"]), "cache local")
    coords = ";".join(f"{p.longitude:.7f},{p.latitude:.7f}" for p in df.itertuples())
    r = requests.get(f"{OSRM}/table/v1/driving/{coords}", params={"annotations": "distance"},
                     timeout=(12, 70), headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "Ok" or not data.get("distances"):
        raise ValueError(f"OSRM nao retornou matriz valida: {data.get('message', data.get('code'))}")
    bruto = data["distances"]
    if len(bruto) != n or any(len(row) != n for row in bruto):
        raise ValueError("OSRM retornou matriz com tamanho inesperado")
    direcional = [[0.0 if i == j else (float(bruto[i][j])/1000 if bruto[i][j] is not None else math.inf)
                   for j in range(n)] for i in range(n)]
    simetrica = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            # Ambos os sentidos devem ser viaveis no grafo fisico nao direcionado.
            a, b = direcional[i][j], direcional[j][i]
            w = (a+b)/2 if math.isfinite(a) and math.isfinite(b) else math.inf
            simetrica[i][j] = simetrica[j][i] = w
    # Evidencia da consulta: hash da resposta, horario UTC e distancia de encaixe na rua.
    snaps_src = [float(x.get("distance", 0)) for x in data.get("sources", [])] if isinstance(data.get("sources"), list) else []
    snaps_dst = [float(x.get("distance", 0)) for x in data.get("destinations", [])] if isinstance(data.get("destinations"), list) else []
    info = {"simetrica": _para_json(simetrica), "direcional": _para_json(direcional),
            "obs": "Km, simetrizacao por media de ida e volta, dados OSRM; sem transito.", "pontos": df[["latitude", "longitude"]].to_dict("records"),
            "consulta_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "endpoint": "https://router.project-osrm.org/table/v1/driving", "perfil": "driving",
            "sha256_resposta_osrm": hashlib.sha256(getattr(r, "content", json.dumps(data, sort_keys=True).encode("utf-8"))).hexdigest(),
            "snap_origens_m": snaps_src, "snap_destinos_m": snaps_dst,
            "distancia_maxima_encaixe_m": max(snaps_src+snaps_dst) if snaps_src or snaps_dst else None,
            "fonte": "HTTP 200, code=Ok, API OSRM"}
    arquivo.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return simetrica, direcional, "API OSRM (salvo em cache)"


def _para_json(matriz):
    return [[round(v, 6) if math.isfinite(v) else None for v in linha] for linha in matriz]


def _reconstruir(matriz):
    return [[float(v) if v is not None else math.inf for v in linha] for linha in matriz]


def aplicar_restricoes(matriz: list[list[float]], limite: float | None = None,
                       bloqueios: list[tuple[int, int]] | None = None) -> list[list[float]]:
    n = len(matriz)
    saida = [list(row) for row in matriz]
    for i in range(n):
        for j in range(n):
            if i != j and limite is not None and saida[i][j] > limite + 1e-10:
                saida[i][j] = math.inf
    for i,j in bloqueios or []:
        if i < 0 or j < 0 or i >= n or j >= n or i == j:
            raise ValueError("Bloqueio de aresta invalido.")
        saida[i][j] = saida[j][i] = math.inf
    return saida


def geocodificar_nome(nome: str, municipio: str, endereco: str = "", email: str = "") -> tuple[float, float] | None:
    """Uma requisicao por chamada; interface limita quantidades e espacamento."""
    q = ", ".join(x for x in [endereco, nome, municipio, "SP", "Brasil"] if x)
    headers = {"User-Agent": USER_AGENT + (f" contato: {email.strip()}" if email else "")}
    resposta = requests.get(f"{NOMINATIM}/search", params={"q": q, "format": "json", "limit": 1,
                     "countrycodes": "br"}, timeout=30, headers=headers)
    resposta.raise_for_status()
    itens = resposta.json()
    if not itens:
        return None
    lat, lon = float(itens[0]["lat"]), float(itens[0]["lon"])
    # Restricao ao estado de SP para evitar falsos positivos fora da regiao.
    if not (-26 <= lat <= -19 and -54 <= lon <= -44):
        return None
    return lat, lon


def geocodificar_poucas(df: pd.DataFrame, indices: list[int], email: str = "") -> tuple[pd.DataFrame, list[str]]:
    if len(indices) > 5:
        raise ValueError("Limite de 5 consultas por operacao para respeitar o servidor publico.")
    df = df.copy()
    relatorio = []
    for k, i in enumerate(indices):
        if k:
            time.sleep(1.2)
        try:
            coords = geocodificar_nome(str(df.at[i, "nome"]), str(df.at[i, "municipio"]),
                                       str(df.at[i, "endereco"]), email)
            if coords:
                df.at[i, "latitude"], df.at[i, "longitude"] = coords
                relatorio.append(f"Encontrada: {df.at[i, 'nome']}")
            else:
                relatorio.append(f"Nao encontrada: {df.at[i, 'nome']}")
        except requests.RequestException as e:
            relatorio.append(f"Erro ao consultar {df.at[i, 'nome']}: {str(e)[:80]}")
    return df, relatorio


def geometria_rota_osrm(df: pd.DataFrame, rota: list[int], *, pasta_cache: Path | None = None) -> tuple[list[list[float]], float, str]:
    """Uma requisicao para a rota INTEIRA, como trilha para exibir no mapa.

    Km da rota geometrica representam percurso dirigido de fato, enquanto
    custo objetivo e simetrizado, podendo diferir.
    """
    pasta = Path(pasta_cache or CACHE)
    pasta.mkdir(parents=True, exist_ok=True)
    chave = chave_cache(df, "geo_3") + "_" + hashlib.sha256(json.dumps(rota).encode()).hexdigest()[:12]
    arq = pasta / f"geometria_{chave}.json"
    if arq.exists():
        data = json.loads(arq.read_text(encoding="utf-8"))
        return data["linha"], data["km"], "cache local"
    coords = ";".join(f"{df.iloc[i]['longitude']:.7f},{df.iloc[i]['latitude']:.7f}" for i in rota)
    res = requests.get(f"{OSRM}/route/v1/driving/{coords}",
                  params={"overview": "full", "geometries": "geojson", "steps": "false"},
                  headers={"User-Agent": USER_AGENT}, timeout=(12,70))
    res.raise_for_status()
    data = res.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM nao retornou geometria: {data.get('message', data.get('code'))}")
    percurso = data["routes"][0]
    linha = [[lat, lon] for lon,lat in percurso["geometry"]["coordinates"]]
    km = float(percurso["distance"])/1000
    arq.write_text(json.dumps({"linha": linha, "km": km,
            "consulta_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sha256_resposta_osrm": hashlib.sha256(getattr(res, "content", json.dumps(data).encode("utf-8"))).hexdigest(),
            "origem": "API OSRM"}, ensure_ascii=False), encoding="utf-8")
    return linha, km, "API OSRM"
