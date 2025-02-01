import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import pandas as pd
from rich import print
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

try:
    from crypto.segredos import CAMINHO, auth_token
except ImportError:
    from segredos import CAMINHO, auth_token
import re

publicTradingApi = 'https://api.bitpreco.com/v1/trading/balance'

COINPAIR_FILE = CAMINHO + '/coinpair.json'

console = Console()


# Definindo a função para carregar opções de criptomoedas
def carregar_opcoes_criptomoedas():
    return [
        {
            'value': 'AAVE-BRL',
            'label': 'AAVE para Real',
        },
        {
            'value': 'ABFY-BRL',
            'label': 'ABFY para Real',
        },
        {'value': 'ADA-BRL', 'label': 'ADA para Real'},
        {'value': 'AKT-BRL', 'label': 'AKT para Real'},
        {
            'value': 'ALGO-BRL',
            'label': 'ALGO para Real',
        },
        {'value': 'ZIL-BRL', 'label': 'ZIL para Real'},
        {'value': 'ZK-BRL', 'label': 'ZK para Real'},
        {'value': 'ZRO-BRL', 'label': 'ZRO para Real'},
        {
            'value': 'BTC-BRL',
            'label': 'Bitcoin para Real',
        },
    ]


def get_coinpair():
    try:
        with open(COINPAIR_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('coinpair', 'BTC-BRL')
    except FileNotFoundError:
        return 'BTC-BRL'


def fetch_bitpreco_history(
    symbol: str = 'BTC_BRL',
    resolution: str = '1',
    time_range: Dict[str, int] = {
        'from': int(datetime.now().timestamp()) - 1184400,
        'to': int(datetime.now().timestamp()),
    },
    countback: int = 0,
    currency_code: str = 'BRL',
) -> Optional[Dict[str, Any]]:
    """
    Busca dados históricos de preços da API da BitPreço.

    Parâmetros:
        symbol (str): Par de negociação, por exemplo, 'BTC_BRL'.
        resolution (str): Resolução do período, por exemplo, '1D'.
        from_timestamp (int): Timestamp de início
        (em segundos desde a época Unix).
        to_timestamp (int): Timestamp de término
        (em segundos desde a época Unix).
        countback (int): Número de registros anteriores.
        currency_code (str): Código da moeda, por exemplo, 'BRL'.

    Retorna:
        dict: Dados históricos de preços se a requisição for bem-sucedida.
        None: Se ocorrer um erro durante a requisição.
    """
    url = 'https://api.bitpreco.com/tradingview/history'

    headers = {
        'accept': '*/*',
        'accept-language': 'pt-BR,pt;q=0.8',
        'origin': 'https://market.bitypreco.com',
        'referer': 'https://market.bitypreco.com/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Brave";v="132"',  # noqa: E501
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',  # noqa: E501
    }

    params = {
        'symbol': symbol,
        'resolution': resolution,
        'from': time_range['from'],
        'to': time_range['to'],
        'countback': countback,
        'currencyCode': currency_code,
    }

    try:
        response = httpx.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Verificar se a resposta contém as chaves esperadas
        if not all(key in data for key in ['t', 'o', 'c', 'h', 'l', 'v', 's']):
            # Debugar a resposta
            # print(f'[yellow]Resposta da API:[/yellow] {data}')
            # print(
            #     '[red]Resposta da API não contém '
            #     + 'todas as chaves esperadas[/red]'
            # )
            return None

        # Criar o DataFrame com os dados organizados em colunas
        df = pd.DataFrame({
            'timestamp': data['t'],
            'open': data['o'],
            'close': data['c'],
            'high': data['h'],
            'low': data['l'],
            'volume': data['v'],
        })

        # Converter timestamp para datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['timestamp'] = (
            df['timestamp']
            .dt.tz_localize('UTC')
            .dt.tz_convert('America/Sao_Paulo')
        )

        return df

    except httpx.RequestError as exc:
        print(f'[red]Erro na requisição:[/red] {exc}')
    except httpx.HTTPStatusError as exc:
        try:
            html_content = exc.response.text
            print('[red]Erro HTTP:[/red]', exc.response.status_code)
            print('[yellow]Conteúdo da página:[/yellow]')
            # Remove HTML tags for cleaner display
            clean_text = re.sub('<[^<]+?>', '', html_content)
            clean_text = '\n'.join(
                line.strip()
                for line in clean_text.splitlines()
                if line.strip()
            )
            print(clean_text)
        except Exception as e:
            print(f'[red]Erro ao processar resposta:[/red] {e}')
    except ValueError:
        print('[red]Erro ao decodificar a resposta JSON.[/red]')
        console.print_exception()
    except Exception as exc:
        print(f'[red]Erro inesperado:[/red] {exc}')

    return None


