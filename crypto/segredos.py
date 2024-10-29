import os

from dotenv import load_dotenv

load_dotenv()

DEGUG = os.getenv('DEBUG')

signature = os.getenv('SIGNATURE')

api_key = os.getenv('API_KEY')

auth_token = signature + api_key  # (strings concatenadas)

SECRET_KEY = os.getenv('SECRET_KEY')

# gerador de chaves aleatórias
if __name__ == '__main__':
    import os

    print(os.urandom(24).hex())
