import pytest

from autochangelog.categorias import Categoria
from autochangelog.commits import analisar_linha, analisar_mensagem, criar_commit


@pytest.mark.parametrize(
    ("linha", "categoria", "escopo", "descricao"),
    [
        ("feat: adiciona login", Categoria.ADICIONADO, None, "Adiciona login"),
        ("fix(api): corrige timeout.", Categoria.CORRIGIDO, "api", "Corrige timeout"),
        ("✨ feat(cli): nova opção", Categoria.ADICIONADO, "cli", "Nova opção"),
        (":bug: fix: erro", Categoria.CORRIGIDO, None, "Erro"),
        ("🔥 chore(.DS_Store): remove arquivo", Categoria.OUTROS, ".DS_Store", "Remove arquivo"),
        ("refactor!: muda API", Categoria.INCOMPATIVEL, None, "Muda API"),
        ("feat(core)!: novo formato", Categoria.INCOMPATIVEL, "core", "Novo formato"),
        ("perf: mais rápido", Categoria.ALTERADO, None, "Mais rápido"),
        ("deprecate: função x", Categoria.OBSOLETO, None, "Função x"),
        ("security: atualiza dependência", Categoria.SEGURANCA, None, "Atualiza dependência"),
        ("FEAT: maiúsculas", Categoria.ADICIONADO, None, "Maiúsculas"),
    ],
)
def test_analisar_linha(linha, categoria, escopo, descricao):
    mudanca = analisar_linha(linha)
    assert mudanca is not None
    assert (mudanca.categoria, mudanca.escopo, mudanca.descricao) == (categoria, escopo, descricao)


@pytest.mark.parametrize("linha", ["Update README.md", "sem padrão", "feat sem dois pontos"])
def test_analisar_linha_fora_do_padrao(linha):
    assert analisar_linha(linha) is None


def test_titulo_fora_do_padrao_vira_alterado():
    (mudanca,) = analisar_mensagem("update README.md")
    assert mudanca.categoria is Categoria.ALTERADO
    assert mudanca.descricao == "Update README.md"


def test_titulo_com_tipo_desconhecido_mantem_texto_original():
    (mudanca,) = analisar_mensagem("Nota: algo importante")
    assert mudanca.descricao == "Nota: algo importante"


def test_revert_do_git():
    (mudanca,) = analisar_mensagem('Revert "feat: login"')
    assert mudanca.categoria is Categoria.REMOVIDO
    assert mudanca.descricao == 'Reverte "feat: login"'


def test_corpo_com_varias_mudancas():
    mudancas = analisar_mensagem(
        "🐛 fix(a): corrige a",
        "✨ feat(b): adiciona b\nTexto: explicativo qualquer\n🐛 fix(a): corrige a",
    )
    assert [(m.categoria, m.escopo) for m in mudancas] == [
        (Categoria.CORRIGIDO, "a"),
        (Categoria.ADICIONADO, "b"),
    ]


def test_rodape_breaking_change():
    mudancas = analisar_mensagem("feat(api): nova rota", "BREAKING CHANGE: remove rota antiga")
    assert mudancas[1].categoria is Categoria.INCOMPATIVEL
    assert mudancas[1].descricao == "Remove rota antiga"
    assert mudancas[1].escopo == "api"


def test_criar_commit():
    commit = criar_commit("a" * 40, "Ana", "2024-01-02", "feat: x\n\ncorpo\n")
    assert commit.titulo == "feat: x"
    assert commit.corpo == "corpo"
    assert commit.hash_curto == "aaaaaaa"
    assert commit.mensagem == "feat: x\n\ncorpo"


def test_categoria_de_texto():
    assert Categoria.de_texto("Adicionado") is Categoria.ADICIONADO
    assert Categoria.de_texto("seguranca") is Categoria.SEGURANCA
    assert Categoria.de_texto("segurança") is Categoria.SEGURANCA
    assert Categoria.de_texto("added") is None
