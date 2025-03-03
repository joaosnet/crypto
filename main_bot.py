import signal
import sys
import threading
import time
from typing import Dict

from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from bot.apis.api_bitpreco import Balance, ExecutedOrders, Ticker
from bot.estrategias.daytrade import execute_trade as estrategia_daytrade
from bot.logs.config_log import console
from bot.models.coin_pair import CoinPair
from bot.parametros import (
    INTERVALO_TENTATIVAS,
    NUMERO_MAXIMO_TENTATIVAS,
    THREAD_LOCK,
)
from compartilhado import get_coinpairs, get_interval
from db.json_csv import (
    save_balance_to_csv,
    save_orders_to_csv,
    save_price_to_csv,
)


class TradingBot:
    def __init__(self):
        self._stop_event = threading.Event()
        self.thread_lock = threading.Lock()
        self.threads = []
        self.progress_bars: Dict[str, Progress] = {}
        self.tasks: Dict[str, int] = {}

    def create_progress_group(self):
        """Cria grupo de barras de progresso para cada par de moedas"""
        progress_group = []
        for coinpair in get_coinpairs():
            progress = Progress(
                SpinnerColumn(),
                TextColumn(
                    f'[blue]{coinpair.bitpreco_format}[/blue] '
                    + '{task.description}'
                ),
                BarColumn(),
                TimeElapsedColumn(),
            )
            task = progress.add_task('Iniciando...', total=100)
            self.progress_bars[coinpair.bitpreco_format] = progress
            self.tasks[coinpair.bitpreco_format] = task
            progress_group.append(
                Panel(progress, title=coinpair.bitpreco_format)
            )

        return Group(*progress_group)

    @classmethod
    def retry_on_connection_error(self, func):
        def wrapper(*args, **kwargs):
            for attempt in range(NUMERO_MAXIMO_TENTATIVAS):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    console.print_exception()
                    if 'timed out' in str(e) or 'ConnectionError' in str(e):
                        if attempt < NUMERO_MAXIMO_TENTATIVAS - 1:
                            console.print(
                                f'[bold magenta]Tentativa {attempt + 1}'
                                + f' falhou: {str(e)}[/bold magenta]'
                            )
                            time.sleep(INTERVALO_TENTATIVAS * (2**attempt))
                            continue
                    raise

        return wrapper

    def execute_trading_cycle(self, coinpair: CoinPair) -> None:
        progress = self.progress_bars[coinpair.bitpreco_format]
        task = self.tasks[coinpair.bitpreco_format]

        try:
            ticker_json = Ticker(coinpair).json()
            save_price_to_csv(ticker_json)
            progress.update(task, advance=10, description='Ticker atualizado')

            balance = Balance().json()
            save_balance_to_csv(balance)
            progress.update(task, advance=10, description='Saldo atualizado')

            executed_orders = ExecutedOrders(coinpair.bitpreco_format).json()
            save_orders_to_csv(executed_orders, coinpair)
            progress.update(task, advance=10, description='Ordens atualizadas')

            estrategia_daytrade(
                progress, task, coinpair, ticker_json, balance, executed_orders
            )
            progress.update(task, advance=30, description='Trade executado')

        except Exception as e:
            progress.update(task, description=f'[red]Erro: {str(e)}[/red]')
            raise

    def trader_loop(self, coinpair: CoinPair):
        while not self._stop_event.is_set():
            try:
                if THREAD_LOCK:
                    with self.thread_lock:
                        self.retry_on_connection_error(
                            self.execute_trading_cycle
                        )(coinpair)
                else:
                    self.retry_on_connection_error(self.execute_trading_cycle)(
                        coinpair
                    )

                delay = get_interval()
                progress = self.progress_bars[coinpair.bitpreco_format]
                task = self.tasks[coinpair.bitpreco_format]
                progress.update(
                    task,
                    description=f'Aguardando {delay}s',
                    completed=100,
                )

                for _ in range(delay):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)

                # Reset progress
                progress.update(task, completed=0)

            except Exception as e:
                if not self._stop_event.is_set():
                    console.print(f'[red]Erro: {str(e)}[/red]')
                    time.sleep(INTERVALO_TENTATIVAS)

    def start(self):
        self._stop_event.clear()
        progress_group = self.create_progress_group()

        with Live(
            progress_group,
            refresh_per_second=4,
            console=console,
            transient=False,
            vertical_overflow="crop",
        ) as live:
            self.live = live
            for coinpair in get_coinpairs():
                thread = threading.Thread(
                    target=self.trader_loop,
                    args=(coinpair,),
                    daemon=True,
                )
                thread.start()
                self.threads.append(thread)

            # Mantém o live display ativo
            while not self._stop_event.is_set():
                time.sleep(0.1)

    def stop(self):
        self._stop_event.set()
        for thread in self.threads:
            thread.join(timeout=5.0)
        console.print('[bold green]Bot encerrado com sucesso![/bold green]')

    def signal_handler(self, signum, frame):
        console.print(
            ':rotating_light: [bold magenta]Iniciando'
            + ' encerramento gracioso...[/bold magenta]'
        )
        self.stop()


def main():
    bot = TradingBot()
    signal.signal(signal.SIGINT, bot.signal_handler)

    try:
        bot.start()
    except Exception as e:
        console.print(f'[bold red]Erro fatal: {str(e)}[/bold red]')
        bot.stop()
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
