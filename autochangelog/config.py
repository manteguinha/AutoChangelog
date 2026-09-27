"""Configuração da ferramenta (arquivo ``.autochangelog.toml`` ou ``pyproject.toml``)."""

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from autochangelog.erros import ErroConfiguracao

ARQUIVO_CONFIGURACAO = ".autochangelog.toml"
PROVEDORES_IA = ("nenhuma", "anthropic", "openai", "ollama")


@dataclass
class Configuracao:
    """Opções de geração. A linha de comando tem precedência sobre o arquivo."""

    saida: str = "CHANGELOG.md"
    ia: str = "nenhuma"
    modelo: str | None = None
    incluir_todos: bool = False
    url_repositorio: str | None = None
    tempo_limite_ia: float = 120.0

    def validar(self) -> None:
        """Garante que os valores são coerentes."""
        if self.ia not in PROVEDORES_IA:
            opcoes = ", ".join(PROVEDORES_IA)
            raise ErroConfiguracao(f"Provedor de IA inválido: '{self.ia}'. Opções: {opcoes}.")
        if not self.saida.strip():
            raise ErroConfiguracao("O arquivo de saída não pode ser vazio.")
        if self.tempo_limite_ia <= 0:
            raise ErroConfiguracao("'tempo_limite_ia' deve ser maior que zero.")

    def aplicar(self, valores: dict[str, Any], origem: str) -> None:
        """Sobrescreve os campos com os valores informados (``None`` é ignorado)."""
        tipos = {campo.name: campo.type for campo in fields(self)}
        for chave, valor in valores.items():
            if chave not in tipos:
                raise ErroConfiguracao(f"Opção desconhecida '{chave}' em {origem}.")
            if valor is None:
                continue
            if chave == "incluir_todos" and not isinstance(valor, bool):
                raise ErroConfiguracao(f"'{chave}' deve ser true/false em {origem}.")
            if chave == "tempo_limite_ia":
                if isinstance(valor, bool) or not isinstance(valor, int | float):
                    raise ErroConfiguracao(f"'{chave}' deve ser um número em {origem}.")
                valor = float(valor)
            elif chave != "incluir_todos" and not isinstance(valor, str):
                raise ErroConfiguracao(f"'{chave}' deve ser um texto em {origem}.")
            setattr(self, chave, valor)


def _ler_toml(caminho: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as erro:
        raise ErroConfiguracao(f"Não foi possível ler {caminho.name}: {erro}") from erro


def carregar_configuracao(raiz: Path) -> Configuracao:
    """Lê ``.autochangelog.toml`` ou, na falta dele, ``[tool.autochangelog]`` do pyproject."""
    configuracao = Configuracao()
    arquivo = raiz / ARQUIVO_CONFIGURACAO
    if arquivo.is_file():
        configuracao.aplicar(_ler_toml(arquivo), ARQUIVO_CONFIGURACAO)
    else:
        pyproject = raiz / "pyproject.toml"
        if pyproject.is_file():
            secao = _ler_toml(pyproject).get("tool", {}).get("autochangelog", {})
            configuracao.aplicar(secao, "pyproject.toml [tool.autochangelog]")
    configuracao.validar()
    return configuracao
