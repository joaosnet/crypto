import os

from dotenv import load_dotenv

# pegando o caminho da pasta atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print(BASE_DIR)

CAMINHO = BASE_DIR + '/db'

load_dotenv()

DEGUG = os.getenv('DEBUG')

signature = os.getenv('SIGNATURE')

api_key = os.getenv('API_KEY')

auth_token = signature + api_key  # (strings concatenadas)

SECRET_KEY = os.getenv('SECRET_KEY')

POSTGRES_CONNECTION = os.getenv('POSTGRES_CONNECTION')

# gerador de chaves aleatórias
if __name__ == '__main__':
    import os

    print(os.urandom(24).hex())
