import webbrowser
from threading import Timer

from crypto import app, server  # noqa: F401
from segredos import DEGUG


# Função para abrir o navegador automaticamente
def open_browser():
    webbrowser.open_new('http://127.0.0.1:8050')


# Iniciando o aplicativo
if __name__ == '__main__':
    # Definir o modo a partir da variável de ambiente
    if DEGUG == '0':
        Timer(1, open_browser).start()
        app.run(debug=False, port=8050)
    elif DEGUG == '1':
        app.run(debug=True, host='0.0.0.0', port=8050)
    else:
        app.run(debug=True, port=8050)
