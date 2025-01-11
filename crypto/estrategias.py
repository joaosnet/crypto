import json
import logging
from datetime import datetime
from typing import Dict, Optional

import duckdb as dd
import fireducks.pandas as pd
import numpy as np
import talib as ta

# from memory_profiler import profile
from rich import console
from rich.logging import RichHandler

try:
    from crypto.segredos import CAMINHO
except ImportError:
    from segredos import CAMINHO

try:
    from api_binance import get_klines
    from api_bitpreco import (
        Buy,
        Sell,
        fetch_bitpreco_history,
        get_coinpair,
    )
except ImportError:
    from crypto.api_binance import get_klines
    from crypto.api_bitpreco import (
        Buy,
        Sell,
        fetch_bitpreco_history,
        get_coinpair,
    )

# Configuração do logger sem as requisições HTTP
FORMAT = '%(message)s'
logging.basicConfig(
    level=logging.ERROR,
    format=FORMAT,
    datefmt='[%X]',
    handlers=[RichHandler()],
)
logger = logging.getLogger(__name__)

console = console.Console()

# Parâmetros Globais
coinpair = get_coinpair()
profitability = 1.05  # Margem de lucro desejada (5%)
risk_per_trade = 0.10  # Arriscar 10% do saldo disponível por operação
short_window = 5  # Período da média móvel de curto prazo
long_window = 10  # Período da média móvel de longo prazo
SIGNAL_BUY = 1  # Alterar de 2 para 1
SIGNAL_SELL = -1  # Alterar de -2 para -1
STOP_LOSS = 0.95  # Limite para stop-loss (5% abaixo do preço de compra)
RSI_OVERSOLD = 30  # Limite inferior do RSI para compra

# Configurações adicionais
TRADE_HISTORY_FILE = CAMINHO + '/trade_history.json'
INDICADORES_FILE = CAMINHO + '/indicadores.csv'
SINAIS_FILE = CAMINHO + '/sinais.csv'
INTERVAL_FILE = CAMINHO + '/interval.json'
BTCBRL_FILE = CAMINHO + '/btc_brl_binance.csv'
BTCBRL_BITY = CAMINHO + '/btc_brl_bity.csv'
BACKTEST_DAYS = 30
MAX_DAILY_TRADES = 100


def get_price_history(symbol='BTCBRL', interval='1m', limit=1000):
    """
    Obtém o histórico de preços da Binance para o símbolo especificado.
    """
    try:
        df = dd.read_csv(BTCBRL_FILE).to_df()
        df1 = dd.read_csv(BTCBRL_BITY).to_df()
        klines = get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
        klines1 = fetch_bitpreco_history(
            symbol='BTC_BRL',
            resolution='1',
            time_range={
                'from': int(datetime.now().timestamp()) - 1184400,
                'to': int(datetime.now().timestamp()),
            },
            countback=0,
        )
        # Convert timestamps to UTC timezone
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

        klines['timestamp'] = pd.to_datetime(klines['Kline open time'])
        if klines['timestamp'].dt.tz is None:
            klines['timestamp'] = klines['timestamp'].dt.tz_localize('UTC')
        klines['timestamp'] = klines['timestamp'].dt.tz_convert('UTC')

        df1['timestamp'] = pd.to_datetime(df1['timestamp'])
        if df1['timestamp'].dt.tz is None:
            df1['timestamp'] = df1['timestamp'].dt.tz_localize('UTC')
        df1['timestamp'] = df1['timestamp'].dt.tz_convert('UTC')

        klines1['timestamp'] = pd.to_datetime(klines1['timestamp'])
        if klines1['timestamp'].dt.tz is None:
            klines1['timestamp'] = klines1['timestamp'].dt.tz_localize('UTC')
        klines1['timestamp'] = klines1['timestamp'].dt.tz_convert('UTC')

        klines = klines.rename(
            columns={
                'Close price': 'close',
                'High price': 'high',
                'Low price': 'low',
            }
        )

        # Filter out duplicate timestamps
        df = df[~df['timestamp'].isin(klines['timestamp'])]
        df1 = df1[~df1['timestamp'].isin(klines1['timestamp'])]

        # Concatenate dataframes
        df = pd.concat([df, klines], ignore_index=True)
        df1 = pd.concat([df1, klines1], ignore_index=True)
        df.to_csv(BTCBRL_FILE, index=False)
        return df1
    except Exception as e:
        logger.error(f'Erro ao obter histórico de preços: {e}')
        console.print_exception()
        return None


