"""Gera um relatorio tecnico PDF a partir da bateria offline ja executada.
Execute na raiz: python scripts/gerar_relatorio.py
"""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image, HRFlowable
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

OUT = ROOT/'docs'/'relatorio_tecnico.pdf'
DATA = ROOT/'data'/'experimentos_offline_referencia.csv'
df = pd.read_csv(DATA)
font_dir = Path('/usr/share/fonts/truetype')
if (font_dir/'dejavu'/'DejaVuSans.ttf').exists():
    p=font_dir/'dejavu'
else:
    p=Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('DV',str(p/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVB',str(p/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DV', normal='DV', bold='DVB')

NAVY=HexColor('#163452')
BLUE=HexColor('#28558c')
LIGHT=HexColor('#f1f5fa')
GRAY=HexColor('#53677d')
WHITE=colors.white

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CapaP',fontName='DVB',fontSize=23,leading=30,textColor=NAVY,spaceAfter=16))
styles.add(ParagraphStyle(name='LeadP',fontName='DV',fontSize=12,leading=18,textColor=BLUE,spaceAfter=13))
styles.add(ParagraphStyle(name='HeadingP',fontName='DVB',fontSize=12.6,leading=18,textColor=NAVY,spaceBefore=11,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='SubheadingP',fontName='DVB',fontSize=10.3,leading=15,textColor=BLUE,spaceBefore=11,spaceAfter=6,keepWithNext=True))
styles.add(ParagraphStyle(name='BodyP',fontName='DV',fontSize=9.05,leading=14.8,textColor=HexColor('#233348'),spaceAfter=6))
styles.add(ParagraphStyle(name='SmallP',fontName='DV',fontSize=7.6,leading=11.8,textColor=GRAY,spaceAfter=2))
styles.add(ParagraphStyle(name='HeadCell',fontName='DVB',fontSize=8,leading=11,textColor=WHITE))
styles.add(ParagraphStyle(name='Cell',fontName='DV',fontSize=8,leading=11,textColor=NAVY))
styles.add(ParagraphStyle(name='CoverDetail',fontName='DV',fontSize=10,leading=18,textColor=GRAY,spaceAfter=4))

story=[]
P=lambda t,st='BodyP':Paragraph(t,styles[st])
H=lambda t: story.append(P(t,'HeadingP'))
B=lambda t: story.append(P(t))
S=lambda t:story.append(P(t,'SubheadingP'))


def page(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setFillColor(NAVY)
    canvas.rect(0,h-15, w,15,fill=1,stroke=0)
    canvas.setStrokeColor(HexColor('#cdd9e5'))
    canvas.line(43,46,w-43,46)
    canvas.setFont('DV',7.6)
    canvas.setFillColor(GRAY)
    canvas.drawString(44,33,'Teoria dos Grafos | Caminhos e Ciclos Hamiltonianos | Bauru')
    canvas.drawRightString(w-44,33,f'Página {doc.page}')
    canvas.restoreState()

story.extend([Spacer(1,54),P('RELATÓRIO TÉCNICO','SmallP'),
              P('Caminhos e Ciclos Hamiltonianos\nna Roteirização de Visitas Técnicas','CapaP'),
              P('Aplicação acadêmica na município de Bauru (SP) · Tema 6','LeadP'),
              HRFlowable(width='100%',thickness=2,color=BLUE,spaceBefore=7,spaceAfter=25),
              P('<b>Disciplina:</b> Teoria dos Grafos','CoverDetail'),
              P('<b>Grupo:</b> [preencher nome ou número]','CoverDetail'),
              P('<b>Integrantes (5):</b> [preencher nomes completos]','CoverDetail'),
              P('<b>Professor(a):</b> [preencher]','CoverDetail'),
              P('<b>Data prevista de entrega:</b> 17/11/2026','CoverDetail'),
              Spacer(1,34),
              P('<b>Estado do documento:</b> relatório-base com experimentos offline de referência; '
                'requer complementação com nomes, participação individual e resultados OSRM '
                'obtidos e validados pelo grupo.','BodyP'),
              Spacer(1,40),
              P('Fonte pública prioritária: Secretaria da Educação do Estado de São Paulo (Escolas Ativas, 2026).','SmallP'),
              PageBreak()])

H('1 · Resumo e objetivo')
B('Este projeto aplica os conceitos de caminho e ciclo hamiltoniano à ordenação de visitas técnicas a escolas estaduais de Bauru, exclusivamente. '
  'Cada escola é modelada como vértice, e a base de saída é um vértice adicional. O sistema permite detectar ou construir um caminho hamiltoniano, '
  'detectar ou construir um ciclo hamiltoniano e, quando exigido, buscar o ciclo de menor custo. A implementação principal é feita em Python sem bibliotecas que resolvam o problema automaticamente.')
H('2 · Motivação e problema real')
B('Uma equipe de suporte precisa visitar várias escolas e, no caso de um ciclo, retornar à base após visitar cada unidade exatamente uma vez. '
  'Uma ordem de visita escolhida manualmente pode aumentar o deslocamento. A abordagem em grafos permite representar restrições sobre deslocamentos e analisar '
  'quando existe uma sequência de visitas viável. A otimização de custo corresponde ao problema do caixeiro viajante simétrico (TSP), como especialização do ciclo hamiltoniano mínimo.')
H('3 · Definição do grafo')
B('<b>Vértices:</b> escolas estaduais selecionadas e um ponto base separado (índice 0). <b>Arestas:</b> deslocamentos entre pares de locais permitidos. '
  '<b>Tipo:</b> grafo simples, não direcionado e ponderado. <b>Peso:</b> km por rua quando calculado pelo OSRM, simetrizados pela média das distâncias de ida e volta. '
  'Quando a API não está disponível, o aplicativo disponibiliza exemplos sintéticos explicitamente identificados.')
B('<b>Restrições:</b> é possível definir uma distância máxima por aresta e excluir conexões manualmente. Uma aresta inexistente é representada por infinito positivo. '
  'A modelagem admite deslocamentos nas ruas que passem pelo mesmo endereço físico sem que isso constitua uma segunda visita formal ao vértice-escola. '
  'Um ciclo hamiltoniano simples exige pelo menos três vértices.')
H('4 · Distinção dos três modos')
for label,body in [
    ('Caminho hamiltoniano','Uma sequência que começa na base e contempla todos os vértices sem repeti-los, sem exigência de retorno.'),
    ('Ciclo hamiltoniano','Sequência que contempla todos os vértices e retorna à base. A base reaparece no final apenas para representar o fechamento.'),
    ('Ciclo hamiltoniano mínimo','Entre todos os ciclos viáveis, minimizar a soma dos pesos. A existência de um ciclo não implica que qualquer ciclo encontrado seja ótimo.')]:
    B(f'<b>{label}:</b> {body}')
H('5 · Origem dos dados e preparação')
B('A base de escolas estaduais sugerida é o recurso <b>Endereços de Escolas 2026</b> do portal Escolas Ativas da SEDUC-SP, com endereços e coordenadas. '
  'O Catálogo de Escolas do INEP é fonte alternativa para nomes, endereços e exportação por município/dependência administrativa. '
  'O projeto permite importar CSV ou XLSX e selecionar escolas estaduais somente de Bauru. A base fixa é a Unidade Regional de Ensino de Bauru, '
  'coordenadas -22.325573, -49.091570, definida pelo grupo e sujeita a conferência no mapa. Coordenadas escolares ausentes podem ser pesquisadas pelo Nominatim.')
B('<b>Integração realizada (29/10/2026):</b> foram incorporados os arquivos enviados pelo grupo: ' 
  'ENDERECO_ESCOLAS_082026.xlsx, da SEDUC-SP, e Análise - Tabela da lista das escolas - Detalhado.csv, do INEP. '
  'O recorte por município Bauru e rede estadual apresentou <b>62 registros SEDUC ativos</b> e <b>61 escolas INEP em funcionamento, sem restrição de atendimento</b>. '
  'O cruzamento pelo código INEP identificou <b>57 correspondências exatas</b>, com 5 registros exclusivos SEDUC e 4 exclusivos INEP. '
  'A base consolidada de rotas usa os 62 registros SEDUC, todos com coordenadas, e conserva os 4 exclusivos INEP em arquivo de revisão.')
B('<b>Qualidade dos dados:</b> duas escolas apresentam discrepância de coordenadas superior a 200 m entre as fontes; a maior é cerca de 1,78 km. '
  'Uma escola possui coordenadas vazias na exportação INEP, mas consta com coordenadas na SEDUC. '
  'A integração não verificou endereços presencialmente e não pode garantir que todas as unidades especiais são pontos apropriados para visita.')
B('<b>Distâncias:</b> a matriz OSRM por ruas ainda não foi obtida para uma seleção real de escolas, porque ainda é necessário consultar a API com a base fixa definida pelo grupo. '
  'Os resultados experimentais de referência desta seção permanecem simulados e são identificados como tal.')

H('6 · Algoritmos')
S('6.1 · Backtracking com poda - exato')
B('Parte do vértice base, registra os já visitados em máscara de bits e realiza busca em profundidade. Para o modo caminho ou ciclo, '
  'interrompe após obter um testemunho, ou comprova ausência se todas as possibilidades forem esgotadas. No modo de menor custo, '
  'ordena candidatos pelo peso, usa uma solução heurística inicial como limite superior e elimina ramos cujo custo parcial já é maior '
  'ou igual ao melhor conhecido. Se o tempo máximo expira, a solução pode ser viável, mas a prova de otimalidade/inexistência fica inconclusiva.')
S('6.2 · Vizinho mais próximo e 2-opt - heurístico')
B('Escolhe o vértice ainda não visitado com a menor aresta a partir do atual. Para ciclos, exige ao final uma ligação de volta à base. '
  'Depois, avalia inversões de segmentos (2-opt) e aceita melhorias somente se todas as arestas forem permitidas. '
  'Em grafos com restrições, a abordagem pode falhar em encontrar um ciclo existente. Mesmo quando encontra uma solução, não fornece prova de ótimo.')
S('6.3 · Custo computacional')
B('No pior caso, a busca exata precisa percorrer permutações dos n - 1 vértices restantes, com ordem de grandeza fatorial. '
  'O vizinho mais próximo pode ser implementado com seleção aproximadamente quadrática; as passagens 2-opt acrescentam um custo variável. '
  'A aplicação mede tempo de execução em milissegundos e informa se a busca exata completou ou atingiu o timeout.')

H('7 · Arquitetura e implementação')
B('<b>app.py:</b> interface de seleção, parametrização, resultado e exportação. '
  '<b>src/algoritmos.py:</b> verificação, busca exata, heurística, custo e validação de rotas. '
  '<b>src/dados.py:</b> importação, consulta Nominatim/OSRM, simetrização e cache JSON. '
  '<b>src/instancias.py:</b> instâncias offline reproduzíveis. '
  '<b>src/experimentos.py:</b> benchmark. '
  '<b>src/mapas.py:</b> Folium e mapa esquemático sem internet. '
  '<b>tests/:</b> testes automatizados com pytest. O algoritmo central não utiliza NetworkX.')

story.append(PageBreak())
H('8 · Metodologia dos testes')
B('Os testes contemplam casos simples com ótimo conhecido, comparação do algoritmo exato contra enumeração independente de permutações em grafos pequenos, '
  'casos com caminho sem ciclo, grafos desconexos, ausência de retorno, simetrização de matrizes, cache de API simulado e tamanho de instâncias de 5, 9, 12 e 16 pontos. '
  'São 43 testes automatizados com pytest, todos aprovados no ambiente de preparação, incluindo validação dos CSVs reais de Bauru. Ainda não foi feita integração real com o servidor OSRM nem teste visual da interface no Windows.')
H('9 · Resultados de referência - dados simulados')
B('Tabela obtida executando a bateria offline gerada pelo próprio programa, no modo de ciclo hamiltoniano mínimo, '
  'com limite de <b>1 segundo por execução exata</b>. Resultados de tempo dependem da máquina e não devem ser generalizados. '
  'Distâncias são aproximações didáticas, não valores medidos em ruas.')
sub=df[(df.cenario=='completo') & (df.problema=='minimo')]
rows=[[P('N vértices','HeadCell'),P('Algoritmo','HeadCell'),P('Custo (km)','HeadCell'),P('Tempo (ms)','HeadCell'),P('Ótimo comprovado','HeadCell')]]
for _,r in sub.iterrows():
    rows.append([P(str(int(r.pontos)),'Cell'),P(r.algoritmo,'Cell'),P(f'{r.distancia_km:.3f}','Cell'),
                 P(f'{r.tempo_ms:.2f}','Cell'),P('Sim' if r.otimo_comprovado else 'Não (tempo/heur.)','Cell')])
t=Table(rows,colWidths=[58,92,100,105,132],repeatRows=1,hAlign='LEFT')
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[LIGHT,WHITE]),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),
    ('LINEBELOW',(0,-1),(-1,-1),.7,HexColor('#cbd5e1'))]))
