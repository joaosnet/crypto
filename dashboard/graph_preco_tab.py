import datetime

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, no_update
from plotly.subplots import make_subplots
from rich.console import Console

from dashboard import app
from dashboard.custom_chart_editor import ChartEditor
from db.duckdb_csv import load_csv_in_dataframe
from segredos import CAMINHO

console = Console()


# Função para calcular indicadores básicos se não estiverem presentes
def add_missing_indicators(df):
    """Adiciona indicadores faltantes para garantir
    que o dataframe tenha colunas necessárias"""
    if df is None or df.empty:
        return df

    # Certificar que as colunas básicas existem
    if 'volume' not in df.columns:
        df['volume'] = 0

    # Verificar e adicionar volume_sma se faltando
    if 'volume_sma' not in df.columns and 'volume' in df.columns:
        try:
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
        except Exception:
            df['volume_sma'] = df['volume']

    # Verificar e adicionar posição se faltando
    if 'position' not in df.columns:
        df['position'] = 0

    return df


# Função para criar figuras compatíveis com ChartEditor
def create_price_figure(  # noqa: PLR0912, PLR0913, PLR0915, PLR0917
    df_bity,
    df=None,
    executed_orders_df=None,
    graf_info=None,
    indicadores=None,
    minutes_ago=None,
    now=None,
):
    try:  # noqa: PLR1702
        # Obtenha a data e hora atuais se não fornecidas
        if now is None:
            now = datetime.datetime.now()
            now = pd.to_datetime(now).tz_localize('America/Sao_Paulo')

        if minutes_ago is None:
            minutes_ago = now - datetime.timedelta(minutes=30)
            minutes_ago = pd.to_datetime(minutes_ago).tz_localize(
                'America/Sao_Paulo'
            )

        if graf_info is None:
            graf_info = ['bity_candlestick', 'ticker', 'orders']

        if indicadores is None:
            indicadores = ['sinais', 'ema_20', 'ema_200']

        if 'rsi' not in indicadores:
            fig1 = go.Figure()
        elif 'rsi' in indicadores and 'rsi' in df_bity.columns:
            fig1 = make_subplots(
                rows=2,
                cols=1,
                vertical_spacing=0.40,
                row_heights=[0.7, 0.3],
                subplot_titles=('BTC-BRL Price', 'RSI'),
            )
        else:
            # Fallback to regular figure if rsi is requested but not available
            fig1 = go.Figure()
            console.print(
                '[yellow]Warning: RSI indicator requested '
                + 'but not found in data[/yellow]'
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
            ),
            # Eixo para Volume
            yaxis2=dict(
                title='Volume',
                titlefont=dict(color='rgba(128, 128, 128, 0.5)'),
                tickfont=dict(color='rgba(128, 128, 128, 0.5)'),
                domain=[0, 0.2],
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
            margin=dict(t=100),
            xaxis_rangeslider_visible='rangeslider' in graf_info,
        )

        # Adicionar dados do DataFrame da Bity se disponível
        if df_bity is not None and not df_bity.empty:
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
            if 'ema_5' in indicadores and 'ema_5' in df_bity.columns:
                fig1.add_trace(
                    go.Scattergl(
                        x=df_bity['timestamp'],
                        y=df_bity['ema_5'],
                        mode='lines',
                        name='EMA 5',
                        line=dict(color='blue', width=1),
                    )
                )

            if 'ema_10' in indicadores and 'ema_10' in df_bity.columns:
                fig1.add_trace(
                    go.Scattergl(
                        x=df_bity['timestamp'],
                        y=df_bity['ema_10'],
                        mode='lines',
                        name='EMA 10',
                        line=dict(color='red', width=1),
                    )
                )

            if 'ema_20' in indicadores and 'ema_20' in df_bity.columns:
                fig1.add_trace(
                    go.Scattergl(
                        x=df_bity['timestamp'],
                        y=df_bity['ema_20'],
                        mode='lines',
                        name='EMA 20',
                        line=dict(color='green', width=1),
                    )
                )

            if 'ema_200' in indicadores and 'ema_200' in df_bity.columns:
                fig1.add_trace(
                    go.Scattergl(
                        x=df_bity['timestamp'],
                        y=df_bity['ema_200'],
                        mode='lines',
                        name='EMA 200',
                        line=dict(color='purple', width=1),
                    )
                )

            if 'rsi' in indicadores and 'rsi' in df_bity.columns:
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

            if 'macd' in indicadores and all(
                col in df_bity.columns
                for col in ['macd', 'macd_signal', 'macd_hist']
            ):
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

            if 'bbands' in indicadores and all(
                col in df_bity.columns
                for col in ['bb_upper', 'bb_middle', 'bb_lower']
            ):
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

            if 'stoch' in indicadores and all(
                col in df_bity.columns for col in ['stoch_k', 'stoch_d']
            ):
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
                # For volume, we'll use either volume_sma
                # if available or just volume
                volume_col = (
                    'volume_sma'
                    if 'volume_sma' in df_bity.columns
                    else 'volume'
                )

                # Add volume with red/green colors based on price direction
                colors = [
                    'red' if close < open else 'green'
                    for close, open in zip(df_bity['close'], df_bity['open'])
                ]

                fig1.add_trace(
                    go.Bar(
                        x=df_bity['timestamp'],
                        y=df_bity[volume_col],
                        name='Volume',
                        yaxis='y2',
                        marker_color=colors,
                    )
                )

            # adicionando os sinais de compra e venda ao gráfico
            if 'sinais' in indicadores and 'position' in df_bity.columns:
                # Adicionar sinais de compra
                buy_signals = df_bity[df_bity['position'] == 1]
                if not buy_signals.empty:
                    fig1.add_trace(
                        go.Scatter(
                            x=buy_signals['timestamp'],
                            y=buy_signals['close']
                            * 0.994,  # Desloca 0.6% para baixo
                            mode='markers',
                            name='Sinal de Compra',
                            marker=dict(
                                color='green',
                                size=12,
                                symbol='triangle-up',
                            ),
                        )
                    )

                # Adicionar sinais de venda
                sell_signals = df_bity[df_bity['position'] == -1]
                if not sell_signals.empty:
                    fig1.add_trace(
                        go.Scatter(
                            x=sell_signals['timestamp'],
                            y=sell_signals['close']
                            * 1.005,  # Desloca 0.5% para cima
                            mode='markers',
                            name='Sinal de Venda',
                            marker=dict(
                                color='red',
                                size=12,
                                symbol='triangle-down',
                            ),
                        )
                    )

        # Adicionar dados do ticker se disponíveis
        if df is not None and 'ticker' in graf_info:
            try:
                df_ticker = pd.DataFrame(df)

                # Verificar e corrigir problemas com a coluna timestamp
                if 'timestamp' in df_ticker.columns:
                    # Converter timestamp para datetime,
                    # manejando formatos mistos
                    df_ticker['timestamp'] = pd.to_datetime(
                        df_ticker['timestamp'], format='mixed', errors='coerce'
                    )

                    # Filtrar apenas registros válidos
                    # e dentro do intervalo de tempo
                    valid_timestamps = df_ticker['timestamp'].notna()
                    df_ticker = df_ticker[valid_timestamps]

                    # Aplicar timezone
                    try:
                        df_ticker['timestamp'] = df_ticker[
                            'timestamp'
                        ].dt.tz_localize('America/Sao_Paulo', ambiguous='NaT')
                    except:  # noqa: E722
                        # Se falhar, tentar converter para apenas data e hora
                        df_ticker['timestamp'] = pd.to_datetime(
                            df_ticker['timestamp'].dt.strftime(
                                '%Y-%m-%d %H:%M:%S'
                            )
                        )
                        df_ticker['timestamp'] = df_ticker[
                            'timestamp'
                        ].dt.tz_localize('America/Sao_Paulo', ambiguous='NaT')

                    # Filtrar por intervalo de tempo
                    # e verificar se há dados válidos
                    df_ticker = df_ticker[
                        (df_ticker['timestamp'] >= minutes_ago)
                        & (df_ticker['timestamp'] <= now)
                    ]

                    if not df_ticker.empty and 'last' in df_ticker.columns:
                        # Converter coluna 'last' para numérico
                        df_ticker['last'] = pd.to_numeric(
                            df_ticker['last'], errors='coerce'
                        )

                        # Filtrar apenas valores válidos
                        df_ticker = df_ticker[df_ticker['last'].notna()]

                        if not df_ticker.empty:
                            fig1.add_trace(
                                go.Scatter(
                                    x=df_ticker['timestamp'],
                                    y=df_ticker['last'],
                                    mode='lines',
                                    name='Último Preço',
                                    line=dict(color='blue', width=1.5),
                                )
                            )
            except Exception as e:
                console.print(
                    f'[red]Erro ao processar dados de ticker: {str(e)}[/red]'
                )

        # Adicionar ordens executadas se disponíveis
        if executed_orders_df is not None and 'orders' in graf_info:
            try:
                orders_df = pd.DataFrame(executed_orders_df)

                if 'time_stamp' in orders_df.columns:
                    # Converter timestamp para datetime,
                    # manejando formatos mistos
                    orders_df['time_stamp'] = pd.to_datetime(
                        orders_df['time_stamp'],
                        format='mixed',
                        errors='coerce',
                    )

                    # Filtrar apenas registros válidos
                    orders_df = orders_df[orders_df['time_stamp'].notna()]

                    # Aplicar timezone
                    try:
                        orders_df['time_stamp'] = orders_df[
                            'time_stamp'
                        ].dt.tz_localize('America/Sao_Paulo', ambiguous='NaT')
                    except Exception:
                        # Se falhar, tentar converter para apenas data e hora
                        orders_df['time_stamp'] = pd.to_datetime(
                            orders_df['time_stamp'].dt.strftime(
                                '%Y-%m-%d %H:%M:%S'
                            )
                        )
                        orders_df['time_stamp'] = orders_df[
                            'time_stamp'
                        ].dt.tz_localize('America/Sao_Paulo', ambiguous='NaT')

                    # Filtrar por intervalo de tempo
                    orders_df = orders_df[
                        (orders_df['time_stamp'] >= minutes_ago)
                        & (orders_df['time_stamp'] <= now)
                    ]

                    if not orders_df.empty:
                        # Adicionar ordens de compra
                        buy_orders = orders_df[orders_df['type'] == 'BUY']
                        if not buy_orders.empty:
                            fig1.add_trace(
                                go.Scatter(
                                    x=buy_orders['time_stamp'],
                                    y=buy_orders['price'],
                                    mode='markers',
                                    name='BUY Executed Orders',
                                    marker=dict(
                                        color='orange', size=10.5, symbol='x'
                                    ),
                                )
                            )

                        # Adicionar ordens de venda
                        sell_orders = orders_df[orders_df['type'] == 'SELL']
                        if not sell_orders.empty:
                            fig1.add_trace(
                                go.Scatter(
                                    x=sell_orders['time_stamp'],
                                    y=sell_orders['price'],
                                    mode='markers',
                                    name='SELL Executed Orders',
                                    marker=dict(
                                        color='green', size=10.5, symbol='x'
                                    ),
                                )
                            )
            except Exception as e:
                console.print(
                    f'[red]Erro ao processar ordens executadas: {str(e)}[/red]'
                )

        return fig1
    except Exception as e:
        console.print_exception(show_locals=True)
        resultado = f'Erro: {e}'
        return go.Figure(
            data=[go.Scatter(x=[0], y=[0], text=resultado, mode='text')],
            layout=go.Layout(title='Erro na criação do gráfico'),
        )


