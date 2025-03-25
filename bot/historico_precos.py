import datetime as dt
import os
from datetime import datetime, timedelta

import pandas as pd

from bot.apis.api_binance import get_klines
from bot.apis.api_bitpreco import (
    dataset_bitpreco,
    fetch_bitpreco_history,
)
from bot.logs.config_log import console
from bot.models.coin_pair import CoinPair, ExchangeType
from bot.parametros import (
    BACKTEST_DAYS,
)
from db.duckdb_csv import load_csv_in_dataframe
from segredos import CAMINHO


def get_price_history(
    coin_pair: str | CoinPair,
    interval: str = '1',
    progress=None,
    task=None,
) -> pd.DataFrame:
    """
    Obtém o histórico de preços da exchange apropriada.

    Args:
        coin_pair: String do par de moedas ou instância de CoinPair
        interval: Intervalo dos candles (default='1')

    Returns:
        DataFrame com histórico de preços
    """
    try:
        # Converter string para CoinPair se necessário
        if isinstance(coin_pair, str):
            base, quote = coin_pair.split('-')
            coin_pair = CoinPair(
                base=base, quote=quote, exchange=ExchangeType.BITPRECO
            )

        end_date = datetime.now(dt.timezone.utc)
        start_date = end_date - timedelta(days=BACKTEST_DAYS)

        # Definir nome do arquivo baseado na exchange e par
        filename = (
            f'{coin_pair.bitpreco_websocket}_{coin_pair.exchange.value}.csv'
        )
        # console.print(f'Carregando dados de {filename}...')
        filepath = os.path.join(CAMINHO, filename)

        df = None
        # Carregar dados do arquivo se existir
        if os.path.exists(filepath):
            df = load_csv_in_dataframe(
                filepath,
                # start_date=start_date,
                # end_date=end_date,
            )

        # Se não tiver dados ou arquivo não existir
        if df is None or df.empty:
            df = fetch_new_data(coin_pair, interval, progress, task)
        else:
            # Atualizar dados mais recentes
            df = update_recent_data(df, coin_pair, interval)

        if df is not None and not df.empty:
            df = process_dataframe(df)
            return df

        console.print('[red]Não foi possível obter dados históricos[/red]')
        return pd.DataFrame()

    except Exception as e:
        console.print(f'Erro ao obter histórico de preços: {e}')
        console.print_exception()
        return pd.DataFrame()


def fetch_new_data(
    coin_pair: CoinPair,
    interval: str,
    progress=None,
    task=None,
) -> pd.DataFrame:
    """Busca dados completos da exchange apropriada"""
    if coin_pair.exchange == ExchangeType.BITPRECO:
        return dataset_bitpreco(
            coin_pair=coin_pair,
            resolution=interval,
            salvar_csv=True,
            existing_progress=progress,
            task_id=task,
        )
    elif coin_pair.exchange == ExchangeType.BINANCE:
        # Ajustar intervalo para formato Binance
        binance_interval = convert_interval_to_binance(interval)
        return get_klines(
            symbol=coin_pair.binance_format, interval=binance_interval
        )
    return pd.DataFrame()


def update_recent_data(
    df: pd.DataFrame, coin_pair: CoinPair, interval: str
) -> pd.DataFrame:
    """Atualiza dados recentes da exchange apropriada"""
    # Garantir que o DataFrame existente está com timezone UTC
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    elif df['timestamp'].dt.tz.tzname(None) != 'UTC':
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

    last_timestamp = df['timestamp'].max()
    from_timestamp = int(last_timestamp.timestamp())

    if coin_pair.exchange == ExchangeType.BITPRECO:
        recent_data = fetch_bitpreco_history(
            symbol=coin_pair.bitpreco_websocket,
            resolution=interval,
            time_range={
                'from': from_timestamp,
                'to': int(datetime.now().timestamp()),
            },
        )
    elif coin_pair.exchange == ExchangeType.BINANCE:
        binance_interval = convert_interval_to_binance(interval)
        recent_data = get_klines(
            symbol=coin_pair.binance_format,
            interval=binance_interval,
            startTime=from_timestamp * 1000,  # Binance usa milissegundos
        )
    else:
        return df

    if recent_data is not None and not recent_data.empty:
        # Garantir que os novos dados também estão com timezone UTC
        recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp'])
        if recent_data['timestamp'].dt.tz is None:
            recent_data['timestamp'] = recent_data['timestamp'].dt.tz_localize(
                'UTC'
            )
        elif recent_data['timestamp'].dt.tz.tzname(None) != 'UTC':
            recent_data['timestamp'] = recent_data['timestamp'].dt.tz_convert(
                'UTC'
            )

        # Concatenar e remover duplicatas
        df = pd.concat([df, recent_data], ignore_index=True)
        df = df.drop_duplicates(subset=['timestamp'], keep='last')
        df = df.sort_values('timestamp')

    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Processa o DataFrame para garantir formato consistente"""
    # Garantir que timestamp está no formato correto
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    elif df['timestamp'].dt.tz.tzname(None) != 'UTC':
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

    return df


def convert_interval_to_binance(interval: str) -> str:
    """Converte intervalo genérico para formato Binance"""
    # Mapeamento de intervalos
    interval_map = {
        '1': '1m',
        '5': '5m',
        '15': '15m',
        '30': '30m',
        '60': '1h',
        '240': '4h',
        'D': '1d',
        'W': '1w',
    }
    return interval_map.get(interval, '1m')
