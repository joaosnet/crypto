import talib as ta


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
