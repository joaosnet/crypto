from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def calcular_trades_crypto(
    capital_inicial,
    risco_por_trade,
    objetivo_por_trade,
    num_trades_lucro,
    num_trades_prejuizo,
):
    """Calcula o resultado dos trades em criptomoedas."""
    perda_total = num_trades_prejuizo * risco_por_trade
    lucro_total = num_trades_lucro * objetivo_por_trade
    lucro_liquido = lucro_total - perda_total
    capital_final = capital_inicial + lucro_liquido
    return lucro_liquido, capital_final


def get_risco_por_trade_crypto(capital_inicial, porcentagem_risco=0.08):
    """Calcula o risco por trade com base
    em uma porcentagem do capital inicial."""
    risco_por_trade = capital_inicial * porcentagem_risco
    return risco_por_trade


def get_objetivo_por_trade_crypto(risco_por_trade, multiplicador_objetivo=2):
    """Calcula o objetivo de lucro por trade,
    geralmente um múltiplo do risco."""
    objetivo_por_trade = risco_por_trade * multiplicador_objetivo
    return objetivo_por_trade


def get_num_trades_lucro(trades_por_mes, taxa_acerto=0.5):
    """Calcula o número de trades com lucro
    com base na taxa de acerto esperada."""
    num_trades_lucro = int(trades_por_mes * taxa_acerto)
    return num_trades_lucro


def get_num_trades_prejuizo(trades_por_mes, num_trades_lucro):
    """Calcula o número de trades com prejuízo,
    dado o total de trades e os trades com lucro."""
    num_trades_prejuizo = trades_por_mes - num_trades_lucro
    return num_trades_prejuizo


def main():  # noqa: PLR0914
    """Função principal que executa a simulação
    de day trading em criptomoedas com Rich output."""

    console = Console()

    # Configuração Inicial
    capital_inicial_crypto = 500  # em reais ou equivalente em cripto
    trades_por_mes = 20
    porcentagem_risco = 0.08  # 8% de risco por trade
    multiplicador_objetivo = 2  # Objetivo é 2x o risco
    taxa_acerto = (
        0.5  # Taxa de acerto de 50% (10 lucros e 10 prejuízos em 20 trades)
    )
    multiplicadores = [1, 2, 3, 4]
    capital_atual_crypto = capital_inicial_crypto

    console.rule(
        '[bold blue]Simulação de Day Trading em Criptomoedas[/bold blue]'
    )

    for multiplicador in multiplicadores:
        risco_por_trade_crypto = (
            get_risco_por_trade_crypto(capital_atual_crypto, porcentagem_risco)
            * multiplicador
        )
        objetivo_por_trade_crypto = get_objetivo_por_trade_crypto(
            risco_por_trade_crypto, multiplicador_objetivo
        )
        num_trades_lucro_crypto = get_num_trades_lucro(
            trades_por_mes, taxa_acerto
        )
        num_trades_prejuizo_crypto = get_num_trades_prejuizo(
            trades_por_mes, num_trades_lucro_crypto
        )

        lucro_liquido_crypto, capital_final_crypto = calcular_trades_crypto(
            capital_atual_crypto,
            risco_por_trade_crypto,
            objetivo_por_trade_crypto,
            num_trades_lucro_crypto,
            num_trades_prejuizo_crypto,
        )

        title = f"""Simulação com [bold magenta]{multiplicador}x
        [/bold magenta] (Multiplicador de Risco/Objetivo)"""
        table = Table(
            title=title, title_style='bold cyan', header_style='bold blue'
        )
        table.add_column('Métrica', style='dim', width=15)
        table.add_column('Valor', justify='right')

        table.add_row('Capital Inicial', f'R${capital_atual_crypto:.2f}')
        table.add_row('Risco por Trade', f'R${risco_por_trade_crypto:.2f}')
        table.add_row(
            'Objetivo por Trade', f'R${objetivo_por_trade_crypto:.2f}'
        )
        table.add_row('Trades com Lucro', f'{num_trades_lucro_crypto}')
        table.add_row('Trades com Prejuízo', f'{num_trades_prejuizo_crypto}')
        table.add_row(
            '[bold green]Lucro Líquido Mensal[/bold green]',
            f'[bold green]R${lucro_liquido_crypto:.2f}[/bold green]',
        )
        table.add_row(
            '[bold cyan]Capital Final[/bold cyan]',
            f'[bold cyan]R${capital_final_crypto:.2f}[/bold cyan]',
        )

        console.print(Panel(table, border_style='blue', padding=(1, 2)))
        capital_atual_crypto = capital_final_crypto

    console.print(
        Panel(
            '[bold green]Simulação Concluída![/bold green]',
            border_style='green',
            padding=(1, 2),
        )
    )
    console.print(
        '[italic dim]Lembre-se: Esta é apenas uma simulação e '
        + 'não garante lucros no mercado real.[/italic dim]'
    )


if __name__ == '__main__':
    main()
