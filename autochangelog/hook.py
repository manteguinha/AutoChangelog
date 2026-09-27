"""Instalação do hook ``post-commit`` que atualiza o changelog a cada commit."""

import shlex
import stat
import sys
from pathlib import Path

from autochangelog.erros import ErroConfiguracao
from autochangelog.git import RepositorioGit

MARCADOR = "# autochangelog-hook"
NOME_HOOK = "post-commit"


def _script() -> str:
    python = shlex.quote(sys.executable)
    return (
        "#!/bin/sh\n"
        f"{MARCADOR}\n"
        "# Atualiza o CHANGELOG.md após cada commit. Remova com: autochangelog hook remover\n"
        f'{python} -m autochangelog gerar "$(git rev-parse --show-toplevel)" --silencioso || true\n'
    )


def caminho_do_hook(repositorio: RepositorioGit) -> Path:
    """Caminho do arquivo do hook ``post-commit``."""
    return repositorio.diretorio_de_hooks() / NOME_HOOK


def instalar_hook(repositorio: RepositorioGit, forcar: bool = False) -> Path:
    """Cria o hook. Não sobrescreve um hook de terceiros sem ``forcar``."""
    caminho = caminho_do_hook(repositorio)
    de_terceiros = caminho.exists() and MARCADOR not in caminho.read_text(
        encoding="utf-8", errors="replace"
    )
    if de_terceiros and not forcar:
        raise ErroConfiguracao(
            f"Já existe um hook {NOME_HOOK} que não foi criado pelo AutoChangelog "
            f"({caminho}). Use --forcar para substituí-lo."
        )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(_script(), encoding="utf-8", newline="\n")
    caminho.chmod(caminho.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return caminho


def remover_hook(repositorio: RepositorioGit) -> Path | None:
    """Remove o hook, se tiver sido criado pelo AutoChangelog."""
    caminho = caminho_do_hook(repositorio)
    if not caminho.exists():
        return None
    if MARCADOR not in caminho.read_text(encoding="utf-8", errors="replace"):
        raise ErroConfiguracao(
            f"O hook {caminho} não foi criado pelo AutoChangelog e não será removido."
        )
    caminho.unlink()
    return caminho
