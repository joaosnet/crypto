import json
from datetime import datetime
from typing import Dict, Optional

from .logs.config_log import console
from .parametros import (
    MAX_DAILY_TRADES,
)


def validate_trade_conditions(
    price: float,
    balance: Dict,
    trade_history: json,
    last_price: Optional[float] = None,
) -> bool:
    """
    Valida condições para execução de trades
    """
    # Verifica número máximo de trades diários
    trades_list = (
        trade_history
        if isinstance(trade_history, list)
        else trade_history.trades
    )

    today_trades = [
        t
        for t in trades_list
        if datetime.strptime(t['time_stamp'], '%Y-%m-%d %H:%M:%S').date()
        == datetime.now().date()
    ]

    if len(today_trades) >= MAX_DAILY_TRADES:
        console.print(
            ':warning: [bold red]Número máximo de trades'
            + ' diários atingido[/bold red]'
        )
        return False

    # Validação de volatilidade extrema
    volatilidade = 0.1
    if (
        last_price is not None
        and abs((price - last_price) / last_price) > volatilidade
    ):
        console.print(
            ':warning: [bold red]Volatilidade muito alta - '
            + 'trade cancelado[/bold red]'
        )
        return False

    return True
