import duckdb as db
import pandas as pd


# Função para carregar os dados do CSV com e sem filtro de data
def load_csv_in_dataframe(
    df: str, start_date=None, end_date=None
) -> pd.DataFrame:
    query = f"SELECT * FROM read_csv_auto('{df}')"
    if start_date is not None and end_date is not None:
        query += (
            f" WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'"
        )
    elif start_date is not None:
        query += f" WHERE timestamp >= '{start_date}'"
    elif end_date is not None:
        query += f" WHERE timestamp <= '{end_date}'"
    df = db.sql(query).df()

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
