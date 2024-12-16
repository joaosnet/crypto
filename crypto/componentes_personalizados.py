import pandas as pd
import plotly.graph_objects as go
from dash import dash_table, dcc

from crypto import dash_utils


def create_table(df=None, id='table'):
    DATA_TABLE_STYLE = {
        'style_header': {
            'backgroundColor': '#1A1B25',
            'color': '#FFFFFF',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'border': '1px solid #2C2D3A',
            'fontFamily': 'Arial, sans-serif',
        },
        'style_cell': {
            'backgroundColor': '#282A3A',
            'color': '#FFFFFF',
            'border': '1px solid #2C2D3A',
            'textAlign': 'center',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'padding': '12px',
        },
        'style_data': {
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        'style_data_conditional': [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#2E3047',
            },
            {
                'if': {'filter_query': '{var} < 0', 'column_id': 'var'},
                'color': '#FF6B6B',
                'fontWeight': 'bold',
            },
            {
                'if': {'filter_query': '{var} >= 0', 'column_id': 'var'},
                'color': '#4ECB71',
                'fontWeight': 'bold',
            },
        ],
        'style_table': {
            'borderRadius': '10px',
            'overflow': 'hidden',
            'border': '1px solid #2C2D3A',
        },
    }

    return dash_table.DataTable(
        df.to_dict('records'),
        [{'name': i, 'id': i, 'hideable': True} for i in df.columns],
        id=id,
        sort_action='native',
        sort_by=[{'column_id': 'timestamp', 'direction': 'desc'}],
        hidden_columns=['success', 'vol', 'avg', 'buy', 'sell', 'high', 'low'],
        style_table=DATA_TABLE_STYLE['style_table'],
        style_header=DATA_TABLE_STYLE['style_header'],
        style_cell=DATA_TABLE_STYLE['style_cell'],
        style_data=DATA_TABLE_STYLE['style_data'],
        style_data_conditional=DATA_TABLE_STYLE['style_data_conditional'],
        page_size=10,
        css=[
            {
                'selector': '.dash-table-tooltip',
                'rule': 'background-color: #1A1B25; color: white; font-family: Arial, sans-serif;',  # noqa: E501
            },
        ],
    )


def graf_preco_atuais(  # noqa: PLR0915
    data_recency=None,
    df=None,
    executed_orders_df=None,
):
    try:
        df = pd.DataFrame(df)

        executed_orders_df = pd.DataFrame(executed_orders_df)

        # Obtenha a data e hora atuais
        data_recency = float(data_recency)
        if data_recency is None:
            data_recency = 3
        # Calcule o início do período de interesse (10 minutos atrás)

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
        return dcc.Graph(
            figure=fig,
            id={'type': 'graph', 'index': 'preco_atuais'},
        )
    except:  # noqa: E722
        return dcc.Graph(
            id={'type': 'graph', 'index': 'preco_atuais'},
        )
