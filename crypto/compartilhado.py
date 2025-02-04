import json

import duckdb

try:
    from segredos import CAMINHO
except ImportError:
    from crypto.segredos import CAMINHO

COINPAIR_FILE = CAMINHO + '/coinpair.json'

INTERVAL_FILE = CAMINHO + '/interval.json'


DEFAULT_COINPAIR = 'BTC-BRL'
DEFAULT_INTERVAL = 30


def coinpair_options():
    try:
        from api_bitpreco import Ticker  # noqa: PLC0415
    except ImportError:
        from crypto.api_bitpreco import Ticker  # noqa: PLC0415

    response = Ticker().json()
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


def get_coinpair():
    try:
        # Consulta SQL para extrair o coinpair do arquivo JSON
        query = f"SELECT coinpair FROM '{COINPAIR_FILE}'"
        result = duckdb.query(query).fetchone()
        if result and result[0]:
            return result[0]
        else:
            return DEFAULT_COINPAIR
    except Exception as e:
        print(f'Erro ao ler {COINPAIR_FILE} com DuckDB: {e}')
        return DEFAULT_COINPAIR


def set_coinpair(coinpair):
    try:
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
