# Importando as bibliotecas necessárias
import datetime

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from dash_iconify import DashIconify
from plotly import express as px
from plotly.subplots import make_subplots
from rich.console import Console

from bot.apis.api_binance import get_klines
from dashboard import app
from dashboard.custom_chart_editor import ChartEditor
from db.duckdb_csv import load_csv_in_dataframe
from segredos import CAMINHO

console = Console()

# Definindo a coluna esquerda
div_graph_preco = html.Div(
    id='left-column',
    # className="eight columns",
    children=[
        # store para armazenar o estado do df de preços quando for atualizado
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
        ),
        dcc.Interval(
            id='interval-component-dash',
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
                            'editor',
                            value='editor',
                            leftSection=DashIconify(
                                id='editor-icon', icon='mdi:chart-line'
                            ),
                            rightSection=DashIconify(
                                id='editor-icon', icon='mdi:chart-line'
                            ),
                        ),
                    ],
                ),
                # tabs panel below
                dmc.TabsPanel(
                    dmc.Stack(
                        gap=0,
                        children=[
                            dcc.Graph(
                                id='grafico-preco',
                                config={'displayModeBar': False},
                            ),
                        ],
                    ),
                    value='Preços',
                    id='tab-precos',
                ),
                dmc.TabsPanel(
                    dmc.ScrollArea(
                        h=250,
                        w=250,
                        id='tab-editor',
                        children=[
                            dmc.Stack(
                                gap=0,
                                children=[
                                    dmc.Skeleton(h=50, mb='xl'),
                                    dmc.Skeleton(h=8, radius='xl'),
                                    dmc.Skeleton(h=8, my=6),
                                    dmc.Skeleton(h=8, w='70%', radius='xl'),
                                ],
                            ),
                        ],
                    ),
                    value='editor',
                    # id='tab-editor',
                ),
            ],
        ),
    ],
)


