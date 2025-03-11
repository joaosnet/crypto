# Importando as bibliotecas necessárias
import json
import traceback

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from dash import (
    ALL,
    Input,
    Output,
    Patch,
    State,
    callback,
    dcc,
    html,
    no_update,
)
from dash import callback_context as ctx
from dash_iconify import DashIconify

from bot.apis.api_bitpreco import Buy, Sell
from compartilhado import (
    get_str_coinpairs,
    set_coinpairs,
)
from dashboard import app, dash_utils
from dashboard.componentes_personalizados import (
    bar_precos_atuais,
)
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
        novo_valor = get_str_coinpairs()

    # Atualiza o valor no arquivo de configuração
    if novo_valor is not None and len(novo_valor) > 0:
        set_coinpairs(novo_valor)

    # Retorna o mesmo valor para todos os campos
    return novo_valor, novo_valor, novo_valor


# Callback para atualizar os ícones das abas
@app.callback(
    Output('preco-icon', 'icon'),
    Input('df-precos', 'data'),
    Input('df-executed-orders', 'data'),
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

    return preco_icon


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


# Função utilitária para criar tabelas dmc padronizadas com paginação, ordenação e ocultação de colunas  # noqa: E501
def criar_tabela_dmc(  # noqa: PLR0913, PLR0917
    df,
    caption='Tabela de dados',
    table_id=None,
    striped=True,
    highlight_hover=True,
    with_border=True,
    with_column_borders=True,
    vertical_spacing='xs',
    horizontal_spacing='md',
    # Parâmetros de paginação
    with_pagination=True,
    rows_per_page=3,
    pagination_size='sm',
    # Parâmetros de ordenação
    sortable=True,
    # Parâmetros de ocultação de colunas
    hidden_columns=None,
):
    """
    Cria uma tabela dmc padronizada a partir de um DataFrame com opções de paginação,
    ordenação e ocultação de colunas.
    """  # noqa: E501
    # Gerar IDs únicos se não fornecidos
    if table_id is None:
        import uuid  # noqa: PLC0415

        table_id = f'table-{str(uuid.uuid4())[:8]}'

    # Ocultar colunas se especificado
    if hidden_columns:
        df = df.drop(
            columns=[col for col in hidden_columns if col in df.columns]
        )

    # Preparar os dados para dmc.Table
    head = df.columns.tolist()

    # Implementação da paginação
    if with_pagination:
        total_rows = len(df)
        total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)

        # IDs específicos para os componentes de paginação
        pagination_id = f'{table_id}-pagination'
        pagination_info_id = f'{table_id}-pagination-info'
        data_store_id = f'{table_id}-data-store'

        # Mostrar apenas a primeira página inicialmente
        body = df.iloc[:rows_per_page].values.tolist() if not df.empty else []

        # Store para os dados completos e estado da paginação
        store_component = dcc.Store(
            id=data_store_id,
            data={
                'data': df.to_dict('records'),
                'current_page': 1,
                'rows_per_page': rows_per_page,
                'total_rows': total_rows,
            },
        )

        # Componente de paginação
        pagination_component = dmc.Group(
            justify='space-between',
            align='center',
            mt='md',
            mb='md',
            children=[
                dmc.Text(
                    id=pagination_info_id,
                    size='sm',
                    children=f'Mostrando 1-{min(rows_per_page, total_rows)} de {total_rows}',  # noqa: E501
                ),
                dmc.Pagination(
                    id=pagination_id,
                    total=total_pages,
                    value=1,
                    size=pagination_size,
                    withEdges=True,
                    siblings=1,
                    boundaries=1,
                ),
            ],
        )

        # Registrar callback para essa tabela específica
        @app.callback(
            [Output(table_id, 'data'), Output(pagination_info_id, 'children')],
            [Input(pagination_id, 'value')],
            [State(data_store_id, 'data')],
        )
        def update_table_page(page, stored_data):
            if not page or not stored_data:
                return no_update, no_update

            df_records = stored_data['data']
            rows_per_page = stored_data['rows_per_page']
            total_rows = stored_data['total_rows']

            # Calcular índices para a página atual
            start_idx = (page - 1) * rows_per_page
            end_idx = min(start_idx + rows_per_page, total_rows)

            # Criar DataFrame temporário para selecionar a página
            df_temp = pd.DataFrame(df_records)

            # Dados para a página atual
            page_data = {
                'head': head,
                'body': df_temp.iloc[start_idx:end_idx].values.tolist()
                if not df_temp.empty
                else [],
                'caption': caption,
            }

            # Atualizar informações de paginação
            info_text = f'Mostrando {start_idx + 1}-{end_idx} de {total_rows}'

            return page_data, info_text

    else:
        body = df.values.tolist()
        pagination_component = None
        store_component = None

    # Adicionar ícones para ordenação das colunas se sortable=True
    if sortable:
        head_with_sort = []
        for col in head:
            head_with_sort.append(
                html.Div(
                    [
                        html.Span(col),
                        html.Span(
                            DashIconify(icon='mdi:sort', width=16),
                            style={'marginLeft': '5px', 'cursor': 'pointer'},
                            id={
                                'type': 'sort-icon',
                                'column': col,
                                'table': table_id,
                            },
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center'},
                )
            )
        head = head_with_sort

    # Criar a tabela com estilização aprimorada
    table = dmc.Table(
        data={
            'head': head,
            'body': body,
            'caption': caption,
        },
        striped=striped,
        highlightOnHover=highlight_hover,
        withTableBorder=with_border,
        withColumnBorders=with_column_borders,
        verticalSpacing=vertical_spacing,
        horizontalSpacing=horizontal_spacing,
        id=table_id,
    )

    # Montar componentes finais em um container responsivo
    components = []

    if store_component:
        components.append(store_component)

    # Container com scroll horizontal para tabelas grandes
    table_container = html.Div(
        table,
        style={
            'overflowX': 'auto',
            'width': '100%',
            'minWidth': '100%',
        },
    )

    components.append(table_container)

    if pagination_component:
        components.append(pagination_component)

    # Container final com largura responsiva
    return html.Div(
        components,
        style={
            'width': '100%',
            'maxWidth': '100%',
            'margin': '0 auto',
        },
    )


# Callback para adicionar o conteúdo da página dentro do tab Preços
# - Usando o dmc.Table
@app.callback(
    Output('historico-tabela-container', 'children'),
    Input('df-precos', 'data'),
    prevent_initial_call=True,
)
def tabela_historico(df1):
    try:
        df1 = pd.DataFrame(df1)
        # Deleted columns success
        if 'success' in df1.columns:
            df1.drop(['success'], axis=1, inplace=True)

        # Reordered columns
        desired_column_order = [
            'timestamp',
            'last',
            'var',
            'vol',
            'high',
            'low',
            'buy',
            'sell',
            'market',
        ]
        available_columns = [
            col for col in desired_column_order if col in df1.columns
        ]
        other_columns = [
            col for col in df1.columns if col not in desired_column_order
        ]
        final_column_order = available_columns + other_columns
        df1 = df1[final_column_order]

        df1 = df1.sort_values(
            by='timestamp', ascending=False, na_position='last'
        )

        # Usar a função utilitária para criar
        # a tabela com paginação e ordenação
        table = criar_tabela_dmc(
            df1,
            caption='Histórico de preços por mercado',
        )

        return [table]
    except Exception as e:
        return html.Div(
            children=[
                html.H5(children=f'Erro ao carregar tabela: {e}'),
                dcc.Markdown(
                    '{}'.format(traceback.format_exc()),
                    style={'font-size': '12pt'},
                ),
            ]
        )


# Callback para download de CSV
@app.callback(
    Output('download-csv', 'data'),
    Input('download-csv-button', 'n_clicks'),
    State('df-precos', 'data'),
    prevent_initial_call=True,
)
def download_csv(n_clicks, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_csv, 'historico_precos.csv', index=False)


# Tabela de ordens com dmc.Table
@app.callback(
    Output('balanco-conta', 'children'),
    Input('df-executed-orders', 'data'),
    Input('df-balance', 'data'),
    Input('df-precos', 'data'),
    prevent_initial_call=True,
)
def ordens_tab(executed_orders_df, balance_df, df_precos):
    try:
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

        # Usar a função utilitária para criar a tabela com paginação
        table = criar_tabela_dmc(
            executed_orders_df,
            caption='Histórico de ordens executadas',
        )
        return [
            dmc.CardSection(
                dmc.Group(
                    children=[
                        dmc.Text('Balanço da Conta', size='lg', fw=700),
                        dmc.ActionIcon(
                            DashIconify(
                                icon='carbon:overflow-menu-horizontal'
                            ),
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
                children=[
                    dcc.Graph(
                        figure=fig,
                        id={'type': 'graph', 'index': 'pie'},
                    ),
                ],
            ),
            dmc.CardSection(table,
                withBorder=True,
                inheritPadding=True,
                mt='sm',
                pb='md',),
        ]
    except Exception:
        return [
            dmc.CardSection(
                dmc.Group(
                    children=[
                        dmc.Text('Deu erro', size='lg', fw=700),
                    ],
                    justify='space-between',
                ),
                withBorder=True,
                inheritPadding=True,
                py='xs',
            ),
            dmc.CardSection(
                children=dmc.CodeHighlight(
                    code=traceback.format_exc(),
                    language='python',
                ),
                withBorder=True,
                inheritPadding=True,
                mt='sm',
                pb='md',
            ),
        ]


# Atualizndo o preco-compra com o valor do último preço
@app.callback(
    Output('preco-compra', 'value'),
    Input('df-precos', 'data'),
    State('market-compra', 'value'),
)
def atualizar_preco_compra_input(df_precos, selected_markets):
    df_precos = pd.DataFrame(df_precos)

    # Se o mercado selecionado for específico, use o preço dele
    if (
        selected_markets
        and len(selected_markets) > 0
        and 'market' in df_precos.columns
    ):
        # Filter for the first selected market
        primary_market = selected_markets[0]
        filtered_df = df_precos[
            df_precos['market'].str.upper() == primary_market
        ]
        if not filtered_df.empty:
            return filtered_df['last'].iloc[0]

    # Caso contrário, use o último preço disponível
    return df_precos['last'].iloc[-1]


# Atualizando o preco-venda com o valor do último preço
@app.callback(
    Output('preco-venda', 'value'),
    Input('df-precos', 'data'),
    State('market-venda', 'value'),
)
def atualizar_preco_venda_input(df_precos, selected_markets):
    df_precos = pd.DataFrame(df_precos)

    # Se o mercado selecionado for específico, use o preço dele
    if (
        selected_markets
        and len(selected_markets) > 0
        and 'market' in df_precos.columns
    ):
        # Filter for the first selected market
        primary_market = selected_markets[0]
        filtered_df = df_precos[
            df_precos['market'].str.upper() == primary_market
        ]
        if not filtered_df.empty:
            return filtered_df['last'].iloc[0]

    # Caso contrário, use o último preço disponível
    return df_precos['last'].iloc[-1]


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
def vender(n_clicks, preco_venda, total_reais, amount, tipo_ordem, mercados):  # noqa: PLR0913, PLR0917
    if n_clicks is not None and mercados and len(mercados) > 0:
        limited = tipo_ordem == 'limited'
        # Usa apenas o primeiro mercado selecionado para a venda
        mercado = mercados[0]
        resposta_venda = Sell(
            preco_venda, preco_venda, amount, limited, market=mercado
        )
        return f'\nVendeu\n{resposta_venda}'
    return 'Selecione pelo menos um mercado'


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
def comprar(n_clicks, preco_compra, total_reais, amount, tipo_ordem, mercados):  # noqa: PLR0913, PLR0917
    if n_clicks is not None and mercados and len(mercados) > 0:
        limited = tipo_ordem == 'limited'
        # Usa apenas o primeiro mercado selecionado para a compra
        mercado = mercados[0]
        resposta_compra = Buy(
            preco_compra, total_reais, amount, limited, market=mercado
        )
        return f'\nComprou\n{resposta_compra}'
    return 'Selecione pelo menos um mercado'


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


# Callback para ordenação de tabela
@app.callback(
    Output({'type': 'table', 'id': ALL}, 'data'),
    Input({'type': 'sort-icon', 'column': ALL, 'table': ALL}, 'n_clicks'),
    State({'type': 'table-data', 'id': ALL}, 'data'),
    prevent_initial_call=True,
)
def sort_table(n_clicks, stored_data):
    """
    Ordena a tabela quando um ícone de ordenação é clicado.
    """
    # Identificar qual coluna foi clicada para ordenação
    if not ctx.triggered:
        return no_update

    trigger = ctx.triggered[0]['prop_id']
    if not trigger:
        return no_update

    # Extrair coluna e tabela do ID
    trigger_dict = json.loads(trigger.split('.')[0])
    column = trigger_dict.get('column')
    table_id = trigger_dict.get('table')

    # Encontrar os dados da tabela correta
    for i, data in enumerate(stored_data):
        if data and data.get('table_id') == table_id:
            df = pd.DataFrame(data['df'])

            # Verificar direção atual de ordenação e alternar
            if data.get('sort_column') == column and data.get(
                'sort_ascending'
            ):
                df = df.sort_values(by=column, ascending=False)
                data['sort_ascending'] = False
            else:
                df = df.sort_values(by=column, ascending=True)
                data['sort_column'] = column
                data['sort_ascending'] = True

            # Atualizar dados
            data['df'] = df.to_dict('records')

            # Retornar dados atualizados
            return [data]

    return no_update


# Adaptar o callback de ordenação para trabalhar com a nova estrutura
@app.callback(
    Output({'type': 'sort-icon', 'column': ALL, 'table': ALL}, 'style'),
    Input({'type': 'sort-icon', 'column': ALL, 'table': ALL}, 'n_clicks'),
    State({'type': 'sort-icon', 'column': ALL, 'table': ALL}, 'id'),
    prevent_initial_call=True,
)
def update_sort_icons(n_clicks, ids):
    """
    Atualiza os ícones de ordenação quando clicados.
    """
    if not ctx.triggered:
        return no_update

    trigger = ctx.triggered[0]['prop_id']
    if not trigger or '.' not in trigger:
        return no_update

    # Identificar qual ícone foi clicado
    clicked_id = json.loads(trigger.split('.')[0])

    # Atualizar estilos para todos os ícones
    styles = []
    for icon_id in ids:
        if (
            icon_id['column'] == clicked_id['column']
            and icon_id['table'] == clicked_id['table']
        ):
            # Ícone clicado - destacar
            styles.append({
                'marginLeft': '5px',
                'cursor': 'pointer',
                'color': 'blue',
            })
        else:
            # Outros ícones - estilo normal
            styles.append({'marginLeft': '5px', 'cursor': 'pointer'})

    return styles