def calculate_indicators(df):
    """
    Calcula indicadores técnicos avançados
    """
    df = df.copy()

    # Converter Series para numpy arrays
    close_arr = df['close'].to_numpy(dtype=float)
    high_arr = df['high'].to_numpy(dtype=float)
    low_arr = df['low'].to_numpy(dtype=float)
    volume_arr = df['volume'].to_numpy(dtype=float)

    # EMAs
    df['EMA_5'] = ta.EMA(close_arr, timeperiod=5)
    df['EMA_10'] = ta.EMA(close_arr, timeperiod=10)
    df['EMA_20'] = ta.EMA(close_arr, timeperiod=20)
    df['EMA_200'] = ta.EMA(close_arr, timeperiod=200)

    # MACD
    df['macd'], df['macd_signal'], df['MACD_hist'] = ta.MACD(
        close_arr, fastperiod=12, slowperiod=26, signalperiod=9
    )

    # RSI
    df['rsi'] = ta.RSI(close_arr, timeperiod=14)

    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(
        close_arr, timeperiod=20, nbdevup=2, nbdevdn=2
    )

    # Stochastic
    df['STOCH_K'], df['STOCH_D'] = ta.STOCH(
        high_arr,
        low_arr,
        close_arr,
        fastk_period=14,
        slowk_period=3,
        slowd_period=3,
    )

    # Volume médio
    df['volume_sma'] = ta.SMA(volume_arr, timeperiod=20)

    # Average True Range (ATR)
    df['atr'] = ta.ATR(high_arr, low_arr, close_arr, timeperiod=14)

    return df


def generate_signals(df):
    """
    Gera sinais de compra e venda baseados em múltiplos indicadores
    """
    df = df.copy()
    df['signal'] = 0
    df['position'] = 0

    # Parâmetros
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    STOCH_OVERBOUGHT = 80
    STOCH_OVERSOLD = 20

    # Identificar tendência
    df['trend'] = np.where(df['close'] > df['EMA_200'], 'alta', 'baixa')

    # Cruzamentos
    df['EMA_cross'] = np.where(
        (df['EMA_5'] > df['EMA_10'])
        & (df['EMA_5'].shift(1) <= df['EMA_10'].shift(1)),
        1,
        np.where(
            (df['EMA_5'] < df['EMA_10'])
            & (df['EMA_5'].shift(1) >= df['EMA_10'].shift(1)),
            -1,
            0,
        ),
    )

    df['MACD_cross'] = np.where(
        (df['macd'] > df['macd_signal'])
        & (df['macd'].shift(1) <= df['macd_signal'].shift(1)),
        1,
        np.where(
            (df['macd'] < df['macd_signal'])
            & (df['macd'].shift(1) >= df['macd_signal'].shift(1)),
            -1,
            0,
        ),
    )

    # Sinais de compra - agora precisa atender apenas 3 das 5 condições
    buy_signals = pd.DataFrame({
        'ema_signal': (df['EMA_cross'] == 1),
        'macd_signal': (df['MACD_cross'] == 1),
        'rsi_signal': (df['rsi'] < RSI_OVERSOLD),
        'bb_signal': (df['close'] <= df['bb_lower']),
        'stoch_signal': (df['STOCH_K'] < STOCH_OVERSOLD),
    })

    # Sinais de venda - agora precisa atender apenas 3 das 5 condições
    sell_signals = pd.DataFrame({
        'ema_signal': (df['EMA_cross'] == -1),
        'macd_signal': (df['MACD_cross'] == -1),
        'rsi_signal': (df['rsi'] > RSI_OVERBOUGHT),
        'bb_signal': (df['close'] >= df['bb_upper']),
        'stoch_signal': (df['STOCH_K'] > STOCH_OVERBOUGHT),
    })

    # Conta quantas condições são atendidas
    buy_count = buy_signals.sum(axis=1)
    sell_count = sell_signals.sum(axis=1)

    # Gera sinais quando pelo menos 3 condições são atendidas
    CONDICOES = 3
    df.loc[buy_count >= CONDICOES, 'signal'] = SIGNAL_BUY
    df.loc[sell_count >= CONDICOES, 'signal'] = SIGNAL_SELL

    # Calcular posições
    df['position'] = df['signal'].fillna(0)

    # Validar sinais
    assert df['position'].isin([SIGNAL_BUY, 0, SIGNAL_SELL]).all(), (
        'Valores de posição inválidos'
    )

    # Salvar dados
    df.to_csv(BTCBRL_BITY, index=False)

    return df


def validate_trade_conditions(
    price: float,
    balance: Dict,
    trade_history: json,
    last_price: Optional[float] = None,
) -> bool:
    """
    Valida condições para execução de trades
    """
    # Verifica número máximo de trades diários
    trades_list = (
        trade_history
        if isinstance(trade_history, list)
        else trade_history.trades
    )

    today_trades = [
        t
        for t in trades_list
        if datetime.strptime(t['time_stamp'], '%Y-%m-%d %H:%M:%S').date()
        == datetime.now().date()
    ]

    if len(today_trades) >= MAX_DAILY_TRADES:
        console.print(
            ':warning: [bold red]Número máximo de trades'
            + ' diários atingido[/bold red]'
        )
        return False

    # Validação de volatilidade extrema
    volatilidade = 0.1
    if (
        last_price is not None
        and abs((price - last_price) / last_price) > volatilidade
    ):
        console.print(
            ':warning: [bold red]Volatilidade muito alta - '
            + 'trade cancelado[/bold red]'
        )
        return False

    return True


