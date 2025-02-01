import pandas as pd
import psycopg2
from api_bitpreco import dataset_bitpreco
from psycopg2.extras import execute_batch
from rich import print
from segredos import DATABASE, HOST, PASSWORD, PORT, USER
from sqlalchemy import create_engine


def connect_db():
    """Estabelece conexão com o TimescaleDB"""
    try:
        conn = psycopg2.connect(
            dbname=DATABASE,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        raise Exception(f'Erro de conexão: {e}')


def get_engine():
    """Cria engine SQLAlchemy para conexão com o banco"""
    return create_engine(
        f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}'
    )


def setup_hypertable(conn, table_name: str):
    """Configura uma hypertable para dados temporais"""
    with conn.cursor() as cur:
        # Criar tabela se não existir
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TIMESTAMPTZ NOT NULL,
                close NUMERIC(18,8),
                open NUMERIC(18,8),
                high NUMERIC(18,8),
                low NUMERIC(18,8),
                volume NUMERIC(18,8),
                ema_5 NUMERIC(18,8),
                ema_10 NUMERIC(18,8),
                ema_20 NUMERIC(18,8),
                ema_200 NUMERIC(18,8),
                macd NUMERIC(18,8),
                macd_signal NUMERIC(18,8),
                macd_hist NUMERIC(18,8),
                rsi NUMERIC(18,8),
                bb_upper NUMERIC(18,8),
                bb_middle NUMERIC(18,8),
                bb_lower NUMERIC(18,8),
                stoch_k NUMERIC(18,8),
                stoch_d NUMERIC(18,8),
                volume_sma NUMERIC(18,8),
                atr NUMERIC(18,8),
                signal BIGINT,
                position BIGINT,
                trend TEXT,
                ema_cross BIGINT,
                macd_cross BIGINT,
                CONSTRAINT crypto_data_unique_timestamp UNIQUE (timestamp)
            )
        """)

        # Converter para hypertable
        try:
            cur.execute(f"""
                SELECT create_hypertable('{table_name}', 'timestamp',
                if_not_exists => TRUE);
                CREATE INDEX IF NOT EXISTS idx_crypto_trend ON {table_name}
                (trend, timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_crypto_signals ON {table_name}
                (signal, position, timestamp DESC);
            """)
        except psycopg2.Error as e:
            print(f'Aviso: Hypertable já existe ou erro: {e}')


def migrate_to_db(symbol: str = 'BTC_BRL', resolution: str = '1'):
    """Migra dados da API BitPreco para TimescaleDB"""
    conn = connect_db()

    # Buscar dados da API BitPreco
    df = dataset_bitpreco(symbol=symbol, resolution=resolution)

    if df is None or df.empty:
        print('Nenhum dado obtido da API BitPreco')
        return

    # Reordenar colunas do DataFrame para corresponder à ordem da query SQL
    columns = [
        'timestamp',
        'close',
        'open',
        'high',
        'low',
        'volume',
        'ema_5',
        'ema_10',
        'ema_20',
        'ema_200',
        'macd',
        'macd_signal',
        'macd_hist',
        'rsi',
        'bb_upper',
        'bb_middle',
        'bb_lower',
        'stoch_k',
        'stoch_d',
        'volume_sma',
        'atr',
        'signal',
        'position',
        'trend',
        'ema_cross',
        'macd_cross',
    ]

    # Garantir que todas as colunas existam
    for col in columns:
        if col not in df.columns:
            df[col] = None

    df = df[columns]

    # Configurar tabela
    setup_hypertable(conn, 'crypto_data')

    # Preparar query de inserção com todas as colunas
    insert_query = """
        INSERT INTO crypto_data (
            timestamp, close, open, high, low, volume,
            ema_5, ema_10, ema_20, ema_200,
            macd, macd_signal, macd_hist, rsi,
            bb_upper, bb_middle, bb_lower,
            stoch_k, stoch_d, volume_sma, atr,
            signal, position, trend, ema_cross, macd_cross
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (timestamp) DO UPDATE SET
            close = EXCLUDED.close,
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            volume = EXCLUDED.volume,
            ema_5 = EXCLUDED.ema_5,
            ema_10 = EXCLUDED.ema_10,
            ema_20 = EXCLUDED.ema_20,
            ema_200 = EXCLUDED.ema_200,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            macd_hist = EXCLUDED.macd_hist,
            rsi = EXCLUDED.rsi,
            bb_upper = EXCLUDED.bb_upper,
            bb_middle = EXCLUDED.bb_middle,
            bb_lower = EXCLUDED.bb_lower,
            stoch_k = EXCLUDED.stoch_k,
            stoch_d = EXCLUDED.stoch_d,
            volume_sma = EXCLUDED.volume_sma,
            atr = EXCLUDED.atr,
            signal = EXCLUDED.signal,
            position = EXCLUDED.position,
            trend = EXCLUDED.trend,
            ema_cross = EXCLUDED.ema_cross,
            macd_cross = EXCLUDED.macd_cross
    """

    # Converter DataFrame em lista de tuplas com verificação
    records = []
    for row in df.itertuples(index=False):
        if len(row) != len(columns):
            print(
                'Aviso: Linha ignorada -'
                + f' número incorreto de campos: {len(row)} vs {len(columns)}'
            )
            continue
        records.append(row)

    if not records:
        print('Erro: Nenhum registro válido para inserir')
        return

    # Debug info
    print(f'Número de colunas na query: {insert_query.count("%s")}')
    print(f'Número de campos em cada registro: {len(records[0])}')

    # Inserir dados em lotes
    batch_size = min(1000, len(records))

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records, page_size=batch_size)

    conn.close()
    print(f'Dados migrados com sucesso! Total de registros: {len(records)}')


def read_from_db(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Lê dados do TimescaleDB com filtro de data usando SQLAlchemy"""
    engine = get_engine()

    if not start_date or not end_date:
        query = """
            SELECT * FROM crypto_data
            ORDER BY timestamp
        """
        df = pd.read_sql_query(query, engine)
    else:
        query = """
            SELECT * FROM crypto_data
            WHERE timestamp BETWEEN %(start)s AND %(end)s
            ORDER BY timestamp
        """
        df = pd.read_sql_query(
            query,
            engine,
            params={'start': start_date, 'end': end_date},
            parse_dates=['timestamp'],
        )

    return df


def save_from_db(data: pd.DataFrame):
    """Salva dados no TimescaleDB com tratamento adequado de valores nulos"""
    # Criar cópia explícita do DataFrame
    data = data.copy()

    # Aplicar as mesmas correções do migrate_to_db
    columns = [
        'timestamp',
        'close',
        'open',
        'high',
        'low',
        'volume',
        'ema_5',
        'ema_10',
        'ema_20',
        'ema_200',
        'macd',
        'macd_signal',
        'macd_hist',
        'rsi',
        'bb_upper',
        'bb_middle',
        'bb_lower',
        'stoch_k',
        'stoch_d',
        'volume_sma',
        'atr',
        'signal',
        'position',
        'trend',
        'ema_cross',
        'macd_cross',
    ]

    # Garantir que todas as colunas existam e criar novo DataFrame
    new_data = pd.DataFrame(columns=columns)
    for col in columns:
        if col in data.columns:
            new_data[col] = data[col]
        else:
            new_data[col] = None

    # Substituir o DataFrame original pelo novo
    data = new_data

    conn = connect_db()

    # Converter NaN/NA para None e garantir tipos corretos
    for col in data.columns:
        if col == 'timestamp':
            continue
        if data[col].dtype == 'Int64':
            # Converter IntegerNA para int comum
            data.loc[:, col] = data[col].fillna(0).astype('int64')
        elif data[col].dtype == 'float64':
            # Substituir NaN por None para dados decimais
            data.loc[:, col] = data[col].where(pd.notnull(data[col]), None)
        elif data[col].dtype == 'object':
            # Substituir NA/empty strings por None para texto
            data.loc[:, col] = data[col].where(
                data[col].notna() & (data[col] != ''),  # noqa: PLC1901
                None,
            )

    # Mesma query de inserção do migrate_to_db
    insert_query = """
        INSERT INTO crypto_data (
            timestamp, close, open, high, low, volume,
            ema_5, ema_10, ema_20, ema_200,
            macd, macd_signal, macd_hist, rsi,
            bb_upper, bb_middle, bb_lower,
            stoch_k, stoch_d, volume_sma, atr,
            signal, position, trend, ema_cross, macd_cross
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (timestamp) DO UPDATE SET
            close = EXCLUDED.close,
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            volume = EXCLUDED.volume,
            ema_5 = EXCLUDED.ema_5,
            ema_10 = EXCLUDED.ema_10,
            ema_20 = EXCLUDED.ema_20,
            ema_200 = EXCLUDED.ema_200,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            macd_hist = EXCLUDED.macd_hist,
            rsi = EXCLUDED.rsi,
            bb_upper = EXCLUDED.bb_upper,
            bb_middle = EXCLUDED.bb_middle,
            bb_lower = EXCLUDED.bb_lower,
            stoch_k = EXCLUDED.stoch_k,
            stoch_d = EXCLUDED.stoch_d,
            volume_sma = EXCLUDED.volume_sma,
            atr = EXCLUDED.atr,
            signal = EXCLUDED.signal,
            position = EXCLUDED.position,
            trend = EXCLUDED.trend,
            ema_cross = EXCLUDED.ema_cross,
            macd_cross = EXCLUDED.macd_cross
    """

    # Converter DataFrame para lista de tuplas após tratamento
    records = [
        tuple(None if pd.isna(val) or val is pd.NA else val for val in row)
        for row in data.values
    ]

    if not records:
        print('Erro: Nenhum registro válido para inserir')
        return

    batch_size = min(1000, len(records))

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records, page_size=batch_size)

    conn.close()
    print(f'Dados salvos com sucesso! Total de registros: {len(records)}')


if __name__ == '__main__':
    # migrate_to_db()
    df = read_from_db('2025-01-26', '2025-01-27')
    print(df)
