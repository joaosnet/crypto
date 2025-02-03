import duckdb

try:
    from segredos import CAMINHO
except ImportError:
    from crypto.segredos import CAMINHO

COINPAIR_FILE = CAMINHO + '/coinpair.json'

INTERVAL_FILE = CAMINHO + '/interval.json'


DEFAULT_COINPAIR = 'BTC-BRL'
DEFAULT_INTERVAL = 30


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
