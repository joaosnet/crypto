import datetime as dt
from datetime import datetime

import duckdb
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from rich import print
from sqlalchemy import create_engine

try:
    from bot.apis.api_bitpreco import dataset_bitpreco
    from segredos import DATABASE, HOST, PASSWORD, PORT, USER
except ImportError:
    from ...bot.apis.api_bitpreco import dataset_bitpreco
    from .segredos import DATABASE, HOST, PASSWORD, PORT, USER


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


def read_latest_data(limit: int = 1000) -> pd.DataFrame:
    """Lê os dados mais recentes do TimescaleDB em ordem crescente"""
    engine = get_engine()

    query = f"""
        WITH latest_records AS (
            SELECT * FROM crypto_data
            ORDER BY timestamp DESC
            LIMIT {limit}
        )
        SELECT * FROM latest_records
        ORDER BY timestamp ASC
    """

    return pd.read_sql_query(query, engine, parse_dates=['timestamp'])


def save_from_db(data: pd.DataFrame):
    """Salva dados no TimescaleDB com tratamento otimizado de valores nulos."""
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

    # Reindexa para garantir as colunas necessárias
    data = data.reindex(columns=columns)

    # Conversões vetorizadas (exceto 'timestamp')
    for col in data.columns:
        if col == 'timestamp':
            continue
        if pd.api.types.is_integer_dtype(data[col]):
            data[col] = data[col].fillna(0).astype('int64')
        elif pd.api.types.is_float_dtype(data[col]):
            data[col] = data[col].where(data[col].notna(), None)
        elif pd.api.types.is_object_dtype(data[col]):
            data[col] = data[col].where(
                data[col].notna() & (data[col] != ''),  # noqa: PLC1901
                None,
            )

    conn = connect_db()

    # Converte DataFrame para lista de tuplas de forma rápida
    records = list(data.itertuples(index=False, name=None))
    if not records:
        print('Erro: Nenhum registro válido para inserir')
        return

    batch_size = 1000  # ou ajuste conforme o volume e performance desejada
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

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records, page_size=batch_size)

    conn.close()
    print(f'Dados salvos com sucesso! Total de registros: {len(records)}')


def save_from_db_optimized(data: pd.DataFrame):
    # Garantir que a coluna 'timestamp' exista
    if 'timestamp' not in data.columns:
        raise ValueError("O DataFrame deve conter uma coluna 'timestamp'")

    # Criar string de conexão PostgreSQL
    conn_str = (
        f'dbname={DATABASE} user={USER}'
        + f' password={PASSWORD} host={HOST} port={PORT}'
    )

    # Criar conexão com o DuckDB
    duckdb_conn = duckdb.connect()

    try:
        # Instalar e carregar a extensão postgres
        duckdb_conn.execute('INSTALL postgres;')
        duckdb_conn.execute('LOAD postgres;')

        # Anexar o banco PostgreSQL
        duckdb_conn.execute(f"ATTACH '{conn_str}' AS pg (TYPE postgres);")

        # Registrar o DataFrame como tabela temporária
        duckdb_conn.register('temp_data', data)

        # Construir query de inserção
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
        insert_columns = ', '.join(columns)

        # Primeiro tentar DELETE + INSERT ao invés de ON CONFLICT
        delete_query = """
            DELETE FROM pg.crypto_data
            WHERE timestamp IN (SELECT timestamp FROM temp_data)
        """

        insert_query = f"""
            INSERT INTO pg.crypto_data ({insert_columns})
            SELECT {insert_columns} FROM temp_data
        """

        # Executar em sequência: delete e depois insert
        duckdb_conn.execute(delete_query)
        duckdb_conn.execute(insert_query)

    except Exception as e:
        print(f'Erro ao salvar dados: {e}')
        raise
    finally:
        # Limpeza
        duckdb_conn.unregister('temp_data')
        duckdb_conn.execute('DETACH pg')
        duckdb_conn.close()

    print(
        'Dados salvos com sucesso usando DuckDB!'
        + f' Total de registros: {len(data)}'
    )


if __name__ == '__main__':
    # Exemplo de uso para dados mais recentes
    # df = read_latest_data(1000)  # últimos 1000 registros
    # print('Dados mais recentes:')
    # print(df)

    # Exemplo com intervalo de datas
    from datetime import datetime, timedelta

    end_date = datetime.now(dt.timezone.utc)
    start_date = end_date - timedelta(days=30)  # último dia

    df_period = read_from_db(
        start_date=start_date.isoformat(), end_date=end_date.isoformat()
    )
    print('\nDados do último dia:')
    print(df_period)
    # Salvando em um arquivo csv para análise
    # apenas as colunas 'timestamp', 'close', 'open', 'high', 'low','volume',
    # df.to_csv(
    #     'crypto/db/crypto_data.csv',
    #     index=False,
    #     columns=['timestamp', 'close', 'open', 'high', 'low', 'volume'],
    # )
