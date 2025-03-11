# Importando as bibliotecas necessárias
import datetime

import dash_mantine_components as dmc

# Diskcache
from dash import dcc, html
from dash_iconify import DashIconify

from compartilhado import (
    coinpair_options,
    get_interval,
    get_str_coinpairs,
)
from dashboard import app
from dashboard.componentes_personalizados import (
    bar_precos_atuais,
)
from dashboard.graph_preco_tab import div_graph_preco

# from crypto.timescaledb import read_from_db


dmc.add_figure_templates()


controle_tempo = html.Div([
    dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Group(
                    children=[
                        dmc.Text('Painel de Controle', size='lg', fw=700),
                    ],
                    justify='space-between',
                ),
                withBorder=True,
                inheritPadding=True,
                py='xs',
            ),
            dmc.CardSection(
                inheritPadding=True,
                mt='sm',
                pb='md',
                children=[
                    dmc.ScrollArea(
                        h=380,
                        scrollbarSize=2,
                        # offsetScrollbars=True,
                        children=[
                            dmc.DatePickerInput(
                                id='date-picker',
                                placeholder='Selecione a data',
                                value=datetime.datetime.now().strftime(
                                    '%Y-%m-%d'
                                ),
                                mb=10,
                            ),
                            dmc.MultiSelect(
                                value=get_str_coinpairs(),
                                id='filtro-cripto',
                                data=coinpair_options(),
                                placeholder='Filtrar Criptomoedas',
                                searchable=True,
                                clearable=True,
                                label='Selecione os pares de moedas',
                                description='Você pode selecionar'
                                + ' múltiplas moedas',
                                nothingFoundMessage='Nenhuma moeda encontrada',
                                mb=10,
                            ),
                            dmc.Text(
                                'Taxa de Atualização do Bot',
                                fw='bold',
                                mb=10,
                            ),
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
                            dmc.Text(
                                'Taxa de Atualização do Dash',
                                fw='bold',
                                mb=10,
                            ),
                            dmc.Slider(
                                id='interval-refresh-dash',
                                value=60,
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
                            dmc.Select(
                                label='Recência dos Dados',
                                description='Tempo de recência dos dados',
                                placeholder='Selecione uma opção',
                                id='data-recency',
                                value='30',
                                data=[
                                    {'label': 'Último 1 minuto', 'value': '1'},
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
                                    {'label': 'Última hora', 'value': '60'},
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
                                    {'label': 'Último dia', 'value': '1440'},
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
                            dmc.Select(
                                label='Recência dos Dados candlestick',
                                description='Tempo de recência do candlestick',
                                placeholder='Selecione uma opção',
                                id='data-recency-candlestick',
                                value='1',
                                data=[
                                    {'label': 'Último 1 minuto', 'value': '1'},
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
                                    {'label': 'Última hora', 'value': '60'},
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
                                    {'label': 'Último dia', 'value': '1440'},
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
                    ),
                ],
            ),
        ],
        withBorder=True,
        shadow='xl',
        radius='md',
        h=450,
    ),
    html.Div(id='latest-timestamp', style={'padding': '5px 0'}),
    html.Div(id='notify-container'),
])

step = 0.00000001

# Coluna Esquerda - Cartão de Compra
card_compra = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text('Comprar', size='lg', fw=700),
                    dmc.Badge('Novo', color='green', variant='light'),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                # Conteúdo do painel de compra
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
                            description='Preço de compra do ativo',
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
                            description='Quantidade em BTC',
                            value=0,
                            min=0,
                            step=step,
                        ),
                        # limited
                        dmc.Select(
                            label='Tipo de Ordem',
                            description='Tipo de ordem de compra',
                            placeholder='Selecione uma opção',
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
                        dmc.MultiSelect(
                            label='Selecione o Mercado',
                            placeholder='Selecione uma opção',
                            id='market-compra',
                            value=get_str_coinpairs(),
                            data=coinpair_options(),
                            mb=10,
                        ),
                        # botao de compra
                        dmc.Button(
                            'Comprar',
                            leftSection=DashIconify(icon='mdi:cart-outline'),
                            variant='filled',
                            color='green',
                            radius='md',
                            id='buy-button',
                            fullWidth=True,
                        ),
                        dmc.Text(
                            id='buy-button-output',
                            size='sm',
                            mb=10,
                        ),
                    ],
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    style={'height': '100%'},
)

# Cartão de Venda
card_venda = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text('Vender', size='lg', fw=700),
                    dmc.Badge('Novo', color='red', variant='light'),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                # Conteúdo do painel de venda
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
                                    description='Quantidade em BTC',
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
                        dmc.MultiSelect(
                            label='Selecione o Mercado',
                            placeholder='Selecione uma opção',
                            id='market-venda',
                            value=get_str_coinpairs(),
                            data=coinpair_options(),
                            mb=10,
                        ),
                        # botao de venda
                        dmc.Button(
                            'Vender',
                            leftSection=DashIconify(
                                icon='mdi:cart-arrow-down'
                            ),
                            variant='filled',
                            color='red',
                            radius='md',
                            id='sell-button',
                            fullWidth=True,
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
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    # style={'height': '100%', 'display': 'none'},  # Inicialmente oculto
    id='card-venda',
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
        # Grupo de preços atuais da moeda selecionada
        html.Div(
            [bar_precos_atuais()],
            id='bar-precos-atuais',
        ),
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

# Histórico de preços e tabela com botão de exportação
historico_precos = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text('Histórico de Preços', size='lg', fw=700),
                    dmc.ActionIcon(
                        DashIconify(icon='carbon:overflow-menu-horizontal'),
                        color='gray',
                        variant='transparent',
                        id='historico-menu',
                    ),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                html.Div(
                    id='historico-tabela-container',
                    children=[
                        # Será preenchido pelo callback
                    ],
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    style={'height': '100%'},
)

balanco_conta = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text('Balanço da Conta', size='lg', fw=700),
                    dmc.ActionIcon(
                        DashIconify(icon='carbon:overflow-menu-horizontal'),
                        color='gray',
                        variant='transparent',
                        id='balanco-menu',
                    ),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                html.Div(
                    id='balanco-tabela-container',
                    children=[
                        # Será preenchido pelo callback
                    ],
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    style={'height': '100%'},
)

# Card para códigos (substituindo a segunda aba)
code_card = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text('Códigos', size='lg', fw=700),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                dmc.CodeHighlight(
                    id='code-highlighter',
                    language='python',
                    code="""
                        # Código da felicidade dos desenvolvedores
def hello_world():
    print("Hello, world!")
                    """,
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    id='code-hist-card',
)

# Gráficos de Linha, Candlestick e Pizza
graficos = dmc.Card(
    children=[
        dmc.CardSection(
            [
                dmc.Text('Gráficos', size='lg', fw=700),
            ],
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            children=[
                dmc.ScrollArea(
                    h=400,
                    children=[
                        div_graph_preco,
                    ],
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    h=450,
)

# Painel lateral para alertas personalizados e indicadores
painel_alertas = dmc.Card(
    children=[
        dmc.CardSection(
            dmc.Group(
                children=[
                    dmc.Text(
                        'Painel de Insights e Alertas', size='lg', fw=700
                    ),
                ],
                justify='space-between',
            ),
            withBorder=True,
            inheritPadding=True,
            py='xs',
        ),
        dmc.CardSection(
            inheritPadding=True,
            mt='sm',
            pb='md',
            children=[
                dmc.ScrollArea(
                    h=380,
                    # w=350,
                    scrollbarSize=2,
                    # offsetScrollbars=True,
                    children=[
                        dmc.Stack(
                            children=[
                                dmc.CheckboxGroup(
                                    id='graf-info',
                                    label='Plots do Gráfico',
                                    description='Selecione informações do'
                                    + ' gráfico que deseja mostrar',
                                    withAsterisk=True,
                                    mb=10,
                                    children=dmc.Group(
                                        [
                                            dmc.Checkbox(
                                                label='Ordens Executadas',
                                                value='orders',
                                            ),
                                            dmc.Checkbox(
                                                label='Dataframe do Ticket',
                                                value='ticker',
                                            ),
                                            dmc.Checkbox(
                                                label='Gráfico de Velas'
                                                + ' da Binance',
                                                value='candlestick',
                                            ),
                                            dmc.Checkbox(
                                                label='Gráfico de Velas'
                                                + ' da Bity',
                                                value='bity_candlestick',
                                            ),
                                            dmc.Checkbox(
                                                label='Mostrar Intervalo'
                                                + ' de Barras',
                                                value='rangeslider',
                                            ),
                                        ],
                                        mt=10,
                                    ),
                                    value=[
                                        'orders',
                                        'bity_candlestick',
                                        'ticker',
                                    ],
                                ),
                                dmc.CheckboxGroup(
                                    id='indicadores-tecnicos',
                                    label='Indicadores Técnicos',
                                    description='Selecione os indicadores'
                                    + ' técnicos',
                                    withAsterisk=True,
                                    mb=10,
                                    children=dmc.Group(
                                        [
                                            dmc.Checkbox(
                                                label='EMA 5', value='ema_5'
                                            ),
                                            dmc.Checkbox(
                                                label='EMA 10', value='ema_10'
                                            ),
                                            dmc.Checkbox(
                                                label='EMA 20', value='ema_20'
                                            ),
                                            dmc.Checkbox(
                                                label='EMA 200',
                                                value='ema_200',
                                            ),
                                            dmc.Checkbox(
                                                label='RSI', value='rsi'
                                            ),
                                            dmc.Checkbox(
                                                label='macd', value='macd'
                                            ),
                                            dmc.Checkbox(
                                                label='Bandas de Bollinger',
                                                value='bbands',
                                            ),
                                            dmc.Checkbox(
                                                label='Estocástico',
                                                value='stoch',
                                            ),
                                            dmc.Checkbox(
                                                label='Volume Médio',
                                                value='volume',
                                            ),
                                            dmc.Checkbox(
                                                label='Sinais', value='sinais'
                                            ),
                                        ],
                                        mt=10,
                                    ),
                                    value=['sinais'],
                                ),
                            ],
                        )
                    ],
                ),
            ],
        ),
    ],
    withBorder=True,
    shadow='xl',
    radius='md',
    h=450,
)

comprar_vender = dmc.Stack(
    [
        card_compra,
        card_venda,
    ],
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
                dmc.GridCol(graficos, span=6),
                dmc.GridCol(historico_precos, span=6),
                dmc.GridCol(painel_alertas, span=3),
                dmc.GridCol(controle_tempo, span=3),
                # Ordens de Compra
                dmc.GridCol(balanco_conta, span=6),
                dmc.GridCol(code_card, span=6),
            ],
            justify='space-around',
            align='stretch',
            # grow=True,
            gutter='xs',
        ),
    ],
)

layout_pagina = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        dmc.NotificationProvider(position='top-right'),
        html.Div(id='conteudo_pagina'),
        dcc.Interval(
            id='interval-component-dash',
            interval=60 * 1000,  # em milissegundos
            n_intervals=0,
        ),
        dcc.Interval(
            id='interval-component',
            interval=30 * 1000,  # em milissegundos
            n_intervals=0,
        ),
    ],
)

nav_link_style = (
    {
        'root': {
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'padding': '8px 4px',
        },
        'label': {
            'fontSize': '12px',
            'marginTop': '4px',
            'textAlign': 'center',
        },
    },
)

Navbar = dmc.AppShellNavbar(
    children=[
        dmc.NavLink(
            label='Dashboard',
            leftSection=DashIconify(icon='mdi:home', height=16),
            href='/',
            active=True,
            styles=nav_link_style,
        ),
        dmc.NavLink(
            label='Histórico de Preços',
            leftSection=DashIconify(icon='mdi:chart-line', height=16),
            href='/historico-precos',
            styles=nav_link_style,
        ),
        dmc.NavLink(
            label='Comprar e Vender',
            leftSection=DashIconify(icon='mdi:cart', height=16),
            href='/comprar-vender',
            styles=nav_link_style,
        ),
        dmc.NavLink(
            label='Configurações',
            leftSection=DashIconify(icon='mdi:cog', height=16),
            href='/configuracoes',
            styles=nav_link_style,
        ),
    ],
    id='app-shell-navbar',
)


appshell = dmc.AppShell(
    [
        dmc.AppShellHeader(header, px=25, py=10),
        Navbar,
        dmc.AppShellMain(layout_pagina),
        dmc.AppShellAside(
            children=[
                dmc.ScrollArea(
                    h=1000,
                    w=300,
                    scrollbarSize=2,
                    offsetScrollbars=True,
                    children=[
                        comprar_vender,
                    ],
                )
            ],
            p='md',
        ),
    ],
    header={'height': 70},
    padding='xl',
    id='app-shell',
    navbar={
        'width': 150,
        'breakpoint': 'sm',
        'collapsed': {'mobile': True, 'desktop': True},
    },
    aside={
        'width': 325,
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