# Função para atualizar dados para o ChartEditor
def update_chart_data(
    start_date=None, end_date=None, graf_info=None, indicadores=None
):
    try:
        # Se nenhuma data for fornecida, use os últimos 30 minutos
        if start_date is None or end_date is None:
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(minutes=30)

        # Converter para timezone correta
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Usar valores padrão se os parâmetros estiverem vazios
        if graf_info is None:
            graf_info = ['bity_candlestick', 'ticker', 'orders']

        if indicadores is None:
            indicadores = ['sinais', 'ema_20', 'ema_200']

        # Carregar dados
        df_bity = load_csv_in_dataframe(
            CAMINHO + '/BTC_BRL_bitpreco.csv',
            start_date=start_date,
            end_date=end_date,
        )

        if df_bity.empty:
            return None, None

        # Adicionar indicadores faltantes
        df_bity = add_missing_indicators(df_bity)

        # Criar figuras com base nos indicadores e graf_info selecionados
        figure1 = create_price_figure(
            df_bity=df_bity,
            minutes_ago=start_date,
            now=end_date,
            graf_info=graf_info,
            indicadores=['ema_20', 'ema_200']
            + [i for i in indicadores if i in {'sinais'}],
        )

        # Segunda figura com foco em volume se estiver selecionado
        volume_indicadores = [
            i for i in indicadores if i in {'volume', 'sinais'}
        ]
        if 'volume' in indicadores:
            figure2 = create_price_figure(
                df_bity=df_bity,
                minutes_ago=start_date,
                now=end_date,
                graf_info=graf_info,
                indicadores=volume_indicadores,
            )
        else:
            # Se volume não estiver selecionado, mostrar emas
            figure2 = create_price_figure(
                df_bity=df_bity,
                minutes_ago=start_date,
                now=end_date,
                graf_info=graf_info,
                indicadores=['ema_5', 'ema_10', 'ema_20', 'ema_200']
                + [i for i in indicadores if i in {'sinais'}],
            )

        # Terceira figura com indicadores técnicos selecionados
        tech_indicadores = [
            i for i in indicadores if i in {'rsi', 'macd', 'bbands', 'stoch'}
        ]
        if tech_indicadores:
            figure3 = create_price_figure(
                df_bity=df_bity,
                minutes_ago=start_date,
                now=end_date,
                graf_info=graf_info,
                indicadores=tech_indicadores
                + [i for i in indicadores if i in {'sinais'}],
            )
        else:
            figure3 = create_price_figure(
                df_bity=df_bity,
                minutes_ago=start_date,
                now=end_date,
                graf_info=graf_info,
                indicadores=['sinais'],
            )

        # Retorna o dataframe e as figuras para atualização do ChartEditor
        return df_bity, [figure1, figure2, figure3]

    except Exception:
        console.print_exception(show_locals=True)
        return None, None


