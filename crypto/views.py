# Importando as bibliotecas necessárias
import datetime
import json
import traceback

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from dash_resizable_panels import Panel, PanelGroup, PanelResizeHandle
from mitosheet.mito_dash.v1 import Spreadsheet, mito_callback

from crypto import app, dash_utils
from crypto.api_binance import get_klines
from crypto.api_bitpreco import Buy, Sell, carregar_opcoes_criptomoedas
from crypto.bot import get_interval
from crypto.componentes_personalizados import graf_preco_atuais

# Definição das variáveis de ambiente
CAMINHO = r'C:\Users\joaod\Documents\2024.2\crypto\crypto'
PRICE_FILE = CAMINHO + '/ticker.csv'
BALANCE_FILE = CAMINHO + '/balance.csv'
ORDERS_FILE = CAMINHO + '/executed_orders.csv'
INTERVAL_FILE = CAMINHO + '/interval.json'


# Definindo a coluna esquerda
left_column = html.Div(
    id='left-column',
    # className="eight columns",
    children=[
        # store para armazenar o estado do df de preços quando for atualizado
        dcc.Store(id='df-precos', storage_type='local'),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
        ),
        dmc.Tabs(
            id='tabs',
            value='Preços',
            children=[
                dmc.TabsList(
                    justify='space-around',
                    grow=True,
                    children=[
                        dmc.TabsTab(
                            'Preços',
                            value='Preços',
                            leftSection=DashIconify(
                                id='preco-icon', icon='cryptocurrency:btc'
                            ),
                        ),
                        dmc.TabsTab(
                            'Ordens de Compra',
                            value='Ordens de Compra',
                            leftSection=DashIconify(
                                id='ordens-icon', icon='mdi:cart-outline'
                            ),
                        ),
                    ],
                ),
                # tabs panel below
                dmc.TabsPanel(
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Skeleton(h=50, mb='xl'),
                            dmc.Skeleton(h=8, radius='xl'),
                            dmc.Skeleton(h=8, my=6),
                            dmc.Skeleton(h=8, w='70%', radius='xl'),
                        ],
                    ),
                    value='Preços',
                    id='tab-precos',
                ),
                dmc.TabsPanel(
                    dmc.Stack(
                        gap=0,
                        children=[
                            dmc.Skeleton(h=50, mb='xl'),
                            dmc.Skeleton(h=8, radius='xl'),
                            dmc.Skeleton(h=8, my=6),
                            dmc.Skeleton(h=8, w='70%', radius='xl'),
                        ],
                    ),
                    value='Ordens de Compra',
                    id='tab-ordens',
                ),
            ],
        ),
    ],
)