# função que gera um dataset com os dados de histórico de preços da BitPreço
def dataset_bitpreco(
    symbol: str = 'BTC_BRL', resolution: str = '1'
) -> pd.DataFrame:
    # Set the starting timestamp (e.g., September 1, 2017)
    start_time = int(datetime(2017, 9, 1).timestamp())
    end_time = int(time.time())
    data_frames = []
    interval = 1184400

    # Calcular o número total de iterações
    total_iterations = (end_time - start_time) // interval + 1

    # Configurar a barra de progresso customizada
    progress = Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
        TimeRemainingColumn(),
    )

    with progress:
        # Adicionar a tarefa principal
        task = progress.add_task(
            f'[cyan]Coletando dados históricos ({symbol})',
            total=total_iterations,
        )

        current_time = start_time
        while current_time < end_time:
            try:
                next_time = min(current_time + interval, end_time)
                df = fetch_bitpreco_history(
                    symbol=symbol,
                    resolution=resolution,
                    time_range={'from': current_time, 'to': next_time},
                    countback=0,
                    currency_code='BRL',
                )
                if df is not None:
                    data_frames.append(df)
                current_time = next_time
                progress.advance(task)  # Avança a barra de progresso
                time.sleep(1)  # Respect API rate limits
            except Exception as e:
                progress.console.print(
                    f'[red]Error at timestamp {current_time}: {e}[/red]'
                )
                current_time += interval
                progress.advance(task)  # Avança mesmo em caso de erro
                continue

    # Combine all data frames into one
    if data_frames:
        full_df = pd.concat(data_frames, ignore_index=True)
        # Save the data to a timescaledb table
        return full_df
    else:
        print('No data was collected')


def Ticker(coinpar='all-brl'):
    # se tiverem letras maiusculas, coloca os pares em letras minusculas
    coinpar = coinpar.lower()
    url = f'https://api.bitpreco.com/{coinpar}/ticker'
    response = httpx.get(url)
    return response


def Orderbook():
    url = 'https://api.bitpreco.com/btc-brl/orderbook'
    response = httpx.get(url)
    return response


def Trades():
    url = 'https://api.bitpreco.com/btc-brl/trades'
    response = httpx.get(url)
    return response


def Balance():
    url = publicTradingApi
    payload = {'cmd': 'balance', 'auth_token': auth_token}
    response = httpx.post(url, data=payload)
    return response


def OpenOrders(market='BTC-BRL'):
    url = publicTradingApi
    payload = {
        'cmd': 'open_orders',
        'auth_token': auth_token,
        'market': market,
    }
    response = httpx.post(url, data=payload)
    return response


def ExecutedOrders(market='BTC-BRL'):
    url = publicTradingApi
    payload = {
        'cmd': 'executed_orders',
        'auth_token': auth_token,
        'market': market,
    }
    response = httpx.post(url, data=payload)
    return response


def Buy(price, volume, amount, limited, market='BTC-BRL'):
    url = publicTradingApi
    payload = {
        'cmd': 'buy',
        'auth_token': auth_token,
        'market': market,
        'price': price,
        'volume': volume,
        'amount': amount,
        'limited': limited,
    }
    response = httpx.post(url, data=payload)
    return response


def Sell(price, volume, amount, limited, market='BTC-BRL'):
    url = publicTradingApi
    payload = {
        'cmd': 'sell',
        'auth_token': auth_token,
        'market': market,
        'price': price,
        'volume': volume,
        'amount': amount,
        'limited': limited,
    }
    response = httpx.post(url, data=payload)
    return response


def OrderCancel(order_id):
    url = publicTradingApi
    payload = {
        'cmd': 'order_cancel',
        'auth_token': auth_token,
        'order_id': order_id,
    }
    response = httpx.post(url, data=payload)
    return response


def AllOrdersCancel():
    url = publicTradingApi
    payload = {'cmd': 'all_orders_cancel', 'auth_token': auth_token}
    response = httpx.post(url, data=payload)
    return response


def OrderStatus(order_id):
    url = publicTradingApi
    payload = {
        'cmd': 'order_status',
        'auth_token': auth_token,
        'order_id': order_id,
    }
    response = httpx.post(url, data=payload)
    return response


def GetQuote(type_mode='BUY', base_amount='0.01', market='BTC-BRL'):
    url = f'{publicTradingApi}/get_quote'
    payload = {
        'auth_token': auth_token,
        'type': type_mode,
        'market': market,
        'base_amount': base_amount,
    }
    response = httpx.post(url, data=payload)
    return response


def ExecuteQuote(quote_id):
    url = f'{publicTradingApi}/execute_quote'
    payload = {
        'auth_token': auth_token,
        'quote_id': quote_id,
    }
    response = httpx.post(url, data=payload)
    return response


def Withdrawal(amount, currency, priority, blockchain, address):
    url = publicTradingApi
    payload = {
        'cmd': 'withdrawal',
        'auth_token': auth_token,
        'amount': amount,
        'currency': currency,
        'priority': priority,
        'blockchain': blockchain,
        'address': address,
    }
    response = httpx.post(url, data=payload)
    return response
