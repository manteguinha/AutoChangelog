"""Provedores de IA para reescrever as entradas do changelog."""

from autochangelog.erros import ErroConfiguracao
from autochangelog.ia.anthropic import ProvedorAnthropic
from autochangelog.ia.base import ProvedorIA
from autochangelog.ia.ollama import ProvedorOllama
from autochangelog.ia.openai import ProvedorOpenAI

PROVEDORES: dict[str, type[ProvedorIA]] = {
    classe.nome: classe for classe in (ProvedorAnthropic, ProvedorOpenAI, ProvedorOllama)
}


def obter_provedor(nome: str, modelo: str | None, tempo_limite: float) -> ProvedorIA | None:
    """Instancia o provedor pelo nome; ``"nenhuma"`` retorna ``None``."""
    if nome == "nenhuma":
        return None
    try:
        classe = PROVEDORES[nome]
    except KeyError:
        raise ErroConfiguracao(f"Provedor de IA desconhecido: '{nome}'.") from None
    return classe(modelo, tempo_limite)


__all__ = ["PROVEDORES", "ProvedorIA", "obter_provedor"]
