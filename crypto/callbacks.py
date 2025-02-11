# Importando as bibliotecas necessárias
import json
import traceback

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dash import ALL, Input, Output, Patch, State, callback, dcc, html
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from mitosheet.mito_dash.v1 import Spreadsheet, mito_callback

from bot.apis.api_bitpreco import Buy, Sell
from compartilhado import (
    get_coinpair,
    set_coinpair,
)
from crypto import app, dash_utils
from crypto.componentes_personalizados import (
    bar_precos_atuais,
)
from crypto.views import layout_dashboard
from db.duckdb_csv import load_csv_in_records

# from crypto.timescaledb import read_from_db
from segredos import CAMINHO

# Definição das variáveis de ambiente
PRICE_FILE = CAMINHO + '/ticker.csv'
BALANCE_FILE = CAMINHO + '/balance.csv'
ORDERS_FILE = CAMINHO + '/executed_orders.csv'
INTERVAL_FILE = CAMINHO + '/interval.json'


# Callback para atualizar a taxa de atualização com base no valor do slider
@app.callback(
    [Output(component_id='interval-component', component_property='interval')],
    [Input('interval-refresh', 'value')],
)
def update_refresh_rate(value):
    # Salva o valor do slider em milissegundos
    interval_value = value * 1000

    # Salvando o valor do intervalo em um arquivo leve
    with open(INTERVAL_FILE, 'w', encoding='utf-8') as f:
        json.dump({'interval': value}, f)

    return [interval_value]


# Callback para atualizar a taxa de atualização com base no valor do slider
@app.callback(
    [
        Output(
            component_id='interval-component-dash',
            component_property='interval',
        )
    ],
    [Input('interval-refresh-dash', 'value')],
)
def update_refresh_rate_dash(value):
    # Salva o valor do slider em milissegundos
    interval_value = value * 1000

    return [interval_value]


# Callback para atualizar os dados do ticker
@app.callback(
    Output('df-precos', 'data'),
    Input('interval-component-dash', 'n_intervals'),
)
def update_df_precos(_):
    # df_precos = pd.read_csv(PRICE_FILE)
    # return df_precos.to_dict('records')
    # Leitura do arquivo CSV usando DuckDB
    return load_csv_in_records(PRICE_FILE)


@app.callback(
    Output('df-executed-orders', 'data'),
    Input('interval-component-dash', 'n_intervals'),
)
def update_df_executed_orders(n_intervals):
    executed_orders_df = pd.read_csv(ORDERS_FILE)
    return executed_orders_df.to_dict('records')


@app.callback(
    Output('df-balance', 'data'),
    Input('interval-component-dash', 'n_intervals'),
)
def update_df_balance(n_intervals):
    balance_df = pd.read_csv(BALANCE_FILE).to_dict('records')
    return balance_df


# Callback para atualizar a coinpair apartir dos filtros
@app.callback(
    [
        Output('filtro-cripto', 'value'),
        Output('market-compra', 'value'),
        Output('market-venda', 'value'),
    ],
    [
        Input('filtro-cripto', 'value'),
        Input('market-compra', 'value'),
        Input('market-venda', 'value'),
    ],
    prevent_initial_call=True,
)
def update_coinpair(filtro, compra, venda):
    # Identifica qual input mudou
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    # Define o novo valor baseado em qual input foi alterado
    if trigger == 'filtro-cripto':
        novo_valor = filtro
    elif trigger == 'market-compra':
        novo_valor = compra
    elif trigger == 'market-venda':
        novo_valor = venda
    else:
        novo_valor = get_coinpair()

    # Atualiza o valor no arquivo de configuração
    if novo_valor is not None:
        set_coinpair(novo_valor)

    # Retorna o mesmo valor para todos os campos
    return novo_valor, novo_valor, novo_valor


