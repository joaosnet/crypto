import duckdb as db
import pandas as pd


# Função para carregar os dados do CSV com e sem filtro de data
def load_csv_in_dataframe(
    df: str, start_date=None, end_date=None
) -> pd.DataFrame:
    # Criar nova conexão para cada consulta
    with db.connect(':memory:') as db1:
        query = f"SELECT * FROM read_csv_auto('{df}')"

        if start_date is not None and end_date is not None:
            query += (
                f" WHERE timestamp >= '{start_date}'"
                + f" AND timestamp <= '{end_date}'"
            )
        elif start_date is not None:
            query += f" WHERE timestamp >= '{start_date}'"
        elif end_date is not None:
            query += f" WHERE timestamp <= '{end_date}'"

        df = db1.sql(query).df()

        # Converter timestamp de volta para datetime UTC
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        return df


def load_csv_in_records(df, start_date=None, end_date=None):
    query = f"SELECT * FROM read_csv_auto('{df}')"
    if start_date is not None and end_date is not None:
        query += (
            f" WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'"
        )
    elif start_date is not None:
        query += f" WHERE timestamp >= '{start_date}'"
    elif end_date is not None:
        query += f" WHERE timestamp <= '{end_date}'"

    csv_sql = db.sql(query)
    result = csv_sql.fetchall()
    # Obtenção dos nomes das colunas - corrigido para acessar como propriedade
    column_names = [desc[0] for desc in csv_sql.description]

    # Conversão para uma lista de dicionários
    data = [dict(zip(column_names, row)) for row in result]

    return data


def save_to_csv_duckdb(df: pd.DataFrame, filepath: str, mode='overwrite'):
    """
    Salva DataFrame no CSV usando DuckDB de forma otimizada
    mode: 'overwrite' ou 'append'
    """
    try:
        # Garantir que timestamp está em UTC antes de salvar
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
            # Salvar timestamp como string ISO format para preservar timezone
            df['timestamp'] = df['timestamp'].dt.strftime(
                '%Y-%m-%d %H:%M:%S%z'
            )

        # Criar ou conectar ao banco temporário em memória
        con = db.connect(':memory:')

        # Registrar o DataFrame como uma view
        con.register('temp_df', df)

        if mode == 'append':
            # Em caso de append, primeiro remover possíveis duplicatas
            query = f"""
            CREATE TABLE IF NOT EXISTS current_data AS
            SELECT * FROM read_csv_auto('{filepath}');

            CREATE TABLE merged AS
            SELECT * FROM (
                SELECT DISTINCT * FROM current_data
                UNION ALL
                SELECT * FROM temp_df
                WHERE timestamp NOT IN (SELECT timestamp FROM current_data)
            ) t
            ORDER BY timestamp;

            COPY (SELECT * FROM merged) TO '{filepath}' (HEADER true);
            """
        else:
            # Em caso de overwrite, simplesmente salvar
            query = (
                f"COPY (SELECT * FROM temp_df) TO '{filepath}' (HEADER true)"
            )

        con.execute(query)
        return True
    except Exception as e:
        print(f'Erro ao salvar dados: {e}')
        return False
    finally:
        con.close()


if __name__ == '__main__':
    import datetime as dt
    from datetime import datetime, timedelta

    from rich import print

    end_date = datetime.now(dt.timezone.utc)
    start_date = end_date - timedelta(days=30)  # último dia
    # Testando a função load_csv_in_dataframe
    df = 'crypto/db/BTC_BRL_bitpreco.csv'
    print(load_csv_in_dataframe(df))

    # Testando a função load_csv_in_records
    # print(
    #     load_csv_in_records(
    #         df,
    #         start_date=start_date.isoformat(),
    #         end_date=end_date.isoformat(),
    #     )
    # )

    df_period = load_csv_in_dataframe(
        df=df, start_date=start_date.isoformat(), end_date=end_date.isoformat()
    )
    print(df_period)
