"""Acesso ao repositório Git via linha de comando."""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from autochangelog.commits import Commit, criar_commit
from autochangelog.erros import ErroGit
from autochangelog.versao import chave_semver

_SEPARADOR_CAMPO = "\x1f"
_SEPARADOR_REGISTRO = "\x1e"
_PADRAO_TAG_VERSAO = re.compile(
    r"^(?P<prefixo>[A-Za-z]*-?)(?P<versao>\d+\.\d+\.\d+(?:[-+][\w.+-]+)?)$"
)


@dataclass(frozen=True)
class Tag:
    """Tag de versão do repositório."""

    nome: str
    versao: str
    data: str

    @property
    def prefixo(self) -> str:
        """Texto antes do número da versão (ex.: ``v``)."""
        return self.nome[: len(self.nome) - len(self.versao)]


def versao_da_tag(nome: str) -> str | None:
    """Extrai a versão semântica de uma tag (``v1.2.3`` → ``1.2.3``)."""
    correspondencia = _PADRAO_TAG_VERSAO.match(nome)
    return correspondencia["versao"] if correspondencia else None


class RepositorioGit:
    """Consulta um repositório Git sem alterar o diretório de trabalho do processo."""

    def __init__(self, diretorio: Path) -> None:
        if shutil.which("git") is None:
            raise ErroGit("O Git não está instalado ou não está no PATH.")
        self.diretorio = Path(diretorio).resolve()
        if not self.diretorio.is_dir():
            raise ErroGit(f"Diretório não encontrado: {self.diretorio}")
        try:
            raiz = self._executar("rev-parse", "--show-toplevel")
        except ErroGit:
            raise ErroGit(f"{self.diretorio} não é um repositório Git.") from None
        self.raiz = Path(raiz).resolve()

    def _executar(self, *argumentos: str) -> str:
        processo = subprocess.run(
            ["git", "-C", str(self.diretorio), *argumentos],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if processo.returncode != 0:
            detalhe = processo.stderr.strip() or processo.stdout.strip()
            raise ErroGit(f"Falha em 'git {' '.join(argumentos)}': {detalhe}")
        return processo.stdout.strip()

    def possui_commits(self) -> bool:
        """Indica se o repositório já tem ao menos um commit."""
        try:
            self._executar("rev-parse", "--verify", "HEAD")
        except ErroGit:
            return False
        return True

    def tags_de_versao(self) -> list[Tag]:
        """Tags no formato de versão semântica, da mais antiga para a mais recente."""
        saida = self._executar(
            "tag",
            "--list",
            "--merged",
            "HEAD",
            f"--format=%(refname:short){_SEPARADOR_CAMPO}%(creatordate:short)",
        )
        tags = []
        for linha in saida.splitlines():
            nome, _, data = linha.partition(_SEPARADOR_CAMPO)
            versao = versao_da_tag(nome)
            if versao:
                tags.append(Tag(nome, versao, data))
        return sorted(tags, key=lambda tag: chave_semver(tag.versao))

    def commits(self, desde: str | None = None, ate: str = "HEAD") -> list[Commit]:
        """Commits (sem merges) no intervalo ``desde..ate``, do mais recente ao mais antigo."""
        intervalo = f"{desde}..{ate}" if desde else ate
        formato = _SEPARADOR_CAMPO.join(["%H", "%an", "%as", "%B"]) + _SEPARADOR_REGISTRO
        saida = self._executar("log", "--no-merges", f"--format={formato}", intervalo)
        commits = []
        for registro in saida.split(_SEPARADOR_REGISTRO):
            registro = registro.strip("\n")
            if not registro:
                continue
            hash_, autor, data, mensagem = registro.split(_SEPARADOR_CAMPO, 3)
            commits.append(criar_commit(hash_, autor, data, mensagem))
        return commits

    def url_remota(self, remoto: str = "origin") -> str | None:
        """URL do remoto informado, ou ``None`` se não existir."""
        try:
            return self._executar("remote", "get-url", remoto) or None
        except ErroGit:
            return None

    def diretorio_de_hooks(self) -> Path:
        """Diretório de hooks (respeita ``core.hooksPath``)."""
        caminho = Path(self._executar("rev-parse", "--git-path", "hooks"))
        return caminho if caminho.is_absolute() else (self.diretorio / caminho).resolve()


def url_web_do_repositorio(url_remota: str | None) -> str | None:
    """Converte a URL de um remoto GitHub/GitLab em URL web (sem ``.git``)."""
    if not url_remota:
        return None
    url = url_remota.strip()
    ssh = re.match(r"^(?:ssh://)?git@(?P<host>[^:/]+)[:/](?P<caminho>.+)$", url)
    if ssh:
        host, caminho = ssh["host"], ssh["caminho"]
    else:
        http = re.match(r"^https?://(?:[^@/]+@)?(?P<host>[^/]+)/(?P<caminho>.+)$", url)
        if not http:
            return None
        host, caminho = http["host"], http["caminho"]
    if "github" not in host and "gitlab" not in host:
        return None
    caminho = caminho.removesuffix("/").removesuffix(".git")
    return f"https://{host}/{caminho}"
