import json

import duckdb

from bot.models.coin_pair import CoinPair, ExchangeType
from segredos import CAMINHO

COINPAIR_FILE = CAMINHO + '/coinpair.json'
INTERVAL_FILE = CAMINHO + '/interval.json'

DEFAULT_COINPAIR = 'BTC-BRL'
DEFAULT_INTERVAL = 30


def coinpair_options():
    try:
        from bot.apis.api_bitpreco import Ticker  # noqa: PLC0415
    except ImportError:
        from bot.apis.api_bitpreco import Ticker  # noqa: PLC0415

    response = Ticker().json()
    # excluindo a linha 'success': True, pois não é um mercado
    response.pop('success', None)
    markets = sorted(response.keys())
    options = []
    for market in markets:
        # Convert market name from lowercase to uppercase with hyphen
        value = market.upper().replace('_', '-')
        # Get coin name (everything before -BRL)
        coin = value.split('-')[0]
        # Create formatted option dict
        option = {'value': value, 'label': f'{coin} para Real'}
        options.append(option)
    return options


def get_str_coinpair() -> str:
    try:
        query = f"SELECT coinpair FROM '{COINPAIR_FILE}'"
        result = duckdb.query(query).fetchone()
        return result[0] if result and result[0] else DEFAULT_COINPAIR
    except Exception as e:
        print(f'Erro ao ler {COINPAIR_FILE} com DuckDB: {e}')
        return DEFAULT_COINPAIR


def get_coinpair() -> CoinPair:
    try:
        query = f"SELECT coinpair FROM '{COINPAIR_FILE}'"
        result = duckdb.query(query).fetchone()
        coinpair_str = result[0] if result and result[0] else DEFAULT_COINPAIR

        # Converter string para CoinPair
        base, quote = coinpair_str.split('-')
        return CoinPair(base=base, quote=quote, exchange=ExchangeType.BITPRECO)
    except Exception as e:
        print(f'Erro ao ler {COINPAIR_FILE} com DuckDB: {e}')
        base, quote = DEFAULT_COINPAIR.split('-')
        return CoinPair(base=base, quote=quote, exchange=ExchangeType.BITPRECO)


def set_coinpair(coinpair):
    try:
        # Verificar se o coinpair está nas opções disponíveis
        options = coinpair_options()
        valid_pairs = [opt['value'] for opt in options]

        if coinpair not in valid_pairs:
            print(
                f'Par de moedas inválido: {coinpair}.'
                + f' Opções válidas: {valid_pairs}'
            )
            return False

        data = {'coinpair': coinpair}
        with open(COINPAIR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f'Erro ao atualizar {COINPAIR_FILE}: {e}')
        return False


def get_interval():
    try:
        # Consulta SQL para extrair o interval do arquivo JSON
        query = f"SELECT interval FROM '{INTERVAL_FILE}'"
        result = duckdb.query(query).fetchone()
        if (
            result
            and result[0]
            and isinstance(result[0], int)
            and result[0] > 0
        ):
            return result[0]
        else:
            return DEFAULT_INTERVAL
    except Exception as e:
        print(f'Erro ao ler {INTERVAL_FILE} com DuckDB: {e}')
        return DEFAULT_INTERVAL


if __name__ == '__main__':
    from rich import print

    print(get_coinpair())
    print(get_interval())
