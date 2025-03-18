import signal
import sys
import threading
import time
from typing import Dict, Type

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
from bot.estrategias.daytrade import DaytradeStrategy
from bot.indicadores.calcular_indicadores import calculate_indicators
from bot.indicadores.gerar_sinais_compra_venda import generate_signals
from bot.indicadores.historico_precos import get_price_history
from bot.logs.config_log import console
from bot.models.coin_pair import CoinPair
from bot.parametros import (
    INTERVALO_TENTATIVAS,
    NUMERO_MAXIMO_TENTATIVAS,
    THREAD_LOCK,
)
from bot.validador_trade import validate_trade_conditions
from compartilhado import get_coinpairs, get_interval
from db.duckdb_csv import save_to_csv_duckdb
from db.json_csv import (
    save_balance_to_csv,
    save_orders_to_csv,
    save_price_to_csv,
)
from segredos import CAMINHO


class TradingBot:
    def __init__(
        self, strategy_class: Type[DaytradeStrategy] = DaytradeStrategy
    ):
        self._stop_event = threading.Event()
        self.thread_lock = threading.Lock()
        self.threads = []
        self.progress_bars: Dict[str, Progress] = {}
        self.tasks: Dict[str, int] = {}
        self.strategy_class = strategy_class
        self.strategy = strategy_class()

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
    def retry_on_connection_error(cls, func):
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

    def execute_trading_cycle(self, coinpair: CoinPair) -> None:  # noqa: PLR0914
        """
        Executa um ciclo completo de negociação:
        1. Obtém dados de mercado (ticker, saldo, ordens)
        2. Valida condições para operar
        3. Obtém histórico de preços e calcula indicadores
        4. Gera sinais de compra/venda
        5. Executa operações com base nos sinais
        """
        progress = self.progress_bars[coinpair.bitpreco_format]
        task = self.tasks[coinpair.bitpreco_format]

        try:
            # 1. Obter dados de mercado
            ticker_json = Ticker(coinpair).json()
            save_price_to_csv(ticker_json)
            progress.update(
                task,
                description=f'Preço atual: {ticker_json["last"]}',
                advance=10,
            )

            balance = Balance().json()
            save_balance_to_csv(balance)
            progress.update(task, description='Saldo atualizado', advance=10)

            executed_orders = ExecutedOrders(coinpair.bitpreco_format).json()
            save_orders_to_csv(executed_orders, coinpair)
            progress.update(task, description='Ordens atualizadas', advance=10)

            # 2. Validar condições para trade
            current_price = float(ticker_json['last'])
            if not validate_trade_conditions(
                current_price, balance, executed_orders
            ):
                return
            progress.update(
                task,
                description='Condições de trade validadas',
                advance=10,
            )

            # 3. Obter histórico e calcular indicadores
            df = get_price_history(progress, task, coin_pair=coinpair)
            progress.update(
                task,
                description='Histórico de preços carregado',
                advance=10,
            )
            if df is None or df.empty:
                console.print('Dados históricos não disponíveis')
                return

            df = calculate_indicators(df)
            progress.update(
                task,
                description='Indicadores calculados',
                advance=10,
            )

            # 4. Gerar sinais de compra/venda
            df = generate_signals(df)
            progress.update(
                task,
                description='Sinais de compra e venda gerados',
                advance=10,
            )

            # 5. Analisar mercado e executar operações
            _signal, trend, risk_factor = (
                self.strategy.analyze_signals_from_dataframe(df)
            )

            console.clear()
            console.log(
                ':chart_with_upwards_trend: [bold cyan]'
                + f'Tendência atual:[/bold cyan] {trend}, '
                f'[bold cyan]Fator de risco:[/bold cyan] {risk_factor}'
            )

            adjusted_risk = self.strategy.adjust_risk(risk_factor)
            last_positon = df['position'].iloc[-1]
            last_signal = df['signal'].iloc[-1]
            last_price = ticker_json['last']

            brl_balance = balance.get('BRL', 0)
            btc_balance = balance.get('BTC', 0)

            # Executa compra se tiver saldo e houver sinal de compra
            if brl_balance > 0 and last_positon == 0 and last_signal == 1:
                self.strategy.execute_buy(
                    executed_orders,
                    brl_balance,
                    adjusted_risk,
                    last_price,
                    coinpair,
                )
                df.iloc[-1, df.columns.get_loc('position')] = 1
            # Executa venda se tiver moeda e houver sinal de venda
            elif btc_balance > 0 and last_positon == 1 and last_signal == -1:
                self.strategy.execute_sell(
                    executed_orders,
                    coinpair,
                    btc_balance,
                    adjusted_risk,
                    last_price,
                )
                df.iloc[-1, df.columns.get_loc('position')] = 0
            else:
                console.print(
                    ':hourglass: [bold yellow]Nenhuma ação necessária '
                    + 'no momento.[/bold yellow]'
                )

            # Salvar os dados com indicadores e sinais
            save_to_csv_duckdb(
                df,
                CAMINHO
                + f'/{coinpair.bitpreco_websocket}_{coinpair.exchange.value}'
                + '.csv',
                mode='append',
            )
            progress.update(task, description='Ciclo completo', advance=30)

        except Exception as e:
            progress.update(task, description=f'[red]Erro: {str(e)}[/red]')
            raise

    def trader_loop(self, coinpair: CoinPair):
        """Loop principal de trading para cada par de moedas"""
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
        """Inicia o bot de trading"""
        self._stop_event.clear()
        progress_group = self.create_progress_group()

        with Live(
            progress_group,
            refresh_per_second=4,
            console=console,
            transient=False,
            vertical_overflow='crop',
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
        """Para o bot de trading"""
        self._stop_event.set()
        for thread in self.threads:
            thread.join(timeout=5.0)
        console.print('[bold green]Bot encerrado com sucesso![/bold green]')

    def signal_handler(self, signum, frame):
        """Manipulador de sinais para encerramento gracioso"""
        console.print(
            ':rotating_light: [bold magenta]Iniciando'
            + ' encerramento gracioso...[/bold magenta]'
        )
        self.stop()


def main():
    bot = TradingBot(strategy_class=DaytradeStrategy)
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
