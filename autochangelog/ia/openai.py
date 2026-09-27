"""Provedor OpenAI ou qualquer API compatível (Groq, OpenRouter, LM Studio...)."""

import os
from typing import ClassVar

from autochangelog.erros import ErroIA
from autochangelog.ia.base import ProvedorIA
from autochangelog.ia.http import postar_json

URL_PADRAO = "https://api.openai.com/v1"


class ProvedorOpenAI(ProvedorIA):
    """Chat Completions. Variáveis: ``OPENAI_API_KEY`` e, opcionalmente, ``OPENAI_BASE_URL``."""

    nome: ClassVar[str] = "openai"
    modelo_padrao: ClassVar[str] = "gpt-4o-mini"

    def completar(self, instrucoes: str, mensagem: str) -> str:
        base = (os.environ.get("OPENAI_BASE_URL") or URL_PADRAO).rstrip("/")
        chave = os.environ.get("OPENAI_API_KEY", "").strip()
        if not chave and base == URL_PADRAO:
            raise ErroIA("Defina a variável de ambiente OPENAI_API_KEY para usar a OpenAI.")
        cabecalhos = {"Authorization": f"Bearer {chave}"} if chave else {}
        corpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": instrucoes},
                {"role": "user", "content": mensagem},
            ],
            "response_format": {"type": "json_object"},
        }
        dados = postar_json(f"{base}/chat/completions", corpo, cabecalhos, self.tempo_limite)
        try:
            escolha = dados["choices"][0]
            texto = escolha["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            raise ErroIA("Resposta inesperada da API compatível com OpenAI.") from erro
        if escolha.get("finish_reason") == "length":
            raise ErroIA("A resposta da OpenAI foi interrompida por limite de tokens.")
        if not isinstance(texto, str) or not texto.strip():
            raise ErroIA("A OpenAI retornou uma resposta vazia.")
        return texto
