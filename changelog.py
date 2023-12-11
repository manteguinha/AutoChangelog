import subprocess
import json
import os
from datetime import datetime

# Cabeçalho inicial para o arquivo CHANGELOG.md
cabecalho = """# CHANGELOG

#### Aqui serão registradas todas as alterações realizadas no projeto.
---
"""

# Função para obter a versão do package.json, se existir
def obter_versao_do_package_json():
    try:
        if not os.path.exists('package.json'):
            return None
        with open('package.json', 'r') as arquivo:
            dados = json.load(arquivo)
            return dados.get('version')
    except (IOError, json.JSONDecodeError) as e:
        print(f"Erro ao ler o arquivo package.json: {e}")
        return None

# Função para verificar se o diretório é um repositório Git
def eh_repositorio_git():
    return subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

# Função para obter o último log do commit usando o comando git
def obter_ultimo_log_do_commit():
    try:
        if not eh_repositorio_git():
            print("Erro: Este diretório não é um repositório Git válido.")
            return
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], stderr=subprocess.STDOUT).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter o último log do commit: {e.output.decode('utf-8')}")
        return ""

# Verifica se o arquivo CHANGELOG.md existe
def changelog_existe():
    return os.path.exists('CHANGELOG.md')

# Verifica se um determinado log já foi registrado no arquivo CHANGELOG.md
def commit_registrado(log):
    try:
        with open('CHANGELOG.md', 'r') as arquivo:
            dados = arquivo.read()
            return log in dados
    except IOError as e:
        print(f"Erro ao ler o arquivo CHANGELOG.md: {e}")
        return False

# Adiciona uma entrada ao arquivo CHANGELOG.md
def adicionar_ao_changelog(versao, log):
    try:
        agora = datetime.now().strftime("%Y-%m-%d")
        entrada_changelog = f"### {f'{versao} - ' if versao else ''}{agora}\n- {log}\n"

        if not commit_registrado(entrada_changelog):
            with open('CHANGELOG.md', 'r+') as arquivo:
                dados = arquivo.read().split('\n')
                if not commit_registrado(dados[0]):
                    dados.insert(0, cabecalho)
                dados.append(entrada_changelog)
                arquivo.seek(0)
                arquivo.write('\n'.join(dados))
    except (IOError, IndexError) as e:
        print(f"Erro ao adicionar entrada ao arquivo CHANGELOG.md: {e}")

# Obtendo a versão do package.json
versao = obter_versao_do_package_json()

# Obtendo o log do último commit
log_commit = obter_ultimo_log_do_commit()

# Verificando se o arquivo CHANGELOG.md existe, se não, cria um novo com o cabeçalho
if not changelog_existe() and eh_repositorio_git():
    try:
        with open('CHANGELOG.md', 'w') as arquivo:
            arquivo.write(cabecalho)
    except IOError as e:
        print(f"Erro ao criar o arquivo CHANGELOG.md: {e}")

# Adicionando as informações do commit no arquivo CHANGELOG.md, se ainda não estiver registrado
if changelog_existe() and eh_repositorio_git():
  adicionar_ao_changelog(versao, log_commit)
