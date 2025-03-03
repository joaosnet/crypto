from db.duckdb_csv import save_to_csv_duckdb
from segredos import CAMINHO

from ..analizador_de_mercado import analyze_market
from ..indicadores.calcular_indicadores import calculate_indicators
from ..indicadores.gerar_sinais_compra_venda import generate_signals

# from memory_profiler import profile
from ..indicadores.historico_precos import get_price_history
from ..logs.config_log import console
from ..models.coin_pair import CoinPair
from ..parametros import (
    SIGNAL_BUY,
    SIGNAL_SELL,
    STOP_LOSS,
    profitability,
    risk_per_trade,
)
from ..validador_trade import validate_trade_conditions


# Função para executar a estratégia de negociação com controle de risco
# @profile
def execute_trade(  # noqa: PLR0913, PLR0917
    progress, task, coin_pair: CoinPair, ticker_json, balance, executed_orders
):
    """
    Executa operações com melhor gerenciamento de risco
    """
    try:
        current_price = float(ticker_json['last'])
        progress.update(
            task,
            description=f'Preço atual: {current_price}',
            advance=10,
        )
        if not validate_trade_conditions(
            current_price, balance, executed_orders
        ):
            return
        progress.update(
            task,
            description='Condições de trade validadas',
            advance=10,
        )

        # Modificar esta linha para usar coin_pair diretamente
        df = get_price_history(progress, task, coin_pair=coin_pair)
        progress.update(
            task,
            description='Histórico de preços carregado',
            advance=10,
        )
        if df is None or df.empty:
            console.print('Dados históricos não disponíveis')
            return

        df = calculate_indicators(df)
        progress.update(
            task,
            description='Indicadores calculados',
            advance=10,
        )
        df = generate_signals(df)
        progress.update(
            task,
            description='Sinais de compra e venda gerados',
            advance=10,
        )

        trend, risk_factor = analyze_market(df)
        # Limpar o console antes do próximo print
        console.clear()
        console.print(
            ':chart_with_upwards_trend: [bold cyan]'
            + f'Tendência atual:[/bold cyan] {trend}, '
            f'[bold cyan]Fator de risco:[/bold cyan] {risk_factor}'
        )

        risk_per_trade = adjust_risk(risk_factor)
        last_positon = df['position'].iloc[-1]
        last_signal = df['signal'].iloc[-1]
        last_price = ticker_json['last']

        brl_balance = balance.get('BRL', 0)
        btc_balance = balance.get('BTC', 0)
        # last_signal = -1
        if brl_balance > 0 and last_positon == 0 and last_signal == SIGNAL_BUY:
            execute_buy(
                executed_orders,
                brl_balance,
                risk_per_trade,
                last_price,
                coin_pair,
            )
            df.iloc[-1, df.columns.get_loc('position')] = SIGNAL_BUY
        elif (
            btc_balance > 0
            and last_positon == SIGNAL_BUY
            and last_signal == SIGNAL_SELL
        ):
            execute_sell(
                executed_orders,
                coin_pair,
                btc_balance,
                risk_per_trade,
                last_price,
            )
            df.iloc[-1, df.columns.get_loc('position')] = 0
        else:
            console.print(
                ':hourglass: [bold yellow]Nenhuma ação necessária '
                + 'no momento.[/bold yellow]'
            )
        # Validar sinais
        assert df['position'].isin([SIGNAL_BUY, 0, SIGNAL_SELL]).all(), (
            'Valores de posição inválidos'
        )
        # Salvar usando função modificada que preserva timezone
        save_to_csv_duckdb(
            df,
            CAMINHO
            + f'/{coin_pair.bitpreco_websocket}_{coin_pair.exchange.value}'
            + '.csv',
            mode='append',
        )

    except Exception as e:
        console.print(f'Erro na execução do trade: {str(e)}')
        console.print_exception()


def adjust_risk(risk_factor):
    adjusted_risk = risk_per_trade * risk_factor
    return min(adjusted_risk, 0.2)


def execute_buy(
    executed_orders,
    brl_balance,
    risk_per_trade,
    last_price,
    coin_pair: CoinPair,
):
    amount_to_invest = brl_balance * risk_per_trade
    amount = amount_to_invest / last_price  # noqa: F841

    # resposta_compra = Buy(
    #     price=price,
    #     volume=amount,
    #     amount=amount,
    #     limited=True,
    #     market=coin_pair.bitpreco_format,
    # )
    resposta_compra = 'success'
    console.print(
        ':four_leaf_clover: [bold green]Compra executada:[/bold green] '
        + str(resposta_compra)
    )


def execute_sell(
    executed_orders,
    coin_pair: CoinPair,
    btc_balance,
    risk_per_trade,
    last_price,
):
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
        if last_price >= take_profit:
            execute_sell_trade(
                coin_pair, amount, last_price, 'SELL (Take Profit)'
            )
        elif last_price <= stop_loss_price:
            execute_sell_trade(
                coin_pair, amount, stop_loss_price, 'SELL (Stop Loss)'
            )
        else:
            console.print(
                ':hourglass: [bold yellow]Preço não atingiu '
                + 'limite de venda.[/bold yellow]'
            )


def execute_sell_trade(coin_pair: CoinPair, amount, price, trade_type):
    # resposta_venda = Sell(
    #     price=price,
    #     volume=amount,
    #     amount=amount,
    #     limited=True,
    #     market=coin_pair.bitpreco_format,
    # )
    resposta_venda = 'success'
    console.print(
        f':four_leaf_clover: [bold yellow]{trade_type} '
        + 'executada:[/bold yellow] '
        + str(resposta_venda)
    )
