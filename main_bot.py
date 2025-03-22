import signal
import sys

from rich.traceback import install

from bot.bot import TradingBot
from bot.logs.config_log import console

# Instala o traceback do rich para melhor visualização de erros
install(show_locals=True)


# Boa prática: ter um ponto de entrada principal para o seu script
# Isso facilita a leitura e a manutenção do código.
def main():
    # Classe principal do bot de trading
    # Aqui você pode adicionar outras estratégias ou configurações
    bot = TradingBot()
    # configuração para interromper o bot com Ctrl+C
    signal.signal(signal.SIGINT, bot.signal_handler)

    try:
        # Tentativa de inicialização do bot
        bot.start()

    except Exception as e:
        # Se o bot falhar, ele irá parar e imprimir uma mensagem de erro
        console.print(f'[bold red]Erro fatal: {str(e)}[/bold red]')
        bot.stop()
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
