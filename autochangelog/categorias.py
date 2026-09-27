"""Seções do Keep a Changelog e o mapeamento de tipos de commit para elas."""

from enum import Enum


class Categoria(Enum):
    """Seções de um lançamento, na ordem em que são exibidas."""

    INCOMPATIVEL = "incompativel"
    ADICIONADO = "adicionado"
    ALTERADO = "alterado"
    OBSOLETO = "obsoleto"
    REMOVIDO = "removido"
    CORRIGIDO = "corrigido"
    SEGURANCA = "seguranca"
    OUTROS = "outros"

    @property
    def titulo(self) -> str:
        """Título exibido no CHANGELOG."""
        return _TITULOS[self]

    @classmethod
    def de_texto(cls, texto: str) -> "Categoria | None":
        """Converte uma chave ou título (sem diferenciar maiúsculas) em categoria."""
        normalizado = texto.strip().lower()
        for categoria in cls:
            if normalizado in (categoria.value, categoria.titulo.lower()):
                return categoria
        return None


_TITULOS = {
    Categoria.INCOMPATIVEL: "⚠️ Incompatível",
    Categoria.ADICIONADO: "Adicionado",
    Categoria.ALTERADO: "Alterado",
    Categoria.OBSOLETO: "Obsoleto",
    Categoria.REMOVIDO: "Removido",
    Categoria.CORRIGIDO: "Corrigido",
    Categoria.SEGURANCA: "Segurança",
    Categoria.OUTROS: "Outros",
}

TIPOS_POR_CATEGORIA: dict[Categoria, tuple[str, ...]] = {
    Categoria.ADICIONADO: ("feat", "feature", "add"),
    Categoria.ALTERADO: ("refactor", "perf", "change", "update"),
    Categoria.OBSOLETO: ("deprecate", "deprecated"),
    Categoria.REMOVIDO: ("revert", "remove"),
    Categoria.CORRIGIDO: ("fix", "bugfix", "hotfix"),
    Categoria.SEGURANCA: ("security", "sec"),
    Categoria.OUTROS: ("docs", "chore", "test", "tests", "ci", "build", "style", "wip"),
}

CATEGORIA_POR_TIPO: dict[str, Categoria] = {
    tipo: categoria for categoria, tipos in TIPOS_POR_CATEGORIA.items() for tipo in tipos
}

TIPOS_CONHECIDOS = frozenset(CATEGORIA_POR_TIPO)


def categoria_do_tipo(tipo: str | None) -> Categoria:
    """Retorna a categoria de um tipo de commit; tipos desconhecidos viram ``ALTERADO``."""
    if tipo is None:
        return Categoria.ALTERADO
    return CATEGORIA_POR_TIPO.get(tipo.lower(), Categoria.ALTERADO)