controle_tempo = html.Div([
    # html.H3(
    #     'Painel de Controle em Tempo Real de Criptomoedas',
    #     style={'text-align': 'center'},
    # ),
    dmc.Paper(
        children=[
            html.Div(
                children=[
                    dmc.DatePicker(
                        id='date-picker',
                        placeholder='Selecione a data',
                        value=datetime.datetime.now().strftime('%Y-%m-%d'),
                        # style={'width': '15%'},
                    ),
                    dmc.Space(h=10),
                    dmc.MultiSelect(
                        value=['BTC-BRL'],
                        id='filtro-cripto',
                        data=carregar_opcoes_criptomoedas(),
                        placeholder='Filtrar Criptomoedas',
                        searchable=True,
                        # style={'width': '20%'},
                    ),
                    dmc.Space(h=10),
                    html.Div(
                        children=[
                            html.Span(
                                'Taxa de Atualização (em Segundos)',
                                style={'font-weight': 'bold'},
                            )
                        ],
                    ),
                    dmc.Space(h=10),
                    html.Div(
                        children=[
                            dmc.Slider(
                                id='interval-refresh',
                                value=int(get_interval()),
                                min=3,
                                max=240,
                                marks=[
                                    {'value': 3, 'label': '3 seg'},
                                    {'value': 60, 'label': '1 min'},
                                    {'value': 120, 'label': '2 min'},
                                    {'value': 180, 'label': '3 min'},
                                    {'value': 240, 'label': '4 min'},
                                ],
                                radius='xs',
                                size='xs',
                                mb=35,
                            ),
                        ],
                    ),
                    dmc.Space(h=10),
                    html.Div(
                        children=[
                            dmc.Select(
                                label='Recência dos Dados',
                                description='Tempo de recência dos dados',
                                placeholder='Selecione uma opção',
                                id='data-recency',
                                value='15',
                                data=[
                                    {
                                        'label': 'Último 1 minuto',
                                        'value': '1',
                                    },
                                    {
                                        'label': 'Últimos 2 minutos',
                                        'value': '3',
                                    },
                                    {
                                        'label': 'Últimos 5 minutos',
                                        'value': '5',
                                    },
                                    {
                                        'label': 'Últimos 15 minutos',
                                        'value': '15',
                                    },
                                    {
                                        'label': 'Últimos 30 minutos',
                                        'value': '30',
                                    },
                                    {
                                        'label': 'Última hora',
                                        'value': '60',
                                    },
                                    {
                                        'label': 'Últimas 2 horas',
                                        'value': '120',
                                    },
                                    {
                                        'label': 'Últimas 4 horas',
                                        'value': '240',
                                    },
                                    {
                                        'label': 'Últimas 6 horas',
                                        'value': '360',
                                    },
                                    {
                                        'label': 'Últimas 12 horas',
                                        'value': '720',
                                    },
                                    {
                                        'label': 'Último dia',
                                        'value': '1440',
                                    },
                                    {
                                        'label': 'Últimos 3 dias',
                                        'value': '4320',
                                    },
                                    {
                                        'label': 'Última Semana',
                                        'value': '10080',
                                    },
                                    {
                                        'label': 'Últimos 30 dias',
                                        'value': '43200',
                                    },
                                ],
                                mb=10,
                            ),
                            dmc.Space(h=10),
                            dmc.Select(
                                label='Recência dos Dados candlestick',
                                description='Tempo de recência do candlestick',
                                placeholder='Selecione uma opção',
                                id='data-recency-candlestick',
                                value='1',
                                data=[
                                    {
                                        'label': 'Último 1 minuto',
                                        'value': '1',
                                    },
                                    {
                                        'label': 'Últimos 2 minutos',
                                        'value': '3',
                                    },
                                    {
                                        'label': 'Últimos 5 minutos',
                                        'value': '5',
                                    },
                                    {
                                        'label': 'Últimos 15 minutos',
                                        'value': '15',
                                    },
                                    {
                                        'label': 'Últimos 30 minutos',
                                        'value': '30',
                                    },
                                    {
                                        'label': 'Última hora',
                                        'value': '60',
                                    },
                                    {
                                        'label': 'Últimas 2 horas',
                                        'value': '120',
                                    },
                                    {
                                        'label': 'Últimas 4 horas',
                                        'value': '240',
                                    },
                                    {
                                        'label': 'Últimas 6 horas',
                                        'value': '360',
                                    },
                                    {
                                        'label': 'Últimas 12 horas',
                                        'value': '720',
                                    },
                                    {
                                        'label': 'Último dia',
                                        'value': '1440',
                                    },
                                    {
                                        'label': 'Últimos 3 dias',
                                        'value': '4320',
                                    },
                                    {
                                        'label': 'Última Semana',
                                        'value': '10080',
                                    },
                                    {
                                        'label': 'Últimos 30 dias',
                                        'value': '43200',
                                    },
                                ],
                                mb=10,
                            ),
                        ],
                        className='three columns',
                    ),
                ],
                className='one row',
                style={'padding': '5px 0'},
            ),
            html.Div(id='latest-timestamp', style={'padding': '5px 0'}),
        ],
        shadow='sm',
        radius='xl',
        p='xl',
    ),
    html.Div(id='notify-container'),
    dmc.Group(
        children=[
            dmc.Button(
                'Load Data',
                id='show-notification',
            ),
            dmc.Button(
                'Update',
                id='update-notification',
            ),
        ],
    ),
])

step = 0.00000001

