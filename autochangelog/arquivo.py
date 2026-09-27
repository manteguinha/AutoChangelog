"""Leitura e atualização idempotente de um CHANGELOG.md existente."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from autochangelog.erros import ErroArquivo
from autochangelog.modelo import NAO_LANCADO, Changelog
from autochangelog.renderizador import (
    CABECALHO,
    links_de_comparacao,
    montar_documento,
    renderizar_lancamento,
)
from autochangelog.versao import chave_semver

_PADRAO_TITULO = re.compile(r"^##\s+(?:\[(?P<entre_colchetes>[^\]]+)\]|(?P<solto>\S+))")
_PADRAO_LINK = re.compile(r"^\[(?P<rotulo>[^\]]+)\]:\s*(?P<url>\S+)\s*$")
_ROTULOS_NAO_LANCADO = {NAO_LANCADO.lower(), "unreleased", "nao lançado", "não lancado"}


@dataclass
class Bloco:
    """Seção ``## [...]`` de um changelog existente."""

    rotulo: str
    texto: str

    @property
    def nao_lancado(self) -> bool:
        """Indica se é o bloco de mudanças não lançadas."""
        return self.rotulo.lower() in _ROTULOS_NAO_LANCADO


@dataclass
class Documento:
    """Changelog existente dividido em preâmbulo, blocos e referências de link."""

    preambulo: str = ""
    blocos: list[Bloco] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)

    def rotulos_lancados(self) -> set[str]:
        """Versões já registradas no arquivo."""
        return {bloco.rotulo for bloco in self.blocos if not bloco.nao_lancado}


def ler_arquivo(caminho: Path) -> str | None:
    """Conteúdo do arquivo, ou ``None`` se ele não existir."""
    if not caminho.exists():
        return None
    try:
        return caminho.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as erro:
        raise ErroArquivo(f"Não foi possível ler {caminho}: {erro}") from erro


def gravar_arquivo(caminho: Path, conteudo: str) -> None:
    """Grava o conteúdo em UTF-8 com quebras de linha ``\\n``."""
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8", newline="\n")
    except OSError as erro:
        raise ErroArquivo(f"Não foi possível gravar {caminho}: {erro}") from erro


def analisar_documento(texto: str) -> Documento:
    """Divide um changelog em partes.

    Lança :class:`ErroArquivo` se o arquivo tiver conteúdo mas nenhum título de versão
    (``## [x.y.z]``), pois não é possível atualizá-lo sem risco de perder informação.
    """
    documento = Documento()
    preambulo: list[str] = []
    atual: tuple[str, list[str]] | None = None

    def fechar_bloco() -> None:
        if atual is not None:
            rotulo, linhas = atual
            documento.blocos.append(Bloco(rotulo, "\n".join(linhas).strip()))

    for linha in texto.replace("\r\n", "\n").split("\n"):
        link = _PADRAO_LINK.match(linha)
        if link:
            documento.links[link["rotulo"]] = link["url"]
            continue
        titulo = _PADRAO_TITULO.match(linha)
        if titulo:
            fechar_bloco()
            atual = ((titulo["entre_colchetes"] or titulo["solto"]).strip(), [linha])
        elif atual is not None:
            atual[1].append(linha)
        else:
            preambulo.append(linha)
    fechar_bloco()

    documento.preambulo = "\n".join(preambulo).strip()
    if not documento.blocos and any(linha.startswith(("### ", "- ", "* ")) for linha in preambulo):
        raise ErroArquivo(
            "O CHANGELOG existente não está no formato Keep a Changelog "
            "(nenhum título '## [versão]' encontrado). "
            "Use --regenerar para recriá-lo a partir do histórico do Git."
        )
    return documento


def mesclar(existente: Documento | None, changelog: Changelog) -> str:
    """Produz o novo conteúdo do arquivo.

    - Versões já presentes no arquivo são mantidas exatamente como estão (inclusive
      edições manuais); só versões novas são adicionadas.
    - O bloco "Não lançado" é sempre substituído pelo gerado (ou removido).
    - Versões que existem só no arquivo (sem tag no Git) são mantidas na posição
      correspondente à sua versão.
    """
    existente = existente or Documento()
    textos_existentes = {b.rotulo: b.texto for b in existente.blocos if not b.nao_lancado}

    blocos: list[tuple[str, str]] = []
    for lancamento in changelog.lancamentos:
        texto = textos_existentes.pop(lancamento.rotulo, None)
        blocos.append((lancamento.rotulo, texto or renderizar_lancamento(lancamento)))

    for rotulo, texto in textos_existentes.items():
        chave = chave_semver(rotulo)
        posicao = len(blocos)
        if chave is not None:
            for indice, (outro, _) in enumerate(blocos):
                chave_outro = chave_semver(outro)
                if chave_outro is not None and chave_outro < chave:
                    posicao = indice
                    break
        blocos.insert(posicao, (rotulo, texto))

    novos_links = links_de_comparacao(changelog)
    todos_links = {**existente.links, **novos_links}
    rotulos = [rotulo for rotulo, _ in blocos]
    links = {r: todos_links[r] for r in rotulos if r in todos_links}
    for rotulo, url in existente.links.items():
        eh_versao = rotulo.lower() in _ROTULOS_NAO_LANCADO or chave_semver(rotulo) is not None
        if rotulo not in links and not eh_versao:
            links[rotulo] = url

    return montar_documento(existente.preambulo or CABECALHO, [t for _, t in blocos], links)
