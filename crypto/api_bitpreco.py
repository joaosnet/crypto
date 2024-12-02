import json

import httpx

try:
    from crypto.segredos import CAMINHO, auth_token
except ImportError:
    from segredos import CAMINHO, auth_token

publicTradingApi = 'https://api.bitpreco.com/v1/trading/balance'

COINPAIR_FILE = CAMINHO + '/coinpair.json'


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


def CoinTraderMonitor():
    response = httpx.get('https://cointradermonitor.com/api/pbb/v1/ticker')
    data = response.json()
    print(f'last: {data["last"]}, volume24h: {data["volume24h"]}')
    return data


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
