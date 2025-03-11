# Importando as bibliotecas necessárias
from dash import (
    Input,
    Output,
)

from dashboard import app
from dashboard.views import layout_dashboard


# pathname
@app.callback(
    Output('conteudo_pagina', 'children'),
    Input('url', 'pathname'),
)
def carregar_pagina(pathname):
    if pathname == '/':
        return layout_dashboard
