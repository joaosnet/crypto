import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import talib as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import GOOG
from rich import print

# Adiciona o diretório raiz ao path para poder importar os módulos do projeto
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Importando as funções e classes relevantes do projeto


class UTBot(Strategy):
    """
    Implementação do seu bot de trading adaptado para o framework de Backtest
    """

    # Parâmetros configuráveis para otimização
    ema_fast = 5
    ema_slow = 20
    ema_trend = 200
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    bb_period = 20
    bb_dev = 2
    stop_loss_pct = 0.95  # 5% abaixo do preço de entrada
    take_profit_pct = 1.03  # 3% acima do preço de entrada
    risk_per_trade = 0.1  # 10% do capital disponível por operação

    def init(self):
        """Inicializar todos os indicadores necessários"""
        # Preços
        self.close = self.data.Close
        self.high = self.data.High
        self.low = self.data.Low
        self.volume = (
            self.data.Volume if hasattr(self.data, 'Volume') else None
        )

        # Calcular EMAs
        self.ema5 = self.I(ta.EMA, self.close, self.ema_fast)
        self.ema10 = self.I(ta.EMA, self.close, 10)
        self.ema20 = self.I(ta.EMA, self.close, self.ema_slow)
        self.ema200 = self.I(ta.EMA, self.close, self.ema_trend)

        # MACD
        self.macd, self.macd_signal, self.macd_hist = self.I(
            ta.MACD,
            self.close,
            fastperiod=self.macd_fast,
            slowperiod=self.macd_slow,
            signalperiod=self.macd_signal,
        )

        # RSI
        self.rsi = self.I(ta.RSI, self.close, timeperiod=self.rsi_period)

        # Bollinger Bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            ta.BBANDS,
            self.close,
            timeperiod=self.bb_period,
            nbdevup=self.bb_dev,
            nbdevdn=self.bb_dev,
        )

        # Stochastic
        self.stoch_k, self.stoch_d = self.I(
            ta.STOCH,
            self.high,
            self.low,
            self.close,
            fastk_period=14,
            slowk_period=3,
            slowd_period=3,
        )

        # ATR para gerenciamento de risco
        self.atr = self.I(
            ta.ATR, self.high, self.low, self.close, timeperiod=14
        )

        # Armazena a última posição e sinal para simular seu sistema atual
        self.last_position = 0
        self.last_signal = 0

    def next(self):
        """Executa a cada nova barra de preço"""
        # Avaliação de tendência
        trend_up = (
            self.ema5[-1] > self.ema20[-1] and self.close[-1] > self.ema200[-1]
        )
        trend_down = (
            self.ema5[-1] < self.ema20[-1] or self.close[-1] < self.ema200[-1]
        )

        # Sinais de entrada
        macd_bullish = crossover(self.macd, self.macd_signal)
        macd_bearish = crossover(self.macd_signal, self.macd)

        rsi_oversold = self.rsi[-1] < self.rsi_oversold
        rsi_overbought = self.rsi[-1] > self.rsi_overbought

        n = 20
        i = 80
        stoch_oversold = self.stoch_k[-1] < n and self.stoch_d[-1] < n
        stoch_overbought = self.stoch_k[-1] > i and self.stoch_d[-1] > i

        price_near_bb_lower = self.close[-1] <= self.bb_lower[-1] * 1.01
        price_near_bb_upper = self.close[-1] >= self.bb_upper[-1] * 0.99

        # Sinais combinados de compra e venda
        buy_signal = (
            trend_up
            and macd_bullish
            and (rsi_oversold or stoch_oversold or price_near_bb_lower)
        )

        sell_signal = (
            trend_down
            or macd_bearish
            or rsi_overbought
            or stoch_overbought
            or price_near_bb_upper
        )

        # Atualizar o último sinal com base nas condições
        if buy_signal:
            self.last_signal = 1  # Compra
        elif sell_signal:
            self.last_signal = -1  # Venda

        # Lógica de execução do trade
        if not self.position:  # Se não temos posição aberta
            if buy_signal and self.last_position == 0:
                # Calcular tamanho da posição baseado no risco
                size = self.risk_per_trade * self.equity / self.close[-1]
                self.buy(size=size)
                self.last_position = 1

                # Registrar possível preço de stop loss
                # e take profit para visualização
                self.stop_price = self.close[-1] * self.stop_loss_pct
                self.target_price = self.close[-1] * self.take_profit_pct
        # Verificar se atingiu take profit, stop loss ou sinal de venda
        elif sell_signal or self.close[-1] <= self.stop_price:
            self.position.close()
            self.last_position = 0

        # Take profit
        elif self.close[-1] >= self.target_price:
            self.position.close()
            self.last_position = 0


