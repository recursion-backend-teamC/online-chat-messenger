import socket
import struct
import threading
import uuid
import time

class ChatServer:
    def __init__(self, host, tcp_port, udp_port, timeout_seconds=1000):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.rooms = {}  # key: room_name, value: {'host_client_token': token, 'participants': set()}
        self.clients = {}  # key: client_token, value: tcp_addr_port
        self.clients_udp = {} # key: client_token, value: udp_addr 必要？
        self.client_names = {}
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # SO_REUSEADDRオプションを設定
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # SO_REUSEADDRオプションを設定
        self.tcp_sock.bind((self.host, self.tcp_port))
        self.udp_sock.bind((self.host, self.udp_port))
        self.tcp_sock.listen(5)
        print(f"Server started on {self.host}:{self.tcp_port}")
        threading.Thread(target=self.listen_udp).start()
        self.timeout_seconds = timeout_seconds
        threading.Thread(target=self.check_timeout).start()

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

            last_activity_time = time.time()

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
                self.clients[client_token] = (addr, time.time())
                # self.clients[client_token] = addr
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
                self.clients[client_token] = (addr, time.time())
                # self.clients[client_token] = addr
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


            # クライアントが存在し、メッセージが空でない場合、活動時間を更新
            if client_token in self.clients and len(message) > 0:
                addr, _ = self.clients[client_token]
                self.clients[client_token] = (addr, time.time())  # 活動時間の更新
            # チャットルーム初回接続時に、UDP接続用のアドレスをサーバーに保存
            if len(message) == 0:
                if not self.clients_udp.get(client_token):
                    self.clients_udp[client_token] = addr
            
            # メッセージが送られてきたとき
            elif len(message) > 0:
                last_activity_time = time.time()
                print(f'message received from {self.client_names[client_token]} in {room_name}. message is', message)

                print("aaa", self.rooms[room_name]['host_client_token'])
                # ホストからの 'exit' メッセージの場合、他のユーザーも強制退出
                if message == "exit" and self.rooms[room_name]['host_client_token'] == client_token:
                    self.dissolve_room(room_name)
                    continue

                room_name_bytes = room_name.encode()
                user_name = self.client_names[client_token]
                user_name_bytes = user_name.encode()
                message_bytes = message.encode()

                header = struct.pack('!B B', len(room_name_bytes), len(user_name_bytes))
                body = room_name_bytes + user_name_bytes + message_bytes
                packet = header + body

                for token in self.rooms[room_name]['participants']:
                    self.udp_sock.sendto(packet, self.clients_udp[token])

    def dissolve_room(self, room_name):
        """部屋を解散させ、すべての参加者に切断を通知します。"""
        # 指定された部屋名をキーにして部屋情報を取得し、その部屋を辞書から削除します。
        room_info = self.rooms.pop(room_name, None)
        if room_info:
            message = "DISCONNECT".encode('utf-8')
            # 部屋の参加者全員にDISCONNECTメッセージを送信します。
            for participant in room_info['participants']:
                participant_addr = self.clients_udp.get(participant)
                if participant_addr:
                    # 各参加者のUDPアドレスに切断メッセージを送信します。
                    self.udp_sock.sendto(message, participant_addr)
                # 参加者のTCPクライアント情報、UDPアドレス情報、名前情報を削除します。
                self.clients.pop(participant, None)  # クライアント情報から削除
                self.clients_udp.pop(participant, None)  # UDPアドレス情報から削除
                self.client_names.pop(participant, None)  # 名前情報から削除
            # 部屋の解散とすべての参加者の切断が完了したことをログに出力します。
            print(f"部屋 '{room_name}' が解散され、すべての参加者が切断されました。")

                    
    def check_timeout(self):
        print("チェックタイムアウトメソッド動いた")
        while True:
            print("ほわいるのなか")
            current_time = time.time()
            # Remove timed out clients
            for client_token, (addr, last_activity_time) in list(self.clients.items()):
                # print("forのなか")
                # print(current_time, last_activity_time, self.timeout_seconds)
                # print("Checking timeout for client:", client_token)
                # print("Current time:", current_time)
                # print("Last activity time:", last_activity_time)
                # print("Difference:", current_time - last_activity_time)
                # print("Timeout threshold:", self.timeout_seconds)
                if current_time - last_activity_time > self.timeout_seconds:
                    print(f"Client {client_token} timed out.")
                    self.remove_client(client_token)  # Call remove_client to handle cleanup
            time.sleep(1)  # Check every second
        print("Timeout check ended.")
        
    def remove_client(self, client_token):
        print(f"Attempting to remove client {client_token} due to timeout or disconnect.")

        # UDPアドレスがあればDISCONNECTメッセージを送信
        udp_addr = self.clients_udp.get(client_token)
        if udp_addr:
            message = "DISCONNECT".encode('utf-8')
            self.udp_sock.sendto(message, udp_addr)
            print(f" DISCONNECT を送りますmessage to {client_token} at {udp_addr}")

        # TCPおよびUDPのクライアント情報を削除
        self.clients.pop(client_token, None)  # セーフな削除
        self.clients_udp.pop(client_token, None)  # セーフな削除

        # クライアントが参加しているルームから削除
        for room_name, room_info in list(self.rooms.items()):
            if client_token in room_info['participants']:
                room_info['participants'].remove(client_token)
                print(f"Removed {client_token} from room {room_name}.")
                if not room_info['participants']:
                    del self.rooms[room_name]
                    print(f"Room {room_name} から削除されました入力がなにもなかったので.")

        # クライアントの名前情報を削除
        self.client_names.pop(client_token, None)

        print(f"Client {client_token} and all associated data have been successfully removed.")



if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    server = ChatServer(HOST, TCP_PORT, UDP_PORT)
    server.start()

