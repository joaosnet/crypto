import pandas as pd

from segredos import CAMINHO

PRICE_FILE = CAMINHO + '/ticker.csv'
BALANCE_FILE = CAMINHO + '/balance.csv'


def save_price_to_csv(ticker_json):
    try:
        df_precos = pd.read_csv(PRICE_FILE)
        if (
            ticker_json['last'] != df_precos['last'].iloc[-1]
            or ticker_json['timestamp'][:-3]
            != df_precos['timestamp'].iloc[-1][:-3]
        ):
            df_precos = df_precos._append(ticker_json, ignore_index=True)
            df_precos.to_csv(PRICE_FILE, index=False)
    except Exception as e:
        if 'No columns to parse from file' in str(e):
            df_precos = pd.DataFrame([ticker_json])

    df_precos.to_csv(PRICE_FILE, index=False)


def save_balance_to_csv(balance_json):
    balance_df = pd.DataFrame([balance_json])
    balance_df.to_csv(BALANCE_FILE, index=False)


def save_orders_to_csv(orders_json, coinpair):
    # Define o caminho do arquivo baseado no coin_pair
    orders_file = CAMINHO + f'/executed_orders_{coinpair.bitpreco_format}.csv'

    # Processa os dados e adiciona a coluna de posicionamento
    processed_orders = []
    for order in orders_json:
        order_data = order.copy()
        # Determina o posicionamento baseado no tipo de ordem
        if order['type'] == 'BUY':
            order_data['posicao'] = 'COMPRADO'
        else:
            order_data['posicao'] = 'VENDIDO'
        processed_orders.append(order_data)

    orders_df = pd.DataFrame(processed_orders)

    # Se o arquivo já existe, append os novos dados
    try:
        existing_df = pd.read_csv(orders_file)
        # Verifica se há novos dados para não duplicar
        new_orders = orders_df[~orders_df['id'].isin(existing_df['id'])]
        if not new_orders.empty:
            final_df = pd.concat([existing_df, new_orders])
            final_df.to_csv(orders_file, index=False)
    except FileNotFoundError:
        # se tiver instancias no dataframe, salva no arquivo
        if not orders_df.empty:
            orders_df.to_csv(orders_file, index=False)
