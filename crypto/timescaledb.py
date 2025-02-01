import pandas as pd
import psycopg2
from api_bitpreco import dataset_bitpreco
from psycopg2.extras import execute_batch
from rich import print
from segredos import POSTGRES_CONNECTION


def connect_db():
    """Estabelece conexão com o TimescaleDB"""
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION)
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        raise Exception(f'Erro de conexão: {e}')


def setup_hypertable(conn, table_name: str):
    """Configura uma hypertable para dados temporais"""
    with conn.cursor() as cur:
        # Criar tabela se não existir
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                timestamp TIMESTAMPTZ NOT NULL,
                close NUMERIC,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                volume NUMERIC,
                ema_5 NUMERIC,
                ema_10 NUMERIC,
                ema_20 NUMERIC,
                ema_200 NUMERIC,
                macd NUMERIC,
                macd_signal NUMERIC,
                macd_hist NUMERIC,
                rsi NUMERIC,
                bb_upper NUMERIC,
                bb_middle NUMERIC,
                bb_lower NUMERIC,
                stoch_k NUMERIC,
                stoch_d NUMERIC,
                volume_sma NUMERIC,
                atr NUMERIC,
                signal INTEGER,
                position INTEGER,
                trend TEXT,
                ema_cross INTEGER,
                macd_cross INTEGER
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
        ) VALUES %s
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

    # Inserir dados em lotes
    batch_size = 1000
    records = df.to_dict('records')

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records, page_size=batch_size)

    conn.close()
    print(f'Dados migrados com sucesso! Total de registros: {len(records)}')


def read_from_db(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Lê dados do TimescaleDB com filtro de data"""

    if not start_date or not end_date:
        query = """
            SELECT * FROM crypto_data
            ORDER BY timestamp
        """
    else:
        query = """
            SELECT * FROM crypto_data
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY timestamp
        """

    conn = connect_db()
    df = pd.read_sql_query(
        query, conn, params=(start_date, end_date), parse_dates=['timestamp']
    )
    conn.close()

    return df


def save_from_db(data: pd.DataFrame):
    # Salva os novos dados no banco de dados
    conn = connect_db()

    # Preparar query de inserção com todas as colunas

    insert_query = """
        INSERT INTO crypto_data (
            timestamp, close, open, high, low, volume,
            ema_5, ema_10, ema_20, ema_200,
            macd, macd_signal, macd_hist, rsi,
            bb_upper, bb_middle, bb_lower,
            stoch_k, stoch_d, volume_sma, atr,
            signal, position, trend, ema_cross, macd_cross
        ) VALUES %s
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

    # Inserir dados em lotes
    batch_size = 1000
    records = data.to_dict('records')

    with conn.cursor() as cur:
        execute_batch(cur, insert_query, records, page_size=batch_size)

    conn.close()
    print(f'Dados salvos com sucesso! Total de registros: {len(records)}')


if __name__ == '__main__':
    df = read_from_db('BTCBRL', '2025-01-26', '2025-01-27')
    print(df.head())