# Callback para atualizar os ícones das abas
@app.callback(
    [Output('preco-icon', 'icon'), Output('ordens-icon', 'icon')],
    [Input('df-precos', 'data'), Input('df-executed-orders', 'data')],
)
def update_tab_icons(df_precos, df_executed_orders):
    df_precos = pd.DataFrame(df_precos)
    df_executed_orders = pd.DataFrame(df_executed_orders)

    # Lógica para o ícone de Preços
    last_price = df_precos['last'].iloc[-1] if not df_precos.empty else 0
    prev_price = (
        df_precos['last'].iloc[-2] if len(df_precos) > 1 else last_price
    )
    preco_icon = (
        'hugeicons:bitcoin-up-02'
        if last_price > prev_price
        else 'hugeicons:bitcoin-down-02'
    )

    # Lógica para o ícone de Ordens de Compra
    num_orders = len(df_executed_orders)
    ordens_icon = 'mdi:cart' if num_orders > 0 else 'mdi:cart-outline'

    return preco_icon, ordens_icon


# Callback para adicionar o conteúdo da página dentro do tab Preços
@app.callback(
    Output('bar-precos-atuais', 'children'),
    Input('data-recency', 'value'),
    Input('df-precos', 'data'),
    Input('df-executed-orders', 'data'),
    prevent_initial_call=True,
)
def preco_atuais(
    data_recency,
    df,
    executed_orders_df,
):
    return bar_precos_atuais(
        data_recency,
        df,
        executed_orders_df,
    )


# Callback para adicionar o conteúdo da página dentro do tab Preços
@app.callback(
    Output({'type': 'spreadsheet', 'id': 'sheet'}, 'data'),
    Input('df-precos', 'data'),
    prevent_initial_call=True,
)
def tabela_historico(
    df1,
):
    df1 = pd.DataFrame(df1)
    # Deleted columns success
    df1.drop(['success'], axis=1, inplace=True)

    # Reordered column last
    df1_columns = [col for col in df1.columns if col != 'last']
    df1_columns.insert(0, 'last')
    df1 = df1[df1_columns]

    # Reordered column var
    df1_columns = [col for col in df1.columns if col != 'var']
    df1_columns.insert(1, 'var')
    df1 = df1[df1_columns]

    # Reordered column timestamp
    df1_columns = [col for col in df1.columns if col != 'timestamp']
    df1_columns.insert(0, 'timestamp')
    df1 = df1[df1_columns]

    # Reordered column vol
    df1_columns = [col for col in df1.columns if col != 'vol']
    df1_columns.insert(3, 'vol')
    df1 = df1[df1_columns]

    # Reordered column market
    df1_columns = [col for col in df1.columns if col != 'market']
    df1_columns.insert(9, 'market')
    df1 = df1[df1_columns]
    df1 = df1.sort_values(by='timestamp', ascending=False, na_position='last')

    return df1.to_dict('records')


@mito_callback(
    Output('output1', 'children'),
    Input({'type': 'spreadsheet', 'id': 'sheet'}, 'spreadsheet_result'),
)
def update_code(spreadsheet_result):
    return html.Div([
        html.H3('Spreadsheet Result'),
        dmc.Code(
            spreadsheet_result.code(),
            style={'whiteSpace': 'pre-wrap'},
            block=True,
        ),
        html.Div(f'Selection: {spreadsheet_result.selection()}'),
        html.Div(f'Dataframes: {spreadsheet_result.dfs()}'),
    ])


# callback para calcular o valor total em reais
# com base na porcentagem do botao clicado
@app.callback(
    Output('total-reais', 'value'),
    Input('reais-10', 'n_clicks'),
    Input('reais-25', 'n_clicks'),
    Input('reais-50', 'n_clicks'),
    Input('reais-100', 'n_clicks'),
    State('df-balance', 'data'),
    prevent_initial_call=True,
)
def calcular_porcentagem_reais(
    n_clicks_10, n_clicks_25, n_clicks_50, n_clicks_100, df_balance
):
    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df_balance = pd.DataFrame(df_balance)
    df_balance = df_balance['BRL'].iloc[0]

    if button_id == 'reais-10':
        valor = float(df_balance) * 0.1
    elif button_id == 'reais-25':
        valor = float(df_balance) * 0.25
    elif button_id == 'reais-50':
        valor = float(df_balance) * 0.5
    elif button_id == 'reais-100':
        valor = float(df_balance)
    else:
        valor = 0
    return valor


