import numpy as np
import pandas as pd

from bot.parametros import (
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    SIGNAL_BUY,
    SIGNAL_SELL,
    STOCH_OVERBOUGHT,
    STOCH_OVERSOLD,
)
from db.duckdb_csv import save_to_csv_duckdb
from segredos import CAMINHO


def generate_signals(df, symbol: str = 'BTC_BRL'):
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

    # Garantir timezone UTC antes de salvar
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

    # Salvar usando função modificada que preserva timezone
    save_to_csv_duckdb(
        df,
        CAMINHO + f'/{symbol}_bitpreco.csv',
    )

    return df
