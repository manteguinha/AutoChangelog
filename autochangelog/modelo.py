"""Estruturas de dados que representam um changelog."""

from dataclasses import dataclass, field

from autochangelog.categorias import Categoria

NAO_LANCADO = "Não lançado"


@dataclass
class Lancamento:
    """Uma versão do changelog (ou o bloco de mudanças ainda não lançadas)."""

    versao: str | None
    data: str | None = None
    tag: str | None = None
    tag_anterior: str | None = None
    secoes: dict[Categoria, list[str]] = field(default_factory=dict)

    @property
    def rotulo(self) -> str:
        """Texto entre colchetes no título (``1.2.0`` ou ``Não lançado``)."""
        return self.versao or NAO_LANCADO

    @property
    def lancado(self) -> bool:
        """Indica se o lançamento já tem versão."""
        return self.versao is not None

    @property
    def total_itens(self) -> int:
        """Quantidade de itens em todas as seções."""
        return sum(len(itens) for itens in self.secoes.values())


@dataclass
class Changelog:
    """Changelog completo, do lançamento mais recente para o mais antigo."""

    lancamentos: list[Lancamento] = field(default_factory=list)
    url_repositorio: str | None = None
