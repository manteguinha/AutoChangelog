"""Montagem do changelog a partir do histórico do Git."""

from collections.abc import Callable, Collection, Sequence
from datetime import date

from autochangelog.categorias import Categoria
from autochangelog.commits import Commit
from autochangelog.erros import ErroConfiguracao, ErroIA
from autochangelog.git import RepositorioGit, Tag
from autochangelog.ia.base import ProvedorIA
from autochangelog.modelo import Changelog, Lancamento
from autochangelog.renderizador import formatar_mudanca

Avisar = Callable[[str], None]


def secoes_por_regras(
    commits: Sequence[Commit], url_repositorio: str | None, incluir_todos: bool
) -> dict[Categoria, list[str]]:
    """Agrupa as mudanças dos commits por categoria, sem IA."""
    secoes: dict[Categoria, list[str]] = {}
    for commit in commits:
        for mudanca in commit.mudancas:
            if mudanca.categoria is Categoria.OUTROS and not incluir_todos:
                continue
            item = formatar_mudanca(mudanca, commit, url_repositorio)
            itens = secoes.setdefault(mudanca.categoria, [])
            if item not in itens:
                itens.append(item)
    return secoes


class GeradorChangelog:
    """Lê tags e commits e produz um :class:`Changelog`."""

    def __init__(
        self,
        repositorio: RepositorioGit,
        *,
        url_repositorio: str | None = None,
        incluir_todos: bool = False,
        provedor: ProvedorIA | None = None,
        avisar: Avisar = lambda _mensagem: None,
    ) -> None:
        self.repositorio = repositorio
        self.url_repositorio = url_repositorio
        self.incluir_todos = incluir_todos
        self.provedor = provedor
        self.avisar = avisar

    def gerar(self, versao_nova: str | None = None, sem_ia_para: Collection[str] = ()) -> Changelog:
        """Gera o changelog completo.

        :param versao_nova: se informada, as mudanças não lançadas viram essa versão.
        :param sem_ia_para: rótulos de versões que não precisam passar pela IA
            (por exemplo, as que já estão no arquivo e serão preservadas).
        """
        tags = self.repositorio.tags_de_versao()
        lancamentos: list[Lancamento] = []

        anterior: Tag | None = None
        for tag in tags:
            commits = self.repositorio.commits(anterior.nome if anterior else None, tag.nome)
            lancamento = Lancamento(
                tag.versao, tag.data, tag.nome, anterior.nome if anterior else None
            )
            self._preencher(lancamento, commits, usar_ia=tag.versao not in sem_ia_para)
            lancamentos.append(lancamento)
            anterior = tag

        pendentes = self.repositorio.commits(anterior.nome if anterior else None, "HEAD")
        if versao_nova:
            self._validar_versao_nova(versao_nova, tags)
            prefixo = anterior.prefixo if anterior else "v"
            lancamento = Lancamento(
                versao_nova,
                date.today().isoformat(),
                f"{prefixo}{versao_nova}",
                anterior.nome if anterior else None,
            )
            self._preencher(lancamento, pendentes, usar_ia=versao_nova not in sem_ia_para)
            lancamentos.append(lancamento)
        elif pendentes:
            lancamento = Lancamento(None, tag_anterior=anterior.nome if anterior else None)
            self._preencher(lancamento, pendentes, usar_ia=True)
            if lancamento.secoes:
                lancamentos.append(lancamento)

        lancamentos.reverse()
        return Changelog(lancamentos, self.url_repositorio)

    @staticmethod
    def _validar_versao_nova(versao: str, tags: Sequence[Tag]) -> None:
        if any(tag.versao == versao for tag in tags):
            raise ErroConfiguracao(
                f"A versão {versao} já existe como tag no Git. Informe uma versão nova."
            )

    def _preencher(self, lancamento: Lancamento, commits: Sequence[Commit], usar_ia: bool) -> None:
        if self.provedor is not None and usar_ia and commits:
            try:
                lancamento.secoes = self.provedor.gerar_secoes(
                    lancamento.rotulo, commits, self.incluir_todos
                )
                return
            except ErroIA as erro:
                self.avisar(
                    f"IA indisponível para [{lancamento.rotulo}] ({erro}). Usando a geração sem IA."
                )
        lancamento.secoes = secoes_por_regras(commits, self.url_repositorio, self.incluir_todos)
