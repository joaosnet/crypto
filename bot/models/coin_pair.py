from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ExchangeType(str, Enum):
    BITPRECO = 'bitpreco'
    BINANCE = 'binance'
    CUSTOM = 'custom'


class CoinPair(BaseModel):
    """Modelo para representar pares de moedas em diferentes exchanges"""

    base: str  # Moeda base (ex: BTC)
    quote: str  # Moeda de cotação (ex: BRL)
    exchange: ExchangeType = ExchangeType.BITPRECO

    @property
    def bitpreco_format(self) -> str:
        """Formato BitPreco: BTC-BRL"""
        return f'{self.base}-{self.quote}'

    @property
    def bitpreco_websocket(self) -> str:
        """Formato BitPreco WebSocket: BTC_BRL"""
        return f'{self.base}_{self.quote}'

    @property
    def binance_format(self) -> str:
        """Formato Binance: BTCBRL"""
        return f'{self.base}{self.quote}'

    def get_format(self, exchange: Optional[ExchangeType] = None) -> str:
        """Retorna o formato apropriado para a exchange especificada"""
        exchange = exchange or self.exchange

        if exchange == ExchangeType.BITPRECO:
            return self.bitpreco_format
        elif exchange == ExchangeType.BINANCE:
            return self.binance_format
        return self.bitpreco_format  # formato padrão

    @classmethod
    def from_string(cls, pair_str: str, exchange: ExchangeType) -> 'CoinPair':
        """Cria um CoinPair a partir de uma string no formato da exchange"""
        if exchange == ExchangeType.BITPRECO:
            if '_' in pair_str:
                base, quote = pair_str.split('_')
            else:
                base, quote = pair_str.split('-')
        elif exchange == ExchangeType.BINANCE:
            # Assume que os últimos 3 ou 4 caracteres são a moeda de cotação
            if pair_str[-4:] in {'USDT', 'BUSD'}:
                base = pair_str[:-4]
                quote = pair_str[-4:]
            else:
                base = pair_str[:-3]
                quote = pair_str[-3:]
        else:
            raise ValueError(f'Exchange não suportada: {exchange}')

        return cls(base=base, quote=quote, exchange=exchange)
