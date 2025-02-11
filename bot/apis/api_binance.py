import time
from datetime import datetime
from decimal import Decimal

import pandas as pd
import requests

from bot.models.models import BinanceKlines, KlineData

try:
    from segredos import CAMINHO
except ImportError:
    import os
    import sys

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    sys.path.append(project_root)
    from segredos import CAMINHO


BASE_URLS = [
    'https://api.binance.com',
    'https://api-gcp.binance.com',
    'https://api1.binance.com',
    'https://api2.binance.com',
    'https://api3.binance.com',
    'https://api4.binance.com',
]

STATUS_CODE = 200

BTCBRL_FILE = CAMINHO + '/btc_brl_binance.csv'


def get_klines(
    symbol='BTCBRL',
    interval='1m',
    startTime=None,  # datetime.now().timestamp() - 10 * 24 * 60 * 60,
    endTime=None,  # datetime.now().timestamp(),
    limit=1000,
):
    # Pegando o timeZone atual
    # timeZone = str(datetime.datetime.now().astimezone().timetz())[15:-3]
    timeZone = '-3:00'
    url = f'{BASE_URLS[0]}/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
        'startTime': startTime,
        'endTime': endTime,
        'timeZone': timeZone,
    }

    response = requests.get(url, params=params)

    if response.status_code == STATUS_CODE:
        response = response.json()
        # Converter os dados brutos para objetos KlineData
        klines_data = []
        for kline in response:
            kline_dict = {
                'timestamp': datetime.fromtimestamp(
                    kline[0] / 1000
                ).astimezone(),
                'open': Decimal(str(kline[1])),
                'high': Decimal(str(kline[2])),
                'low': Decimal(str(kline[3])),
                'close': Decimal(str(kline[4])),
                'volume': Decimal(str(kline[5])),
                'kline_close_time': datetime.fromtimestamp(
                    kline[6] / 1000
                ).astimezone(),
                'quote_asset_volume': Decimal(str(kline[7])),
                'number_of_trades': int(kline[8]),
                'taker_buy_base_volume': Decimal(str(kline[9])),
                'taker_buy_quote_volume': Decimal(str(kline[10])),
            }
            klines_data.append(KlineData(**kline_dict))

        binance_klines = BinanceKlines(
            data=klines_data, symbol=symbol, interval=interval
        )

        # Converter para DataFrame
        df = pd.DataFrame([k.model_dump() for k in binance_klines.data])
        return df
    else:
        resposta = response.raise_for_status()
        return str(resposta)


def dataset_binance():
    # Set the starting timestamp (e.g., September 1, 2017)
    start_time = int(datetime(2017, 9, 1).timestamp() * 1000)

    # Get the current timestamp
    end_time = int(time.time() * 1000)

    # Initialize a list to store data frames
    data_frames = []

    # Maximum interval per request (200 days in milliseconds)
    max_interval = 200 * 24 * 60 * 60 * 1000

    # Loop over the time range
    current_time = start_time
    while current_time < end_time:
        next_time = min(current_time + max_interval, end_time)
        df = get_klines(
            symbol='BTCBRL',
            interval='2h',
            startTime=current_time,
            endTime=next_time,
            limit=1500,
        )
        df['timestamp'] = pd.to_datetime(df['Kline open time'])
        df = df.rename(
            columns={
                'Close price': 'close',
                'High price': 'high',
                'Low price': 'low',
            }
        )
        data_frames.append(df)
        current_time = next_time
        time.sleep(1)  # Respect API rate limits

    # Combine all data frames into one
    full_df = pd.concat(data_frames, ignore_index=True)

    # Save the data to a CSV file
    full_df.to_csv(BTCBRL_FILE, index=False)
