from typing import List

from compartilhado import coinpair_options

from .models.coin_pair import CoinPair, ExchangeType


# Converter as opções do coinpair_options para CoinPair
def get_available_pairs() -> List[CoinPair]:
    options = coinpair_options()
    pairs = []
    for option in options:
        value = option['value']
        base, quote = value.split('-')
        pairs.append(
            CoinPair(base=base, quote=quote, exchange=ExchangeType.BITPRECO)
        )
    return pairs


# Parâmetros Globais
AVAILABLE_PAIRS: List[CoinPair] = get_available_pairs()

profitability = 1.05  # Margem de lucro desejada (5%)
risk_per_trade = 0.10  # Arriscar 10% do saldo disponível por operação
short_window = 5  # Período da média móvel de curto prazo
long_window = 10  # Período da média móvel de longo prazo
SIGNAL_BUY = 1  # Alterar de 2 para 1
SIGNAL_SELL = -1  # Alterar de -2 para -1
STOP_LOSS = 0.95  # Limite para stop-loss (5% abaixo do preço de compra)

# Configurações adicionais
BACKTEST_DAYS = 120
MAX_DAILY_TRADES = 100

# Parâmetros RSI e Stochastic
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30  # Limite inferior do RSI para compra
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# Quantidade de condicoes de compra e venda
CONDICOES_COMPRA = 3
CONDICOES_VENDA = 3

# Parametros de Tentativas caso a internet caia
NUMERO_MAXIMO_TENTATIVAS = 3
INTERVALO_TENTATIVAS = 5

THREAD_LOCK = False
