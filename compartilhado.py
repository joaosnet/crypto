import json
from typing import Union

import duckdb

from bot.models.coin_pair import CoinPair, ExchangeType
from segredos import CAMINHO

COINPAIR_FILE = CAMINHO + '/coinpair.json'
INTERVAL_FILE = CAMINHO + '/interval.json'

DEFAULT_COINPAIR = 'BTC-BRL'
DEFAULT_INTERVAL = 30


# Para criar as opções de coinpair, é necessário importar a API BitPreço
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


def get_str_coinpairs() -> list[str]:
    try:
        query = f"SELECT coinpair FROM '{COINPAIR_FILE}'"
        result = duckdb.query(query).fetchone()
        if result and result[0]:
            if isinstance(result[0], str):
                return [result[0]]
            return result[0]
        return [DEFAULT_COINPAIR]
    except Exception as e:
        print(f'Erro ao ler {COINPAIR_FILE} com DuckDB: {e}')
        return [DEFAULT_COINPAIR]


def get_str_coinpair() -> str:
    return get_str_coinpairs()[0]


def get_coinpairs() -> list[CoinPair]:
    coinpairs = get_str_coinpairs()
    result = []
    for pair in coinpairs:
        base, quote = pair.split('-')
        result.append(
            CoinPair(base=base, quote=quote, exchange=ExchangeType.BITPRECO)
        )
    return result


def get_coinpair() -> CoinPair:
    return get_coinpairs()[0]


def set_coinpairs(coinpairs: Union[str, list[str]]) -> bool:
    try:
        # Converter string única para lista
        if isinstance(coinpairs, str):
            coinpairs = [coinpairs]

        # Verificar se os coinpairs estão nas opções disponíveis
        options = coinpair_options()
        valid_pairs = [opt['value'] for opt in options]

        # Verificar se todos os pares são válidos
        for pair in coinpairs:
            if pair not in valid_pairs:
                print(
                    f'Par de moedas inválido: {pair}.'
                    + f' Opções válidas: {valid_pairs}'
                )
                return False

        data = {'coinpair': coinpairs}
        with open(COINPAIR_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f'Erro ao atualizar {COINPAIR_FILE}: {e}')
        return False


# Alias para manter compatibilidade
set_coinpair = set_coinpairs


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

    print(coinpair_options())
    # print(get_coinpairs())
    # print(get_str_coinpairs())
    # # setando um novo coinpair inválido
    # print(set_coinpairs('ETH-BRL'))
    # print(get_coinpairs())
    # print(get_str_coinpairs())
    # print(set_coinpairs('BTC-BRL'))
    # print(get_coinpair())
    # print(get_str_coinpair())
    # setando múltiplas moedas válidas
    lista_de_moedas = ['USDT-BRL', 'BTC-BRL', 'USDC-BRL']
    print(set_coinpairs(lista_de_moedas))
    print(get_coinpairs())
    print(get_str_coinpairs())
