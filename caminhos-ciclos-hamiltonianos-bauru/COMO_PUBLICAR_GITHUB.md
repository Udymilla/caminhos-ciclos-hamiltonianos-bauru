# Publicar este projeto no GitHub (Windows)

1. Entre em <https://github.com/new> e crie um repositório **vazio** com o nome `caminhos-ciclos-hamiltonianos-bauru`. Escolha público ou privado de acordo com as regras do professor.
2. **Não marque** a criação de README, `.gitignore` ou licença no GitHub, pois esses arquivos já estão aqui.
3. Extraia o ZIP e entre na pasta `caminhos-ciclos-hamiltonianos-bauru`.
4. Clique com o botão direito dentro da pasta e abra **Git Bash Here** (ou abra um terminal na pasta com Git instalado).
5. Execute os comandos abaixo **um de cada vez**, substituindo o endereço `https://github.com/SEU-USUARIO/caminhos-ciclos-hamiltonianos-bauru.git` pela URL HTTPS do seu repositório:

```bash
git init -b main
git add .
git commit -m "Projeto Hamiltonianos Bauru - versao de entrega"
git remote add origin https://github.com/SEU-USUARIO/caminhos-ciclos-hamiltonianos-bauru.git
git push -u origin main
```

6. Entre na página do repositório e confira se aparecem `app.py`, `README.md`, `src/`, `tests/`, `data/` e `requirements.txt`.
7. Copie o endereço do repositório para o relatório e para a entrega ao professor.

Se `git commit` pedir a identidade, configure o nome e o e-mail de sua conta GitHub, **sem digitar sua senha no terminal**, por exemplo:

```bash
git config --global user.name "NOME QUE DESEJA EXIBIR"
git config --global user.email "EMAIL-DA-SUA-CONTA"
```

O GitHub pode abrir o navegador para autenticação. Não publique senhas, tokens, chaves ou arquivos com dados pessoais. A versão de relatório PDF disponível em etapas anteriores ainda tinha campos `[PREENCHER]`: **não inclua esse PDF incompleto**. Se já possui o PDF preenchido, publique-o separadamente ou adicione a versão definitiva à pasta `docs/` e faça outro commit.

Se receber `remote origin already exists`, use `git remote -v` para conferir o remoto existente em vez de executar `git remote add` de novo.
