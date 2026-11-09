# Roteiro de apresentação - 10 minutos (5 integrantes)

> Preencha os nomes abaixo, e realize um ensaio cronometrado. Todos devem entender e ser capazes de explicar os três modos.

**Integrante 1 - 0:00 a 1:30 (contexto)**  
Apresente o problema real: um técnico sai de uma base, percorre escolas estaduais e retorna. Explique a diferença entre simplesmente montar uma rota e **detectar/construir caminho e ciclo hamiltoniano**.

**Integrante 2 - 1:30 a 3:00 (modelo)**  
Explique `G=(V,E)`: cada escola e a base é vértice, aresta é deslocamento permitido, peso em km. Mostre que o grafo é não direcionado e como a média das distâncias OSRM de ida/volta foi definida. Comente efeitos do limite em km.

**Integrante 3 - 3:00 a 4:45 (exato)**  
Mostre `src/algoritmos.py`: busca em profundidade/backtracking, marcação de visitados por máscara de bits, poda de custo. Em `Corredor`, execute caminho e depois ciclo: o primeiro existe, o segundo não.

**Integrante 4 - 4:45 a 6:30 (heurística)**  
Apresente vizinho mais próximo e 2-opt, explicando que a heurística não garante ótimo ou inexistência. No cenário pequeno, execute comparação e veja tempo/custo.

**Integrante 5 - 6:30 a 8:30 (software, testes)**  
Mostre a interface redesenhada: Visão geral, Resultados e rota e Experimentos. O mapa e as interpretações aparecem após executar a roteirização; a metodologia está no código e na documentação, não nas telas. Explique instâncias de tamanhos 5, 9, 12 e 16, casos sem solução e timeouts.

**Discussão conjunta - 8:30 a 10:00**  
Apresente limitações, fontes, robustez offline, eventuais diferenças do OSRM (assimetria), declaração de uso de IA. Prepare-se para uma nova instância solicitada pelo professor.

## Demonstrações rápidas sugeridas

1. Corredor - **caminho** - Exato: rota válida.
2. Corredor - **ciclo** - Exato: ausência comprovada.
3. Completo 5 pontos - **mínimo** - comparação de dois algoritmos.
4. Completo 16 pontos - **mínimo** - mostrar rapidez heurística e limite do exato.
5. Base de escolas reais: importar CSV/XLSX 2026, mostrar a base fixa da Unidade Regional de Ensino de Bauru e executar uma rota OSRM se já houver conexão ou cache disponível.

## Perguntas prováveis e respostas

**Por que é hamiltoniano?** Porque cada vértice-escola aparece uma única vez no percurso; num ciclo a base retorna ao final.

**E se não existir um ciclo?** O exato pode comprovar a inexistência quando encerra a busca; a heurística não pode.

**Como garantir o mínimo?** Somente busca exata concluída; se houver timeout não há garantia.

**Por que o peso OSRM é média ida/volta?** Para criar grafo matematicamente não direcionado. Em operação real seria melhor modelar o grafo dirigido.

**Por que não usaram NetworkX?** Os algoritmos centrais estão em Python puro e podem ser auditados. Folium e matplotlib só exibem dados.

**Quais são os dados fictícios?** Os pontos e pesos dos cinco exemplos didáticos offline. A base 2026 é real apenas após a importação do arquivo oficial e validação.
