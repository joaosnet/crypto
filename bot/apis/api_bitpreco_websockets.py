import phxsocket

from segredos import auth_token

# Endpoints WebSocket da Bitypreço
ORDERBOOK_SOCKET_URL = (
    'wss://websocket.bitpreco.com/orderbook/socket/websocket'
)
NOTIFICATIONS_SOCKET_URL = (
    'wss://websocket.bitpreco.com/notifications/socket/websocket'
)


def Ticker():
    """
    Conecta ao WebSocket da Bitypreço para receber atualizações de preços
    (ticker).
    """
    socket = phxsocket.Client(ORDERBOOK_SOCKET_URL, {})

    if socket.connect():
        channel = socket.channel('ticker:ALL-BRL', {})
        resp = channel.join()

        if resp:

            def handle_price(payload):
                print('Atualização de preço recebida:')
                print(payload)

            channel.on('price', handle_price)

            print(
            'Conectado ao tópico ticker:ALL-BRL. Aguardando atualizações...'
            )

            # Mantém a conexão aberta
            try:
                while True:
                    socket.heartbeat()
            except KeyboardInterrupt:
                print('Conexão encerrada pelo usuário.')
                socket.close()
        else:
            print('Falha ao ingressar no canal ticker:ALL-BRL.')
    else:
        print('Falha ao conectar ao WebSocket.')


def Orderbook(market='BTC-BRL'):
    """
    Conecta ao WebSocket da Bitypreço para
    receber atualizações do Livro de Ordens.
    """
    socket = phxsocket.Client(ORDERBOOK_SOCKET_URL, {})

    if socket.connect():
        topic = f'orderbook:{market}'
        channel = socket.channel(topic, {})
        resp = channel.join()

        if resp:

            def handle_snapshot(payload):
                print(f'Livro de Ordens atualizado para o mercado {market}:')
                print(payload)

            channel.on('snapshot', handle_snapshot)

            print(f'Conectado ao tópico {topic}. Aguardando atualizações...')

            # Mantém a conexão aberta
            try:
                while True:
                    socket.heartbeat()
            except KeyboardInterrupt:
                print('Conexão encerrada pelo usuário.')
                socket.close()
        else:
            print(f'Falha ao ingressar no canal {topic}.')
    else:
        print('Falha ao conectar ao WebSocket.')


def Notifications():
    """
    Conecta ao WebSocket da Bitypreço para receber notificações privadas.
    """
    params = {'authToken': auth_token}
    socket = phxsocket.Client(NOTIFICATIONS_SOCKET_URL, params)

    if socket.connect():
        topic = f'notifications:{auth_token}'
        channel = socket.channel(topic, {})
        resp = channel.join()

        if resp:

            def handle_flash(payload):
                print('Notificação recebida:')
                print(payload)

            channel.on('flash', handle_flash)

            print(
            'Conectado ao tópico de notificações. Aguardando notificações...'
            )

            # Mantém a conexão aberta
            try:
                while True:
                    socket.heartbeat()
            except KeyboardInterrupt:
                print('Conexão encerrada pelo usuário.')
                socket.close()
        else:
            print('Falha ao ingressar no canal de notificações.')
    else:
        print('Falha ao conectar ao WebSocket de notificações.')
