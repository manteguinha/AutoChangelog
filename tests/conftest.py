"""Fixtures compartilhadas: repositórios Git temporários."""

import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest


class RepoTeste:
    """Repositório Git temporário com atalhos para commits e tags."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        caminho.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "teste@exemplo.com")
        self.git("config", "user.name", "Teste")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "tag.gpgsign", "false")

    def git(self, *argumentos: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.caminho), *argumentos],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(self, mensagem: str) -> str:
        self.git("commit", "-q", "--allow-empty", "-m", mensagem)
        return self.git("rev-parse", "HEAD")

    def tag(self, nome: str, anotada: bool = False) -> None:
        if anotada:
            self.git("tag", "-a", nome, "-m", nome)
        else:
            self.git("tag", nome)

    def ler(self, nome: str = "CHANGELOG.md") -> str:
        return (self.caminho / nome).read_text(encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> RepoTeste:
    return RepoTeste(tmp_path / "repo")


@pytest.fixture
def criar_repo(tmp_path: Path) -> Callable[[str], RepoTeste]:
    def criar(nome: str) -> RepoTeste:
        caminho = tmp_path / nome
        caminho.mkdir()
        return RepoTeste(caminho)

    return criar


@pytest.fixture(autouse=True)
def _ambiente_limpo(monkeypatch: pytest.MonkeyPatch) -> None:
    for variavel in (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OLLAMA_HOST",
    ):
        monkeypatch.delenv(variavel, raising=False)
