"""Baixa/abre fontes oficiais e gera CSVs EXCLUSIVAMENTE do municipio de Bauru.

Exemplos (Windows, na pasta do projeto):
  python scripts/gerar_csvs_bauru.py --download-seduc
  python scripts/gerar_csvs_bauru.py --seduc "C:/Downloads/ENDERECO_ESCOLAS_082026.xlsx" --inep "C:/Downloads/inep_export.csv"

Nao inventa escolas nem coordenadas. O INEP pode fornecer registros sem latitude/longitude.
"""
import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.dados import (RAIZ, baixar_base_2026, ler_escolas, apenas_escolas_estaduais_bauru,
                       csv_padronizado, cruzar_seduc_inep)


def processar_origem(arquivo: Path, saida: Path, etiqueta: str):
    tabela, meta = ler_escolas(arquivo)
    filtro, resumo = apenas_escolas_estaduais_bauru(tabela)
    if filtro.empty:
        raise ValueError(f"Arquivo {arquivo} nao contem escolas estaduais no municipio de Bauru. "
                         "Confira a coluna Municipio e a rede (nao confunda Diretoria de Bauru com cidade de Bauru).")
    saida.write_bytes(csv_padronizado(filtro))
    print(f"{etiqueta}: {len(filtro)} escolas estaduais em Bauru de {len(tabela)} registros, "
          f"{int(filtro.latitude.notna().sum())} com coordenadas; CSV: {saida}")
    return filtro


def main(argv=None):
    cli = argparse.ArgumentParser(description="Exportar SEDUC e INEP para CSV - Bauru apenas")
    cli.add_argument("--download-seduc", action="store_true", help="Baixar XLSX SEDUC 2026 automaticamente (precisa de internet)")
    cli.add_argument("--seduc", type=Path, help="XLSX/CSV SEDUC obtido no portal oficial")
    cli.add_argument("--inep", type=Path, help="CSV/XLSX exportado no Catalogo do INEP (Bauru-SP, Estadual)")
    cli.add_argument("--saida", type=Path, default=ROOT / "data", help="Pasta para salvar os CSVs")
    args = cli.parse_args(argv)
    args.saida.mkdir(parents=True, exist_ok=True)
    caminho_seduc = args.seduc
    if args.download_seduc:
        try:
            caminho_seduc = baixar_base_2026(args.saida / "fonte_original_seduc_2026.xlsx")
        except Exception as exc:
            print(f"Falha no download automatico SEDUC: {exc}",file=sys.stderr)
            print("Baixe manualmente em https://dados.educacao.sp.gov.br/dataset/escolas-ativas ",file=sys.stderr)
            print("e execute --seduc CAMINHO_DO_ARQUIVO.xlsx",file=sys.stderr)
            return 2
    if not caminho_seduc and not args.inep:
        cli.error("Informe --download-seduc ou --seduc ou --inep")
    try:
        seduc = processar_origem(caminho_seduc, args.saida / "escolas_bauru_seduc_2026.csv", "SEDUC-SP") if caminho_seduc else None
        inep = processar_origem(args.inep, args.saida / "escolas_bauru_inep_exportacao.csv", "INEP") if args.inep else None
        if seduc is not None and inep is not None:
            consolidado, meta = cruzar_seduc_inep(seduc,inep)
            arq = args.saida / "escolas_bauru_consolidadas.csv"
            base = consolidado.copy()
            # Acrescenta validacao por codigo INEP no arquivo final.
            colunas = [c for c in ["codigo_inep", "nome", "municipio", "endereco", "latitude", "longitude", "rede", "origem", "validado_inep", "alerta_coordenadas", "distancia_coordenadas_fontes_km"] if c in base]
            arq.write_bytes(base[colunas].to_csv(index=False).encode("utf-8-sig"))
            print(f"CONSOLIDADO: {len(base)} unidades distintas, {meta['coincidencias_codigo_inep']} conferidas pelo codigo INEP; CSV: {arq}")
            so_inep = inep[~inep["codigo_inep"].isin(set(seduc["codigo_inep"]))]
            exclusivos = args.saida / "escolas_bauru_inep_nao_seduc.csv"
            exclusivos.write_bytes(csv_padronizado(so_inep))
            print(f"INEP APENAS: {len(so_inep)} registros para conferência: {exclusivos}")
            revisoes = base[base["alerta_coordenadas"].astype(str).str.len() > 0]
            revisoes.to_csv(args.saida / "revisao_cadastros_bauru.csv", index=False, encoding="utf-8-sig")
            print(f"ALERTAS SEDUC: {len(revisoes)}; confira também as {len(so_inep)} exclusivas INEP.")
        elif seduc is not None:
            print("INEP nao informado; adicione --inep arquivo.csv para cruzar fontes.")
        else:
            print("SEDUC nao informado. O CSV INEP pode nao conter coordenadas: forneca --seduc para cruzamento.")
    except (ValueError, OSError) as exc:
        print(f"ERRO: {exc}",file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
