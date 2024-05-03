import socket
import struct
import threading
import uuid
# import time

class ChatServer:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.rooms = {}  # key: room_name, value: {'host_client_token': token, 'participants': set()}
        self.clients = {}  # key: client_token, value: tcp_addr_port
        self.clients_udp = {} # key: client_token, value: udp_addr 必要？
        self.client_names = {}
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
                # print(addr)
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
                self.clients[client_token] = addr
                self.client_names[client_token] = user_name

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
                self.clients[client_token] = addr
                self.client_names[client_token] = user_name
                

            print('rooms are:', self.rooms)
            print('clients are:', self.clients)
            print('client names are', self.client_names)

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client_sock.close()


    # udpアドレスもclientsに格納する必要あり?
    def listen_udp(self):
        while True:
            data, addr = self.udp_sock.recvfrom(4096)
            # ヘッダー
            room_name_size, token_size = struct.unpack('!B B', data[:2])
            # ボディ
            room_name = data[2:2 + room_name_size].decode('utf-8')
            client_token = data[2 + room_name_size:2 + room_name_size + token_size].decode('utf-8')
            message = data[2 + room_name_size + token_size:].decode()


            # チャットルーム初回接続時に、UDP接続用のアドレスをサーバーに保存
            if len(message) == 0:
                if not self.clients_udp.get(client_token):
                    self.clients_udp[client_token] = addr
            
            # メッセージが送られてきたとき
            elif len(message) > 0:
                print(f'message received from {self.client_names[client_token]} in {room_name}. message is', message)

                room_name_bytes = room_name.encode()
                user_name = self.client_names[client_token]
                user_name_bytes = user_name.encode()
                message_bytes = message.encode()

                header = struct.pack('!B B', len(room_name_bytes), len(user_name_bytes))
                body = room_name_bytes + user_name_bytes + message_bytes
                packet = header + body

                for token in self.rooms[room_name]['participants']:
                    self.udp_sock.sendto(packet, self.clients_udp[token])


if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    server = ChatServer(HOST, TCP_PORT, UDP_PORT)
    server.start()
