import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para poder importar os módulos do projeto
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from datetime import datetime, timedelta, timezone

import pandas as pd
from backtesting import Backtest
from rich.traceback import install

from bot.estrategias.TripleIndicatoStrategy import TripleIndicator
from bot.logs.config_log import console
from bot.parametros import BACKTEST_DAYS
from db.duckdb_csv import load_csv_in_dataframe

# Importando funções e classes relevantes do projeto
install(show_locals=True)


def run_backtest(data, strategy_class, **strategy_params):
    bt = Backtest(
        data,
        strategy_class,
        cash=10000000,
        commission=0.002,  # 0.2% por operação
        exclusive_orders=True,
        **strategy_params,
    )

    stats = bt.run()
    console.print(f'Testando {strategy_class.__name__}')
    console.print(f'Retorno Total: {stats['Return [%]']:.2f}%')
    console.print(f'Retorno Anualizado: {stats['Return (Ann.) [%]']:.2f}%')
    console.print(f'Máximo Drawdown: {stats['Max. Drawdown [%]']:.2f}%')
    console.print(f'Rácio de Sharpe: {stats['Sharpe Ratio']:.2f}')
    console.print(f'Número de Trades: {stats['# Trades']}')
    console.print(f'Win Rate: {stats['Win Rate [%]']:.2f}%')
    console.print(f'Profit Factor: {stats['Profit Factor']:.2f}')
    console.print('-' * 50)

    return bt, stats


# Função para carregar dados históricos
def load_data(csv_path=None):
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=BACKTEST_DAYS)
    df = load_csv_in_dataframe(
        csv_path,
        start_date=start_date,
        end_date=end_date,
    )

    # Assegure-se de que os nomes das colunas estão no formato esperado
    column_map = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
    }

    df = df.rename(
        columns={k: v for k, v in column_map.items() if k in df.columns}
    )

    # Converter a coluna de timestamp para índice do tipo DateTimeIndex
    if 'timestamp' in df.columns:
        df.set_index('timestamp', inplace=True)
        df.index = pd.to_datetime(df.index)

    return df


def run_optimization(bt, strategy_class):
    """Executa a otimização com tratamento de erros."""
    try:
        # Adapta os parâmetros conforme a estratégia utilizada
        if strategy_class == TripleIndicator:
            stats = optimize_triple_indicator(bt)
        else:
            console.print(
                f'[yellow]Estratégia {strategy_class.__name__} '
                + 'não suporta otimização.[/yellow]'
            )
            return None

        console.print('Parâmetros ótimos:', stats._strategy)
        return stats
    except (TypeError, ValueError, MemoryError) as e:
        console.print(f'[bold red]Erro durante otimização: {e}[/bold red]')
        console.print('Continuando sem otimização...')
        return None


def optimize_triple_indicator(bt):
    """Otimiza os parâmetros para a estratégia TripleIndicator"""
    return bt.optimize(
        short_sma=range(5, 15, 5),
        long_sma=range(20, 60, 20),
        indicators_validation=[1, 2, 3, 4, 5, 6],
        rsi_oversold=range(20, 40, 10),
        rsi_overbought=range(60, 80, 10),
        # Mantém fixos os parâmetros mais pesados para otimização
        rsi=range(14, 20, 2),
        macd_fastperiod=range(5, 15, 5),
        macd_slowperiod=range(20, 30, 5),
        macd_signalperiod=range(9, 15, 2),
        stoch_k_period=range(3, 5, 1),
        stoch_d_period=range(3, 5, 1),
        stoch_slowk_period=range(3, 5, 1),
        volume_sma_period=range(10, 30, 5),
        atr_period=range(14, 20, 2),
        maximize='Sharpe Ratio',
        method='sambo',
        max_tries=100,
    )


def run_multiple_strategies(data):
    """Executa o backtesting para diferentes
    estratégias e compara os resultados"""
    strategies = [TripleIndicator]

    best_stats = None
    best_bt = None
    best_strategy = None
    best_sharpe = -float('inf')

    for strategy in strategies:
        console.print(f'[bold blue]Testando {strategy.__name__}[/bold blue]')
        bt, stats = run_backtest(data, strategy)

        # Verificar se esta estratégia é melhor que a anterior
        if stats['Sharpe Ratio'] > best_sharpe:
            best_stats = stats
            best_bt = bt
            best_strategy = strategy
            best_sharpe = stats['Sharpe Ratio']

        # Salvar gráfico individual da estratégia
        bt.plot(
            filename=f'{strategy.__name__}.html',
            open_browser=False,
            resample='1h',
        )

        # Otimizar a estratégia
        opt_stats = run_optimization(bt, strategy)
        if opt_stats is not None:
            bt.plot(
                filename=f'{strategy.__name__}_Optimized.html',
                open_browser=False,
                resample='1h',
            )
            # Verificar se a versão otimizada é melhor
            if opt_stats['Sharpe Ratio'] > best_sharpe:
                best_stats = opt_stats
                best_bt = bt
                best_strategy = strategy
                best_sharpe = opt_stats['Sharpe Ratio']

    # Exibir a melhor estratégia encontrada
    if best_strategy is not None:
        console.print(
            '[bold green]Melhor estratégia: '
            + f'{best_strategy.__name__}[/bold green]'
        )
        console.print(f'Sharpe Ratio: {best_sharpe:.2f}')
        console.print(f'Retorno: {best_stats['Return [%]']:.2f}%')

        # Abrir o gráfico da melhor estratégia
        best_bt.plot(open_browser=True)
    else:
        console.print(
            '[bold red]Nenhuma estratégia com Sharpe '
            + 'Ratio válido foi encontrada.[/bold red]'
        )

    return best_bt, best_stats, best_strategy


if __name__ == '__main__':
    # Tente buscar seus dados primeiro
    data_path = (
        Path(__file__).resolve().parent.parent.parent
        / 'db'
        / 'BTC_BRL_bitpreco.csv'
    )
    if data_path.exists():
        data = load_data(csv_path=data_path)
        console.print(f'Dados carregados: {len(data)} registros')

        # Executar backtesting comparando múltiplas estratégias
        best_bt, best_stats, best_strategy = run_multiple_strategies(data)
    else:
        console.print(
            '[bold red]Arquivo de dados não'
            + f' encontrado: {data_path}[/bold red]'
        )
