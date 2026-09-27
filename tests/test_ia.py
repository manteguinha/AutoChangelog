import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from autochangelog.categorias import Categoria
from autochangelog.cli import principal
from autochangelog.commits import criar_commit
from autochangelog.erros import ErroConfiguracao, ErroIA
from autochangelog.ia import obter_provedor
from autochangelog.ia.base import interpretar_resposta, montar_instrucoes, montar_mensagem

RESPOSTA_IA = {"adicionado": ["Login com Google"], "corrigido": ["Falha ao salvar"]}


class ServidorFalso:
    """Servidor HTTP local que imita as APIs dos provedores."""

    def __init__(self) -> None:
        self.requisicoes: list[tuple[str, dict[str, str], dict[str, Any]]] = []
        self.texto_resposta = json.dumps(RESPOSTA_IA)
        self.status = 200
        servidor = self

        class Manipulador(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                tamanho = int(self.headers.get("Content-Length", 0))
                corpo = json.loads(self.rfile.read(tamanho))
                servidor.requisicoes.append((self.path, dict(self.headers), corpo))
                dados = json.dumps(servidor._corpo_resposta(self.path, corpo)).encode()
                self.send_response(servidor.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(dados)))
                self.end_headers()
                self.wfile.write(dados)

            def log_message(self, *argumentos: object) -> None:
                pass

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Manipulador)
        self.url = f"http://127.0.0.1:{self._http.server_address[1]}"
        threading.Thread(target=self._http.serve_forever, args=(0.05,), daemon=True).start()

    def _corpo_resposta(self, caminho: str, corpo: dict[str, Any]) -> dict[str, Any]:
        if self.status != 200:
            return {"error": {"type": "invalid_request_error", "message": "falhou"}}
        if caminho.endswith("/chat/completions"):
            return {
                "choices": [{"message": {"content": self.texto_resposta}, "finish_reason": "stop"}]
            }
        if caminho == "/api/chat":
            return {"message": {"role": "assistant", "content": self.texto_resposta}}
        return {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": corpo["model"],
            "content": [{"type": "text", "text": self.texto_resposta}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }

    def encerrar(self) -> None:
        self._http.shutdown()


@pytest.fixture
def servidor() -> Iterator[ServidorFalso]:
    falso = ServidorFalso()
    yield falso
    falso.encerrar()


@pytest.fixture
def repo_ia(repo):
    repo.commit("feat: login google")
    repo.commit("fix: salvar")
    repo.tag("v1.0.0")
    repo.commit("feat: pendente")
    return repo


def _configurar(provedor: str, servidor: ServidorFalso, monkeypatch) -> None:
    if provedor == "openai":
        monkeypatch.setenv("OPENAI_BASE_URL", f"{servidor.url}/v1")
        monkeypatch.setenv("OPENAI_API_KEY", "chave-teste")
    elif provedor == "ollama":
        monkeypatch.setenv("OLLAMA_HOST", servidor.url.removeprefix("http://"))
    else:
        monkeypatch.setenv("ANTHROPIC_BASE_URL", servidor.url)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-teste")


@pytest.mark.parametrize("provedor", ["anthropic", "openai", "ollama"])
def test_geracao_com_ia(provedor, servidor, repo_ia, monkeypatch):
    _configurar(provedor, servidor, monkeypatch)
    assert principal([str(repo_ia.caminho), "--ia", provedor, "-q"]) == 0
    texto = repo_ia.ler()
    assert "### Adicionado\n\n- Login com Google" in texto
    assert "### Corrigido\n\n- Falha ao salvar" in texto
    assert len(servidor.requisicoes) == 2  # [Não lançado] e [1.0.0]
    enviados = [json.dumps(corpo, ensure_ascii=False) for _, _, corpo in servidor.requisicoes]
    assert any("feat: pendente" in texto for texto in enviados)
    _, cabecalhos, corpo = servidor.requisicoes[0]
    if provedor == "openai":
        assert cabecalhos["Authorization"] == "Bearer chave-teste"
        assert corpo["response_format"] == {"type": "json_object"}
    if provedor == "anthropic":
        assert corpo["model"] == "claude-opus-5"
        assert corpo["fallbacks"] == "default"


def test_ia_nao_reenvia_versoes_ja_registradas(servidor, repo_ia, monkeypatch):
    _configurar("ollama", servidor, monkeypatch)
    principal([str(repo_ia.caminho), "--ia", "ollama", "-q"])
    servidor.requisicoes.clear()
    principal([str(repo_ia.caminho), "--ia", "ollama", "-q"])
    assert len(servidor.requisicoes) == 1  # só o bloco [Não lançado]


def test_modelo_personalizado(servidor, repo_ia, monkeypatch):
    _configurar("ollama", servidor, monkeypatch)
    principal([str(repo_ia.caminho), "--ia", "ollama", "--modelo", "qwen2.5", "-q"])
    assert servidor.requisicoes[0][2]["model"] == "qwen2.5"


@pytest.mark.parametrize("provedor", ["anthropic", "openai", "ollama"])
def test_resposta_invalida_usa_geracao_sem_ia(provedor, servidor, repo_ia, monkeypatch, capsys):
    _configurar(provedor, servidor, monkeypatch)
    servidor.texto_resposta = "não sei responder"
    assert principal([str(repo_ia.caminho), "--ia", provedor, "-q"]) == 0
    assert "- Login google (`" in repo_ia.ler()
    assert "Usando a geração sem IA" in capsys.readouterr().err


@pytest.mark.parametrize("provedor", ["anthropic", "openai", "ollama"])
def test_erro_http_usa_geracao_sem_ia(provedor, servidor, repo_ia, monkeypatch, capsys):
    _configurar(provedor, servidor, monkeypatch)
    servidor.status = 400
    assert principal([str(repo_ia.caminho), "--ia", provedor, "-q"]) == 0
    assert "- Pendente (`" in repo_ia.ler()
    assert "IA indisponível" in capsys.readouterr().err


def test_openai_sem_chave(repo_ia, capsys):
    assert principal([str(repo_ia.caminho), "--ia", "openai", "-q"]) == 0
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_ollama_fora_do_ar(repo_ia, monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")
    assert principal([str(repo_ia.caminho), "--ia", "ollama", "-q"]) == 0
    assert "Não foi possível conectar" in capsys.readouterr().err


def test_interpretar_resposta():
    texto = (
        "Aqui está:\n```json\n"
        '{"Adicionado": ["- A", "A", " "], "outros": ["x"], "seguranca": []}\n```'
    )
    assert interpretar_resposta(texto, incluir_todos=False) == {Categoria.ADICIONADO: ["A"]}
    assert interpretar_resposta(texto, incluir_todos=True) == {
        Categoria.ADICIONADO: ["A"],
        Categoria.OUTROS: ["x"],
    }
    assert interpretar_resposta("{}", incluir_todos=False) == {}


@pytest.mark.parametrize(
    "texto", ["sem json", "[1, 2]", '{"novidades": ["a"]}', '{"adicionado": "a"}', "{quebrado}"]
)
def test_interpretar_resposta_invalida(texto):
    with pytest.raises(ErroIA):
        interpretar_resposta(texto, incluir_todos=False)


def test_prompt():
    commit = criar_commit("a" * 40, "Ana", "2024-01-01", "feat: x\n\ndetalhe")
    mensagem = montar_mensagem("1.0.0", [commit])
    assert "Lançamento: 1.0.0" in mensagem and "- feat: x\n  \n  detalhe" in mensagem
    assert '"outros"' not in montar_instrucoes(False).split("Regras:")[1].split("\n")[1]
    assert '"outros"' in montar_instrucoes(True)


def test_obter_provedor():
    assert obter_provedor("nenhuma", None, 10) is None
    provedor = obter_provedor("openai", None, 10)
    assert provedor is not None and provedor.modelo == "gpt-4o-mini"
    with pytest.raises(ErroConfiguracao):
        obter_provedor("gpt", None, 10)
