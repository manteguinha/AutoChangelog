"""Provedor Anthropic (Claude), usando o SDK oficial."""

from typing import ClassVar

from autochangelog.erros import ErroIA
from autochangelog.ia.base import ProvedorIA

_MODELOS_COM_FALLBACK = ("claude-opus-5", "claude-fable-5")


class ProvedorAnthropic(ProvedorIA):
    """Claude via Messages API. Credenciais: ``ANTHROPIC_API_KEY`` (ou perfil ``ant``)."""

    nome: ClassVar[str] = "anthropic"
    modelo_padrao: ClassVar[str] = "claude-opus-5"

    def completar(self, instrucoes: str, mensagem: str) -> str:
        try:
            import anthropic
        except ImportError as erro:
            raise ErroIA(
                "O pacote 'anthropic' não está instalado. "
                "Instale com: pip install 'autochangelog[anthropic]'"
            ) from erro

        try:
            cliente = anthropic.Anthropic(timeout=self.tempo_limite)
            parametros = {
                "model": self.modelo,
                "max_tokens": 16000,
                "system": instrucoes,
                "messages": [{"role": "user", "content": mensagem}],
            }
            if self.modelo.startswith(_MODELOS_COM_FALLBACK):
                # Se o modelo recusar a solicitação, a API a repete em um modelo alternativo.
                resposta = cliente.beta.messages.create(
                    **parametros, betas=["server-side-fallback-2026-07-01"], fallbacks="default"
                )
            else:
                resposta = cliente.messages.create(**parametros)
        except anthropic.AuthenticationError as erro:
            raise ErroIA("Chave da Anthropic inválida ou ausente (ANTHROPIC_API_KEY).") from erro
        except anthropic.NotFoundError as erro:
            raise ErroIA(f"Modelo '{self.modelo}' não encontrado na Anthropic.") from erro
        except anthropic.RateLimitError as erro:
            raise ErroIA("Limite de requisições da Anthropic atingido.") from erro
        except anthropic.APIStatusError as erro:
            mensagem_erro = f"Erro da API Anthropic (HTTP {erro.status_code}): {erro.message}"
            raise ErroIA(mensagem_erro) from erro
        except anthropic.APIConnectionError as erro:
            raise ErroIA("Não foi possível conectar à API da Anthropic.") from erro
        except anthropic.AnthropicError as erro:
            raise ErroIA(f"Falha ao usar a Anthropic: {erro}") from erro

        if resposta.stop_reason == "refusal":
            raise ErroIA("A Anthropic recusou a solicitação.")
        if resposta.stop_reason == "max_tokens":
            raise ErroIA("A resposta da Anthropic foi interrompida por limite de tokens.")
        texto = "".join(bloco.text for bloco in resposta.content if bloco.type == "text")
        if not texto.strip():
            raise ErroIA("A Anthropic retornou uma resposta vazia.")
        return texto