# Callback para calcular a quantidade de BTC
# com base na porcentagem do botao clicado
@app.callback(
    Output(
        'amount-venda',
        'value',
        allow_duplicate=True,
    ),
    Input('amount-10', 'n_clicks'),
    Input('amount-25', 'n_clicks'),
    Input('amount-50', 'n_clicks'),
    Input('amount-100', 'n_clicks'),
    State('df-balance', 'data'),
    prevent_initial_call=True,
)
def calcular_porcentagem_btc(
    n_clicks_10, n_clicks_25, n_clicks_50, n_clicks_100, df_balance
):
    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    df_balance = pd.DataFrame(df_balance)
    df_balance = df_balance['BTC'].iloc[0]

    if button_id == 'amount-10':
        valor = float(df_balance) * 0.1
    elif button_id == 'amount-25':
        valor = float(df_balance) * 0.25
    elif button_id == 'amount-50':
        valor = float(df_balance) * 0.5
    elif button_id == 'amount-100':
        valor = float(df_balance)
    else:
        valor = 0
    return valor


@app.callback(
    Output('tab-ordens', 'children'),
    Input('tabs', 'value'),
    Input('df-executed-orders', 'data'),
    Input('df-balance', 'data'),
    Input('df-precos', 'data'),
    prevent_initial_call=True,
)
def ordens_tab(value, executed_orders_df, balance_df, df_precos):
    try:
        if value == 'Ordens de Compra':
            executed_orders_df = pd.DataFrame(executed_orders_df)
            # Criando um Gráfico de anel para o balance da minha conta
            balance_df = pd.DataFrame(balance_df)
            df_precos = pd.DataFrame(df_precos)

            balance_df = balance_df.drop(
                columns=['success', 'utimestamp', 'timestamp']
            )
            balance_df = balance_df.loc[
                :, (balance_df != 0).any(axis=0)
            ]  # Remove columns with all zeros

            # Multiplicando o valor do bitcoin pelo valor do último preço
            if 'BTC' in balance_df.columns:
                balance_df['BTC'] *= df_precos['last'].iloc[-1]

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=balance_df.columns,
                        values=balance_df.iloc[0],
                        hole=0.3,
                        domain={'row': 1, 'column': 0},
                        # a cor do BTC é laranja e a cor do BRL é verde
                        marker_colors=['#FFA500', '#008000'],
                    )
                ]
            )
            # adicionando o saldo em reais aproximado como indicador no gráfico
            if balance_df.columns[0] == 'BRL':
                valor_aproximado = balance_df.iloc[0].sum()
                refeencia = 0
                dash_utils.add_trace(
                    fig,
                    'Saldo em Reais',
                    valor_aproximado,
                    1,
                    1,
                )
            elif (
                balance_df.columns[0] == 'BTC'
                or balance_df.columns[0] == 'BTC_LOCKED'
            ):
                valor_aproximado = (
                    balance_df['BTC'].sum() + balance_df['BRL'].sum()
                )
                refeencia = (
                    executed_orders_df['price'].iloc[0]
                    * executed_orders_df['amount'].iloc[0]
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Saldo em Reais',
                    valor_aproximado,
                    refeencia,
                    1,
                    1,
                )

            fig.update_layout(
                title_text='Distribuição do saldo da conta',
                grid={'rows': 1, 'columns': 2, 'pattern': 'independent'},
            )

            # Criando a Table com as ordens de compra e venda
            table = Spreadsheet(
                executed_orders_df, id={'type': 'spreadsheet', 'id': 'sheet2'}
            )
            return html.Div(
                children=[
                    dcc.Graph(
                        figure=fig,
                        mathjax=True,
                        id={'type': 'graph', 'index': 'pie'},
                    ),
                    html.Hr(),
                    table,
                ],
            )
    except Exception as error:
        return html.Div(
            children=[
                html.H5(children=f'{error}'),
                dcc.Markdown(
                    '{}'.format(traceback.format_exc()),
                    style={'font-size': '14pt'},
                ),
            ]
        )


