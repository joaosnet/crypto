import sys
from pathlib import Path

import pandas as pd
import talib as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Adiciona o diretório raiz ao path para poder importar os módulos do projeto
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Importando funções e classes relevantes do projeto


# Estratégia cruzamento de médias móveis básica
class SmaCross(Strategy):
    # Parâmetros que podem ser otimizados
    n1 = 10  # período da SMA rápida
    n2 = 20  # período da SMA lenta

    def init(self):
        price = self.data.Close
        self.ma1 = self.I(ta.SMA, price, self.n1)
        self.ma2 = self.I(ta.SMA, price, self.n2)

    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()


# Estratégia baseada no seu sistema de daytrade
class DaytradeStrategy(Strategy):
    # Parâmetros que podem ser otimizados
    ema_short = 10
    ema_long = 20
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30

    def init(self):
        # Preços
        self.close = self.data.Close
        self.high = self.data.High
        self.low = self.data.Low
        self.volume = (
            self.data.Volume if hasattr(self.data, 'Volume') else None
        )

        # EMAs
        self.ema_fast = self.I(ta.EMA, self.close, self.ema_short)
        self.ema_slow = self.I(ta.EMA, self.close, self.ema_long)
        self.ema_200 = self.I(ta.EMA, self.close, 200)

        # MACD
        self.macd, self.macd_signal, _ = self.I(
            ta.MACD, self.close, fastperiod=12, slowperiod=26, signalperiod=9
        )

        # RSI
        self.rsi = self.I(ta.RSI, self.close, timeperiod=self.rsi_period)

        # Bollinger Bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            ta.BBANDS, self.close, timeperiod=20, nbdevup=2, nbdevdn=2
        )

    def next(self):
        # Condições de compra
        trend_up = self.ema_fast[-1] > self.ema_slow[-1]
        macd_signal = crossover(self.macd, self.macd_signal)
        rsi_oversold = self.rsi[-1] < self.rsi_oversold
        price_above_ema200 = self.close[-1] > self.ema_200[-1]
        price_near_bb_lower = self.close[-1] <= self.bb_lower[-1] * 1.01

        # Condições de venda
        trend_down = self.ema_fast[-1] < self.ema_slow[-1]
        macd_signal_down = crossover(self.macd_signal, self.macd)
        rsi_overbought = self.rsi[-1] > self.rsi_overbought
        price_near_bb_upper = self.close[-1] >= self.bb_upper[-1] * 0.99

        # Regras de entrada e saída
        if not self.position:  # Se não temos posição
            if (
                trend_up
                and macd_signal
                and (rsi_oversold or price_near_bb_lower)
                and price_above_ema200
            ):
                self.buy()
        else:  # Se temos posição
            if trend_down and (
                macd_signal_down or rsi_overbought or price_near_bb_upper
            ):
                self.sell()

            # Adicione uma lógica de stop loss
            # (5% abaixo do preço de entrada por exemplo)
            if (
                self.position.is_long
                and self.close[-1] < self.position.entry_price * 0.95
            ):
                self.position.close()


def run_backtest(data, strategy_class, **strategy_params):
    bt = Backtest(
        data,
        strategy_class,
        cash=10000,
        commission=0.002,  # 0.2% por operação
        exclusive_orders=True,
        **strategy_params,
    )

    stats = bt.run()
    print(f'Testando {strategy_class.__name__}')
    print(f'Retorno Total: {stats["Return [%]"]:.2f}%')
    print(f'Retorno Anualizado: {stats["Return (Ann.) [%]"]:.2f}%')
    print(f'Máximo Drawdown: {stats["Max. Drawdown [%]"]:.2f}%')
    print(f'Rácio de Sharpe: {stats["Sharpe Ratio"]:.2f}')
    print(f'Número de Trades: {stats["# Trades"]}')
    print(f'Win Rate: {stats["Win Rate [%]"]:.2f}%')
    print(f'Profit Factor: {stats["Profit Factor"]:.2f}')
    print('-' * 50)

    return bt, stats


# Função para carregar dados históricos
# (pode ser personalizada para seu dataset)
def load_data(symbol='BTCBRL', timeframe='1d', csv_path=None):
    if csv_path:
        df = pd.read_csv(csv_path, parse_dates=True, index_col=0)
    else:
        # Se necessário importar da biblioteca backtesting:
        from backtesting.test import GOOG  # noqa: PLC0415

        return GOOG

    # Assegure-se de que os nomes das colunas estão no formato esperado
    column_map = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
    }

    df = df.rename(
        columns={k: v for k, v in column_map.items() if k in df.columns}
    )
    return df


if __name__ == '__main__':
    # Tente buscar seus dados primeiro
    try:
        data_path = (
            Path(__file__).resolve().parent.parent.parent
            / 'db'
            / 'BTC_BRL_bitpreco.csv'
        )
        if data_path.exists():
            data = load_data(csv_path=data_path)
        else:
            # Use dados de exemplo caso não encontre seus dados
            from backtesting.test import GOOG

            data = GOOG
    except Exception as e:
        print(f'Erro ao carregar dados: {e}')
        from backtesting.test import GOOG

        data = GOOG

    # Execute backtests para ambas as estratégias
    bt1, stats1 = run_backtest(data, SmaCross)
    bt1.plot(filename='SmaCross.html', open_browser=False)

    bt2, stats2 = run_backtest(data, DaytradeStrategy)
    bt2.plot(filename='DaytradeStrategy.html', open_browser=False)

    # Otimização de parâmetros (opcional, descomente se quiser usar)
    # stats = bt2.optimize(
    #     ema_short=range(5, 20, 5),
    #     ema_long=range(20, 100, 20),
    #     rsi_period=[7, 14, 21],
    #     rsi_oversold=range(20, 40, 5),
    #     rsi_overbought=range(60, 85, 5),
    #     maximize='Sharpe Ratio',
    #     method='grid'
    # )
    # print("Parâmetros ótimos:", stats._strategy)
    # bt2.plot(filename='DaytradeStrategy_Optimized.html', open_browser=False)
