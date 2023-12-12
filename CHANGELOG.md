# CHANGELOG

#### Aqui serão registradas todas as alterações realizadas no projeto.
---

### 2023-12-11
- 🔧 fix(changelog.py): corrige a classe ChangelogGenerator para adicionar um método faltante
- ✨ feat(changelog.py): adiciona suporte para fornecer um diretório como argumento para gerar o changelog
- A classe ChangelogGenerator foi modificada para adicionar um método faltante chamado `gerar_changelog(diretorio)`. Esse método permite que um diretório seja fornecido como argumento para gerar o changelog nesse diretório específico. Isso torna o script mais flexível, pois agora é possível gerar o changelog em diferentes diretórios, não apenas no diretório atual.

### 2023-12-11
- 📝 docs(.gitignore): adiciona padrões de arquivos a serem ignorados
- 📝 docs(README.md): atualiza links e informações do arquivo README.md

- O arquivo .gitignore foi adicionado para especificar os padrões de arquivos que devem ser ignorados pelo Git. Isso inclui arquivos de atalhos do Windows, arquivos do Mac, arquivos do VSCode, arquivos de ambiente, cache e arquivos compilados, logs e dados temporários.

- O arquivo README.md foi atualizado para corrigir os links e informações. Agora, o link para clonar o repositório aponta para o repositório correto. Além disso, o link para o site do autor foi substituído pelo link para o seu próprio site.

### 2023-12-11
- 🔥 chore(.DS_Store): remove o arquivo .DS_Store
- 📝 docs(CHANGELOG.md): atualiza o arquivo CHANGELOG.md
- 🔨 refactor(changelog.py): adiciona hífen no início de cada mensagem de log

- O arquivo .DS_Store foi removido, pois é um arquivo específico do sistema operacional e não deve ser versionado no repositório.

- O arquivo CHANGELOG.md foi atualizado para corrigir links e informações. O link para clonar o repositório foi corrigido para apontar para o repositório correto. Além disso, o link para o site do autor foi substituído pelo link para o seu próprio site.

- No arquivo changelog.py, foi adicionado um hífen no início de cada mensagem de log obtida dos commits. Isso melhora a legibilidade do changelog gerado.