# Atualizndo o preco-compra com o valor do último preço
@app.callback(
    Output('preco-compra', 'value'),
    Input('df-precos', 'data'),
)
def atualizar_preco_compra_input(df_precos):
    df_precos = pd.DataFrame(df_precos)

    preco_compra = df_precos['last'].iloc[-1]
    return preco_compra


# Atualizando o preco-venda com o valor do último preço
@app.callback(
    Output('preco-venda', 'value'),
    Input('df-precos', 'data'),
)
def atualizar_preco_venda_input(df_precos):
    df_precos = pd.DataFrame(df_precos)
    ultimo_preco = df_precos['last'].iloc[-1]

    return ultimo_preco


# Chamada para aproximar o amount de compra para bitcoin
@app.callback(
    Output('amount', 'value'),
    State('df-precos', 'data'),
    Input('total-reais', 'value'),
    State('preco-compra', 'value'),
    State('limited', 'value'),
    prevent_initial_call=True,
)
def aproximar_amount_compra(  # noqa: PLR0913, PLR0917
    df,
    total_reais,
    preco_compra,
    tipo_ordem,
):
    # low_market_price = pd.DataFrame(df)['low'].iloc[-1]
    try:
        total_reais = float(total_reais)
    except:  # noqa: E722
        total_reais = -1
    # calculando o valor total em reais
    if total_reais is not None and total_reais >= 0:
        if tipo_ordem in {'limited', 'market'}:
            amount = total_reais / preco_compra
            return amount
        else:
            return 0
    else:
        return 0


# Chamada para aproximar o amount de venda para bitcoin
@app.callback(
    Output('amount-venda', 'value'),
    State('df-precos', 'data'),
    Input('total-reais-venda', 'value'),
    State('preco-venda', 'value'),
    State('limited-sell', 'value'),
    prevent_initial_call=True,
)
def aproximar_amount_venda(  # noqa: PLR0913, PLR0917
    _df,
    total_reais,
    preco_compra,
    tipo_ordem,
):
    # low_market_price = pd.DataFrame(df)['low'].iloc[-1]
    try:
        total_reais = float(total_reais)
    except:  # noqa: E722
        total_reais = -1
    # calculando o valor total em reais
    if total_reais is not None and total_reais >= 0:
        if tipo_ordem in {'limited', 'market'}:
            amount = total_reais / preco_compra
            return amount
        else:
            return 0
    else:
        return 0


# Callback para vender
@app.callback(
    Output('sell-button-output', 'children'),
    Input('sell-button', 'n_clicks'),
    State('preco-venda', 'value'),
    State('total-reais-venda', 'value'),
    State('amount-venda', 'value'),
    State('limited', 'value'),
    State('market-venda', 'value'),
    prevent_initial_call=True,
)
def vender(n_clicks, preco_venda, total_reais, amount, tipo_ordem, mercado):  # noqa: PLR0913, PLR0917
    if n_clicks is not None:
        limited = tipo_ordem == 'limited'
        resposta_venda = Sell(
            preco_venda, preco_venda, amount, limited, market=mercado
        )
        return f'\nVendeu\n{resposta_venda}'
    return n_clicks


# Callback para comprar
@app.callback(
    Output('buy-button-output', 'children'),
    Input('buy-button', 'n_clicks'),
    State('preco-compra', 'value'),
    State('total-reais', 'value'),
    State('amount', 'value'),
    State('limited', 'value'),
    State('market-compra', 'value'),
    prevent_initial_call=True,
)
def comprar(n_clicks, preco_compra, total_reais, amount, tipo_ordem, mercado):  # noqa: PLR0913, PLR0917
    if n_clicks is not None:
        limited = tipo_ordem == 'limited'
        resposta_compra = Buy(
            preco_compra, total_reais, amount, limited, market=mercado
        )
        return f'\nComprou\n{resposta_compra}'
    return n_clicks


# pathname
@app.callback(
    Output('conteudo_pagina', 'children'),
    Input('url', 'pathname'),
)
def carregar_pagina(pathname):
    if pathname == '/':
        return layout_dashboard


