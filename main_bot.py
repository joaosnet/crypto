import time

import pandas as pd
from rich.progress import Progress

from bot.apis.api_bitpreco import Balance, ExecutedOrders, Ticker
from bot.estrategias.daytrade import execute_trade as estrategia_daytrade
from bot.logs.config_log import console
from compartilhado import get_coinpair, get_interval
from segredos import CAMINHO

PRICE_FILE = CAMINHO + '/ticker.csv'
BALANCE_FILE = CAMINHO + '/balance.csv'
ORDERS_FILE = CAMINHO + '/executed_orders.csv'


def save_price_to_csv(ticker_json):
    try:
        df_precos = pd.read_csv(PRICE_FILE)
        if (
            ticker_json['last'] != df_precos['last'].iloc[-1]
            or ticker_json['timestamp'][:-3]
            != df_precos['timestamp'].iloc[-1][:-3]
        ):
            df_precos = df_precos._append(ticker_json, ignore_index=True)
            df_precos.to_csv(PRICE_FILE, index=False)
    except Exception as e:
        if 'No columns to parse from file' in str(e):
            df_precos = pd.DataFrame([ticker_json])

    df_precos.to_csv(PRICE_FILE, index=False)


def save_balance_to_csv(balance_json):
    balance_df = pd.DataFrame([balance_json])
    balance_df.to_csv(BALANCE_FILE, index=False)


def save_orders_to_csv(orders_json):
    orders_df = pd.DataFrame(orders_json)
    orders_df.to_csv(ORDERS_FILE, index=False)


def main():
    retry_delay = 5
    max_retries = 3
    with Progress(console=console, transient=True) as progress:  # noqa: PLR1702
        task = progress.add_task(
            'Executando bot...',
            total=100,
        )
        while True:
            try:
                for attempt in range(max_retries):
                    try:
                        coinpair = get_coinpair()
                        ticker_json = Ticker(coinpair).json()
                        # console.print(
                        #     f'[bold cyan]Ticker: {ticker_json}[/bold cyan]'
                        # )
                        save_price_to_csv(ticker_json)
                        progress.update(
                            task,
                            advance=10,
                            description='Ticker json atualizado',
                        )

                        balance = Balance().json()
                        save_balance_to_csv(balance)
                        progress.update(
                            task,
                            advance=10,
                            description='Saldo atualizado',
                        )

                        executed_orders = ExecutedOrders(
                            coinpair.bitpreco_format
                        ).json()
                        save_orders_to_csv(executed_orders)
                        progress.update(
                            task,
                            advance=10,
                            description='Ordens executadas atualizadas',
                        )
                        estrategia_daytrade(
                            progress,
                            task,
                            coinpair,
                            ticker_json,
                            balance,
                            executed_orders,
                        )
                        progress.update(
                            task,
                            advance=30,
                            description='Trade executado',
                        )
                        break  # Success, exit retry loop
                    except Exception as e:
                        console.print_exception()
                        if 'timed out' in str(e) or 'ConnectionError' in str(
                            e
                        ):
                            if attempt < max_retries - 1:
                                console.print(
                                    f'[bold magenta]Tentativa {attempt + 1}'
                                    + f' falhou: {str(e)}[/bold magenta]'
                                )
                                time.sleep(
                                    retry_delay * (2**attempt)
                                )  # Exponential backoff
                                continue
                            raise  # Re-raise the last exception if all retries failed  # noqa: E501

                # Tempo que pode ser controlado pelo dashboard
                # Atraves de um arquivo leve e rapido
                # Obtém o valor do delay do arquivo `interval.json`
                delay = get_interval()
                progress.update(
                    task,
                    completed=100,
                    description=f':clock1: [bold cyan]Esperando {delay}'
                    + ' segundos...[/bold cyan]',
                )
                time.sleep(delay)

            except KeyboardInterrupt:
                console.print(
                    ':rotating_light: [bold magenta]Saindo...[/bold magenta]'
                )
                break
            except Exception as e:
                if 'timed out' in str(e) or 'ConnectionError' in str(e):
                    console.print(
                        f'[bold magenta]Erro de conexão após {max_retries}'
                        + f' tentativas: {str(e)}[/bold magenta]'
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    console.print(
                        f'[bold magenta]Erro: {str(e)}[/bold magenta]'
                    )
                    console.print_exception()
                    break
            progress.reset(task_id=task)


if __name__ == '__main__':
    main()
