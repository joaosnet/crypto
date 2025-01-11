import webbrowser
from threading import Timer

from rich.console import Console

from crypto import app, server  # noqa: F401
from crypto.segredos import DEGUG


# Função para abrir o navegador automaticamente
def open_browser():
    webbrowser.open_new('http://127.0.0.1:8050')


# Iniciando o aplicativo
if __name__ == '__main__':
    # Colocar um temporizador para abrir o navegador alguns segundos depois de
    # iniciar o servidor
    # Definir o modo a partir da variável de ambiente
    if DEGUG == '0':
        Timer(1, open_browser).start()
        app.run(debug=False)
    elif DEGUG == '1':
        app.run(debug=True, host='0.0.0.0')
    else:
        console = Console()
        console.print(
            'Variavel Ambiente DEBUG não definida.', style='bold red'
        )
        app.run(debug=True)
