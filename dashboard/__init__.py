import dash_mantine_components as dmc
from dash import Dash, _dash_renderer  # noqa: PLC2701
from rich.traceback import install

from segredos import SECRET_KEY

install(show_locals=True)
_dash_renderer._set_react_version('18.2.0')
# Inicializando o aplicativo Dash
app = Dash(
    __name__,
    title='DashBoard Crypto Ativos',
    url_base_pathname='/',
    external_stylesheets=dmc.styles.ALL,
)
server = app.server
app.config.suppress_callback_exceptions = True

server.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///db.sqlite3',
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)


from dashboard import (  # noqa: E402, F401
    callbacks,
    graph_preco_tab,
    routers,
    views,
)
