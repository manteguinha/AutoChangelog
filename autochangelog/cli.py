"""Interface de linha de comando."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from autochangelog import __versao__
from autochangelog.arquivo import analisar_documento, gravar_arquivo, ler_arquivo, mesclar
from autochangelog.config import PROVEDORES_IA, carregar_configuracao
from autochangelog.erros import ErroAutoChangelog, ErroConfiguracao, ErroGit
from autochangelog.gerador import GeradorChangelog
from autochangelog.git import RepositorioGit, url_web_do_repositorio
from autochangelog.hook import instalar_hook, remover_hook
from autochangelog.ia import obter_provedor
from autochangelog.versao import detectar_versao

COMANDOS = ("gerar", "hook")


class Saida:
    """Mensagens para o usuário: resultado no stdout, avisos e erros no stderr."""

    def __init__(self, silencioso: bool = False) -> None:
        self.silencioso = silencioso

    def info(self, mensagem: str) -> None:
        if not self.silencioso:
            print(mensagem)

    def aviso(self, mensagem: str) -> None:
        print(f"⚠️  {mensagem}", file=sys.stderr)

    def erro(self, mensagem: str) -> None:
        print(f"❌ {mensagem}", file=sys.stderr)


def criar_parser() -> argparse.ArgumentParser:
    """Define os comandos e opções da ferramenta."""
    parser = argparse.ArgumentParser(
        prog="autochangelog",
        description=(
            "Gera e mantém um CHANGELOG.md no padrão Keep a Changelog a partir do "
            "histórico do Git, com ou sem IA."
        ),
        epilog="Sem comando, 'gerar' é usado. Ex.: autochangelog . --versao 1.2.0",
    )
    parser.add_argument(
        "-V", "--versao-ferramenta", action="version", version=f"%(prog)s {__versao__}"
    )
    comandos = parser.add_subparsers(dest="comando", metavar="COMANDO")

    gerar = comandos.add_parser(
        "gerar",
        help="gera ou atualiza o CHANGELOG.md (padrão)",
        description="Gera ou atualiza o changelog.",
    )
    gerar.add_argument(
        "diretorio", nargs="?", default=".", help="repositório Git (padrão: diretório atual)"
    )
    gerar.add_argument("-s", "--saida", help="arquivo de saída (padrão: CHANGELOG.md)")
    gerar.add_argument(
        "-v",
        "--versao",
        metavar="VERSAO",
        help="lança as mudanças pendentes como VERSAO; use 'auto' para ler do "
        "package.json, pyproject.toml, Cargo.toml, composer.json ou VERSION",
    )
    gerar.add_argument(
        "--ia",
        choices=PROVEDORES_IA,
        help="provedor de IA para redigir as entradas (padrão: nenhuma)",
    )
    gerar.add_argument("-m", "--modelo", help="modelo do provedor de IA")
    gerar.add_argument(
        "--incluir-todos",
        action="store_true",
        default=None,
        help="inclui docs, testes, CI e manutenção na seção 'Outros'",
    )
    gerar.add_argument("--url-repositorio", help="URL web do repositório para os links")
    gerar.add_argument(
        "--regenerar",
        action="store_true",
        help="recria o arquivo inteiro, descartando o conteúdo atual",
    )
    gerar.add_argument(
        "--simular", action="store_true", help="mostra o resultado sem gravar o arquivo"
    )
    gerar.add_argument(
        "-q", "--silencioso", action="store_true", help="exibe apenas avisos e erros"
    )

    hook = comandos.add_parser(
        "hook",
        help="instala ou remove o hook post-commit",
        description="Atualiza o changelog automaticamente após cada commit.",
    )
    hook.add_argument("acao", choices=("instalar", "remover"))
    hook.add_argument("diretorio", nargs="?", default=".", help="repositório Git")
    hook.add_argument(
        "--forcar", action="store_true", help="substitui um hook post-commit existente"
    )
    return parser


def _resolver_versao(valor: str | None, raiz: Path, saida: Saida) -> str | None:
    if valor is None:
        return None
    if valor.strip().lower() == "auto":
        detectada = detectar_versao(raiz)
        if detectada is None:
            raise ErroConfiguracao(
                "Não foi possível detectar a versão: nenhum package.json, pyproject.toml, "
                "Cargo.toml, composer.json ou VERSION com versão encontrado."
            )
        versao, arquivo = detectada
        saida.info(f"🔎 Versão {versao} detectada em {arquivo}.")
        return versao
    versao = valor.strip().removeprefix("v")
    if not versao:
        raise ErroConfiguracao("A versão informada está vazia.")
    return versao


def executar_gerar(argumentos: argparse.Namespace, saida: Saida) -> int:
    """Comando ``gerar``."""
    repositorio = RepositorioGit(Path(argumentos.diretorio))
    if not repositorio.possui_commits():
        raise ErroGit("O repositório ainda não tem commits.")

    configuracao = carregar_configuracao(repositorio.raiz)
    configuracao.aplicar(
        {
            "saida": argumentos.saida,
            "ia": argumentos.ia,
            "modelo": argumentos.modelo,
            "incluir_todos": argumentos.incluir_todos,
            "url_repositorio": argumentos.url_repositorio,
        },
        "linha de comando",
    )
    configuracao.validar()

    caminho = Path(configuracao.saida)
    if not caminho.is_absolute():
        caminho = repositorio.raiz / caminho

    texto_atual = ler_arquivo(caminho)
    documento = (
        analisar_documento(texto_atual)
        if texto_atual is not None and not argumentos.regenerar
        else None
    )

    url = configuracao.url_repositorio or url_web_do_repositorio(repositorio.url_remota())
    provedor = obter_provedor(configuracao.ia, configuracao.modelo, configuracao.tempo_limite_ia)
    if provedor is not None:
        saida.info(f"🤖 Usando IA: {provedor.nome} ({provedor.modelo})")

    gerador = GeradorChangelog(
        repositorio,
        url_repositorio=url.rstrip("/") if url else None,
        incluir_todos=configuracao.incluir_todos,
        provedor=provedor,
        avisar=saida.aviso,
    )
    versao = _resolver_versao(argumentos.versao, repositorio.raiz, saida)
    changelog = gerador.gerar(versao, documento.rotulos_lancados() if documento else ())
    conteudo = mesclar(documento, changelog)

    if argumentos.simular:
        print(conteudo, end="")
        return 0
    if conteudo == texto_atual:
        saida.info(f"✅ {caminho.name} já está atualizado.")
        return 0
    gravar_arquivo(caminho, conteudo)
    acao = "criado" if texto_atual is None else "atualizado"
    total = len(changelog.lancamentos)
    saida.info(f"🎉 {caminho.name} {acao} ({total} lançamento(s)): {caminho}")
    return 0


def executar_hook(argumentos: argparse.Namespace, saida: Saida) -> int:
    """Comando ``hook``."""
    repositorio = RepositorioGit(Path(argumentos.diretorio))
    if argumentos.acao == "instalar":
        caminho = instalar_hook(repositorio, forcar=argumentos.forcar)
        saida.info(f"🪝 Hook instalado em {caminho}")
    elif remover_hook(repositorio) is None:
        saida.info("Nenhum hook do AutoChangelog para remover.")
    else:
        saida.info("🧹 Hook removido.")
    return 0


def principal(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do comando ``autochangelog``."""
    argumentos_brutos = list(sys.argv[1:] if argv is None else argv)
    ajuda_ou_versao = {"-h", "--help", "-V", "--versao-ferramenta"}
    if not argumentos_brutos or (
        argumentos_brutos[0] not in COMANDOS and argumentos_brutos[0] not in ajuda_ou_versao
    ):
        argumentos_brutos.insert(0, "gerar")

    argumentos = criar_parser().parse_args(argumentos_brutos)
    saida = Saida(getattr(argumentos, "silencioso", False))
    try:
        if argumentos.comando == "hook":
            return executar_hook(argumentos, saida)
        return executar_gerar(argumentos, saida)
    except ErroAutoChangelog as erro:
        saida.erro(str(erro))
        return 1
    except KeyboardInterrupt:
        saida.erro("Operação cancelada.")
        return 130
