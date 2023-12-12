<p align="center">
  <img src="/changelog.jpeg" width="200" style="border-radius: 10%;" alt="Project Logo or Banner" />
</p>

<h1 align="center">✨ AutoChangelog ✨</h1>

<p align="center">
  <i>Uma ferramenta para registrar todas as alterações no projeto de forma organizada.</i>
</p>

<p align="center">
  <a href="#📜-sobre">Sobre</a> •
  <a href="#✨-funcionalidades">Funcionalidades</a> •
  <a href="#🚀-como-usar">Como Usar</a> •
  <a href="#💖-contribuindo">Contribuindo</a>
</p>

## 📜 Sobre

Seja bem-vindo à ferramenta de Registro de Alterações (CHANGELOG)! ✨

Este projeto oferece um método para registrar todas as mudanças e atualizações realizadas em seu código. Utilizando comandos do Git e manipulação de arquivos, o `CHANGELOG.md` é mantido atualizado automaticamente sempre que um novo commit é feito.

## ✨ Funcionalidades

- 📝 **Registro de Alterações Automático**: As alterações são registradas de forma automática no arquivo `CHANGELOG.md`.
- ⚙️ **Verificação de Versão**: Verifica a versão do `package.json` (se existir) para registrar informações relevantes.

## 🚀 Como Usar

### Pré-requisitos

Antes de começar, verifique se você tem:

- Python (versão 3.8 ou superior)
- Git instalado e configurado

### ⚙️ Instalação

1. Clone o repositório:

```shell
git clone https://github.com/seu-usuario/AutoChangelog.git
cd AutoChangelog
```

2. Execute o [changelog.py](/caminho/para/o/changelog.py) diretamente no diretório que deseja criar o CHANGELOG.md:

```shell
python changelog.py /caminho/do/diretorio
```

### 📝 Configuração Adicional

Para a funcionalidade completa, certifique-se de que:

- Utilizando o [OpenCommit](https://github.com/di-sukharev/opencommit) o resultado fica ainda melhor.
- Se for um arquivo Node.JS, deve existir um arquivo `package.json` para obter informações de versão.
- O diretório está configurado como um repositório Git para registrar as alterações.

## 💖 Contribuindo

Se deseja contribuir para este projeto, aqui está como pode fazer:

1. Fork o projeto
2. Crie sua Branch de Feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adicionando MinhaFeature'`)
4. Faça push para a Branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

<p align="center">
  Feito com 💜 por <a href="https://seu-site.com" target="_blank">Seu Nome</a>
</p>