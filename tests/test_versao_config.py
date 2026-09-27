import pytest

from autochangelog.config import Configuracao, carregar_configuracao
from autochangelog.erros import ErroConfiguracao
from autochangelog.versao import detectar_versao


@pytest.mark.parametrize(
    ("arquivo", "conteudo", "esperado"),
    [
        ("package.json", '{"version": "1.2.3"}', "1.2.3"),
        ("pyproject.toml", '[project]\nversion = "2.0.0"\n', "2.0.0"),
        ("pyproject.toml", '[tool.poetry]\nversion = "0.4.1"\n', "0.4.1"),
        ("Cargo.toml", '[package]\nversion = "0.1.0"\n', "0.1.0"),
        ("composer.json", '{"version": "v3.1.0"}', "3.1.0"),
        ("VERSION", "4.5.6\n", "4.5.6"),
    ],
)
def test_detectar_versao(tmp_path, arquivo, conteudo, esperado):
    (tmp_path / arquivo).write_text(conteudo, encoding="utf-8")
    assert detectar_versao(tmp_path) == (esperado, arquivo)


def test_detectar_versao_ignora_arquivos_invalidos(tmp_path):
    (tmp_path / "package.json").write_text("{invalido", encoding="utf-8")
    (tmp_path / "VERSION").write_text("1.0.0", encoding="utf-8")
    assert detectar_versao(tmp_path) == ("1.0.0", "VERSION")


def test_detectar_versao_sem_manifesto(tmp_path):
    assert detectar_versao(tmp_path) is None


def test_configuracao_padrao(tmp_path):
    assert carregar_configuracao(tmp_path) == Configuracao()


def test_configuracao_do_arquivo_proprio(tmp_path):
    (tmp_path / ".autochangelog.toml").write_text(
        'ia = "ollama"\nmodelo = "qwen"\nincluir_todos = true\ntempo_limite_ia = 30\n',
        encoding="utf-8",
    )
    configuracao = carregar_configuracao(tmp_path)
    assert (configuracao.ia, configuracao.modelo, configuracao.incluir_todos) == (
        "ollama",
        "qwen",
        True,
    )
    assert configuracao.tempo_limite_ia == 30.0


def test_configuracao_do_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.autochangelog]\nsaida = "docs/CHANGELOG.md"\n', encoding="utf-8"
    )
    assert carregar_configuracao(tmp_path).saida == "docs/CHANGELOG.md"


@pytest.mark.parametrize(
    "conteudo",
    ['ia = "gpt"\n', "desconhecida = 1\n", 'incluir_todos = "sim"\n', "modelo = 3\n", "[quebrado"],
)
def test_configuracao_invalida(tmp_path, conteudo):
    (tmp_path / ".autochangelog.toml").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(tmp_path)