# Callback para adicionar o conteúdo da página dentro do tab Preços
@app.callback(
    Output('grafico-preco', 'figure'),
    Input('interval-component-dash', 'n_intervals'),
    Input('data-recency', 'value'),
    Input('data-recency-candlestick', 'value'),
    State('df-precos', 'data'),
    State('df-executed-orders', 'data'),
    Input('graf-info', 'value'),
    Input('indicadores-tecnicos', 'value'),
    Input('tabs', 'value'),
    prevent_initial_call=True,
)
def preco_tab(  # noqa: PLR0912, PLR0913, PLR0915, PLR0917
    n_intervals,
    data_recency,
    data_recency_candlestick,
    df,
    executed_orders_df,
    graf_info,
    indicadores,
    value,
):
    # Obtenha a data e hora atuais
    now = datetime.datetime.now()
    data_recency = float(data_recency)
    if data_recency is None:
        data_recency = 3
    # Calcule o início do período de interesse (10 minutos atrás)
    minutes_ago = now - datetime.timedelta(minutes=data_recency)
    minutes_ago = pd.to_datetime(minutes_ago).tz_localize('America/Sao_Paulo')
    now = pd.to_datetime(now).tz_localize('America/Sao_Paulo')
    try:
        if 'rsi' not in indicadores:
            fig1 = go.Figure()
        elif 'rsi' in indicadores:
            fig1 = make_subplots(
                rows=2,
                cols=1,
                # shared_xaxes=True,  # Compartilhar eixo x
                vertical_spacing=0.40,  # Aumentar espaçamento
                row_heights=[0.7, 0.3],
                subplot_titles=('BTC-BRL Price', 'RSI'),  # Adicionar títulos
            )

        fig1.update_layout(
            title='BTC-BRL Prices Over Time',
            xaxis=dict(
                title='Timestamp',
                rangeslider=dict(visible=True),
                range=[
                    minutes_ago.strftime('%Y-%m-%d %H:%M:%S'),
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                ],
            ),
            # Eixo principal para preço
            yaxis=dict(
                title='Price (BRL)',
                titlefont=dict(color='blue'),
                tickfont=dict(color='blue'),
                side='left',
                # autorange=True,
            ),
            # Eixo para Volume
            yaxis2=dict(
                title='Volume',
                titlefont=dict(
                    color='rgba(128, 128, 128, 0.5)'
                ),  # gray with 50% opacity
                tickfont=dict(
                    color='rgba(128, 128, 128, 0.5)'
                ),  # gray with 50% opacity
                domain=[0, 0.2],  # Make volume chart 20% of height on bottom
                anchor='x',
            ),
            # Eixo para macd
            yaxis3=dict(
                title='macd',
                titlefont=dict(color='orange'),
                tickfont=dict(color='orange'),
                anchor='free',
                overlaying='y',
                side='right',
                position=0.95,
                autorange=True,
            ),
            # Eixo para ATR
            yaxis4=dict(
                title='ATR',
                titlefont=dict(color='brown'),
                tickfont=dict(color='brown'),
                anchor='free',
                overlaying='y',
                side='right',
                position=0.90,
                autorange=True,
            ),
            # Layout geral
            showlegend=True,
            legend=dict(
                orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1
            ),
            margin=dict(t=100),  # Margem superior para acomodar a legenda
            xaxis_rangeslider_visible='rangeslider' in graf_info,
        )

        if 'candlestick' in graf_info:
            # convertendo o tempo de recência para
            # o formato de intervalo suportado
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

            df2 = get_klines(
                interval=intervalo,
                startTime=minutes_ago,
                endTime=now,
            )

            fig1.add_trace(
                go.Candlestick(
                    x=df2['timestamp'],
                    open=df2['open'],
                    high=df2['high'],
                    low=df2['low'],
                    close=df2['close'],
                    name='Api Binance',
                )
            )
        indicadores_tecnicos = [
            'ema_5',
            'ema_10',
            'ema_20',
            'ema_200',
            'rsi',
            'macd',
            'bbands',
            'stoch',
            'sinais',
            'volume',
        ]
        if 'bity_candlestick' in graf_info or any(
            indicador in indicadores for indicador in indicadores_tecnicos
        ):
            df_bity = load_csv_in_dataframe(
                CAMINHO + '/BTC_BRL_bitpreco.csv',
                start_date=minutes_ago,
                end_date=now,
            )
            if df_bity.empty is False:
                df_bity['timestamp'] = pd.to_datetime(
                    df_bity['timestamp']
                ).dt.tz_convert('America/Sao_Paulo')
                # df_bity = df_bity[
                #     (df_bity['timestamp'] >= minutes_ago)
                #     & (df_bity['timestamp'] <= now)
                # ]
                if 'bity_candlestick' in graf_info:
                    fig1.add_trace(
                        go.Candlestick(
                            x=df_bity['timestamp'],
                            open=df_bity['open'],
                            high=df_bity['high'],
                            low=df_bity['low'],
                            close=df_bity['close'],
                            name='Bity dataframe',
                        )
                    )
                # Add EMAs based on checkbox selection
                if 'ema_5' in indicadores:
                    fig1.add_trace(
                        go.Scattergl(
                            x=df_bity['timestamp'],
                            y=df_bity['ema_5'],
                            mode='lines',
                            name='EMA 5',
                            line=dict(color='blue', width=1),
                        )
                    )

                if 'ema_10' in indicadores:
                    fig1.add_trace(
                        go.Scattergl(
                            x=df_bity['timestamp'],
                            y=df_bity['ema_10'],
                            mode='lines',
                            name='EMA 10',
                            line=dict(color='red', width=1),
                        )
                    )

                if 'ema_20' in indicadores:
                    fig1.add_trace(
                        go.Scattergl(
                            x=df_bity['timestamp'],
                            y=df_bity['ema_20'],
                            mode='lines',
                            name='EMA 20',
                            line=dict(color='green', width=1),
                        )
                    )

                if 'ema_200' in indicadores:
                    fig1.add_trace(
                        go.Scattergl(
                            x=df_bity['timestamp'],
                            y=df_bity['ema_200'],
                            mode='lines',
                            name='EMA 200',
                            line=dict(color='purple', width=1),
                        )
                    )

                if 'rsi' in indicadores:
                    # Add RSI
                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['rsi'],
                            mode='lines',
                            name='RSI',
                            line=dict(color='purple', width=1),
                        ),
                        row=2,
                        col=1,
                    )

                    # Add overbought/oversold lines
                    fig1.add_hline(
                        y=70, line_color='red', line_dash='dash', row=2, col=1
                    )
                    fig1.add_hline(
                        y=30,
                        line_color='green',
                        line_dash='dash',
                        row=2,
                        col=1,
                    )
                    fig1.add_hline(
                        y=50, line_color='gray', line_dash='dash', row=2, col=1
                    )

                    # Configure RSI subplot layout
                    fig1.update_yaxes(
                        title_text='RSI',
                        range=[0, 100],
                        row=2,
                        col=1,
                        tickmode='linear',
                        tick0=0,
                        dtick=20,
                        gridcolor='gray',
                        gridwidth=0.5,
                    )

                if 'macd' in indicadores:
                    # Add macd line
                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['macd'],
                            mode='lines',
                            name='macd',
                            yaxis='y3',
                            line=dict(color='orange', width=1),
                        )
                    )

                    # Add signal line
                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['macd_signal'],
                            mode='lines',
                            name='Signal',
                            yaxis='y3',
                            line=dict(color='cyan', width=1),
                        )
                    )

                    # Add macd histogram with conditional colors
                    colors = [
                        'red' if hist < 0 else 'green'
                        for hist in df_bity['macd_hist']
                    ]
                    fig1.add_trace(
                        go.Bar(
                            x=df_bity['timestamp'],
                            y=df_bity['macd_hist'],
                            name='macd Histogram',
                            yaxis='y3',
                            marker_color=colors,
                        )
                    )

                if 'bbands' in indicadores:
                    # Add Bollinger Bands
                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['bb_upper'],
                            mode='lines',
                            name='Upper BB',
                            line=dict(color='gray', width=1),
                        )
                    )

                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['bb_middle'],
                            mode='lines',
                            name='Middle BB',
                            line=dict(color='gray', width=1),
                        )
                    )

                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['bb_lower'],
                            mode='lines',
                            name='Lower BB',
                            line=dict(color='gray', width=1),
                        )
                    )

                if 'stoch' in indicadores:
                    # Add Stochastic
                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['stoch_k'],
                            mode='lines',
                            name='Stoch %K',
                            line=dict(color='blue', width=1),
                        )
                    )

                    fig1.add_trace(
                        go.Scatter(
                            x=df_bity['timestamp'],
                            y=df_bity['stoch_d'],
                            mode='lines',
                            name='Stoch %D',
                            line=dict(color='orange', width=1),
                        )
                    )

                if 'volume' in indicadores:
                    # Add volume SMA
                    # Add volume with red/green colors based on price direction
                    colors = [
                        'red' if close < open else 'green'
                        for close, open in zip(
                            df_bity['close'], df_bity['open']
                        )
                    ]

                    fig1.add_trace(
                        go.Bar(
                            x=df_bity['timestamp'],
                            y=df_bity['volume_sma'],
                            name='Volume SMA',
                            yaxis='y2',
                            marker_color=colors,
                        )
                    )

            # adicionando os sinais de compra(1)df[signal]
            # e venda(-1) df[signal] ao gráfico
            if 'sinais' in indicadores:
                fig1.add_trace(
                    go.Scatter(
                        x=df_bity[df_bity['position'] == 1]['timestamp'],
                        y=df_bity[df_bity['position'] == 1]['close']
                        * 0.994,  # Desloca 0.1% para baixo
                        mode='markers',
                        name='Sinal de Compra',
                        marker=dict(
                            color='green',
                            size=12,  # Aumentei um pouco o tamanho
                            symbol='triangle-up',
                        ),
                    )
                )
                fig1.add_trace(
                    go.Scatter(
                        x=df_bity[df_bity['position'] == -1]['timestamp'],
                        y=df_bity[df_bity['position'] == -1]['close']
                        * 1.005,  # Desloca 0.1% para cima
                        mode='markers',
                        name='Sinal de Venda',
                        marker=dict(
                            color='red',
                            size=12,  # Aumentei um pouco o tamanho
                            symbol='triangle-down',
                        ),
                    )
                )

        if 'ticker' in graf_info:
            df = pd.DataFrame(df)
            # Excluir linhas fora do intervalo de interesse
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(
                'America/Sao_Paulo'
            )
            df = df[
                (df['timestamp'] >= minutes_ago) & (df['timestamp'] <= now)
            ]
            fig1.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['last'],
                    mode='lines',
                    name='Último Preço',
                    line=dict(color='blue', width=1.5),
                )
            )

        if 'orders' in graf_info:
            executed_orders_df = pd.DataFrame(executed_orders_df)
            # adicionando marcadores com as ordens de compra e venda
            executed_orders_df['time_stamp'] = pd.to_datetime(
                executed_orders_df['time_stamp']
            ).dt.tz_localize('America/Sao_Paulo')
            executed_orders_df = executed_orders_df[
                (executed_orders_df['time_stamp'] >= minutes_ago)
                & (executed_orders_df['time_stamp'] <= now)
            ]
            if not executed_orders_df.empty:
                fig1.add_trace(
                    go.Scatter(
                        x=executed_orders_df[
                            executed_orders_df['type'] == 'BUY'
                        ]['time_stamp'],
                        y=executed_orders_df[
                            executed_orders_df['type'] == 'BUY'
                        ]['price'],
                        mode='markers',
                        name='BUY Executed Orders',
                        marker=dict(color='orange', size=10.5, symbol='x'),
                    )
                )
                fig1.add_trace(
                    go.Scatter(
                        x=executed_orders_df[
                            executed_orders_df['type'] == 'SELL'
                        ]['time_stamp'],
                        y=executed_orders_df[
                            executed_orders_df['type'] == 'SELL'
                        ]['price'],
                        mode='markers',
                        name='SELL Executed Orders',
                        marker=dict(color='green', size=10.5, symbol='x'),
                    )
                )

        return fig1
    except Exception as e:
        # retornando uma figura com o erro
        console.print_exception(show_locals=True)
        resultado = f'Erro: {e}'
        return go.Figure(
            data=[go.Scatter(x=[0], y=[0], text=resultado, mode='text')],
            layout=go.Layout(title='Erro na atualização do gráfico'),
        )


