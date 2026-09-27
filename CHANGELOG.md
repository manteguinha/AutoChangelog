# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-09-27

### ⚠️ Incompatível

- Reescreve o AutoChangelog como pacote Python ([9d31f46](https://github.com/manteguinha/AutoChangelog/commit/9d31f461adfd823b201ebd2ae0207f5fe1a86ca3))
- O script changelog.py foi removido; use o comando autochangelog ([9d31f46](https://github.com/manteguinha/AutoChangelog/commit/9d31f461adfd823b201ebd2ae0207f5fe1a86ca3))

### Adicionado

- **changelog.py:** Adiciona verificação se o arquivo package.json existe e obtém a versão ([f9e68d8](https://github.com/manteguinha/AutoChangelog/commit/f9e68d8f29411aa48d9585b0e22cf2b3621f1009))
- **changelog.py:** Adiciona suporte para fornecer um diretório como argumento para gerar o changelog ([23eb81a](https://github.com/manteguinha/AutoChangelog/commit/23eb81aa1c0a66ed2cc5ee5484c4c8c39d2bd8c8))

### Alterado

- Update README.md ([591c7d1](https://github.com/manteguinha/AutoChangelog/commit/591c7d15139444622d42e466d23008d379cf8f44))
- **README.md:** Atualiza links e seções do README ([e437e05](https://github.com/manteguinha/AutoChangelog/commit/e437e05438cb2d2ce7b7da79514a0c30021cbdcb))
- **changelog.py:** Adiciona hífen no início de cada mensagem de log ([85d7129](https://github.com/manteguinha/AutoChangelog/commit/85d71295afdc5809a17652fa41ab94a0743293bf))
- Delete .DS_Store ([b491f51](https://github.com/manteguinha/AutoChangelog/commit/b491f5135684838bd6a658d54da0550d0b5ad4a6))
- First commit ([170c37c](https://github.com/manteguinha/AutoChangelog/commit/170c37c15221d926872b95d69b04a73e42b9095d))

### Corrigido

- **changelog.py:** Corrige a formatação do log do commit no CHANGELOG ([f9e68d8](https://github.com/manteguinha/AutoChangelog/commit/f9e68d8f29411aa48d9585b0e22cf2b3621f1009))
- **changelog.py:** Corrige a classe ChangelogGenerator para adicionar um método faltante ([23eb81a](https://github.com/manteguinha/AutoChangelog/commit/23eb81aa1c0a66ed2cc5ee5484c4c8c39d2bd8c8))

[2.0.0]: https://github.com/manteguinha/AutoChangelog/releases/tag/v2.0.0
