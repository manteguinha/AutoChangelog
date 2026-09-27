import pytest

from autochangelog.erros import ErroGit
from autochangelog.git import RepositorioGit, url_web_do_repositorio, versao_da_tag


def test_diretorio_que_nao_e_repositorio(tmp_path):
    with pytest.raises(ErroGit, match="não é um repositório Git"):
        RepositorioGit(tmp_path)


def test_diretorio_inexistente(tmp_path):
    with pytest.raises(ErroGit, match="não encontrado"):
        RepositorioGit(tmp_path / "nada")


def test_repositorio_sem_commits(repo):
    assert RepositorioGit(repo.caminho).possui_commits() is False


def test_subdiretorio_usa_raiz(repo):
    repo.commit("feat: a")
    sub = repo.caminho / "a" / "b"
    sub.mkdir(parents=True)
    assert RepositorioGit(sub).raiz == repo.caminho.resolve()


def test_tags_ordenadas_por_versao(repo):
    repo.commit("feat: a")
    repo.tag("v1.10.0")
    repo.tag("v1.2.0", anotada=True)
    repo.tag("nao-e-versao")
    repo.commit("feat: b")
    repo.tag("2.0.0-beta.1")
    nomes = [tag.nome for tag in RepositorioGit(repo.caminho).tags_de_versao()]
    assert nomes == ["v1.2.0", "v1.10.0", "2.0.0-beta.1"]


def test_commits_ignoram_merges_e_respeitam_intervalo(repo):
    repo.commit("feat: a")
    repo.tag("v1.0.0")
    repo.git("checkout", "-q", "-b", "ramo")
    repo.commit("fix: b")
    repo.git("checkout", "-q", "main")
    repo.commit("feat: c")
    repo.git("merge", "-q", "--no-ff", "ramo", "-m", "Merge branch 'ramo'")
    commits = RepositorioGit(repo.caminho).commits("v1.0.0")
    assert sorted(c.titulo for c in commits) == ["feat: c", "fix: b"]


@pytest.mark.parametrize(
    ("nome", "versao"),
    [
        ("v1.2.3", "1.2.3"),
        ("1.2.3", "1.2.3"),
        ("release-2.0.0", "2.0.0"),
        ("v1.0.0-rc.1", "1.0.0-rc.1"),
        ("v1.2", None),
        ("latest", None),
    ],
)
def test_versao_da_tag(nome, versao):
    assert versao_da_tag(nome) == versao


@pytest.mark.parametrize(
    ("remota", "web"),
    [
        ("git@github.com:dono/proj.git", "https://github.com/dono/proj"),
        ("https://github.com/dono/proj.git", "https://github.com/dono/proj"),
        ("https://token@github.com/dono/proj", "https://github.com/dono/proj"),
        ("ssh://git@gitlab.com/grupo/sub/proj.git", "https://gitlab.com/grupo/sub/proj"),
        ("https://bitbucket.org/dono/proj.git", None),
        ("/caminho/local", None),
        (None, None),
    ],
)
def test_url_web_do_repositorio(remota, web):
    assert url_web_do_repositorio(remota) == web
