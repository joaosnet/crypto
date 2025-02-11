import logging

from rich import console
from rich.logging import RichHandler

console = console.Console()

# Configuração do logger sem as requisições HTTP
FORMAT = '%(message)s'
logging.basicConfig(
    level=logging.ERROR,
    format=FORMAT,
    datefmt='[%X]',
    handlers=[RichHandler()],
)
logger = logging.getLogger(__name__)
