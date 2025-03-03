import os
import subprocess
import sys

import psutil
from rich import print


def get_script_path(script_name: str) -> str:
    """Retorna o caminho absoluto do script."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, script_name)


def is_script_running(script_name: str) -> bool:
    """Verifica se um script Python específico está em execução."""
    current_pid = os.getpid()
    # script_path = get_script_path(script_name)
    # print(f'[blue]Procurando por:[/blue] {script_path}')
    # print(f'[blue]PID atual:[/blue] {current_pid}')

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Pula o processo atual
            if proc.info['pid'] == current_pid:
                continue

            # Verifica se é um processo Python
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if not cmdline:
                    continue

                # Pula processos do process_manager
                if any('process_manager.py' in cmd for cmd in cmdline):
                    continue

                # Pula processos task.exe que chamam check_bot
                if any(
                    'task.exe' in cmd and 'check_bot' in ' '.join(cmdline)
                    for cmd in cmdline
                ):
                    continue

                # print('[yellow]Processo Python encontrado:[/yellow]')
                # print(f'  PID: {proc.info["pid"]}')
                # print(f'  Nome: {proc.info["name"]}')
                # print(f'  Comando: {" ".join(cmdline)}')

                # Verifica se o último argumento
                # é exatamente o script que procuramos
                if (
                    len(cmdline) > 1
                    and os.path.basename(cmdline[-1]) == script_name
                ):
                    print(
                        '[green]>>> Processo do bot encontrado!'
                        + f'[/green] PID: {proc.info["pid"]}'
                    )
                    return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue
        except Exception as e:
            print(f'[red]Erro ao verificar processo:[/red] {e}')
            continue

    print('[blue]Nenhum processo correspondente encontrado.[/blue]')
    return False


def start_background_process(script_name: str):
    script_path = get_script_path(script_name)
    subprocess.Popen(
        [
            r'C:\Users\joaod\Documents\GitHub\crypto\.venv/Scripts\python.exe',
            script_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def main():
    n = 2
    if len(sys.argv) != n:
        print('[red]Uso: python process_manager.py <script_name>[/red]')
        sys.exit(1)

    script_name = sys.argv[1]

    if is_script_running(script_name):
        print(f'[yellow]{script_name} já está em execução[/yellow]')
        sys.exit(0)
    else:
        print(f'[green]Iniciando {script_name} em segundo plano...[/green]')
        start_background_process(script_name)


if __name__ == '__main__':
    main()
