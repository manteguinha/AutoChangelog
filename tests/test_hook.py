import stat

from autochangelog.cli import principal


def test_instalar_e_remover_hook(repo, capsys):
    repo.commit("feat: a")
    assert principal(["hook", "instalar", str(repo.caminho)]) == 0
    hook = repo.caminho / ".git" / "hooks" / "post-commit"
    assert "autochangelog-hook" in hook.read_text()
    assert hook.stat().st_mode & stat.S_IXUSR
    # Reinstalar é permitido.
    assert principal(["hook", "instalar", str(repo.caminho)]) == 0
    assert principal(["hook", "remover", str(repo.caminho)]) == 0
    assert not hook.exists()
    assert principal(["hook", "remover", str(repo.caminho)]) == 0
    assert "Nenhum hook" in capsys.readouterr().out


def test_hook_de_terceiros_e_protegido(repo, capsys):
    repo.commit("feat: a")
    hook = repo.caminho / ".git" / "hooks" / "post-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho outro\n")
    assert principal(["hook", "instalar", str(repo.caminho)]) == 1
    assert principal(["hook", "remover", str(repo.caminho)]) == 1
    assert "--forcar" in capsys.readouterr().err
    assert principal(["hook", "instalar", str(repo.caminho), "--forcar"]) == 0
    assert "autochangelog-hook" in hook.read_text()


def test_hook_atualiza_changelog_apos_commit(repo):
    repo.commit("feat: a")
    principal(["hook", "instalar", str(repo.caminho)])
    repo.commit("fix: b")
    texto = repo.ler()
    assert "- B (`" in texto and "- A (`" in texto
