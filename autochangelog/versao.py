"""Detecção da versão do projeto a partir dos arquivos de manifesto mais comuns."""

import json
import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

_PADRAO_SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?")

ChaveSemver = tuple[int, int, int, int, tuple[tuple[int, int | str], ...]]


def chave_semver(texto: str) -> ChaveSemver | None:
    """Chave de ordenação semântica da primeira versão no texto (``None`` se não houver).

    Versões de pré-lançamento (``1.0.0-rc.1``) ficam antes da versão final.
    """
    correspondencia = _PADRAO_SEMVER.search(texto)
    if not correspondencia:
        return None
    maior, menor, correcao, pre = correspondencia.groups()
    identificadores = tuple(
        (0, int(parte)) if parte.isdigit() else (1, parte)
        for parte in (pre or "").split(".")
        if parte
    )
    return (int(maior), int(menor), int(correcao), 0 if pre else 1, identificadores)


def _ler_json(caminho: Path) -> Any:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _ler_toml(caminho: Path) -> dict[str, Any]:
    return tomllib.loads(caminho.read_text(encoding="utf-8"))


def _obter(dados: Any, *chaves: str) -> Any:
    for chave in chaves:
        if not isinstance(dados, dict):
            return None
        dados = dados.get(chave)
    return dados


def _versao_pyproject(caminho: Path) -> Any:
    dados = _ler_toml(caminho)
    return _obter(dados, "project", "version") or _obter(dados, "tool", "poetry", "version")


_FONTES: tuple[tuple[str, Callable[[Path], Any]], ...] = (
    ("package.json", lambda caminho: _obter(_ler_json(caminho), "version")),
    ("pyproject.toml", _versao_pyproject),
    ("Cargo.toml", lambda caminho: _obter(_ler_toml(caminho), "package", "version")),
    ("composer.json", lambda caminho: _obter(_ler_json(caminho), "version")),
    ("VERSION", lambda caminho: caminho.read_text(encoding="utf-8").strip()),
)


def detectar_versao(diretorio: Path) -> tuple[str, str] | None:
    """Retorna ``(versao, arquivo)`` do primeiro manifesto com versão válida, se houver."""
    for nome, extrair in _FONTES:
        caminho = diretorio / nome
        if not caminho.is_file():
            continue
        try:
            versao = extrair(caminho)
        except (OSError, ValueError):  # JSONDecodeError e TOMLDecodeError herdam de ValueError
            continue
        if isinstance(versao, str) and versao.strip():
            return versao.strip().removeprefix("v"), nome
    return None
