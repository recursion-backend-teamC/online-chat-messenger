import socket
import struct
import threading
import uuid

class ChatServer:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.rooms = {}  # key: room_name, value: {'host_client_token': token, 'participants': set()}
        self.clients = {}  # key: client_token, value: {'tcp': tcp_addr, 'udp': udp_addr}
        self.clients_udp = {}
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_sock.bind((self.host, self.tcp_port))
        self.udp_sock.bind((self.host, self.udp_port))
        self.tcp_sock.listen(5)
        print(f"Server started on {self.host}:{self.tcp_port}")
        threading.Thread(target=self.listen_udp).start()

    def start(self):
        try:
            while True:
                client_sock, addr = self.tcp_sock.accept()
                threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("Shutting down the server...")
        self.tcp_sock.close()
        self.udp_sock.close()


    def handle_client(self, client_sock, addr):
        try:
            # ヘッダを受信（32バイト）
            header = client_sock.recv(32)
            if not header:
                return

            # ヘッダから各情報を解析
            room_name_size, operation, state, operation_payload_size_bytes = struct.unpack('!B B B 29s', header)
            operation_payload_size = int.from_bytes(operation_payload_size_bytes.strip(b'\x00'), byteorder='big')

            # ルーム名とオペレーションペイロードを受信
            room_name_bytes = client_sock.recv(room_name_size)
            operation_payload_bytes = client_sock.recv(operation_payload_size)

            # データをデコード
            room_name = room_name_bytes.decode('utf-8')
            user_name = operation_payload_bytes.decode('utf-8')

            # 操作に基づいた処理
            print(f"Received room name: {room_name}")
            print(f"Received operation payload(username): {user_name}")

            # ルーム作成
            if operation == 1 and state == 0:
                # ステート1の応答を送信(操作コード、状態コード)
                response = struct.pack('!B B', 1, 1)
                client_sock.send(response)

                # ステート2の応答を送信
                client_token = str(uuid.uuid4())
                response = struct.pack('!B B 255s', 1, 2, client_token.encode('utf-8'))
                client_sock.send(response)
                print(f"{user_name} created room: '{room_name}' with token: {client_token}")

                # 部屋のホストと参加者を記録
                self.rooms[room_name] = {'host_client_token': client_token, 'participants': set([client_token])}
                self.clients[client_token] = {'tcp': addr, 'udp': None}
                # self.clients[client_token]['tcp'] = addr

            # ルーム参加
            elif operation == 2 and state == 0:
                # ステート1の応答を送信(操作コード、状態コード)
                response = struct.pack('!B B', 2, 1)
                client_sock.send(response)

                # ステート2の応答を送信
                client_token = str(uuid.uuid4())
                response = struct.pack('!B B 255s', 2, 2, client_token.encode('utf-8'))
                client_sock.send(response)
                print(f"{user_name} joined room: '{room_name}' with token: {client_token}")

                # 部屋の参加者を更新
                self.rooms[room_name]['participants'].add(client_token)
                self.clients[client_token] = {'tcp': addr, 'udp': None}
                # self.clients[client_token]['tcp'] = addr
                

            print('rooms are:', self.rooms)
            print('clients are:', self.clients)

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client_sock.close()


    # udpアドレスもclientsに格納する必要あり
    def listen_udp(self):
        while True:
            data, addr = self.udp_sock.recvfrom(4096)
            # ヘッダー
            room_name_size, token_size = struct.unpack('!B B', data[:2])
            # ボディ
            room_name = data[2:2 + room_name_size].decode('utf-8')
            client_token = data[2 + room_name_size:2 + room_name_size + token_size].decode('utf-8')
            message = data[2 + room_name_size + token_size:].decode()

            print(room_name, client_token, message)
            print(self.clients)


            if not self.clients_udp.get(client_token):
                # [client_token]['udp'] == None:
                self.clients[client_token]['udp'] = addr

            # print(room_name, client_token, message)
            # print(addr)
            # print(self.clients[client_token])

            print('message received', room_name, client_token, message)
            # client_tcp_addr = self.clients[client_token]['tcp']

            # broadcast
            for token in self.rooms[room_name]['participants']:
                print('start broadcast')
                # print('in for loop', client_tcp_addr, participant)
                if not (token == client_token):
                    print('in if statement', self.clients[token]['udp'])
                    self.udp_sock.sendto(data, self.clients[token]['udp'])



if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    server = ChatServer(HOST, TCP_PORT, UDP_PORT)
    server.start()
