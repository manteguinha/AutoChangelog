"""Requisições HTTP com JSON usando apenas a biblioteca padrão."""

import json
import urllib.error
import urllib.request
from typing import Any

from autochangelog.erros import ErroIA


def postar_json(
    url: str, corpo: dict[str, Any], cabecalhos: dict[str, str], tempo_limite: float
) -> dict[str, Any]:
    """Envia ``corpo`` como JSON via POST e retorna a resposta decodificada."""
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", **cabecalhos},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
            conteudo = resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace").strip()[:500]
        raise ErroIA(f"{url} respondeu HTTP {erro.code}: {detalhe or erro.reason}") from erro
    except urllib.error.URLError as erro:
        raise ErroIA(f"Não foi possível conectar a {url}: {erro.reason}") from erro
    except TimeoutError as erro:
        raise ErroIA(f"Tempo limite esgotado ao acessar {url}.") from erro
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ErroIA(f"{url} retornou uma resposta que não é JSON.") from erro
    if not isinstance(dados, dict):
        raise ErroIA(f"{url} retornou uma resposta inesperada.")
    return dados
