import talib as ta
from backtesting import Strategy

from ..logs.config_log import console
from ..models.coin_pair import CoinPair
from ..parametros import (
    CONDICOES_COMPRA,
    CONDICOES_VENDA,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    SIGNAL_BUY,
    SIGNAL_SELL,
    STOCH_OVERBOUGHT,
    STOCH_OVERSOLD,
    STOP_LOSS,
    profitability,
    risk_per_trade,
)


class DaytradeStrategy(Strategy):
    """
    Estratégia de Daytrade que usa EMAs, RSI, MACD, Bollinger Bands e Stochastic
    para gerar sinais de compra/venda quando pelo menos X indicadores estiverem alinhados.

    Esta classe serve tanto para backtesting quanto para uso no bot em tempo real.
    """

    # Parâmetros da estratégia (podem ser otimizados no backtesting)
    ema_short = 5
    ema_medium = 10
    ema_long = 20
    ema_trend = 200
    rsi_period = 14
    bb_period = 20
    bb_std = 2
    macd_fastperiod = 12
    macd_slowperiod = 26
    macd_signalperiod = 9
    stoch_k_period = 14
    stoch_slowk_period = 3
    stoch_slowd_period = 3
    volume_sma_period = 20
    atr_period = 14

    def init(self):
        """Inicializa os indicadores - usado no backtesting"""
        price = self.data.Close

        # Inicializa os indicadores técnicos
        self.ema_5 = self.I(ta.EMA, price, self.ema_short)
        self.ema_10 = self.I(ta.EMA, price, self.ema_medium)
        self.ema_20 = self.I(ta.EMA, price, self.ema_long)
        self.ema_200 = self.I(ta.EMA, price, self.ema_trend)

        self.rsi = self.I(ta.RSI, price, self.rsi_period)

        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            ta.BBANDS,
            price,
            timeperiod=self.bb_period,
            nbdevup=self.bb_std,
            nbdevdn=self.bb_std,
        )

        self.macd, self.macd_signal, self.macd_hist = self.I(
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
            slowd_period=self.stoch_slowd_period,
        )

        self.volume_sma = self.I(
            ta.SMA, self.data.Volume, self.volume_sma_period
        )
        self.atr = self.I(
            ta.ATR, self.data.High, self.data.Low, price, self.atr_period
        )

    def next(self):
        """Implementação para backtesting - executa a cada nova barra"""
        if not self.position:
            # Verifica condições de compra
            if self.should_buy():
                self.buy()
            # Verifica condições de venda
            elif self.should_sell():
                self.sell()
        else:
            # Gerencia posições existentes
            if self.position.is_long and self.should_sell():
                self.position.close()
            elif self.position.is_short and self.should_buy():
                self.position.close()

    def should_buy(self):
        """Verifica se deve comprar com base nos indicadores"""
        # Sinais de compra
        ema_signal = (self.ema_5[-1] > self.ema_10[-1]) and (
            self.ema_5[-2] <= self.ema_10[-2]
        )
        macd_signal = (self.macd[-1] > self.macd_signal[-1]) and (
            self.macd[-2] <= self.macd_signal[-2]
        )
        rsi_signal = self.rsi[-1] < RSI_OVERSOLD
        bb_signal = self.data.Close[-1] <= self.bb_lower[-1]
        stoch_signal = self.stoch_k[-1] < STOCH_OVERSOLD

        # Conta quantas condições são atendidas
        buy_signals = sum([
            ema_signal,
            macd_signal,
            rsi_signal,
            bb_signal,
            stoch_signal,
        ])

        return buy_signals >= CONDICOES_COMPRA

    def should_sell(self):
        """Verifica se deve vender com base nos indicadores"""
        # Sinais de venda
        ema_signal = (self.ema_5[-1] < self.ema_10[-1]) and (
            self.ema_5[-2] >= self.ema_10[-2]
        )
        macd_signal = (self.macd[-1] < self.macd_signal[-1]) and (
            self.macd[-2] >= self.macd_signal[-2]
        )
        rsi_signal = self.rsi[-1] > RSI_OVERBOUGHT
        bb_signal = self.data.Close[-1] >= self.bb_upper[-1]
        stoch_signal = self.stoch_k[-1] > STOCH_OVERBOUGHT

        # Conta quantas condições são atendidas
        sell_signals = sum([
            ema_signal,
            macd_signal,
            rsi_signal,
            bb_signal,
            stoch_signal,
        ])

        return sell_signals >= CONDICOES_VENDA

    def analyze_signals_from_dataframe(self, df):
        """
        Analisa sinais a partir de um DataFrame para uso no trading bot em tempo real

        Retorna:
            - signal: int (-1 para venda, 0 para nada, 1 para compra)
            - trend: str (alta, baixa, neutral)
            - risk_factor: float (fator de risco para ajustar o tamanho da posição)
        """
        # Verifica os últimos valores (última linha do DataFrame)
        last_row = df.iloc[-1]

        # Identifica a tendência
        trend = 'alta' if last_row['close'] > last_row['ema_200'] else 'baixa'

        # Analisa volatilidade para ajustar o risco
        volatility = last_row['atr'] / last_row['close']
        risk_factor = max(0.5, min(1.0, 1.0 - volatility * 10))

        # Determina o sinal com base nos indicadores já calculados no DataFrame
        signal = last_row['signal']

        return signal, trend, risk_factor

    @staticmethod
    def adjust_risk(risk_factor):
        """Ajusta o fator de risco para limitar a exposição"""
        adjusted_risk = risk_per_trade * risk_factor
        return min(adjusted_risk, 0.2)

    @staticmethod
    def execute_buy(
        executed_orders, brl_balance, risk_per_trade, last_price, coin_pair
    ):
        """Executa uma ordem de compra"""
        amount_to_invest = brl_balance * risk_per_trade
        amount = amount_to_invest / float(last_price)

        # Simulação de resposta para teste
        resposta_compra = 'success'
        console.print(
            ':four_leaf_clover: [bold green]Compra executada:[/bold green] '
            + str(resposta_compra)
        )
        return resposta_compra

    @staticmethod
    def execute_sell(
        executed_orders, coin_pair, btc_balance, risk_per_trade, last_price
    ):
        """Executa uma ordem de venda com base nas condições de take profit/stop loss"""
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
            if float(last_price) >= take_profit:
                return DaytradeStrategy.execute_sell_trade(
                    coin_pair, amount, last_price, 'SELL (Take Profit)'
                )
            elif float(last_price) <= stop_loss_price:
                return DaytradeStrategy.execute_sell_trade(
                    coin_pair, amount, stop_loss_price, 'SELL (Stop Loss)'
                )
            else:
                console.print(
                    ':hourglass: [bold yellow]Preço não atingiu '
                    + 'limite de venda.[/bold yellow]'
                )
                return None
        return None

    @staticmethod
    def execute_sell_trade(coin_pair, amount, price, trade_type):
        """Executa uma ordem de venda"""
        # Simulação de resposta para teste
        resposta_venda = 'success'
        console.print(
            f':four_leaf_clover: [bold yellow]{trade_type} '
            + 'executada:[/bold yellow] '
            + str(resposta_venda)
        )
        return resposta_venda