story.append(t)
story.append(Spacer(1,12))
B('Nos cenários de 5 e 9 vértices o exato terminou e certificou o ótimo. Nas instâncias de 12 e 16 vértices, '
  'a busca exata atingiu 1 segundo, portanto o custo mostrado é apenas o melhor encontrado, sem comprovação. '
  'A heurística terminou rapidamente, mas não dispõe de garantia de otimalidade. No cenário corredor há caminho e não ciclo; '
  'no cenário desconexo não há caminho nem ciclo.')

fig,ax=plt.subplots(figsize=(8.0,3.5),dpi=140)
for nome,cor in [('Exato','#194f87'),('Heuristica','#e47739')]:
    fil=sub[sub.algoritmo==nome]
    ax.plot(fil.pontos,fil.tempo_ms,marker='o',linewidth=2,label=nome,color=cor)
ax.set_yscale('symlog',linthresh=1)
ax.set_xticks([5,9,12,16]);ax.set_xlabel('Número de vértices');ax.set_ylabel('Tempo medido (ms)')
ax.grid(alpha=.18);ax.legend(frameon=False)
fig.tight_layout()
chart=ROOT/'docs'/'_grafico_relatorio.png'
fig.savefig(chart,bbox_inches='tight')
plt.close(fig)
story.append(Image(str(chart),width=16.5*cm,height=7.2*cm))
story.append(P('Figura - tempos medidos na bateria offline de referência (eixo y em escala simétrica logarítmica).','SmallP'))

