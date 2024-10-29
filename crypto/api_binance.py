import pandas as pd
import requests

BASE_URLS = [
    'https://api.binance.com',
    'https://api-gcp.binance.com',
    'https://api1.binance.com',
    'https://api2.binance.com',
    'https://api3.binance.com',
    'https://api4.binance.com',
]

STATUS_CODE = 200


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
        df = pd.DataFrame(
            response,
            columns=[
                'Kline open time',
                'Open price',
                'High price',
                'Low price',
                'Close price',
                'Volume',
                'Kline Close time',
                'Quote asset volume',
                'Number of trades',
                'Taker buy base asset volume',
                'Taker buy quote asset volume',
                'Unused field, ignore',
            ],
        )
        df = df.drop(columns=['Unused field, ignore'])
        # transform timestamp Kline open time and Kline close time to datetime
        df['Kline open time'] = pd.to_datetime(
            df['Kline open time'],
            unit='ms',
        )
        df['Kline Close time'] = pd.to_datetime(
            df['Kline Close time'], unit='ms'
        )
        df['Kline open time'] = (
            df['Kline open time']
            .dt.tz_localize('UTC')
            .dt.tz_convert('America/Sao_Paulo')
        )
        df['Kline Close time'] = (
            df['Kline Close time']
            .dt.tz_localize('UTC')
            .dt.tz_convert('America/Sao_Paulo')
        )
        numeric_columns = [
            'Open price',
            'High price',
            'Low price',
            'Close price',
            'Volume',
            'Quote asset volume',
            'Taker buy base asset volume',
            'Taker buy quote asset volume',
        ]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)
        return df
    else:
        resposta = response.raise_for_status()
        return str(resposta)