def load_crypto_data(csv_path):
    """Carrega e prepara dados de criptomoedas do CSV"""
    try:
        df = pd.read_csv(csv_path, parse_dates=True)

        # Verificar se o dataframe tem uma coluna de data
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # Adaptar nomes das colunas para o formato esperado pelo Backtest
        column_map = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        }

        # Renomear apenas as colunas que existem
        df = df.rename(
            columns={k: v for k, v in column_map.items() if k in df.columns}
        )

        # Verificar se temos todas as colunas necessárias
        required_columns = ['Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_columns):
            print('Aviso: Dados não contêm todas as colunas necessárias.')
            return None

        return df
    except Exception as e:
        print(f'Erro ao carregar dados: {e}')
        return None


def run_backtest_analysis(data, strategy_class, **params):
    """Executa o backtest e exibe análise detalhada dos resultados"""
    # Configuração do backtest
    bt = Backtest(
        data,
        strategy_class,
        cash=10000,  # Capital inicial
        commission=0.002,  # Taxa de 0.2%
        margin=1.0,  # Sem margem
        trade_on_close=False,
        hedging=False,
        exclusive_orders=True,
        **params,
    )

    # Executar o backtest
    stats = bt.run()

    # Exibir estatísticas detalhadas
    print('\n' + '=' * 50)
    print(f'ANÁLISE DE BACKTEST - {strategy_class.__name__}')
    print('=' * 50)
    print(
        f'Período: {data.index[0].strftime("%d/%m/%Y")} a'
        + f' {data.index[-1].strftime("%d/%m/%Y")}'
    )
    print(f'Total de barras analisadas: {len(data)}')
    print('\nESTATÍSTICAS DE RETORNO:')
    print(f'Retorno Total: {stats["Return [%]"]:.2f}%')
    print(f'Retorno Anualizado: {stats["Return (Ann.) [%]"]:.2f}%')
    print(f'Volatilidade (Anualizada): {stats["Volatility (Ann.) [%]"]:.2f}%')
    print(f'Índice de Sharpe: {stats["Sharpe Ratio"]:.2f}')
    print(f'Sortino Ratio: {stats["Sortino Ratio"]:.2f}')
    print(f'Calmar Ratio: {stats["Calmar Ratio"]:.2f}')
    print(f'Máximo Drawdown: {stats["Max. Drawdown [%]"]:.2f}%')

    print('\nESTATÍSTICAS DE TRADES:')
    print(f'Número Total de Trades: {stats["# Trades"]}')
    print(f'Taxa de Acerto: {stats["Win Rate [%]"]:.2f}%')
    print(f'Melhor Trade: {stats["Best Trade [%]"]:.2f}%')
    print(f'Pior Trade: {stats["Worst Trade [%]"]:.2f}%')
    print(f'Tempo Médio no Mercado: {stats["Avg. Trade Duration"]}')
    print(f'Profit Factor: {stats["Profit Factor"]:.2f}')
    print(f'Expectancy [%]: {stats["Expectancy [%]"]:.2f}%')
    print(f'SQN: {stats["SQN"]:.2f}')

    # Gerar gráfico do backtest
    filename = (
        f'{strategy_class.__name__}_'
        + f'{datetime.now().strftime("%Y%m%d_%H%M")}.html'
    )
    print(f'\nGráfico do backtest salvo como {filename}')
    bt.plot(filename=filename, open_browser=True)

    return bt, stats


def optimize_strategy(
    data, strategy_class, optimization_params, maximize='Return [%]'
):
    """Otimiza os parâmetros da estratégia"""
    bt = Backtest(
        data,
        strategy_class,
        cash=10000,
        commission=0.002,
        exclusive_orders=True,
    )

    print(f'\nOtimizando {strategy_class.__name__}...')
    print(f'Parâmetros a otimizar: {list(optimization_params.keys())}')
    print(f'Métrica de otimização: {maximize}')

    stats = bt.optimize(
        **optimization_params,
        maximize=maximize,
        method='grid',  # ou 'skopt' se disponível
        max_tries=100,
    )

    print('\nRESULTADOS DA OTIMIZAÇÃO:')
    print(f'Melhores parâmetros: {stats._strategy}')
    print(f'{maximize}: {stats[maximize]:.2f}')
    print(f'Retorno Total: {stats["Return [%]"]:.2f}%')
    print(f'Índice de Sharpe: {stats["Sharpe Ratio"]:.2f}')
    print(f'Drawdown Máximo: {stats["Max. Drawdown [%]"]:.2f}%')
    print(f'Win Rate: {stats["Win Rate [%]"]:.2f}%')

    # Executar backtest com os melhores parâmetros
    return bt, stats


if __name__ == '__main__':
    # Tentar carregar dados reais do projeto
    data_path = (
        Path(__file__).resolve().parent.parent.parent
        / 'db'
        / 'BTC_BRL_bitpreco.csv'
    )

    if data_path.exists():
        data = load_crypto_data(data_path)
        if data is None:
            # Fallback para dados de exemplo
            data = GOOG
            print(
                'Usando dados de teste GOOG devido a erro nos dados de cripto'
            )
    else:
        # Fallback para dados de exemplo
        data = GOOG
        print(
            'Arquivo de dados de cripto não encontrado.'
            + ' Usando dados de teste GOOG.'
        )

    # Executar backtest da estratégia UTBot
    bt, stats = run_backtest_analysis(data, UTBot)
    # Otimização (descomente para usar)
    """
    optimization_params = {
        'ema_fast': range(3, 15, 2),
        'ema_slow': range(15, 35, 5),
        'rsi_period': [7, 14, 21],
        'rsi_oversold': range(20, 40, 5),
        'rsi_overbought': range(60, 85, 5),
        'risk_per_trade': [0.05, 0.1, 0.15, 0.2]
    }
    bt_opt, stats_opt = optimize_strategy(
        data,
        UTBot,
        optimization_params,
        maximize='Sharpe Ratio'
    )
    # Plot com parâmetros otimizados
    bt_opt.plot(filename='UTBot_Optimized.html', open_browser=False)
    """
