import os
import sys

import psutil
from rich import print


def get_script_path(script_name: str) -> str:
    """Retorna o caminho absoluto do script."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, script_name)


def kill_process(script_name: str) -> bool:
    """Mata processos que estejam executando o script especificado."""
    script_path = get_script_path(script_name)
    print(f'[blue]Procurando processo para encerrar:[/blue] {script_path}')

    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Verifica se é um processo Python
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if not cmdline:
                    continue

                # Pula processos do process_manager e kill_process
                if any(
                    x in ' '.join(cmdline)
                    for x in ['process_manager.py', 'kill_process.py']
                ):
                    continue

                # Pula processos task.exe
                if any('task.exe' in cmd for cmd in cmdline):
                    continue

                print(
                    '[yellow]Verificando processo:[/yellow]'
                    + f' PID {proc.info["pid"]}'
                )
                print(f'  Comando: {" ".join(cmdline)}')

                # Verifica se o último argumento é o script que procuramos
                if (
                    len(cmdline) > 1
                    and os.path.basename(cmdline[-1]) == script_name
                ):
                    print(
                        '[red]Encerrando processo[/red]'
                        + f' PID {proc.info["pid"]}'
                    )
                    proc.kill()
                    found = True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue
        except Exception as e:
            print(f'[red]Erro ao verificar/matar processo:[/red] {e}')
            continue

    if not found:
        print(
            f'[yellow]Nenhum processo encontrado para {script_name}[/yellow]'
        )
    else:
        print(
            f'[green]Processo(s) do {script_name}'
            + ' encerrado(s) com sucesso![/green]'
        )

    return found


def main():
    tamanho_argumentos = 2
    if len(sys.argv) != tamanho_argumentos:
        print('[red]Uso: python kill_process.py <script_name>[/red]')
        sys.exit(1)

    script_name = sys.argv[1]
    kill_process(script_name)


if __name__ == '__main__':
    main()