H('10 · Discussão, limitações e trabalhos futuros')
B('Os resultados demonstram o custo crescente do algoritmo exato e a rapidez relativa da heurística para os cenários escolhidos. '
  'Porém, o desempenho depende da instância e do limite de tempo; não se deve afirmar que a heurística sempre supera o exato ou que produz ótima rota. '
  'Na modelagem não direcionada, a média da distância de ida e volta pode diferir da distância efetivamente percorrida; '
  'o mapa pode apresentar uma trilha dirigida pela rede viária com extensão diferente do custo matemático. '
  'Além disso, OSRM não considera trânsito, disponibilidade de estacionamento, horários de abertura nem duração da visita. '
  'Como melhoria futura, seria possível comparar também o TSP assimétrico, incluir tempo de deslocamento e manter um cache offline de dados reais verificados.')

H('11 · Validação pendente pelo grupo')
for t in [
    'Inserir nomes e dados acadêmicos, e detalhar as contribuições individuais.',
    'Confirmar no mapa ou presencialmente os dois registros com coordenadas SEDUC e INEP discrepantes e revisar unidades especiais.',
    'Conferir a localização do ponto base fixo no mapa e rodar rotas sobre a matriz OSRM por ruas.',
    'Registrar e apresentar três instâncias de diferentes tamanhos, complementando com os dados reais e um caso sem solução.',
    'Executar a aplicação Streamlit no Windows e ensaiar a demonstração ao vivo, incluindo testes pedidos pelo professor.',
]:
    B('☐ '+t)