@app.callback(
    Output('mantine-provider', 'forceColorScheme'),
    Output('theme-store', 'data'),
    Input('color-scheme-toggle', 'checked'),
    State('mantine-provider', 'forceColorScheme'),
    prevent_initial_call=True,
)
def switch_theme(_, theme):
    new_theme = 'dark' if theme == 'light' else 'light'
    return new_theme, new_theme


@callback(
    Output({'type': 'graph', 'index': ALL}, 'figure', allow_duplicate=True),
    Input(
        'mantine-provider',
        'forceColorScheme',
    ),
    State({'type': 'graph', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def update_figure(theme, ids):
    template = (
        pio.templates['mantine_light']
        if theme == 'light'
        else pio.templates['mantine_dark']
    )
    patched_figures = []
    for i in ids:
        patched_fig = Patch()
        patched_fig['layout']['template'] = template
        patched_figures.append(patched_fig)

    return patched_figures


# Callback para abrir o navbar
@app.callback(
    Output('app-shell', 'navbar'),
    Input('burger-button', 'opened'),
    State('app-shell', 'navbar'),
    prevent_initial_call=True,
)
def toggle_navbar(opened, navbar):
    navbar['collapsed']['mobile'] = not opened
    navbar['collapsed']['desktop'] = not opened
    return navbar


# Callback para abrir o aside
@app.callback(
    Output('app-shell', 'aside'),
    Input('aside-toggle', 'opened'),
    State('app-shell', 'aside'),
    prevent_initial_call=True,
)
def toggle_aside(opened, aside):
    aside['collapsed']['desktop'] = not opened
    aside['collapsed']['tablet'] = not opened
    aside['collapsed']['mobile'] = not opened
    return aside


# Callback para dispara uma notificação
# quando um trigger do estrategias.py é acionado
# @callback(
#     Output('notify-container', 'children'),
#     Input('interval-component-dash', 'n_intervals'),
#     prevent_initial_call=True,
# )
# def alerta_preco(n_intervals):
#     # lendo o arquivo de ordens
#     log_file_path = CAMINHO + r'\log.csv'
#     log_df = pd.read_csv(log_file_path, sep=';', encoding='utf-8')

#     # Converte a coluna 'time' para datetime
#     log_df['time'] = pd.to_datetime(log_df['time'], format='mixed')

#     # verificando se o ultimo log foi a seguntos atrás ou agora mesmo
#     last_log = log_df['time'].iloc[-1]

#     now = datetime.datetime.now()  # Obtém a data e hora atuais

#     # Calcula a diferença entre os dois objetos datetime
#     time_difference = now - last_log
#     # Acessa o atributo seconds do objeto timedelta
#     tempo_comparado = get_interval() * 0.5
#     auto_close = tempo_comparado * 1000
#     if time_difference.seconds < tempo_comparado:
#         loglevel = log_df['levelname'].iloc[-1]
#         if loglevel == 'INFO':
#             return dmc.Notification(
#                 id='my-notification',
#                 title='Mensagem do Robô',
#                 message=log_df['message'].iloc[-1],
#                 color='blue',
#                 action='show',
#                 autoClose=auto_close,
#                 icon=DashIconify(icon='logos:geekbot'),
#             )
#         elif loglevel == 'WARNING':
#             return dmc.Notification(
#                 id='my-notification',
#                 title='Atenção',
#                 message=log_df['message'].iloc[-1],
#                 color='yellow',
#                 action='show',
#                 autoClose=auto_close,
#                 icon=DashIconify(icon='twemoji:warning'),
#             )
#         elif loglevel == 'ERROR':
#             return dmc.Notification(
#                 id='my-notification',
#                 title='Mensagem do Robô',
#                 message=log_df['message'].iloc[-1],
#                 color='red',
#                 action='show',
#                 autoClose=auto_close,
#                 icon=DashIconify(icon='twemoji:cross-mark'),
#             )
#         else:
#             return dmc.Notification(
#                 id='my-notification',
#                 title='Mensagem do Robô',
#                 message=log_df['message'].iloc[-1],
#                 color='green',
#                 action='show',
#                 autoClose=auto_close,
#                 icon=DashIconify(icon='twemoji:check-mark'),
#             )
#     else:
#         return
