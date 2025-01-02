# estrategias.py
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, Optional

import numpy as np
import pandas as pd
import talib as ta
from rich import console
from rich.logging import RichHandler

try:
    from crypto.segredos import CAMINHO
except ImportError:
    from segredos import CAMINHO

try:
    from api_binance import get_klines
    from api_bitpreco import (
        # Balance,
        Buy,
        OpenOrders,
        Sell,
        # Ticker,
        get_coinpair,
    )
except ImportError:
    from crypto.api_binance import get_klines
    from crypto.api_bitpreco import (
        # Balance,
        Buy,
        OpenOrders,
        Sell,
        # Ticker,
        get_coinpair,
    )

# Configuração do logger sem as requisições HTTP
FORMAT = '%(message)s'
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt='[%X]', handlers=[RichHandler()]
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
BTCBRL_FILE = CAMINHO + '/btc_brl_full.csv'
BACKTEST_DAYS = 30
MAX_DAILY_TRADES = 5


def bot_msg(levelname: str, message: str):
    """Salva apenas operações de trade no arquivo CSV"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    trade_data = f'{timestamp};{levelname};{message}\n'
    with open(f'{CAMINHO}/log.csv', 'a', encoding='utf-8') as f:
        f.write(trade_data)


class TradeHistory:
    def __init__(self):
        self.trades = self._load_trades()

    @staticmethod
    def _load_trades():
        try:
            with open(TRADE_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # Se arquivo estiver vazio
                    return []
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            # Criar arquivo com lista vazia se não existir ou estiver inválido
            with open(TRADE_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []

    def save_trade(self, trade_type: str, price: float, volume: float):
        trade = {
            'timestamp': datetime.now().isoformat(),
            'type': trade_type,
            'price': price,
            'volume': volume,
        }
        self.trades.append(trade)
        with open(TRADE_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.trades, f)


# Função para obter dados históricos de preços da Binance
def get_price_history(symbol='BTCBRL', interval='1m', limit=1000):
    """
    Obtém o histórico de preços da Binance para o símbolo especificado.
    """
    try:
        df = pd.read_csv(BTCBRL_FILE)
        klines = get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
        # adicionando os novos dados ao dataframe
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        klines['timestamp'] = pd.to_datetime(klines['Kline open time'])
        klines = klines.rename(
            columns={
                'Close price': 'close',
                'High price': 'high',
                'Low price': 'low',
            }
        )
        # para combinar os dataframes, comparo as datas da coluna timestamp
        # e vejo quais não incluir do klines
        df = df[~df['timestamp'].isin(klines['timestamp'])]
        # concateno os dataframes
        df = pd.concat([df, klines], ignore_index=True)
        return df
    except Exception as e:
        logger.error(f'Erro ao obter histórico de preços: {e}')
        console.print_exception()
        return None


# Função para calcular indicadores técnicos avançados
def calculate_indicators(df):
    """
    Calcula indicadores técnicos avançados
    """
    df = df.copy()

    # Médias móveis
    df['short_ma'] = ta.SMA(df['close'], timeperiod=short_window)
    df['long_ma'] = ta.SMA(df['close'], timeperiod=long_window)
    df['MA20'] = ta.SMA(df['close'], timeperiod=20)
    df['MA200'] = ta.SMA(df['close'], timeperiod=200)

    # Indicadores adicionais
    df['rsi'] = ta.RSI(df['close'], timeperiod=14)
    df['macd'], df['macd_signal'], _ = ta.MACD(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(df['close'])
    df['atr'] = ta.ATR(df['high'], df['low'], df['close'])

    return df


# Função para gerar sinais de compra/venda usando indicadores técnicos
def generate_signals(df):
    """
    Gera sinais de compra e venda baseados em múltiplos indicadores.
    """
    df = df.copy()
    df['signal'] = 0

    # Condições de Compra
    buy_conditions = (
        (df['short_ma'] > df['long_ma'])
        | (df['short_ma'] > df['MA20'])
        | (df['short_ma'] > df['MA200'])
    ) & (df['rsi'] <= RSI_OVERSOLD)

    # Condições de Venda
    sell_conditions = (
        (df['short_ma'] < df['long_ma'])
        & (df['rsi'] >= 70)  # Sobrecomprado
        & (
            (df['close'] < df['bb_lower'])  # Preço abaixo da banda inferior
            | (df['macd'] < df['macd_signal'])  # Cruzamento MACD
        )
    )

    # Aplicar sinais
    df['signal'] = np.where(
        buy_conditions, SIGNAL_BUY, np.where(sell_conditions, SIGNAL_SELL, 0)
    )

    # Calcular mudanças de posição e preencher NaN inicial
    df['position'] = df['signal'].diff().fillna(0)

    # Adicionar validação
    assert df['position'].isin([1, 0, -1]).all(), (
        'Valores de posição inválidos detectados'
    )

    # Salvar sinais
    df.to_csv(BTCBRL_FILE, index=False)

    return df


def validate_trade_conditions(
    price: float,
    balance: Dict,
    trade_history: TradeHistory,
    last_price: Optional[float] = None,
) -> bool:
    """
    Valida condições para execução de trades
    """
    # Verifica número máximo de trades diários
    today_trades = [
        t
        for t in trade_history.trades
        if datetime.fromisoformat(t['timestamp']).date()
        == datetime.now().date()
    ]
    if len(today_trades) >= MAX_DAILY_TRADES:
        bot_msg('WARNING', 'Número máximo de trades diários atingido')
        return False
    # Validação de volatilidade extrema
    if last_price is not None and abs((price - last_price) / last_price) > 0.1:
        bot_msg('WARNING', 'Volatilidade muito alta - trade cancelado')
        return False

    return True


# Função para executar a estratégia de negociação com controle de risco
def execute_trade(ticker_json, balance):
    """
    Executa operações com melhor gerenciamento de risco
    """
    try:
        risk_per_trade = 0.25
        trade_executed = False
        trade_history = TradeHistory()
        current_price = float(ticker_json['last'])

        if not validate_trade_conditions(
            current_price, balance, trade_history
        ):
            return

        df = get_price_history()
        if df is None or df.empty:
            logger.warning('Dados históricos não disponíveis')
            return

        df = calculate_indicators(df)
        df = generate_signals(df)  # Adicionar esta linha para gerar os sinais

        # Análise de tendência
        trend = analyze_trend(df)
        risk_factor = calculate_risk_factor(df)
        bot_msg(
            'INFO', f'Tendência atual: {trend}, Fator de risco: {risk_factor}'
        )
        logging.warning(
            f'Tendência atual: {trend}, Fator de risco: {risk_factor}'
        )
        # Ajusta volume baseado no risco
        adjusted_risk = risk_per_trade * risk_factor
        risk_per_trade = min(adjusted_risk, 0.2)
        # Obter o último sinal gerado
        last_signal = df['position'].iloc[-1]
        last_price = ticker_json['last']
        # open_orders = OpenOrders(coinpair).json()

        # Verificar ordens abertas
        # if open_orders:
        #     bot_msg('INFO', 'Existem ordens abertas. Aguardando execução.')
        #     logging.warning('Existem ordens abertas. Aguardando execução.')
        #     time.sleep(30)

        # Verificar saldo disponível
        brl_balance = balance.get('BRL', 0)
        btc_balance = balance.get('BTC', 0)

        # Estratégia de Compra
        if last_signal == SIGNAL_BUY and brl_balance > 0:
            amount_to_invest = brl_balance * risk_per_trade
            amount = amount_to_invest / last_price
            price = last_price

            # Executar compra
            resposta_compra = Buy(
                price=price,
                volume=amount,
                amount=amount,
                limited=True,
                market=coinpair,
            )
            # resposta_compra = None
            trade_type = 'Compra'
            # trade_executed = True
            bot_msg('INFO', f'Compra executada: {resposta_compra}')
            console.print(
                f':four_leaf_clover: [bold green]Compra executada:[/bold green] {resposta_compra}'
            )

        # Estratégia de Venda (Take Profit e Stop Loss)
        elif last_signal == SIGNAL_SELL and btc_balance > 0:
            amount = btc_balance * risk_per_trade
            price = last_price

            # Calcular Take Profit e Stop Loss
            take_profit = price * profitability
            stop_loss_price = price * STOP_LOSS

            # Condição de Take Profit ou Stop Loss
            if last_price >= take_profit:
                resposta_venda = Sell(
                    price=take_profit,
                    volume=amount,
                    amount=amount,
                    limited=True,
                    market=coinpair,
                )
                # resposta_venda = None
                trade_type = 'Venda (Take Profit)'
                # trade_executed = True
                bot_msg(
                    'INFO', f'Venda executada (Take Profit): {resposta_venda}'
                )
                console.print(
                    f':four_leaf_clover: [bold yellow]Venda executada (Take Profit)[/bold yellow]: {resposta_venda}'
                )
            elif last_price <= stop_loss_price:
                resposta_venda = Sell(
                    price=stop_loss_price,
                    volume=amount,
                    amount=amount,
                    limited=True,
                    market=coinpair,
                )
                # resposta_venda = None
                trade_type = 'Venda (Stop Loss)'
                # trade_executed = True
                bot_msg(
                    'INFO', f'Venda executada (Stop Loss): {resposta_venda}'
                )
                console.print(
                    f':four_leaf_clover: [bold blue]Venda executada (Stop Loss)[/bold blue]: {resposta_venda}'
                )
            else:
                bot_msg('INFO', 'Preço não atingiu limite de venda.')

        else:
            bot_msg('INFO', 'Nenhuma ação necessária no momento.')

        # Registra trade
        if trade_executed:
            trade_history.save_trade(trade_type, price, amount)

    except Exception as e:
        logger.error(
            f'Erro na execução do trade: {str(e)}',
            # exc_info=True,
        )
        print(traceback.format_exc())


def analyze_trend(df: pd.DataFrame) -> str:
    """
    Analisa tendência do mercado
    """
    last_rows = df.tail(20)
    trend_up = (last_rows['short_ma'] > last_rows['long_ma']).sum() / 20

    if trend_up > 0.7:
        return 'STRONG_UP'
    elif trend_up > 0.5:
        return 'UP'
    elif trend_up < 0.3:
        return 'STRONG_DOWN'
    elif trend_up < 0.5:
        return 'DOWN'
    return 'NEUTRAL'


def calculate_risk_factor(df: pd.DataFrame) -> float:
    """
    Calcula fator de risco baseado na volatilidade
    """
    volatility = df['close'].pct_change().std()
    atr = df['atr'].iloc[-1]

    risk_factor = 1.0
    if volatility > 0.02:  # Alta volatilidade
        risk_factor *= 0.7
    if atr > df['atr'].mean() * 1.5:  # ATR alto
        risk_factor *= 0.8

    return max(0.3, min(risk_factor, 1.0))
