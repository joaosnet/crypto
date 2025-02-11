import os
import re

# Adicionando o caminho do diretório pai ao sys.path
import sys
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

import httpx
import pandas as pd
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

try:
    from bot.models.models import BitPrecoHistory, PriceData
    from segredos import CAMINHO, auth_token

    from ..logs.config_log import console
    from ..models.coin_pair import CoinPair
except ImportError:
    # Adiciona o diretório raiz do projeto ao PYTHONPATH
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.append(project_root)
    # Fallback para importação local
    from bot.logs.config_log import console
    from bot.models.coin_pair import CoinPair
    from bot.models.models import BitPrecoHistory, PriceData
    from segredos import CAMINHO, auth_token  # type: ignore


publicTradingApi = 'https://api.bitpreco.com/v1/trading/balance'


def fetch_bitpreco_history(
    symbol: str = 'BTC_BRL',
    resolution: str = '1',
    time_range: Dict[str, int] = {
        'from': int(datetime.now().timestamp()) - 1184400,
        'to': int(datetime.now().timestamp()),
    },
    countback: int = 0,
    currency_code: str = 'BRL',
) -> Optional[pd.DataFrame]:
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

        price_data = []
        for t, o, c, h, l, v in zip(  # noqa: E741
            data['t'], data['o'], data['c'], data['h'], data['l'], data['v']
        ):
            price_dict = {
                'timestamp': datetime.fromtimestamp(t).astimezone(),
                'open': Decimal(str(o)),
                'close': Decimal(str(c)),
                'high': Decimal(str(h)),
                'low': Decimal(str(l)),
                'volume': Decimal(str(v)),
            }
            price_data.append(PriceData(**price_dict))

        bitpreco_history = BitPrecoHistory(
            data=price_data, symbol=symbol, resolution=resolution
        )

        # Converter para DataFrame
        df = pd.DataFrame([p.model_dump() for p in bitpreco_history.data])
        return df

    except httpx.RequestError as exc:
        console.print(f'[red]Erro na requisição:[/red] {exc}')
    except httpx.HTTPStatusError as exc:
        try:
            html_content = exc.response.text
            console.print('[red]Erro HTTP:[/red]', exc.response.status_code)
            console.print('[yellow]Conteúdo da página:[/yellow]')
            # Remove HTML tags for cleaner display
            clean_text = re.sub('<[^<]+?>', '', html_content)
            clean_text = '\n'.join(
                line.strip()
                for line in clean_text.splitlines()
                if line.strip()
            )
            console.print(clean_text)
        except Exception as e:
            console.print(f'[red]Erro ao processar resposta:[/red] {e}')
    except ValueError:
        console.print('[red]Erro ao decodificar a resposta JSON.[/red]')
        console.print_exception()
    except Exception as exc:
        console.print(f'[red]Erro inesperado:[/red] {exc}')

    return None


# função que gera um dataset com os dados de histórico de preços da BitPreço
def dataset_bitpreco(
    coin_pair: CoinPair, resolution: str = '1', salvar_csv: bool = False
) -> pd.DataFrame:
    # Set the starting timestamp (e.g., September 1, 2017)
    start_time = int(datetime(2017, 9, 1).timestamp())
    end_time = int(time.time())
    data_frames = []
    interval = 1184400

    # Usar o formato apropriado para a BitPreco
    symbol = coin_pair.bitpreco_websocket

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
        if salvar_csv:
            # transformando o timestamp para formato utc
            full_df['timestamp'] = full_df['timestamp'].dt.tz_convert('UTC')
            full_df.to_csv(f'{CAMINHO}/{symbol}_bitpreco.csv', index=False)
            return full_df
        else:
            return full_df
    else:
        console.print('No data was collected')


def Ticker(coin_pair=None):
    # se não especificado, usa 'all-brl'
    if isinstance(coin_pair, CoinPair):
        pair_str = coin_pair.get_format().lower()
    elif isinstance(coin_pair, str):
        pair_str = coin_pair.lower()
    else:
        pair_str = 'all-brl'

    url = f'https://api.bitpreco.com/{pair_str}/ticker'
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


if __name__ == '__main__':
    dataset_bitpreco(
        salvar_csv=True, coin_pair=CoinPair(base='BTC', quote='BRL')
    )
    # print(Ticker().json())
