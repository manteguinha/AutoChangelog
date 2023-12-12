import subprocess
import json
import os
from datetime import datetime
import sys

class ChangelogGenerator:
    def __init__(self):
        # Cabeçalho do arquivo CHANGELOG
        self.cabecalho = """# CHANGELOG\n\n#### Aqui serão registradas todas as alterações realizadas no projeto.\n---\n"""

    def obter_versao_do_package_json(self):
        try:
            # Verifica se o arquivo package.json existe e obtém a versão
            if not os.path.exists('package.json'):
                return None
            with open('package.json', 'r') as arquivo:
                dados = json.load(arquivo)
                return dados.get('version')
        except (IOError, json.JSONDecodeError) as e:
            # Trata exceções ao ler ou decodificar o arquivo JSON
            print(f"Erro ao ler o arquivo package.json: {e}")
            return None

    def eh_repositorio_git(self):
        # Verifica se o diretório atual é um repositório Git válido
        return subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

    def obter_ultimo_log_do_commit(self):
        try:
            if not self.eh_repositorio_git():
                # Se não for um repositório Git válido, exibe um erro
                print("Erro: Este diretório não é um repositório Git válido.")
                return

            # Obtém o último log do commit
            logs = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], stderr=subprocess.STDOUT).decode('utf-8').strip()

            # Separa as linhas do log
            logs_split = logs.splitlines()

            # Adiciona um hífen no início de cada linha para o formato do CHANGELOG
            logs_with_hyphen = "\n".join(f"- {line}" if line else "" for line in logs_split)

            return logs_with_hyphen
        except subprocess.CalledProcessError as e:
            # Trata erros ao obter o log do commit
            print(f"Erro ao obter o último log do commit: {e.output.decode('utf-8')}")
            return ""

    def changelog_existe(self):
        # Verifica se o arquivo CHANGELOG.md existe
        return os.path.exists('CHANGELOG.md')

    def commit_registrado(self, log):
        try:
            # Verifica se um commit específico já está registrado no CHANGELOG
            with open('CHANGELOG.md', 'r') as arquivo:
                dados = arquivo.read()
                return log in dados
        except IOError as e:
            # Trata exceções ao ler o arquivo CHANGELOG.md
            print(f"Erro ao ler o arquivo CHANGELOG.md: {e}")
            return False

    def adicionar_ao_changelog(self, versao, log):
        try:
            agora = datetime.now().strftime("%Y-%m-%d")
            entrada_changelog = f"### {f'{versao} - ' if versao else ''}{agora}\n{log}\n"

            # Adiciona a entrada no CHANGELOG se não estiver registrada
            if not self.commit_registrado(entrada_changelog):
                with open('CHANGELOG.md', 'r+') as arquivo:
                    dados = arquivo.read().split('\n')
                    if not self.commit_registrado(dados[0]):
                        dados.insert(0, self.cabecalho)
                    dados.append(entrada_changelog)
                    arquivo.seek(0)
                    arquivo.write('\n'.join(dados))
                    print("🎉 Changelog atualizado! Novidades fresquinhas! 📝✨")
            else:
                print("Sem alterações para adicionar ao Changelog. Tudo está atualizado! 🌟")
        except (IOError, IndexError) as e:
            # Trata exceções ao adicionar entrada ao arquivo CHANGELOG.md
            print(f"Erro ao adicionar entrada ao arquivo CHANGELOG.md: {e}")

    def gerar_changelog(self, diretorio):
        try:
            os.chdir(diretorio)  # Altera para o diretório fornecido como argumento
            versao = self.obter_versao_do_package_json()
            log_commit = self.obter_ultimo_log_do_commit()

            # Cria o arquivo CHANGELOG.md se não existir e o diretório for um repositório Git
            if not self.changelog_existe() and self.eh_repositorio_git():
                with open('CHANGELOG.md', 'w') as arquivo:
                    arquivo.write(self.cabecalho)

            # Adiciona ao CHANGELOG se existir e o diretório for um repositório Git
            if self.changelog_existe() and self.eh_repositorio_git():
                self.adicionar_ao_changelog(versao, log_commit)
        except Exception as e:
            # Trata exceções gerais ao gerar o changelog
            print(f"Erro ao gerar changelog: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Verifica se foi fornecido um diretório como argumento
        print("Por favor, forneça o diretório como argumento.")
        sys.exit(1)

    diretorio_alvo = sys.argv[1]
    changelog = ChangelogGenerator()
    changelog.gerar_changelog(diretorio_alvo)
