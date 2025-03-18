import talib as ta
from backtesting import Strategy


class TripleIndicator(Strategy):
    """
    Estratégia usando 4 EMA's, RSI e MACD, ATR, Stochastic e  Volume Medio
    gera sinal de compra ou venda se 3 indicadores estiverem alinhados
    e usa o volume com validador de tendencia.
    """

    short_sma = 5
    long_sma = 31
    sma_200 = 200
    rsi = 17
    rsi_oversold = 28
    rsi_overbought = 69
    macd_fastperiod = 7
    macd_slowperiod = 22
    macd_signalperiod = 12
    stoch_k_period = 4
    stoch_d_period = 3
    stoch_slowk_period = 3
    volume_sma_period = 21
    atr_period = 16
    indicators_validation = 4

    def init(self):
        price = self.data.Close
        self.sma_fast = self.I(ta.SMA, price, self.short_sma)
        self.sma_slow = self.I(ta.SMA, price, self.long_sma)
        self.sma_200 = self.I(ta.SMA, price, self.sma_200)
        self.rsi = self.I(ta.RSI, price, self.rsi)
        self.macd, self.macd_signal, _macd_histogram = self.I(
            ta.MACD,
            price,
            fastperiod=self.macd_fastperiod,
            slowperiod=self.macd_slowperiod,
            signalperiod=self.macd_signalperiod,
        )
        self.stoch_k, self.stoch_d = self.I(
            ta.STOCH,
            self.data.High,
            self.data.Low,
            price,
            fastk_period=self.stoch_k_period,
            slowk_period=self.stoch_slowk_period,
            slowd_period=self.stoch_d_period,
        )
        self.volume_sma = self.I(
            ta.SMA, self.data.Volume, self.volume_sma_period
        )
        self.atr = self.I(
            ta.ATR,
            self.data.High,
            self.data.Low,
            price,
            timeperiod=self.atr_period,
        )

    def next(self):
        # Condições de compra - Relaxadas para gerar mais trades
        trend_up = self.sma_fast[-1] > self.sma_slow[-1]
        rsi_oversold = self.rsi[-1] < self.rsi_oversold
        macd_signal = self.macd[-1] > self.macd_signal[-1]
        stoch_k_cross = self.stoch_k[-1] > self.stoch_d[-1]
        volume_increase = self.data.Volume[-1] > self.volume_sma[-1]

        # Condições de venda - Relaxadas para gerar mais trades
        trend_down = self.sma_fast[-1] < self.sma_slow[-1]
        rsi_overbought = self.rsi[-1] > self.rsi_overbought
        macd_signal_down = self.macd[-1] < self.macd_signal[-1]
        stoch_d_cross = self.stoch_k[-1] < self.stoch_d[-1]

        # Regras de entrada e saída modificadas para gerar mais sinais
        if not self.position:
            # Compra se pelo menos 2 indicadores estiverem alinhados
            buy_signals = sum([
                trend_up,
                rsi_oversold,
                macd_signal,
                stoch_k_cross,
            ])
            if buy_signals >= self.indicators_validation and volume_increase:
                self.buy()

            # Venda se pelo menos 2 indicadores estiverem alinhados
            sell_signals = sum([
                trend_down,
                rsi_overbought,
                macd_signal_down,
                stoch_d_cross,
            ])
            if sell_signals >= self.indicators_validation and volume_increase:
                self.sell()
        # Fechar posições existentes quando o cenário mudar
        elif self.position.is_long:
            if trend_down and (rsi_overbought or macd_signal_down):
                self.position.close()
        elif self.position.is_short:
            if trend_up and (rsi_oversold or macd_signal):
                self.position.close()
