import json

import pytest

from autochangelog import __versao__
from autochangelog.cli import principal


def _preparar(repo):
    repo.git("remote", "add", "origin", "git@github.com:dono/proj.git")
    repo.commit("feat: primeira versão")
    repo.commit("docs: readme")
    repo.tag("v0.1.0")
    repo.commit("fix(core): corrige falha")
    repo.commit("chore: limpeza")


def test_gera_changelog(repo, capsys):
    _preparar(repo)
    assert principal([str(repo.caminho)]) == 0
    texto = repo.ler()
    assert "## [Não lançado]\n\n### Corrigido\n\n- **core:** Corrige falha" in texto
    assert "## [0.1.0] - " in texto
    assert "Readme" not in texto and "Limpeza" not in texto
    assert "[0.1.0]: https://github.com/dono/proj/releases/tag/v0.1.0" in texto
    assert "criado" in capsys.readouterr().out


def test_subcomando_gerar_explicito_e_idempotencia(repo, capsys):
    _preparar(repo)
    assert principal(["gerar", str(repo.caminho)]) == 0
    primeiro = repo.ler()
    assert principal(["gerar", str(repo.caminho)]) == 0
    assert repo.ler() == primeiro
    assert "já está atualizado" in capsys.readouterr().out


def test_incluir_todos(repo):
    _preparar(repo)
    principal([str(repo.caminho), "--incluir-todos"])
    texto = repo.ler()
    assert "### Outros" in texto and "Readme" in texto and "Limpeza" in texto


def test_simular_nao_grava(repo, capsys):
    _preparar(repo)
    assert principal([str(repo.caminho), "--simular"]) == 0
    assert not (repo.caminho / "CHANGELOG.md").exists()
    assert capsys.readouterr().out.startswith("# Changelog")


def test_lancar_versao(repo):
    _preparar(repo)
    assert principal([str(repo.caminho), "--versao", "v0.2.0", "-q"]) == 0
    texto = repo.ler()
    assert "Não lançado" not in texto
    assert "## [0.2.0] - " in texto
    assert "[0.2.0]: https://github.com/dono/proj/compare/v0.1.0...v0.2.0" in texto
    # Depois de criar a tag, o arquivo continua igual.
    repo.tag("v0.2.0")
    antes = repo.ler()
    assert principal([str(repo.caminho), "-q"]) == 0
    assert repo.ler().replace(antes, "") == ""


def test_versao_auto(repo, capsys):
    _preparar(repo)
    (repo.caminho / "package.json").write_text(json.dumps({"version": "0.3.0"}))
    assert principal([str(repo.caminho), "--versao", "auto"]) == 0
    assert "## [0.3.0]" in repo.ler()
    assert "detectada em package.json" in capsys.readouterr().out


def test_versao_auto_sem_manifesto(repo, capsys):
    _preparar(repo)
    assert principal([str(repo.caminho), "--versao", "auto"]) == 1
    assert "Não foi possível detectar a versão" in capsys.readouterr().err


def test_versao_existente_e_erro(repo, capsys):
    _preparar(repo)
    assert principal([str(repo.caminho), "--versao", "0.1.0"]) == 1
    assert "já existe" in capsys.readouterr().err


def test_saida_personalizada_e_url(repo):
    _preparar(repo)
    argumentos = ["--saida", "docs/HISTORICO.md", "--url-repositorio", "https://gitlab.com/g/p/"]
    assert principal([str(repo.caminho), *argumentos]) == 0
    texto = repo.ler("docs/HISTORICO.md")
    assert "https://gitlab.com/g/p/-/commit/" in texto


def test_sem_remoto_usa_hash_sem_link(repo):
    repo.commit("feat: algo")
    principal([str(repo.caminho)])
    texto = repo.ler()
    assert "- Algo (`" in texto
    assert "]: " not in texto


def test_regenerar_formato_antigo(repo, capsys):
    _preparar(repo)
    (repo.caminho / "CHANGELOG.md").write_text("# CHANGELOG\n\n### 2023-12-11\n- algo\n")
    assert principal([str(repo.caminho)]) == 1
    assert "--regenerar" in capsys.readouterr().err
    assert principal([str(repo.caminho), "--regenerar"]) == 0
    assert "## [0.1.0]" in repo.ler()


def test_diretorio_invalido(tmp_path, capsys):
    assert principal([str(tmp_path)]) == 1
    assert "não é um repositório Git" in capsys.readouterr().err


def test_repositorio_sem_commits(repo, capsys):
    assert principal([str(repo.caminho)]) == 1
    assert "ainda não tem commits" in capsys.readouterr().err


def test_ia_invalida_e_erro_de_uso(repo):
    repo.commit("feat: a")
    with pytest.raises(SystemExit) as saida:
        principal([str(repo.caminho), "--ia", "gpt"])
    assert saida.value.code == 2


def test_config_do_repositorio(repo):
    repo.commit("feat: a")
    repo.commit("docs: b")
    (repo.caminho / ".autochangelog.toml").write_text("incluir_todos = true\n")
    principal([str(repo.caminho)])
    assert "### Outros" in repo.ler()


def test_versao_da_ferramenta(capsys):
    with pytest.raises(SystemExit):
        principal(["--versao-ferramenta"])
    assert __versao__ in capsys.readouterr().out


def test_sem_argumentos_usa_diretorio_atual(repo, monkeypatch):
    repo.commit("feat: a")
    monkeypatch.chdir(repo.caminho)
    assert principal([]) == 0
    assert (repo.caminho / "CHANGELOG.md").exists()