# Inicializar o ChartEditor com configurações para atualização automática
editor = ChartEditor(
    app,
    instance_id='principal',  # ID de instância único para primeira página
    card_size=1500,
    initial_cards=3,  # Iniciar com três gráficos padrão
    update_interval_id='interval-component-dash',
    data_update_function=update_chart_data,
    default_title='Criptomoeda Chart',
    figure_titles=[
        'Preço BTC-BRL com EMAs',
        'Volume BTC-BRL',
        'Indicadores Técnicos',
    ],
)

# Inicializar o ChartEditor globalmente
chart_editor = editor.get_layout()


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
def preco_tab(  # noqa: PLR0913, PLR0917
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
    data_recency = float(data_recency if data_recency is not None else 30)

    # Calcule o início do período de interesse
    minutes_ago = now - datetime.timedelta(minutes=data_recency)
    minutes_ago = pd.to_datetime(minutes_ago).tz_localize('America/Sao_Paulo')
    now = pd.to_datetime(now).tz_localize('America/Sao_Paulo')

    # Atualizar os parâmetros do data_update_function do ChartEditor
    editor.update_data_params = {'start_date': minutes_ago, 'end_date': now}

    try:
        # Carregar dados da BitPreço
        df_bity = load_csv_in_dataframe(
            CAMINHO + '/BTC_BRL_bitpreco.csv',
            start_date=minutes_ago,
            end_date=now,
        )

        # Adicionar indicadores faltantes
        df_bity = add_missing_indicators(df_bity)

        # Criar figura usando a função helper
        return create_price_figure(
            df_bity=df_bity,
            df=df,
            executed_orders_df=executed_orders_df,
            graf_info=graf_info,
            indicadores=indicadores,
            minutes_ago=minutes_ago,
            now=now,
        )

    except Exception as e:
        console.print_exception(show_locals=True)
        resultado = f'Erro: {e}'
        return go.Figure(
            data=[go.Scatter(x=[0], y=[0], text=resultado, mode='text')],
            layout=go.Layout(title='Erro na atualização do gráfico'),
        )


@app.callback(
    Output(
        'principal-pattern-match-container', 'children', allow_duplicate=True
    ),
    Input('graf-info', 'value'),
    Input('indicadores-tecnicos', 'value'),
    Input('data-recency', 'value'),
    prevent_initial_call=True,
)
def update_chart_editor_with_selections(graf_info, indicadores, data_recency):
    """
    Atualiza os gráficos do ChartEditor com base nas seleções do usuário.
    """
    # Obter data atual e calcular início do período
    now = datetime.datetime.now()
    data_recency = float(data_recency if data_recency is not None else 30)
    minutes_ago = now - datetime.timedelta(minutes=data_recency)

    # Atualizar parâmetros para a função de atualização
    editor.update_data_params = {
        'start_date': minutes_ago,
        'end_date': now,
        'graf_info': graf_info,
        'indicadores': indicadores,
    }

    return no_update
