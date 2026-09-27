"""Provedor Ollama (modelos locais)."""

import os
from typing import ClassVar

from autochangelog.erros import ErroIA
from autochangelog.ia.base import ProvedorIA
from autochangelog.ia.http import postar_json

HOST_PADRAO = "http://localhost:11434"


class ProvedorOllama(ProvedorIA):
    """API local do Ollama. Variável opcional: ``OLLAMA_HOST``."""

    nome: ClassVar[str] = "ollama"
    modelo_padrao: ClassVar[str] = "llama3.1"

    def completar(self, instrucoes: str, mensagem: str) -> str:
        host = (os.environ.get("OLLAMA_HOST") or HOST_PADRAO).strip().rstrip("/")
        if "://" not in host:
            host = f"http://{host}"
        corpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": instrucoes},
                {"role": "user", "content": mensagem},
            ],
            "stream": False,
            "format": "json",
        }
        dados = postar_json(f"{host}/api/chat", corpo, {}, self.tempo_limite)
        try:
            texto = dados["message"]["content"]
        except (KeyError, TypeError) as erro:
            raise ErroIA(f"Resposta inesperada do Ollama: {dados.get('error', dados)}") from erro
        if not isinstance(texto, str) or not texto.strip():
            raise ErroIA("O Ollama retornou uma resposta vazia.")
        return texto