# Coluna Esquerda
right_column = html.Div(
    id='right-column',
    # className="four columns",
    children=[
        dmc.Tabs(
            value='Comprar',
            children=[
                dmc.TabsList(
                    justify='space-around',
                    grow=True,
                    children=[
                        dmc.TabsTab(
                            'Comprar',
                            value='Comprar',
                            leftSection=DashIconify(icon='mdi:cart-outline'),
                        ),
                        dmc.TabsTab(
                            'Vender',
                            value='Vender',
                            leftSection=DashIconify(
                                icon='mdi:cart-arrow-down'
                            ),
                        ),
                    ],
                ),
                # tabs panel below
                dmc.TabsPanel(
                    dmc.Stack(
                        gap=0,
                        children=[
                            # Compra
                            dmc.Paper(
                                children=[
                                    dmc.Flex(
                                        direction={
                                            'base': 'column',
                                            'sm': 'column',
                                        },
                                        gap={'base': 'sm', 'sm': 'lg'},
                                        justify={'sm': 'center'},
                                        align={
                                            'base': 'center',
                                            'sm': 'center',
                                        },
                                        children=[
                                            # price
                                            dmc.NumberInput(
                                                id='preco-compra',
                                                label='Preço unitário',
                                                description='Preço de compra do ativo',  # noqa: E501
                                                value=0,
                                                min=0,
                                                step=step,
                                            ),
                                            # volume
                                            dmc.Stack(
                                                [
                                                    dmc.NumberInput(
                                                        id='total-reais',
                                                        label='Total em reais',
                                                        value=0,
                                                        min=0,
                                                        step=step,
                                                    ),
                                                    dmc.Group(
                                                        children=[
                                                            dmc.ButtonGroup(
                                                                id='reais-buttons',
                                                                children=[
                                                                    dmc.Button(
                                                                        '10%',
                                                                        id='reais-10',
                                                                        variant='subtle',
                                                                    ),
                                                                    dmc.Button(
                                                                        '25%',
                                                                        id='reais-25',
                                                                        variant='subtle',
                                                                    ),
                                                                    dmc.Button(
                                                                        '50%',
                                                                        id='reais-50',
                                                                        variant='subtle',
                                                                    ),
                                                                    dmc.Button(
                                                                        '100%',
                                                                        id='reais-100',
                                                                        variant='subtle',
                                                                    ),
                                                                ],
                                                            ),
                                                        ],
                                                        gap='xs',
                                                        justify='center',
                                                    ),
                                                ],
                                                align='center',
                                                style={'width': '100%'},
                                            ),
                                            # amount
                                            dmc.NumberInput(
                                                id='amount',
                                                label='Quantia',
                                                description='Quantidade em BTC',  # noqa: E501
                                                value=0,
                                                min=0,
                                                step=step,
                                            ),
                                            # limited
                                            dmc.Select(
                                                label='Tipo de Ordem',
                                                description='Tipo de ordem de compra',  # noqa: E501
                                                placeholder='Selecione uma opção',  # noqa: E501
                                                id='limited',
                                                value='limited',
                                                data=[
                                                    {
                                                        'value': 'limited',
                                                        'label': 'Limitada',
                                                    },
                                                    {
                                                        'value': 'market',
                                                        'label': 'Mercado',
                                                    },
                                                ],
                                                mb=10,
                                            ),
                                            # market='BTC-BRL'
                                            dmc.Select(
                                                label='Selecione o Mercado',
                                                placeholder='Selecione uma opção',  # noqa: E501
                                                id='market-compra',
                                                value='BTC-BRL',
                                                data=carregar_opcoes_criptomoedas(),
                                                mb=10,
                                            ),
                                            # botao de compra
                                            dmc.Button(
                                                'Comprar?',
                                                variant='outline',
                                                id='buy-button',
                                            ),
                                            dmc.Text(
                                                id='buy-button-output',
                                                size='sm',
                                                mb=10,
                                            ),
                                        ],
                                    ),
                                ],
                                # definindo tamanho fixo
                                style={'width': '100%'},
                                shadow='md',
                                radius='lg',
                                p='xl',
                                withBorder=True,
                            ),
                        ],
                    ),
                    value='Comprar',
                ),
                dmc.TabsPanel(
                    dmc.Stack(
                        gap=0,
                        children=[
                            # Venda
                            dmc.Flex(
                                children=[
                                    # price
                                    dmc.NumberInput(
                                        id='preco-venda',
                                        label='Preço unitário',
                                        description='Preço de venda do ativo',
                                        value=0,
                                        min=0,
                                        step=step,
                                    ),
                                    # volume
                                    dmc.NumberInput(
                                        id='total-reais-venda',
                                        label='Total em reais',
                                        value=0,
                                        min=0,
                                        step=step,
                                    ),
                                    # amount
                                    dmc.Stack(
                                        [
                                            dmc.NumberInput(
                                                id='amount-venda',
                                                label='Quantia',
                                                description='Quantidade em BTC',  # noqa: E501
                                                value=0,
                                                min=0,
                                                step=step,
                                            ),
                                            dmc.Group(
                                                children=[
                                                    dmc.ButtonGroup(
                                                        children=[
                                                            dmc.Button(
                                                                '10%',
                                                                id='amount-10',
                                                                variant='subtle',
                                                            ),
                                                            dmc.Button(
                                                                '25%',
                                                                id='amount-25',
                                                                variant='subtle',
                                                            ),
                                                            dmc.Button(
                                                                '50%',
                                                                id='amount-50',
                                                                variant='subtle',
                                                            ),
                                                            dmc.Button(
                                                                '100%',
                                                                id='amount-100',
                                                                variant='subtle',
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                                gap='sm',
                                                justify='center',
                                            ),
                                        ],
                                        align='center',
                                        style={'width': '100%'},
                                    ),
                                    # limited
                                    dmc.Select(
                                        label='Tipo de Ordem',
                                        description='Tipo de ordem de venda',
                                        placeholder='Selecione uma opção',
                                        id='limited-sell',
                                        value='limited',
                                        data=[
                                            {
                                                'value': 'limited',
                                                'label': 'Limitada',
                                            },
                                            {
                                                'value': 'market',
                                                'label': 'Mercado',
                                            },
                                        ],
                                        mb=10,
                                    ),
                                    # market='BTC-BRL'
                                    dmc.Select(
                                        label='Selecione o Mercado',
                                        placeholder='Selecione uma opção',
                                        id='market-venda',
                                        value='BTC-BRL',
                                        data=carregar_opcoes_criptomoedas(),
                                        mb=10,
                                    ),
                                    # botao de venda
                                    dmc.Button(
                                        'Vender?',
                                        variant='outline',
                                        id='sell-button',
                                    ),
                                    dmc.Text(
                                        id='sell-button-output',
                                        size='sm',
                                        mb=10,
                                    ),
                                ],
                                # centralizando o conteudo
                                direction={'base': 'column', 'sm': 'column'},
                                gap={'base': 'sm', 'sm': 'lg'},
                                justify={'sm': 'center'},
                                align={'base': 'center', 'sm': 'center'},
                            ),
                        ],
                    ),
                    value='Vender',
                ),
            ],
        ),
    ],
)

horizontal_panel_group = PanelGroup(
    id='horizontal_panel_group',
    children=[
        Panel(
            id='panel-1',
            children=[
                # vertical_panel_group,
                left_column,
            ],
            defaultSizePercentage=85,
        ),
        PanelResizeHandle(
            html.Div(
                style={
                    'backgroundColor': 'white',
                    'height': '100%',
                    'width': '5px',
                }
            )
        ),
        Panel(
            id='panel-2',
            children=[
                right_column,
            ],
        ),
    ],
    direction='horizontal',
)

theme_toggle = dmc.Switch(
    offLabel=DashIconify(icon='radix-icons:moon', width=20),
    onLabel=DashIconify(icon='radix-icons:sun', width=20),
    size='xl',
    variant='transparent',
    color='yellow',
    id='color-scheme-toggle',
    ms='auto',
    checked=True,
)


# Cabecalho da aplicação
header = dmc.Group(
    [
        dmc.Burger(id='burger-button', opened=False),
        html.Img(src=app.get_asset_url('fotos_site/logo.png'), width=40),
        dmc.Text('Painel de Criptomoedas', size='xl', fw=700),
        dmc.Switch(
            offLabel=DashIconify(icon='radix-icons:moon', width=20),
            onLabel=DashIconify(icon='radix-icons:sun', width=20),
            size='xl',
            variant='transparent',
            color='yellow',
            id='color-scheme-toggle',
            ms='auto',
            checked=True,
        ),
        # Botão para abrir o aside
        dmc.Burger(id='aside-toggle', opened=False),
    ],
    justify='space-between',
    align='center',
)

# Seção de Preços Atuais com variação 24h e ícones
preco_atual = dmc.Paper(
    dmc.Stack([
        html.Div(
            children=[
                dmc.Text('Preços Atuais', size='lg', fw=700),
                html.Hr(),
                dmc.Skeleton(
                    visible=False,
                    id='precos-at',
                    children=graf_preco_atuais(),
                    mb=10,
                ),
            ],
            style={'padding': '10px'},
        )
    ]),
    shadow='md',
    radius='lg',
    p='xl',
)

# Histórico de preços e tabela com botão de exportação
historico_precos = dmc.Paper(
    children=[
        dmc.Stack(
            [
                dmc.Tabs(
                    id='tabs-historico-precos',
                    value='Histórico de Preços',
                    children=[
                        dmc.TabsList(
                            justify='space-around',
                            grow=True,
                            children=[
                                dmc.TabsTab(
                                    'Histórico de Preços',
                                    value='Histórico de Preços',
                                ),
                                dmc.TabsTab(
                                    'Codigos',
                                    value='code-hist',
                                ),
                            ],
                        ),
                        # tabs panel below
                        dmc.TabsPanel(
                            dmc.Stack(
                                gap=0,
                                children=[
                                    dmc.Text(
                                        'Histórico de Preços',
                                        size='lg',
                                        fw=700,
                                    ),
                                    html.Hr(),
                                    html.Div(
                                        Spreadsheet(
                                            id={
                                                'type': 'spreadsheet',
                                                'id': 'sheet',
                                            }
                                        ),
                                    ),
                                ],
                            ),
                            value='Histórico de Preços',
                            id='tab-historico',
                        ),
                        dmc.TabsPanel(
                            dmc.Stack(
                                gap=0,
                                children=[
                                    html.Div(id='output1'),
                                ],
                            ),
                            value='code-hist',
                            id='code-hist',
                        ),
                    ],
                ),
            ],
        )
    ],
    shadow='md',
    radius='lg',
    p='xl',
)

# Gráficos de Linha, Candlestick e Pizza
graficos = dmc.Paper(
    children=[
        dmc.Group(
            [
                dmc.Text('Gráficos', size='lg', fw=700),
                # dcc.Graph(id='grafico-linha'),
                # dcc.Graph(id='grafico-candlestick'),
                # dcc.Graph(id='grafico-pizza'),
            ],
        )
    ],
    shadow='md',
    radius='lg',
    p='xl',
)

# Painel lateral para alertas personalizados e indicadores
painel_alertas = dmc.Paper(
    dmc.Stack(
        [
            dmc.Text('Painel de Insights e Alertas', size='lg', fw=700),
            dmc.Text('Configurar alertas personalizados', c='gray'),
            dmc.NumberInput(
                id='alerta-preco',
                label='Alerta de Preço',
                description='Definir um preço para alerta',
                value=0,
                min=0,
                step=0.01,
            ),
            dmc.Button('Ativar Alerta', id='botao-alerta'),
            dmc.Text('Indicadores de Tendência', c='gray'),
            dmc.CheckboxGroup(
                id='indicadores-tendencia',
                label='Indicadores de Tendência',
                description='Selecione os indicadores de tendência',
                withAsterisk=True,
                mb=10,
                children=dmc.Group(
                    [
                        dmc.Checkbox(label='Média Móvel', value='sma'),
                        dmc.Checkbox(label='RSI', value='rsi'),
                    ],
                    mt=10,
                ),
                value=['sma', 'rsi'],
            ),
        ],
    ),
    shadow='md',
    radius='lg',
    p='xl',
)

# Layout do Dashboard Principal
layout_dashboard = html.Div(
    id='app-container',
    children=[
        dcc.Store(id='df-precos', storage_type='local'),
        dcc.Store(id='df-executed-orders', storage_type='local'),
        dcc.Store(id='df-balance', storage_type='local'),
        dmc.Grid(
            [
                horizontal_panel_group,
                dmc.GridCol(preco_atual, span=4),
                dmc.GridCol(historico_precos, span=4),
                dmc.GridCol(graficos, span=4),
                dmc.GridCol(painel_alertas, span=4),
            ],
            gutter='xs',
        ),
    ],
)

layout_pagina = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        dmc.NotificationProvider(position='top-right'),
        html.Div(id='conteudo_pagina'),
    ],
)

appshell = dmc.AppShell(
    [
        dmc.AppShellHeader(header, px=25, py=10),
        dmc.AppShellNavbar(
            controle_tempo,
        ),
        dmc.AppShellMain(layout_pagina),
    ],
    header={'height': 70},
    padding='xl',
    id='app-shell',
    navbar={
        'width': 300,
        'breakpoint': 'sm',
        'collapsed': {'mobile': True, 'desktop': True},
    },
    aside={
        'width': 300,
        'breakpoint': 'sm',
        'collapsed': {'desktop': True, 'mobile': True},
    },
)

# Definindo o layout do aplicativo
app.layout = dmc.MantineProvider(
    [
        dcc.Store(id='theme-store', storage_type='local', data='light'),
        appshell,
    ],
    id='mantine-provider',
    forceColorScheme='light',
)


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


# Callback para atualizar os dados do ticker
@app.callback(
    Output('df-precos', 'data'),
    Input('interval-component', 'n_intervals'),
)
def update_df_precos(n_intervals):
    # ticker_json = Ticker().json()
    df_precos = pd.read_csv(PRICE_FILE)
    # df_precos = save_price_to_csv(ticker_json)
    return df_precos.to_dict('records')


@app.callback(
    Output('df-executed-orders', 'data'),
    Input('interval-component', 'n_intervals'),
)
def update_df_executed_orders(n_intervals):
    executed_orders_df = pd.read_csv(ORDERS_FILE)
    return executed_orders_df.to_dict('records')


@app.callback(
    Output('df-balance', 'data'),
    Input('interval-component', 'n_intervals'),
)
def update_df_balance(n_intervals):
    balance_df = pd.read_csv(BALANCE_FILE)
    return balance_df.to_dict('records')


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
    Output('precos-at', 'children'),
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
    return graf_preco_atuais(
        data_recency,
        df,
        executed_orders_df,
    )


# Callback para adicionar o conteúdo da página dentro do tab Preços
@app.callback(
    Output('tab-precos', 'children'),
    Input('data-recency', 'value'),
    Input('data-recency-candlestick', 'value'),
    Input('df-precos', 'data'),
    Input('df-executed-orders', 'data'),
    Input('tabs', 'value'),
    prevent_initial_call=True,
)
def preco_tab(  # noqa: PLR0915
    data_recency,
    data_recency_candlestick,
    df,
    executed_orders_df,
    value,
):
    df = pd.DataFrame(df)

    executed_orders_df = pd.DataFrame(executed_orders_df)

    # Obtenha a data e hora atuais
    now = datetime.datetime.now()
    data_recency = float(data_recency)
    if data_recency is None:
        data_recency = 3
    # Calcule o início do período de interesse (10 minutos atrás)
    minutes_ago = now - datetime.timedelta(minutes=data_recency)

    try:
        # table = create_table(df)
        # Criando um gráfico de indicadores para os preços
        df_now = {
            'minPrice': df['low'].iloc[-1],
            'avgPrice': df['avg'].iloc[-1],
            'maxPrice': df['high'].iloc[-1],
            'count': len(df),
            'amountTraded': df['vol'].iloc[-1],
        }
        df_prev = {
            'minPrice': df['low'].iloc[-2]
            if len(df) > 1
            else df['low'].iloc[-1],
            'avgPrice': df['avg'].iloc[-2]
            if len(df) > 1
            else df['avg'].iloc[-1],
            'maxPrice': df['high'].iloc[-2]
            if len(df) > 1
            else df['high'].iloc[-1],
            'count': len(df) - 1 if len(df) > 1 else len(df),
            'amountTraded': df['vol'].iloc[-2]
            if len(df) > 1
            else df['last'].sum(),
        }

        fig = go.Figure()
        if df_now['count'] > 0:
            if df_prev['count'] > 0:
                # Ultimo preço
                dash_utils.add_delta_trace(
                    fig,
                    'Último Preço',
                    df['last'].iloc[-1],
                    df['last'].iloc[-2],
                    0,
                    0,
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Menor Preço 24h',
                    df_now['minPrice'],
                    df_prev['minPrice'],
                    0,
                    1,
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Preço médio',
                    df_now['avgPrice'],
                    df_prev['avgPrice'],
                    0,
                    2,
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Preço Máximo',
                    df_now['maxPrice'],
                    df_prev['maxPrice'],
                    1,
                    0,
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Transações',
                    df_now['count'],
                    df_prev['count'],
                    1,
                    1,
                )
                dash_utils.add_delta_trace(
                    fig,
                    'Quantidade Negociada',
                    df_now['amountTraded'],
                    df_prev['amountTraded'],
                    1,
                    2,
                )
            else:
                dash_utils.add_trace(
                    fig, 'Último Preço', df['last'].iloc[-1], 0, 0
                )
                dash_utils.add_trace(
                    fig, 'Menor Preço 24h', df_now['minPrice'][0], 0, 1
                )
                dash_utils.add_trace(
                    fig, 'Preço médio', df_now['avgPrice'][0], 0, 2
                )
                dash_utils.add_trace(
                    fig, 'Preço Máximo', df_now['maxPrice'][0], 1, 0
                )
                dash_utils.add_trace(
                    fig, 'Transações', df_now['count'][0], 1, 1
                )
                dash_utils.add_trace(
                    fig,
                    'Quantidade Negociada',
                    df_now['amountTraded'][0],
                    1,
                    2,
                )
            fig.update_layout(
                grid={'rows': 2, 'columns': 3, 'pattern': 'independent'},
            )
        else:
            fig.update_layout(
                annotations=[
                    {
                        'text': 'No transactions found',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'size': 28},
                    }
                ]
            )
        # criando o gráfico de candlestick
        fig1 = go.Figure()

        # convertendo o tempo de recência para o formato de intervalo suportado
        interval_mapping = {
            '1': '1m',
            '3': '3m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '1h',
            '120': '2h',
            '240': '4h',
            '360': '6h',
            '720': '12h',
            '1440': '1d',
            '4320': '3d',
            '10080': '1w',
            '43200': '1M',
        }

        intervalo = interval_mapping.get(
            str(int(data_recency_candlestick)), '1m'
        )

        df2 = get_klines(interval=intervalo)

        fig1.add_trace(
            go.Candlestick(
                x=df2['Kline open time'],
                open=df2['Open price'],
                high=df2['High price'],
                low=df2['Low price'],
                close=df2['Close price'],
                name='Api Binance',
            )
        )

        fig1.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['last'],
                mode='lines',
                name='Último Preço',
                line=dict(color='white', width=1),
            )
        )

        # adicionando marcadores com as ordens de compra e venda
        fig1.add_trace(
            go.Scatter(
                x=executed_orders_df[executed_orders_df['type'] == 'BUY'][
                    'time_stamp'
                ],
                y=executed_orders_df[executed_orders_df['type'] == 'BUY'][
                    'price'
                ],
                mode='markers',
                name='BUY Executed Orders',
                marker=dict(color='orange', size=10.5, symbol='x'),
            )
        )
        fig1.add_trace(
            go.Scatter(
                x=executed_orders_df[executed_orders_df['type'] == 'SELL'][
                    'time_stamp'
                ],
                y=executed_orders_df[executed_orders_df['type'] == 'SELL'][
                    'price'
                ],
                mode='markers',
                name='SELL Executed Orders',
                marker=dict(color='green', size=10.5, symbol='x'),
            )
        )

        fig1.update_layout(
            title='BTC-BRL Prices Over Time',
            xaxis_title='Timestamp',
            yaxis_title='Price (BRL)',
            template='plotly_dark',
            xaxis_rangeslider_visible=True,
            xaxis_range=[
                minutes_ago.strftime('%Y-%m-%d %H:%M:%S'),
                now.strftime('%Y-%m-%d %H:%M:%S'),
            ],
        )
        return [
            html.Div(
                children=[
                    dcc.Graph(figure=fig, mathjax=True),
                ],
            ),
            html.Div(
                children=[
                    html.Hr(),
                    dcc.Graph(figure=fig1, mathjax=True),
                ],
            ),
            # html.Div(
            #     children=[table],
            # ),
        ]
    except Exception as e:
        tb = traceback.format_exc()
        resultado = f'Erro: {e}'
        return html.Div(
            children=[
                html.H5(children=f'{resultado}'),
                dcc.Markdown(
                    '{}'.format(tb),
                    style={'font-size': '14pt'},
                ),
            ]
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
        html.Code(
            f'Code: {spreadsheet_result.code()}',
            style={'whiteSpace': 'pre-wrap'},
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
                    dcc.Graph(figure=fig, mathjax=True),
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
    State('df-executed-orders', 'data'),
    State('df-balance', 'data'),
    Input('df-precos', 'data'),
)
def atualizar_preco_venda_input(df_executed_orders, df_balance, df_precos):
    df_precos = pd.DataFrame(df_precos)
    df_executed_orders = pd.DataFrame(df_executed_orders)
    df_balance = pd.DataFrame(df_balance)
    # o gatilho vai aqui
    sell_trigger = 380000.00
    ultimo_preco = df_precos['last'].iloc[-1]
    if ultimo_preco > sell_trigger:
        Sell(
            ultimo_preco,
            ultimo_preco,
            df_balance['BTC'].iloc[0],
            True,
            market='BTC-BRL',
        )

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
@callback(
    Output('notify-container', 'children'),
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True,
)
def alerta_preco(n_intervals):
    # lendo o arquivo de ordens
    log_file_path = r'C:\Users\joaod\Documents\2024.2\crypto\log.csv'
    log_df = pd.read_csv(log_file_path, encoding='utf-8')

    # Converte a coluna 'time' para datetime
    log_df['time'] = pd.to_datetime(log_df['time'], format='ISO8601')

    # verificando se o ultimo log foi a seguntos atrás ou agora mesmo
    last_log = log_df['time'].iloc[-1]

    now = datetime.datetime.now()  # Obtém a data e hora atuais

    # Calcula a diferença entre os dois objetos datetime
    time_difference = now - last_log
    # Acessa o atributo seconds do objeto timedelta
    tempo_comparado = get_interval() * 0.5
    auto_close = tempo_comparado * 1000
    if time_difference.seconds < tempo_comparado:
        loglevel = log_df['levelname'].iloc[-1]
        if loglevel == ' INFO ':
            return dmc.Notification(
                id='my-notification',
                title='Mensagem do Robô',
                message=log_df['message'].iloc[-1],
                color='blue',
                action='show',
                autoClose=auto_close,
                icon=DashIconify(icon='logos:geekbot'),
            )
        elif loglevel == ' WARNING ':
            return dmc.Notification(
                id='my-notification',
                title='Atenção',
                message=log_df['message'].iloc[-1],
                color='yellow',
                action='show',
                autoClose=auto_close,
                icon=DashIconify(icon='twemoji:warning'),
            )
        elif loglevel == ' ERROR ':
            return dmc.Notification(
                id='my-notification',
                title='Mensagem do Robô',
                message=log_df['message'].iloc[-1],
                color='red',
                action='show',
                autoClose=auto_close,
                icon=DashIconify(icon='twemoji:cross-mark'),
            )
        else:
            return dmc.Notification(
                id='my-notification',
                title='Mensagem do Robô',
                message=log_df['message'].iloc[-1],
                color='green',
                action='show',
                autoClose=auto_close,
                icon=DashIconify(icon='twemoji:check-mark'),
            )
    else:
        return
