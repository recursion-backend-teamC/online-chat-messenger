import socket
import struct
import threading
import uuid
import time

class ChatServer:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.rooms = {}  # key: room_name, value: {'host_client_token': token, 'participants': set()}
        self.clients = {}  # key: client_token, value: (addr, last_activity_time)
        self.timeout_seconds = 5  # タイムアウト時間（秒）
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # SO_REUSEADDRオプションを設定
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # SO_REUSEADDRオプションを設定
        self.tcp_sock.bind((self.host, self.tcp_port))
        self.udp_sock.bind((self.host, self.udp_port))
        self.tcp_sock.listen(5)
        print(f"Server started on {self.host}:{self.tcp_port}")
        threading.Thread(target=self.listen_udp).start()
        threading.Thread(target=self.check_timeout).start()

    def start(self):
        while True:
            client_sock, addr = self.tcp_sock.accept()
            threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()
            

    def handle_client(self, client_sock, addr):
        try:
            while True:
                # データを受信
                data = client_sock.recv(4096)
                if not data:
                    break  # データがない場合は切断されたとみなしてループを抜ける

                # メッセージを受信した時点で最終アクティビティ時間を更新する
                last_activity_time = time.time()

                # ヘッダから各情報を解析
                header = data[:32]
                room_name_size, operation, state, operation_payload_size_bytes = struct.unpack('!B B B 29s', header)
                operation_payload_size = int.from_bytes(operation_payload_size_bytes.strip(b'\x00'), byteorder='big')

                # ルーム名とオペレーションペイロードを受信
                room_name_bytes = data[32:32 + room_name_size]
                operation_payload_bytes = data[32 + room_name_size:32 + room_name_size + operation_payload_size]

                # データをデコード
                room_name = room_name_bytes.decode('utf-8')
                user_name = operation_payload_bytes.decode('utf-8')

                # クライアントの最終アクティビティ時間を更新
                client_token = self.clients.get(client_sock)
                if client_token:
                    self.clients[client_token] = (addr, last_activity_time)

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
                    self.rooms[room_name] = {'host_client_token': client_token, 'participants': set([addr])}
                    self.clients[client_token] = (addr, last_activity_time)

                    print('rooms are:', self.rooms)

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
                    self.rooms[room_name]['participants'].add(addr)
                    self.clients[client_token] = (addr, last_activity_time)

                    print(self.rooms)

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            client_sock.close()

    def listen_udp(self):
        while True:
            data, addr = self.udp_sock.recvfrom(4096)
            last_activity_time = time.time()
            # ヘッダー
            room_name_size, token_size = struct.unpack('!B B', data[:2])
            # ボディ
            room_name = data[2:2 + room_name_size].decode('utf-8')
            client_token = data[2 + room_name_size:2 + room_name_size + token_size].decode('utf-8')
            message = data[2 + room_name_size + token_size:]

            print(room_name, client_token, message)
            print(self.clients)

            client_tcp_addr = self.clients[client_token]

            for participant in self.rooms[room_name]['participants']:
                # print('in for loop', client_tcp_addr, participant)
                if not (participant == client_tcp_addr):
                    # print('in if statement', client_tcp_addr, participant)
                    self.udp_sock.sendto(message, participant)

    def check_timeout(self):
        while True:
            current_time = time.time()
            # Remove timed out clients
            for client_token, (addr, last_activity_time) in list(self.clients.items()):
                print(current_time, last_activity_time, self.timeout_seconds)
                if current_time - last_activity_time > self.timeout_seconds:
                    # print(f"Client {client_token} timed out.")
                    del self.clients[client_token]
                    # Remove client from rooms
                    for room_name, room_info in self.rooms.items():
                        if addr in room_info['participants']:
                            room_info['participants'].remove(addr)
                            # print(f"Client {client_token} removed from room {room_name}.")
            time.sleep(1)  # Check every second



if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    server = ChatServer(HOST, TCP_PORT, UDP_PORT)
    server.start()
