import datetime as dt
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

import numpy as np
import pandas as pd
import talib as ta
from compartilhado import get_coinpair

# from memory_profiler import profile
from rich import console
from rich.logging import RichHandler

try:
    from duckdb_csv import load_csv_in_dataframe
    # from timescaledb import read_from_db, save_from_db_optimized
except ImportError:
    from .duckdb_csv import load_csv_in_dataframe
    # from .timescaledb import read_from_db, save_from_db_optimized


try:
    from api_bitpreco import (
        Buy,
        Sell,
        fetch_bitpreco_history,
    )
except ImportError:
    from crypto.api_bitpreco import (
        Buy,
        Sell,
        fetch_bitpreco_history,
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
BACKTEST_DAYS = 30
MAX_DAILY_TRADES = 100


def get_price_history(symbol='BTC_BRL', interval='1'):
    """
    Obtém o histórico de preços combinando dados do TimescaleDB e BitPreco.
    """
    try:
        # Buscar dados históricos do banco
        end_date = datetime.now(dt.timezone.utc)
        start_date = end_date - timedelta(days=BACKTEST_DAYS)  # último dia
        df_bitpreco = load_csv_in_dataframe(
            'crypto/db/BTC_BRL_bitpreco.csv',
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        # print(df_bitpreco)
        if df_bitpreco is not None and not df_bitpreco.empty:
            # Garantir que timestamp está no formato correto
            df_bitpreco['timestamp'] = pd.to_datetime(df_bitpreco['timestamp'])
            if df_bitpreco['timestamp'].dt.tz is None:
                df_bitpreco['timestamp'] = df_bitpreco[
                    'timestamp'
                ].dt.tz_localize('UTC')

            # Pegar o último timestamp do banco
            last_timestamp = df_bitpreco['timestamp'].max()
            from_timestamp = int(last_timestamp.timestamp())
        else:
            # Se não há dados no banco, buscar período padrão
            from_timestamp = int(datetime.now().timestamp()) - 1184400
            df_bitpreco = pd.DataFrame()

        # Buscar dados mais recentes da API
        klines1 = fetch_bitpreco_history(
            symbol=symbol,
            resolution=interval,
            time_range={
                'from': from_timestamp,
                'to': int(datetime.now().timestamp()),
            },
            countback=0,
        )

        if klines1 is not None and not klines1.empty:
            # Garantir que timestamp está no formato correto
            klines1['timestamp'] = pd.to_datetime(klines1['timestamp'])
            if klines1['timestamp'].dt.tz is None:
                klines1['timestamp'] = klines1['timestamp'].dt.tz_localize(
                    'UTC'
                )
            # Se estiver em outro fuso horário, converter para UTC
            elif klines1['timestamp'].dt.tz.zone != 'UTC':
                klines1['timestamp'] = klines1['timestamp'].dt.tz_convert(
                    'UTC'
                )

            # Concatenar os dataframes removendo duplicatas
            df_final = pd.concat([df_bitpreco, klines1], ignore_index=True)
            df_final = df_final.drop_duplicates(
                subset=['timestamp'], keep='last'
            )

            # Ordenar por timestamp
            df_final = df_final.sort_values('timestamp')

            return df_final

        return df_bitpreco

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
    df['ema_5'] = ta.EMA(close_arr, timeperiod=5)
    df['ema_10'] = ta.EMA(close_arr, timeperiod=10)
    df['ema_20'] = ta.EMA(close_arr, timeperiod=20)
    df['ema_200'] = ta.EMA(close_arr, timeperiod=200)

    # MACD
    df['macd'], df['macd_signal'], df['macd_hist'] = ta.MACD(
        close_arr, fastperiod=12, slowperiod=26, signalperiod=9
    )

    # RSI
    df['rsi'] = ta.RSI(close_arr, timeperiod=14)

    # Bollinger Bands
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(
        close_arr, timeperiod=20, nbdevup=2, nbdevdn=2
    )

    # Stochastic
    df['stoch_k'], df['stoch_d'] = ta.STOCH(
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
    """Gera sinais de compra e venda com tratamento adequado de tipos"""
    # Criar cópia explícita do DataFrame
    df = df.copy()

    # Garantir tipos corretos para colunas numéricas antes de calcular
    numeric_columns = [
        'close',
        'open',
        'high',
        'low',
        'volume',
        'ema_5',
        'ema_10',
        'ema_20',
        'ema_200',
        'macd',
        'macd_signal',
        'macd_hist',
        'rsi',
        'bb_upper',
        'bb_middle',
        'bb_lower',
        'stoch_k',
        'stoch_d',
        'volume_sma',
        'atr',
    ]

    # Converter colunas numéricas para float de forma segura
    for col in numeric_columns:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col], errors='coerce').astype(
                'float64'
            )

    # Inicializar colunas inteiras com valores padrão
    integer_columns = ['signal', 'position', 'ema_cross', 'macd_cross']
    for col in integer_columns:
        # Garantir que a coluna existe e está inicializada como inteiro
        if col not in df.columns:
            df[col] = pd.Series(0, index=df.index, dtype='int64')
        else:
            # Converter para float primeiro, então para int
            df[col] = (
                pd.to_numeric(df[col], errors='coerce')
                .fillna(0)
                .astype('int64')
            )

    # Parâmetros
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    STOCH_OVERBOUGHT = 80
    STOCH_OVERSOLD = 20

    # Identificar tendência
    df['trend'] = np.where(df['close'] > df['ema_200'], 'alta', 'baixa')

    # Cruzamentos
    df['ema_cross'] = np.where(
        (df['ema_5'] > df['ema_10'])
        & (df['ema_5'].shift(1) <= df['ema_10'].shift(1)),
        1,
        np.where(
            (df['ema_5'] < df['ema_10'])
            & (df['ema_5'].shift(1) >= df['ema_10'].shift(1)),
            -1,
            0,
        ),
    )

    df['macd_cross'] = np.where(
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
        'ema_signal': (df['ema_cross'] == 1),
        'macd_signal': (df['macd_cross'] == 1),
        'rsi_signal': (df['rsi'] < RSI_OVERSOLD),
        'bb_signal': (df['close'] <= df['bb_lower']),
        'stoch_signal': (df['stoch_k'] < STOCH_OVERSOLD),
    })

    # Sinais de venda - agora precisa atender apenas 3 das 5 condições
    sell_signals = pd.DataFrame({
        'ema_signal': (df['ema_cross'] == -1),
        'macd_signal': (df['macd_cross'] == -1),
        'rsi_signal': (df['rsi'] > RSI_OVERBOUGHT),
        'bb_signal': (df['close'] >= df['bb_upper']),
        'stoch_signal': (df['stoch_k'] > STOCH_OVERBOUGHT),
    })

    # Conta quantas condições são atendidas
    buy_count = buy_signals.sum(axis=1)
    sell_count = sell_signals.sum(axis=1)

    # Gera sinais quando pelo menos 3 condições são atendidas
    CONDICOES_COMPRA = 3
    CONDICOES_VENDA = 3
    df.loc[buy_count >= CONDICOES_COMPRA, 'signal'] = SIGNAL_BUY
    df.loc[sell_count >= CONDICOES_VENDA, 'signal'] = SIGNAL_SELL

    # Calcular posições
    df['position'] = df['signal'].fillna(0)

    # Validar sinais
    assert df['position'].isin([SIGNAL_BUY, 0, SIGNAL_SELL]).all(), (
        'Valores de posição inválidos'
    )

    # Garantir tipos corretos antes de salvar - versão melhorada
    for col in integer_columns:
        # Converter valores não inteiros para 0 e garantir tipo int64
        df[col] = df[col].apply(
            lambda x: 0
            if pd.isna(x) or not isinstance(x, (int, np.integer))
            else x
        )
        df[col] = df[col].astype('int64')

    # Garantir que trend seja texto e não tenha valores nulos
    df['trend'] = df['trend'].fillna('neutral').astype(str)

    # Salvar dados
    # save_from_db_optimized(df)
    # save_from_db(df)
    df.to_csv(
        'crypto/db/BTC_BRL_bitpreco.csv',
        mode='a',
        index=False,
        header=False,
    )

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

    # resposta_compra = Buy(
    #     price=price,
    #     volume=amount,
    #     amount=amount,
    #     limited=True,
    #     market=coinpair,
    # )
    resposta_compra = 'success'
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
    # resposta_venda = Sell(
    #     price=price,
    #     volume=amount,
    #     amount=amount,
    #     limited=True,
    #     market=coinpair,
    # )
    resposta_venda = 'success'
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
    trend_up = (last_rows['ema_5'] > last_rows['ema_10']).sum() / 20

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
