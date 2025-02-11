from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Annotated

# Tipo personalizado para timestamp em UTC
UTCTimestamp = Annotated[
    datetime,
    Field(
        default_factory=lambda: datetime.now().astimezone(),
        description='Timestamp in UTC timezone',
    ),
]


class PriceData(BaseModel):
    timestamp: UTCTimestamp
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @model_validator(mode='before')
    def ensure_tz_aware(cls, data):
        if isinstance(data, dict) and 'timestamp' in data:
            ts = data['timestamp']
            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    data['timestamp'] = ts.astimezone()
                else:
                    # Garantir que está em UTC
                    data['timestamp'] = ts.astimezone(timezone.utc)
        return data


class KlineData(PriceData):
    kline_close_time: UTCTimestamp
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal


class BitPrecoHistory(BaseModel):
    data: List[PriceData]
    symbol: str = 'BTC_BRL'
    resolution: str = '1'


class BinanceKlines(BaseModel):
    data: List[KlineData]
    symbol: str = 'BTCBRL'
    interval: str = '1m'


class TechnicalIndicators(BaseModel):
    ema_5: Decimal | None = None
    ema_10: Decimal | None = None
    ema_20: Decimal | None = None
    ema_200: Decimal | None = None
    macd: Decimal | None = None
    macd_signal: Decimal | None = None
    macd_hist: Decimal | None = None
    rsi: Decimal | None = None
    bb_upper: Decimal | None = None
    bb_middle: Decimal | None = None
    bb_lower: Decimal | None = None
    stoch_k: Decimal | None = None
    stoch_d: Decimal | None = None
    volume_sma: Decimal | None = None
    atr: Decimal | None = None

    @model_validator(mode='before')
    def convert_nan_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, Decimal) and (
                    value.is_nan() or value.is_infinite()
                ):
                    data[key] = None
        return data


class SignalData(PriceData, TechnicalIndicators):
    signal: int = Field(default=0, ge=-1, le=1)  # garante que seja -1, 0 ou 1
    position: int = Field(
        default=0, ge=-1, le=1
    )  # garante que seja -1, 0 ou 1
    ema_cross: int = Field(default=0, ge=-1, le=1)
    macd_cross: int = Field(default=0, ge=-1, le=1)
    trend: str = 'neutral'


class BitPrecoSignals(BaseModel):
    data: List[SignalData]
    symbol: str = 'BTC_BRL'