# Callback para adicionar o editor de gráficos ao tab Preços
@app.callback(
    Output('tab-editor', 'children'),
    Input('tabs', 'value'),
    State('data-recency', 'value'),
    prevent_initial_call=True,
)
def editor_grafico(value, data_recency):
    if value == 'editor':
        try:
            # Configurar período de tempo
            now = datetime.datetime.now()
            data_recency = float(data_recency or 3)
            minutes_ago = now - datetime.timedelta(minutes=data_recency)

            # Converter para timezone correta
            minutes_ago = pd.to_datetime(minutes_ago)
            now = pd.to_datetime(now)

            # Carregar dados
            df_bity = load_csv_in_dataframe(
                CAMINHO + '/BTC_BRL_bitpreco.csv',
                start_date=minutes_ago,
                end_date=now,
            )

            if df_bity.empty:
                return dmc.Alert(
                    'Não há dados disponíveis para o período selecionado',
                    color='red',
                )

            # Criar figura padrão
            df = px.data.iris()
            default_fig = px.scatter(
                df, x='sepal_length', y='sepal_width', color='species'
            )

            # Inicializar editor
            editor = ChartEditor(
                app=app,
                data_source=df_bity.to_dict('list'),
                default_figure=default_fig,
                figure_title='BTC-BRL Chart',
                container_id='chart-editor-container',
                modal_size='85%',
                card_size=600,  # Aumentar tamanho do card
            )

            return editor.get_layout()

        except Exception as e:
            console.print_exception(show_locals=True)
            return dmc.Alert(
                f'Erro ao carregar o editor: {str(e)}',
                color='red',
            )

    return dmc.Skeleton(
        height=400,
        width='100%',
    )
