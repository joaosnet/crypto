# estrategias.py
import logging

import numpy as np
import pandas as pd

try:
    from api_binance import get_klines
    from api_bitpreco import (
        Balance,
        Buy,
        OpenOrders,
        Sell,
        Ticker,
        get_coinpair,
    )
except ImportError:
    from crypto.api_binance import get_klines
    from crypto.api_bitpreco import (
        Balance,
        Buy,
        OpenOrders,
        Sell,
        Ticker,
        get_coinpair,
    )

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s , %(levelname)s , %(message)s',
    filename='log.csv',
    encoding='utf-8',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Parâmetros Globais
coinpair = get_coinpair()
profitability = 1.05  # Margem de lucro desejada (5%)
risk_per_trade = 0.10  # Arriscar 10% do saldo disponível por operação
short_window = 7  # Período da média móvel de curto prazo
long_window = 21  # Período da média móvel de longo prazo
SIGNAL_BUY = 2
SIGNAL_SELL = -2


# Função para obter dados históricos de preços da Binance
def get_price_history(symbol='BTCBRL', interval='1h', limit=100):
    """
    Obtém o histórico de preços da Binance para o símbolo especificado.
    """
    try:
        df = get_klines(symbol=symbol, interval=interval, limit=limit)
        df['timestamp'] = pd.to_datetime(df['Kline open time'])
        df = df.rename(columns={'Close price': 'close'})
        return df[['timestamp', 'close']]
    except Exception as e:
        logger.error(f'Erro ao obter histórico de preços: {e}')
        return None


# Função para calcular indicadores técnicos
def calculate_indicators(df):
    """
    Calcula as médias móveis de curto e longo prazo.
    """
    df = df.copy()
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    return df


# Função para gerar sinais de compra/venda
def generate_signals(df):
    """
    Gera sinais de compra e venda baseados no cruzamento de médias móveis.
    """
    df = df.copy()
    df['signal'] = 0
    df.loc[short_window:, 'signal'] = np.where(
        df['short_ma'][short_window:] > df['long_ma'][short_window:], 1, -1
    )
    df['position'] = df['signal'].diff()
    return df


# Função para executar a estratégia de negociação
def execute_trade(ticker_json, balance):
    """
    Executa as operações de compra ou venda com base nos sinais gerados.
    """
    try:
        if coinpair == 'BTC-BRL':
            # Obter dados históricos e calcular indicadores
            df = get_price_history()
            if df is None or df.empty:
                logger.warning('Dados históricos não disponíveis.')
                return

            df = calculate_indicators(df)
            df = generate_signals(df)

            # Obter o último sinal gerado
            last_signal = df['position'].iloc[-1]
            logger.info(f'Último sinal gerado: {last_signal}')
            last_price = ticker_json['last']
            open_orders = OpenOrders(coinpair).json()

            # Verificar se há ordens abertas
            if open_orders:
                logger.info('Existem ordens abertas. Aguardando execução.')
                return

            # Verificar saldo disponível
            brl_balance = balance.get('BRL', 0)
            btc_balance = balance.get('BTC', 0)

            # Estratégia de Compra
            if last_signal == SIGNAL_BUY and brl_balance > 0:
                amount_to_invest = brl_balance * risk_per_trade
                amount = amount_to_invest / last_price
                limited = True
                volume = amount * last_price
                price = last_price

                # Executar compra
                # resposta_compra = Buy(
                #     price, volume, amount, limited, market=coinpair
                # )
                # logger.info(f'Compra executada: {resposta_compra}')
                logger.info('Compra executada.')

            # Estratégia de Venda
            elif last_signal == SIGNAL_SELL and btc_balance > 0:
                amount = btc_balance * risk_per_trade
                limited = True
                volume = amount * last_price
                price = last_price

                # Executar venda
                # resposta_venda = Sell(
                #     price, volume, amount, limited, market=coinpair
                # )
                # logger.info(f'Venda executada: {resposta_venda}')
                logger.info('Venda executada.')

            else:
                logger.info('Nenhuma ação necessária no momento.')

    except Exception as e:
        logger.error(f'Erro ao executar a negociação: {e}')


# Exemplo de uso
if __name__ == '__main__':
    # Supondo que temos funções para obter o ticker e o balance
    ticker_json = Ticker(market=coinpair).json()  # Exemplo de preço atual
    balance = Balance().json()  # Exemplo de saldo

    execute_trade(ticker_json, balance)
