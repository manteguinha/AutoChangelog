"""Leitura de mensagens de commit no padrão Conventional Commits."""

import re
from dataclasses import dataclass, field

from autochangelog.categorias import TIPOS_CONHECIDOS, Categoria, categoria_do_tipo

# Aceita um gitmoji opcional (":sparkles:" ou o próprio emoji) antes do tipo.
_PADRAO_CABECALHO = re.compile(
    r"^(?:(?::[\w+-]+:|[^\w\s(\[]+)\s*)?"
    r"(?P<tipo>[A-Za-z]+)"
    r"(?:\((?P<escopo>[^()]*)\))?"
    r"(?P<quebra>!)?"
    r":\s*(?P<descricao>\S.*)$"
)
_PADRAO_REVERT = re.compile(r'^Revert "(?P<original>.+)"$')
_PADRAO_RODAPE_QUEBRA = re.compile(r"^BREAKING[ -]CHANGE:\s*(?P<texto>.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Mudanca:
    """Uma mudança individual descrita em um commit."""

    categoria: Categoria
    descricao: str
    escopo: str | None = None
    tipo: str | None = None


@dataclass(frozen=True)
class Commit:
    """Commit lido do Git com as mudanças extraídas da mensagem."""

    hash: str
    autor: str
    data: str
    titulo: str
    corpo: str = ""
    mudancas: tuple[Mudanca, ...] = field(default=())

    @property
    def hash_curto(self) -> str:
        """Primeiros 7 caracteres do hash."""
        return self.hash[:7]

    @property
    def mensagem(self) -> str:
        """Mensagem completa (título e corpo)."""
        return f"{self.titulo}\n\n{self.corpo}".strip()


def _capitalizar(texto: str) -> str:
    texto = texto.strip().rstrip(".")
    return texto[:1].upper() + texto[1:]


def analisar_linha(linha: str, *, exigir_tipo_conhecido: bool = False) -> Mudanca | None:
    """Interpreta uma linha no formato ``tipo(escopo)!: descrição``.

    Retorna ``None`` se a linha não seguir o padrão (ou, com ``exigir_tipo_conhecido``,
    se o tipo não for reconhecido).
    """
    correspondencia = _PADRAO_CABECALHO.match(linha.strip())
    if not correspondencia:
        return None
    tipo = correspondencia["tipo"].lower()
    if exigir_tipo_conhecido and tipo not in TIPOS_CONHECIDOS:
        return None
    categoria = Categoria.INCOMPATIVEL if correspondencia["quebra"] else categoria_do_tipo(tipo)
    escopo = (correspondencia["escopo"] or "").strip() or None
    return Mudanca(categoria, _capitalizar(correspondencia["descricao"]), escopo, tipo)


def analisar_mensagem(titulo: str, corpo: str = "") -> tuple[Mudanca, ...]:
    """Extrai as mudanças de uma mensagem de commit.

    - O título é interpretado como Conventional Commit; se não seguir o padrão, vira
      uma mudança em "Alterado" (ou "Removido" para reverts do Git).
    - Linhas do corpo que também sigam o padrão com um tipo conhecido geram mudanças
      extras (comum em commits gerados por ferramentas como OpenCommit).
    - Rodapés ``BREAKING CHANGE:`` geram mudanças em "Incompatível".
    """
    mudancas: list[Mudanca] = []

    principal = analisar_linha(titulo, exigir_tipo_conhecido=True)
    if principal is None:
        revert = _PADRAO_REVERT.match(titulo.strip())
        if revert:
            descricao = f'Reverte "{revert["original"]}"'
            principal = Mudanca(Categoria.REMOVIDO, descricao, tipo="revert")
        else:
            principal = Mudanca(Categoria.ALTERADO, _capitalizar(titulo))
    mudancas.append(principal)

    for linha in corpo.splitlines():
        extra = analisar_linha(linha, exigir_tipo_conhecido=True)
        if extra is not None and extra not in mudancas:
            mudancas.append(extra)

    for quebra in _PADRAO_RODAPE_QUEBRA.finditer(corpo):
        mudancas.append(
            Mudanca(
                Categoria.INCOMPATIVEL,
                _capitalizar(quebra["texto"]),
                principal.escopo,
                principal.tipo,
            )
        )

    return tuple(mudancas)


def criar_commit(hash_: str, autor: str, data: str, mensagem: str) -> Commit:
    """Cria um :class:`Commit` a partir da mensagem bruta do Git."""
    linhas = mensagem.strip().splitlines() or [""]
    titulo = linhas[0].strip()
    corpo = "\n".join(linhas[1:]).strip()
    return Commit(hash_, autor, data, titulo, corpo, analisar_mensagem(titulo, corpo))
