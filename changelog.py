import subprocess
import json
import os
from datetime import datetime
import sys

class ChangelogGenerator:
    def __init__(self):
        self.cabecalho = """# CHANGELOG\n\n#### Aqui serão registradas todas as alterações realizadas no projeto.\n---\n"""

    def obter_versao_do_package_json(self):
        try:
            if not os.path.exists('package.json'):
                return None
            with open('package.json', 'r') as arquivo:
                dados = json.load(arquivo)
                return dados.get('version')
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erro ao ler o arquivo package.json: {e}")
            return None

    def eh_repositorio_git(self):
        return subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

    def obter_ultimo_log_do_commit(self):
        try:
            if not self.eh_repositorio_git():
                print("Erro: Este diretório não é um repositório Git válido.")
                return
            return subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], stderr=subprocess.STDOUT).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f"Erro ao obter o último log do commit: {e.output.decode('utf-8')}")
            return ""

    def changelog_existe(self):
        return os.path.exists('CHANGELOG.md')

    def commit_registrado(self, log):
        try:
            with open('CHANGELOG.md', 'r') as arquivo:
                dados = arquivo.read()
                return log in dados
        except IOError as e:
            print(f"Erro ao ler o arquivo CHANGELOG.md: {e}")
            return False

    def adicionar_ao_changelog(self, versao, log):
        try:
            agora = datetime.now().strftime("%Y-%m-%d")
            entrada_changelog = f"### {f'{versao} - ' if versao else ''}{agora}\n- {log}\n"

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
            print(f"Erro ao adicionar entrada ao arquivo CHANGELOG.md: {e}")

    def gerar_changelog(self):
        versao = self.obter_versao_do_package_json()
        log_commit = self.obter_ultimo_log_do_commit()

        if not self.changelog_existe() and self.eh_repositorio_git():
            try:
                with open('CHANGELOG.md', 'w') as arquivo:
                    arquivo.write(self.cabecalho)
                    print("📝 Arquivo CHANGELOG.md criado! Começando a registrar mudanças! ✨")
            except IOError as e:
                print(f"Erro ao criar o arquivo CHANGELOG.md: {e}")

        if self.changelog_existe() and self.eh_repositorio_git():
            self.adicionar_ao_changelog(versao, log_commit)

    def gerar_changelog(self, diretorio):
        try:
            os.chdir(diretorio)  # Altera para o diretório fornecido como argumento
            versao = self.obter_versao_do_package_json()
            log_commit = self.obter_ultimo_log_do_commit()

            if not self.changelog_existe() and self.eh_repositorio_git():
                with open('CHANGELOG.md', 'w') as arquivo:
                    arquivo.write(self.cabecalho)

            if self.changelog_existe() and self.eh_repositorio_git():
                self.adicionar_ao_changelog(versao, log_commit)
        except Exception as e:
            print(f"Erro ao gerar changelog: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Por favor, forneça o diretório como argumento.")
        sys.exit(1)

    diretorio_alvo = sys.argv[1]
    changelog = ChangelogGenerator()
    changelog.gerar_changelog(diretorio_alvo)