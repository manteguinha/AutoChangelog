"""Conversão do modelo de changelog em Markdown."""

from autochangelog.categorias import Categoria
from autochangelog.commits import Commit, Mudanca
from autochangelog.modelo import Changelog, Lancamento

CABECALHO = """# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/)."""

SEM_MUDANCAS = "_Nenhuma mudança relevante para usuários._"


def _eh_gitlab(url_repositorio: str) -> bool:
    return "gitlab" in url_repositorio


def url_commit(url_repositorio: str, hash_: str) -> str:
    """URL web de um commit."""
    caminho = "/-/commit/" if _eh_gitlab(url_repositorio) else "/commit/"
    return f"{url_repositorio}{caminho}{hash_}"


def url_comparacao(url_repositorio: str, de: str, para: str) -> str:
    """URL web que compara duas referências."""
    caminho = "/-/compare/" if _eh_gitlab(url_repositorio) else "/compare/"
    return f"{url_repositorio}{caminho}{de}...{para}"


def url_tag(url_repositorio: str, tag: str) -> str:
    """URL web de uma tag."""
    caminho = "/-/tags/" if _eh_gitlab(url_repositorio) else "/releases/tag/"
    return f"{url_repositorio}{caminho}{tag}"


def formatar_mudanca(mudanca: Mudanca, commit: Commit, url_repositorio: str | None) -> str:
    """Item de lista para uma mudança: ``**escopo:** Descrição ([abc1234](url))``."""
    escopo = f"**{mudanca.escopo}:** " if mudanca.escopo else ""
    if url_repositorio:
        referencia = f"[{commit.hash_curto}]({url_commit(url_repositorio, commit.hash)})"
    else:
        referencia = f"`{commit.hash_curto}`"
    return f"{escopo}{mudanca.descricao} ({referencia})"


def renderizar_lancamento(lancamento: Lancamento) -> str:
    """Bloco Markdown de um lançamento, começando pelo título ``## [...]``."""
    titulo = f"## [{lancamento.rotulo}]"
    if lancamento.data:
        titulo += f" - {lancamento.data}"
    partes = [titulo]
    for categoria in Categoria:
        itens = lancamento.secoes.get(categoria)
        if itens:
            lista = "\n".join(f"- {item}" for item in itens)
            partes.append(f"### {categoria.titulo}\n\n{lista}")
    if len(partes) == 1:
        partes.append(SEM_MUDANCAS)
    return "\n\n".join(partes)


def links_de_comparacao(changelog: Changelog) -> dict[str, str]:
    """Referências de link (``[1.0.0]: url``) de cada lançamento, quando possível."""
    url = changelog.url_repositorio
    if not url:
        return {}
    links = {}
    for lancamento in changelog.lancamentos:
        destino = lancamento.tag or "HEAD"
        if lancamento.tag_anterior:
            links[lancamento.rotulo] = url_comparacao(url, lancamento.tag_anterior, destino)
        elif lancamento.tag:
            links[lancamento.rotulo] = url_tag(url, lancamento.tag)
    return links


def montar_documento(preambulo: str, blocos: list[str], links: dict[str, str]) -> str:
    """Junta cabeçalho, blocos e referências de link em um único texto."""
    partes = [preambulo.strip(), *(bloco.strip() for bloco in blocos)]
    if links:
        partes.append("\n".join(f"[{rotulo}]: {url}" for rotulo, url in links.items()))
    return "\n\n".join(parte for parte in partes if parte) + "\n"


def renderizar(changelog: Changelog) -> str:
    """Documento completo de um changelog novo."""
    blocos = [renderizar_lancamento(lancamento) for lancamento in changelog.lancamentos]
    return montar_documento(CABECALHO, blocos, links_de_comparacao(changelog))
