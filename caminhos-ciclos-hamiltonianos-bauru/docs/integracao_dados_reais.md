# Bases reais integradas - Bauru, SP (2026)

**Status da versão 5:** os dois arquivos enviados pelo grupo foram incluídos em `data/fontes_originais/`; os CSVs normalizados e filtrados estão em `data/` e são carregados automaticamente pelo aplicativo.

- `escolas_bauru_consolidadas.csv`: **62 unidades SEDUC**, 57 conferidas por código INEP, todas com coordenadas.
- `escolas_bauru_seduc_2026.csv`: 62 unidades SEDUC.
- `escolas_bauru_inep_exportacao.csv`: 61 registros INEP da rede estadual em funcionamento e sem restrição de atendimento (60 com coordenadas preenchidas).
- `escolas_bauru_inep_nao_seduc.csv`: quatro registros exclusivos da exportação INEP, preservados para revisão, mas não inseridos automaticamente na base principal.
- `revisao_cadastros_bauru.csv`: 12 apontamentos de diferença cadastral ou geográfica, conforme `relatorio_integracao_bauru_2026.json`.

**Importante:** esses arquivos já estão prontos; não é necessário baixá-los novamente para testar. Os dados eram completos o suficiente para não exigir geocodificação em massa. O único endereço sem coordenada na exportação INEP possui correspondência com coordenada SEDUC.

## Como usar

1. Dê dois cliques em `iniciar_windows.bat` e aguarde a abertura do Streamlit.
2. Deixe selecionada a opção inicial **Arquivo oficial no computador**. O aplicativo deve informar 62 escolas.
3. Opcionalmente marque **Mostrar somente escolas conferidas nas duas fontes** (57).
4. Selecione até 24 escolas. A base é adicionada automaticamente: **Unidade Regional de Ensino de Bauru**, latitude **-22.325573**, longitude **-49.091570** (conferir no mapa). Não há campos para alterá-la.
5. Em **Tipo de problema**, escolha caminho hamiltoniano, ciclo hamiltoniano ou ciclo mínimo e execute os algoritmos.
6. Em **Distâncias**, escolha **Distâncias por ruas (OSRM)** para obter km rodoviários; precisa de rede na primeira consulta e até 25 vértices por consulta. O app usa cache JSON.
7. Para comparar com testes garantidamente executáveis sem internet, escolha os cenários **Demonstração offline**, que são fictícios e rotulados.

## Pontos a conferir

- Escola `35049645`: diferença aproximada de **1,78 km** entre coordenadas SEDUC e INEP; confirmar local.
- Escola `35457802`: diferença aproximada de **0,29 km** entre as duas fontes; confirmar entrada/acesso.
- Quatro escolas somente INEP: CSV específico, sem inclusão automática na rota.
- A SEDUC e o INEP podem usar diferentes definições/coberturas de escola da rede estadual.

Os pesos de distância por rua e a geometria OSRM **ainda não foram gerados**, porque dependem de consultas à API. A base fixa já foi definida, mas os valores OSRM ainda precisam ser consultados e salvos em cache.
