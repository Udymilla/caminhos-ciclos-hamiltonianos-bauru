# Caminhos e Ciclos Hamiltonianos — Escolas de Bauru

Projeto acadêmico da disciplina **Teoria dos Grafos — Tema 6**, aplicado à roteirização de visitas técnicas às escolas estaduais do **município de Bauru (SP)**.

## Integrantes — Grupo 1

- Karina Zaniti Sanches
- Leonardo Valentim do Nascimento
- Lucas Leão Franco Paes
- Natasha Cristine Barbosa Teixeira
- Udymilla Gonçalves Chagas

## O que o sistema faz

A aplicação representa as escolas selecionadas como vértices de um grafo ponderado. A **Unidade Regional de Ensino de Bauru** é o vértice 0 (ponto inicial fixo), nas coordenadas aproximadas `-22.325573, -49.091570`.

Oferece três operações:

1. **Caminho hamiltoniano:** visitar cada vértice uma vez, sem precisar voltar à base.
2. **Ciclo hamiltoniano:** visitar cada vértice uma vez e voltar à base.
3. **Ciclo hamiltoniano mínimo:** buscar o ciclo válido de menor custo.

Os algoritmos principais foram implementados em Python:

- **Backtracking com poda:** busca exata, capaz de demonstrar otimalidade apenas se a busca terminar sem atingir o limite de tempo.
- **Vizinho mais próximo + 2-opt:** heurística rápida, que pode obter boas soluções, mas não garante a melhor.

A interface usa **Streamlit**, os mapas usam **Folium** e os gráficos utilizam **Matplotlib**. A base integra dados da SEDUC-SP e do INEP, com **62 registros principais** do município de Bauru. As distâncias por ruas vêm de consultas à API **OSRM** (OpenStreetMap), com armazenamento em cache quando disponível.

## Instalação e execução

**Windows:** instale Python 3.11 ou superior, baixe o projeto, extraia o conteúdo e execute `iniciar_windows.bat`. Em seguida, acesse <http://localhost:8501>.

**Linux / macOS:** `bash iniciar_linux_mac.sh`.

Ou execute manualmente, no terminal aberto na pasta do projeto:

```bash
python -m venv .venv
# Ative o ambiente virtual (Windows: .venv\Scripts\activate; Linux/macOS: source .venv/bin/activate)
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O cálculo inicial das distâncias OSRM requer acesso à internet. É possível utilizar os **cenários de teste offline**, claramente identificados como didáticos.

## Testes

```bash
python -m pytest -q
```

Foram aprovados **58 testes automatizados** na versão V7/V8 (revalidados no empacotamento para o GitHub). Isso não substitui testes visuais da aplicação no computador da apresentação.

## Resultados de referência — consultas OSRM (09/11/2026)

A pasta `data/resultados_osrm/` contém matrizes, mapas HTML, JSON de evidências e CSV de comparação obtidos pelo grupo na validação em Windows. Para as três instâncias, com a base incluída:

| Vértices | Exato (km) | Heurística (km) | Otimalidade do exato |
|---|---:|---:|---|
| 5 | 41,645 | 41,645 | Comprovada |
| 8 | 61,455 | 63,385 | Comprovada |
| 12 | 65,268 | 65,268 | **Não comprovada:** busca interrompida aos 4 s |

**Atenção:** a função objetivo usa uma **matriz não direcionada** calculada pela média das distâncias de ida e volta do OSRM. O comprimento efetivo do caminho exibido no mapa pode ser diferente. O OSRM usa rotas da rede viária e não considera trânsito em tempo real nem acesso a portões.

Para reproduzir a validação com conexão, execute `validar_distancias_windows.bat`, que chama `scripts/validar_osrm_real.py`.

## Organização

```text
app.py                      Interface do usuário
src/algoritmos.py           Backtracking, heurística, validação de rotas
src/dados.py                Dados e consultas ao OSRM
src/base_fixa.py            Unidade Regional de Ensino (vértice 0)
src/mapas.py                Visualização das rotas
src/apresentacao.py         Explicações dos resultados
src/experimentos.py         Experimentos e comparação
scripts/                    Importação, validação OSRM, relatórios
tests/                      Testes automatizados
data/                       CSVs consolidados, exemplos e evidências
requirements.txt            Dependências Python
```

## Fontes e limitações

- [SEDUC-SP, dados de escolas](https://dados.educacao.sp.gov.br/)
- [INEP, Catálogo de Escolas](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas)
- [OSRM](https://project-osrm.org/)
- [OpenStreetMap](https://www.openstreetmap.org/)

As coordenadas e os cadastros de escolas podem apresentar divergências ou desatualizações. Os dados originais podem ser obtidos nas fontes acima. As escolas incluídas no conjunto de experimentos OSRM foram selecionadas com base na auditoria geográfica.

