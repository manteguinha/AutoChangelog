"""Contrato comum dos provedores de IA, prompt e validação da resposta."""

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from autochangelog.categorias import Categoria
from autochangelog.commits import Commit
from autochangelog.erros import ErroIA

INSTRUCOES_SISTEMA = """Você é um redator técnico que escreve changelogs no formato \
Keep a Changelog, em português do Brasil, para as pessoas que usam o projeto.

Você recebe os commits de um lançamento e devolve os itens do changelog agrupados por seção.

Regras:
- Use apenas estas chaves de seção: {chaves}.
- "incompativel" é só para mudanças que quebram compatibilidade.
- Cada item é uma frase curta e clara, começando com letra maiúscula e sem ponto final.
- Descreva o efeito da mudança para quem usa o projeto, não detalhes de implementação.
- Junte commits que tratam da mesma mudança em um único item e não repita itens.
- Não invente mudanças que não estejam nos commits e não inclua hashes de commit.
- Quando houver escopo relevante, comece o item com ele em negrito, por exemplo: \
"**cli:** Adiciona a opção --simular".
{regra_outros}
Responda somente com um objeto JSON, sem texto adicional, no formato:
{{"adicionado": ["..."], "corrigido": ["..."]}}
Omita seções sem itens. Se nada for relevante, responda {{}}."""

_REGRA_SEM_OUTROS = (
    "- Ignore mudanças internas sem efeito para quem usa o projeto (testes, CI, "
    'formatação, tarefas de manutenção); não use a seção "outros".'
)
_REGRA_COM_OUTROS = (
    '- Coloque mudanças internas (testes, CI, documentação, manutenção) em "outros".'
)


def montar_instrucoes(incluir_todos: bool) -> str:
    """Prompt de sistema."""
    categorias = [c for c in Categoria if incluir_todos or c is not Categoria.OUTROS]
    chaves = ", ".join(f'"{c.value}"' for c in categorias)
    regra = _REGRA_COM_OUTROS if incluir_todos else _REGRA_SEM_OUTROS
    return INSTRUCOES_SISTEMA.format(chaves=chaves, regra_outros=regra)


def montar_mensagem(rotulo: str, commits: Sequence[Commit]) -> str:
    """Mensagem do usuário com os commits do lançamento."""
    partes = [f"Lançamento: {rotulo}", f"Commits ({len(commits)}), do mais recente ao mais antigo:"]
    for commit in commits:
        mensagem = commit.mensagem.replace("\n", "\n  ")
        partes.append(f"- {mensagem}")
    return "\n".join(partes)


def _extrair_json(texto: str) -> object:
    texto = texto.strip()
    cerca = re.search(r"```(?:json)?\s*(.*?)```", texto, re.DOTALL)
    if cerca:
        texto = cerca.group(1).strip()
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim < inicio:
        raise ErroIA("A resposta da IA não contém um objeto JSON.")
    try:
        return json.loads(texto[inicio : fim + 1])
    except json.JSONDecodeError as erro:
        raise ErroIA(f"A resposta da IA não é um JSON válido: {erro}") from erro


def interpretar_resposta(texto: str, incluir_todos: bool) -> dict[Categoria, list[str]]:
    """Valida a resposta da IA e a converte em seções."""
    dados = _extrair_json(texto)
    if not isinstance(dados, dict):
        raise ErroIA("A resposta da IA deve ser um objeto JSON.")

    secoes: dict[Categoria, list[str]] = {}
    for chave, itens in dados.items():
        categoria = Categoria.de_texto(str(chave))
        if categoria is None:
            raise ErroIA(f"A IA retornou uma seção desconhecida: '{chave}'.")
        if not isinstance(itens, list) or not all(isinstance(item, str) for item in itens):
            raise ErroIA(f"A seção '{chave}' deve ser uma lista de textos.")
        if categoria is Categoria.OUTROS and not incluir_todos:
            continue
        limpos = []
        for item in itens:
            item = re.sub(r"^\s*[-*]\s+", "", item).strip()
            if item and item not in limpos:
                limpos.append(item)
        if limpos:
            secoes.setdefault(categoria, []).extend(limpos)
    return secoes


class ProvedorIA(ABC):
    """Provedor de IA capaz de responder a um prompt de texto."""

    nome: ClassVar[str]
    modelo_padrao: ClassVar[str]

    def __init__(self, modelo: str | None = None, tempo_limite: float = 120.0) -> None:
        self.modelo = modelo or self.modelo_padrao
        self.tempo_limite = tempo_limite

    @abstractmethod
    def completar(self, instrucoes: str, mensagem: str) -> str:
        """Envia o prompt e retorna o texto da resposta."""

    def gerar_secoes(
        self, rotulo: str, commits: Sequence[Commit], incluir_todos: bool
    ) -> dict[Categoria, list[str]]:
        """Gera as seções de um lançamento a partir dos commits."""
        if not commits:
            return {}
        instrucoes = montar_instrucoes(incluir_todos)
        resposta = self.completar(instrucoes, montar_mensagem(rotulo, commits))
        return interpretar_resposta(resposta, incluir_todos)