H('12 · Participação individual do grupo (completar)')
for num in range(1,6):
    B(f'<b>Integrante {num}:</b> [nome] - [tarefas implementadas, testes realizados e revisão efetuada].')
H('13 · Uso de ferramentas de IA')
B('O projeto recebeu apoio do ChatGPT (OpenAI) na elaboração inicial do código Python, organização da arquitetura, '
  'documentação, casos de teste e redação do relatório-base. Os integrantes deverão revisar cada módulo, '
  'validar os resultados e declarar detalhadamente quais conteúdos foram mantidos, alterados e testados. '
  'A responsabilidade pela exatidão do relatório e apresentação é dos integrantes.')
H('14 · Referências')
for x in [
    'INEP. Catálogo de Escolas. https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas',
    'SEDUC-SP. Escolas Ativas, edição 2026. https://dados.educacao.sp.gov.br/dataset/escolas-ativas',
    'OpenStreetMap. Nominatim. https://nominatim.openstreetmap.org/',
    'Project OSRM. https://project-osrm.org/',
    'Python Folium. https://python-visualization.github.io/folium/',
    'Streamlit. https://streamlit.io/',
]:
    story.append(P(x,'SmallP'))

pdf=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=43,leftMargin=43,
                      topMargin=42,bottomMargin=60,title='Caminhos e Ciclos Hamiltonianos - Bauru',author='Projeto acadêmico - Grupo a preencher')
pdf.build(story,onFirstPage=page,onLaterPages=page)
chart.unlink(missing_ok=True)
print(OUT,OUT.stat().st_size)
