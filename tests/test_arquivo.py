import pytest

from autochangelog.arquivo import analisar_documento, mesclar
from autochangelog.categorias import Categoria
from autochangelog.erros import ErroArquivo
from autochangelog.modelo import Changelog, Lancamento
from autochangelog.renderizador import SEM_MUDANCAS, renderizar

URL = "https://github.com/dono/proj"


def _changelog() -> Changelog:
    return Changelog(
        [
            Lancamento(None, tag_anterior="v1.1.0", secoes={Categoria.ADICIONADO: ["Novo"]}),
            Lancamento("1.1.0", "2024-02-01", "v1.1.0", "v1.0.0", {Categoria.CORRIGIDO: ["Bug"]}),
            Lancamento("1.0.0", "2024-01-01", "v1.0.0", None, {}),
        ],
        URL,
    )


def test_renderizar():
    texto = renderizar(_changelog())
    assert texto.startswith("# Changelog\n")
    assert "## [Não lançado]\n\n### Adicionado\n\n- Novo" in texto
    assert "## [1.1.0] - 2024-02-01\n\n### Corrigido\n\n- Bug" in texto
    assert f"## [1.0.0] - 2024-01-01\n\n{SEM_MUDANCAS}" in texto
    assert texto.endswith(
        f"[Não lançado]: {URL}/compare/v1.1.0...HEAD\n"
        f"[1.1.0]: {URL}/compare/v1.0.0...v1.1.0\n"
        f"[1.0.0]: {URL}/releases/tag/v1.0.0\n"
    )


def test_links_gitlab():
    changelog = _changelog()
    changelog.url_repositorio = "https://gitlab.com/g/p"
    texto = renderizar(changelog)
    assert "https://gitlab.com/g/p/-/compare/v1.0.0...v1.1.0" in texto
    assert "https://gitlab.com/g/p/-/tags/v1.0.0" in texto


def test_mescla_e_idempotente():
    texto = renderizar(_changelog())
    assert mesclar(analisar_documento(texto), _changelog()) == texto


def test_mescla_preserva_edicoes_manuais_e_substitui_nao_lancado():
    texto = renderizar(_changelog()).replace("- Bug", "- Bug corrigido à mão")
    texto = texto.replace("- Novo", "- Antigo pendente")
    resultado = mesclar(analisar_documento(texto), _changelog())
    assert "- Bug corrigido à mão" in resultado
    assert "- Antigo pendente" not in resultado
    assert "- Novo" in resultado


def test_mescla_adiciona_versao_nova_e_remove_nao_lancado():
    documento = analisar_documento(renderizar(_changelog()))
    novo = _changelog()
    novo.lancamentos[0] = Lancamento(
        "1.2.0", "2024-03-01", "v1.2.0", "v1.1.0", {Categoria.ADICIONADO: ["Novo"]}
    )
    resultado = mesclar(documento, novo)
    assert "Não lançado" not in resultado
    assert resultado.index("## [1.2.0]") < resultado.index("## [1.1.0]")
    assert f"[1.2.0]: {URL}/compare/v1.1.0...v1.2.0" in resultado


def test_mescla_mantem_versao_manual_na_ordem_e_links_extras():
    texto = renderizar(_changelog()) + "[site]: https://exemplo.com\n"
    texto = texto.replace(
        "## [1.0.0]", "## [1.0.5] - 2024-01-15\n\n### Corrigido\n\n- Manual\n\n## [1.0.0]"
    )
    resultado = mesclar(analisar_documento(texto), _changelog())
    assert resultado.index("## [1.1.0]") < resultado.index("## [1.0.5]")
    assert resultado.index("## [1.0.5]") < resultado.index("## [1.0.0]")
    assert resultado.rstrip().endswith("[site]: https://exemplo.com")


def test_mescla_preserva_preambulo_personalizado():
    texto = renderizar(_changelog()).replace("# Changelog", "# Histórico do Projeto")
    assert mesclar(analisar_documento(texto), _changelog()).startswith("# Histórico do Projeto")


def test_aceita_unreleased_em_ingles():
    documento = analisar_documento("# Changelog\n\n## [Unreleased]\n\n- x\n")
    assert documento.blocos[0].nao_lancado
    assert documento.rotulos_lancados() == set()


def test_arquivo_em_formato_antigo_exige_regenerar():
    antigo = "# CHANGELOG\n\n### 2023-12-11\n- feat: algo\n"
    with pytest.raises(ErroArquivo, match="--regenerar"):
        analisar_documento(antigo)


def test_arquivo_so_com_cabecalho_e_aceito():
    documento = analisar_documento("# Changelog\n\nTexto.\n")
    assert documento.preambulo == "# Changelog\n\nTexto."
    assert documento.blocos == []
