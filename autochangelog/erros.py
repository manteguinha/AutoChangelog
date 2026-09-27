"""Exceções da ferramenta."""


class ErroAutoChangelog(Exception):
    """Erro base: qualquer falha que deve ser exibida ao usuário e encerrar a execução."""


class ErroGit(ErroAutoChangelog):
    """Falha ao consultar o repositório Git."""


class ErroArquivo(ErroAutoChangelog):
    """Falha ao ler ou gravar o CHANGELOG."""


class ErroConfiguracao(ErroAutoChangelog):
    """Configuração ou argumento inválido."""


class ErroIA(ErroAutoChangelog):
    """Falha ao gerar conteúdo com um provedor de IA."""
