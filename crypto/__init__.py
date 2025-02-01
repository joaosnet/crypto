import os
import subprocess

import dash_mantine_components as dmc
import psutil
from dash import Dash, _dash_renderer  # noqa: PLC2701
from mitosheet.mito_dash.v1 import activate_mito
from rich.traceback import install

from crypto.segredos import SECRET_KEY

install(show_locals=True)
_dash_renderer._set_react_version('18.2.0')

# Caminhos relativos para o bot e o executável Python do ambiente virtual
# BOT_PATH = os.path.join(os.path.dirname(__file__), 'bot.py')
# VENV_PYTHON = os.path.join(
#     os.path.dirname(__file__), '..', '.venv', 'bin', 'python'
# )


# def is_bot_running():
#     """
#     Verifica se o bot está em execução.
#     """
#     for process in psutil.process_iter(['pid', 'name', 'cmdline']):
#         # Verifica se o script bot.py está entre os processos em execução
#         if process.info['cmdline'] and BOT_PATH in process.info['cmdline']:
#             return True
#     return False


# def start_bot():
#     """
#     Inicia o bot como um processo independente, se ele não estiver rodando.
#     """
#     if not is_bot_running():
#         subprocess.Popen(
#             [VENV_PYTHON, BOT_PATH],
#             close_fds=True,
#             # creationflags=subprocess.CREATE_NEW_CONSOLE
#             # if os.name == 'nt'
#             # else 0x08000000,
#             env={
#                 **os.environ,
#                 'PYTHONPATH': os.path.abspath(
#                     os.path.join(os.path.dirname(__file__), '..')
#                 ),
#             },
#         )
#         print(
#             'Bot iniciado como um processo independente no ambiente virtual.'
#         )


# Verifica se o bot está rodando e inicializa se necessário
# start_bot()

# Inicializando o aplicativo Dash
app = Dash(
    __name__,
    title='DashBoard Crypto Ativos',
    url_base_pathname='/',
    external_stylesheets=dmc.styles.ALL,
)
activate_mito(app)
server = app.server
app.config.suppress_callback_exceptions = True

server.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///db.sqlite3',
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)


from crypto import views  # noqa: E402, F401
