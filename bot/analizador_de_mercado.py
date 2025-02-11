import pandas as pd


def analyze_trend(df: pd.DataFrame) -> str:
    """
    Analisa tendência do mercado
    """
    STRONG_UP_THRESHOLD = 0.7
    UP_THRESHOLD = 0.5
    STRONG_DOWN_THRESHOLD = 0.3
    DOWN_THRESHOLD = 0.5

    # Ensure numeric dtypes and handle NaN values properly
    df = df.copy()
    df['ema_5'] = pd.to_numeric(df['ema_5'], errors='coerce')
    df['ema_10'] = pd.to_numeric(df['ema_10'], errors='coerce')

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
    # Ensure numeric dtypes
    df = df.copy()
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['atr'] = pd.to_numeric(df['atr'], errors='coerce')

    # Calculate volatility using numeric values
    volatility = df['close'].pct_change().std()
    atr = df['atr'].iloc[-1]
    atr_mean = df['atr'].mean()

    risk_factor = 1.0
    high_volatility = 0.02
    if volatility > high_volatility:  # Alta volatilidade
        risk_factor *= 0.7
    if atr > atr_mean * 1.5:  # ATR alto
        risk_factor *= 0.8

    return max(0.3, min(risk_factor, 1.0))


def analyze_market(df: pd.DataFrame) -> tuple[str, float]:
    """
    Analisa o mercado e retorna tendência e fator de risco
    """
    # Convert DataFrame columns to appropriate types before analysis
    df = df.infer_objects(copy=False)

    trend = analyze_trend(df)
    risk_factor = calculate_risk_factor(df)
    return trend, risk_factor
