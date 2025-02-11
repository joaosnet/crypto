import os

from dotenv import load_dotenv

# pegando o caminho da pasta atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


CAMINHO = os.path.join(BASE_DIR, 'db')
# print(CAMINHO)
load_dotenv()

DEGUG = os.getenv('DEBUG')

signature = os.getenv('SIGNATURE')

api_key = os.getenv('API_KEY')

auth_token = signature + api_key  # (strings concatenadas)

SECRET_KEY = os.getenv('SECRET_KEY')

POSTGRES_CONNECTION = os.getenv('POSTGRES_CONNECTION')

DBNAME = os.getenv('DBNAME_timescaledb')
DATABASE = os.getenv('DATABASE_timescaledb')
USER = os.getenv('USER_timescaledb')
PASSWORD = os.getenv('PASSWORD_timescaledb')
HOST = os.getenv('HOST_timescaledb')
PORT = os.getenv('PORT_timescaledb')

# gerador de chaves aleatórias
if __name__ == '__main__':
    import os

    print(os.urandom(24).hex())
