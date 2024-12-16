import json
import time

import pandas as pd
from rich import print

try:
    from crypto.api_bitpreco import (
        Balance,
        ExecutedOrders,
        Ticker,
        get_coinpair,
    )
    from crypto.estrategias import execute_trade
except:  # noqa: E722
    from api_bitpreco import Balance, ExecutedOrders, Ticker, get_coinpair
    from estrategias import execute_trade

try:
    from crypto.segredos import CAMINHO
except ImportError:
    from segredos import CAMINHO

PRICE_FILE = CAMINHO + '/ticker.csv'
BALANCE_FILE = CAMINHO + '/balance.csv'
ORDERS_FILE = CAMINHO + '/executed_orders.csv'
INTERVAL_FILE = CAMINHO + '/interval.json'


def save_price_to_csv(ticker_json):
    df_precos = pd.read_csv(PRICE_FILE)
    if (
        ticker_json['last'] != df_precos['last'].iloc[-1]
        or ticker_json['timestamp'][:-3]
        != df_precos['timestamp'].iloc[-1][:-3]
    ):
        df_precos = df_precos._append(ticker_json, ignore_index=True)
        df_precos.to_csv(PRICE_FILE, index=False)


def save_balance_to_csv(balance_json):
    balance_df = pd.DataFrame([balance_json])
    balance_df.to_csv(BALANCE_FILE, index=False)


def save_orders_to_csv(orders_json):
    orders_df = pd.DataFrame(orders_json)
    orders_df.to_csv(ORDERS_FILE, index=False)


def get_interval():
    try:
        with open(INTERVAL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(
                'interval', 30
            )  # Valor padrão de 30 segundos se não houver arquivo

    except FileNotFoundError:
        return 30  # Valor padrão de 30 segundos se o arquivo não existir


def main():
    while True:
        try:
            coinpair = get_coinpair()
            ticker_json = Ticker(coinpair).json()
            save_price_to_csv(ticker_json)

            balance = Balance().json()
            save_balance_to_csv(balance)

            executed_orders = ExecutedOrders(coinpair).json()
            save_orders_to_csv(executed_orders)

            execute_trade(ticker_json, balance)

            # Tempo que pode ser controlado pelo dashboard
            # Atraves de um arquivo leve e rapido
            # Obtém o valor do delay do arquivo `interval.json`
            delay = get_interval()
            time.sleep(delay)

        except (Exception, KeyboardInterrupt):
            if KeyboardInterrupt:
                print(
                    ':rotating_light: [bold magenta]Saindo...[/bold magenta]'
                )
                break
            else:
                print('[bold magenta]ErroWorld[/bold magenta]')
                continue


if __name__ == '__main__':
    main()