# Função para executar a estratégia de negociação com controle de risco
# @profile
def execute_trade(ticker_json, balance, executed_orders):
    """
    Executa operações com melhor gerenciamento de risco
    """
    try:
        current_price = float(ticker_json['last'])

        if not validate_trade_conditions(
            current_price, balance, executed_orders
        ):
            return

        df = get_price_history()
        if df is None or df.empty:
            logger.warning('Dados históricos não disponíveis')
            return

        df = calculate_indicators(df)
        df = generate_signals(df)

        trend, risk_factor = analyze_market(df)
        console.print(
            ':chart_with_upwards_trend: [bold cyan]'
            + f'Tendência atual:[/bold cyan] {trend}, '
            f'[bold cyan]Fator de risco:[/bold cyan] {risk_factor}'
        )

        risk_per_trade = adjust_risk(risk_factor)
        last_signal = df['position'].iloc[-1]
        last_price = ticker_json['last']

        brl_balance = balance.get('BRL', 0)
        btc_balance = balance.get('BTC', 0)
        # last_signal = -1
        if last_signal == SIGNAL_BUY and brl_balance > 0:
            execute_buy(
                executed_orders,
                brl_balance,
                risk_per_trade,
                last_price,
            )
        elif last_signal == SIGNAL_SELL and btc_balance > 0:
            execute_sell(
                executed_orders,
                btc_balance,
                risk_per_trade,
                last_price,
            )
        else:
            console.print(
                ':hourglass: [bold yellow]Nenhuma ação necessária '
                + 'no momento.[/bold yellow]'
            )

    except Exception as e:
        logger.error(f'Erro na execução do trade: {str(e)}')
        console.print_exception()


def analyze_market(df):
    trend = analyze_trend(df)
    risk_factor = calculate_risk_factor(df)
    return trend, risk_factor


def adjust_risk(risk_factor):
    risk_per_trade = 0.25
    adjusted_risk = risk_per_trade * risk_factor
    return min(adjusted_risk, 0.2)


def execute_buy(executed_orders, brl_balance, risk_per_trade, last_price):
    amount_to_invest = brl_balance * risk_per_trade
    amount = amount_to_invest / last_price
    price = last_price

    resposta_compra = Buy(
        price=price,
        volume=amount,
        amount=amount,
        limited=True,
        market=coinpair,
    )
    console.print(
        ':four_leaf_clover: [bold green]Compra executada:[/bold green] '
        + str(resposta_compra)
    )


def execute_sell(executed_orders, btc_balance, risk_per_trade, last_price):
    amount = btc_balance * risk_per_trade
    ultima_compra = next(
        (
            order
            for order in executed_orders
            if order['type'] == 'BUY' and order['status'] == 'FILLED'
        ),
        None,
    )

    if ultima_compra is not None:
        preco_compra = ultima_compra['price']
        take_profit = preco_compra * profitability
        stop_loss_price = preco_compra * STOP_LOSS
        console.print(
            ':moneybag: [bold blue]Preço de compra:'
            + f'[/bold blue] {preco_compra}\n'
            f'[bold blue]Take Profit:[/bold blue] {take_profit}\n'
            f'[bold blue]Stop Loss:[/bold blue] {stop_loss_price}'
        )
        if last_price >= take_profit:
            execute_sell_trade(amount, last_price, 'SELL (Take Profit)')
        elif last_price <= stop_loss_price:
            execute_sell_trade(amount, stop_loss_price, 'SELL (Stop Loss)')
        else:
            console.print(
                ':hourglass: [bold yellow]Preço não atingiu '
                + 'limite de venda.[/bold yellow]'
            )


def execute_sell_trade(amount, price, trade_type):
    resposta_venda = Sell(
        price=price,
        volume=amount,
        amount=amount,
        limited=True,
        market=coinpair,
    )
    console.print(
        f':four_leaf_clover: [bold yellow]{trade_type} '
        + 'executada:[/bold yellow] '
        + str(resposta_venda)
    )


def analyze_trend(df: pd.DataFrame) -> str:
    """
    Analisa tendência do mercado
    """
    STRONG_UP_THRESHOLD = 0.7
    UP_THRESHOLD = 0.5
    STRONG_DOWN_THRESHOLD = 0.3
    DOWN_THRESHOLD = 0.5

    last_rows = df.tail(20)
    trend_up = (last_rows['EMA_5'] > last_rows['EMA_10']).sum() / 20

    if trend_up > STRONG_UP_THRESHOLD:
        return 'STRONG_UP'
    elif trend_up > UP_THRESHOLD:
        return 'UP'
    elif trend_up < STRONG_DOWN_THRESHOLD:
        return 'STRONG_DOWN'
    elif trend_up < DOWN_THRESHOLD:
        return 'DOWN'
    return 'NEUTRAL'


def calculate_risk_factor(df: pd.DataFrame) -> float:
    """
    Calcula fator de risco baseado na volatilidade
    """
    volatility = df['close'].pct_change().std()
    atr = df['atr'].iloc[-1]

    risk_factor = 1.0
    high_volatility = 0.02
    if volatility > high_volatility:  # Alta volatilidade
        risk_factor *= 0.7
    if atr > df['atr'].mean() * 1.5:  # ATR alto
        risk_factor *= 0.8

    return max(0.3, min(risk_factor, 1.0))
