import socket
import struct
import threading
import random
import sys 

import threading
import time
class ChatClient:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.local_ip = self.generate_random_loopback_ip()  # ランダムなループバックIPを生成
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.token = ''
        self.user_name = ''
        self.room_name = ''
        self.last_activity_time = time.time()
        self.timeout_seconds = 300  # 5分のタイムアウト
        self.active = True
        threading.Thread(target=self.monitor_activity).start()

        print(self.local_ip)
        
        # TCPソケットとUDPソケットをローカルIPアドレスにバインド
        # 0番は、空いているポートが自動的に割り振られる
        self.tcp_sock.bind((self.local_ip, 0))
        self.udp_sock.bind((self.local_ip, 0))
        


    def generate_random_loopback_ip(self):
        # 127.0.0.1 から 127.0.0.255 までのランダムなループバックIPを生成
        return '127.0.0.' + str(random.randint(1, 255))



    def start(self):
        try:
            self.tcp_sock.connect((self.host, self.tcp_port))
            print("Connected to server")
            threading.Thread(target=self.receive_messages).start()

            while True:
                self.user_name =  input("Enter your name: ")
                choice = input("Enter 'create' to create a new room or 'join' to join an existing room: ")

                if choice.lower() == 'create':
                    self.room_name = input("Enter room name: ")
                    self.create_room(self.room_name, self.user_name)
                elif choice.lower() == 'join':
                    self.room_name = input("Enter room name: ")
                    self.join_room(self.room_name, 2, self.user_name)

                self.chat()

        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        print("Disconnecting from server...")
        self.tcp_sock.close()
        self.udp_sock.close()

    def create_room(self, room_name, operation_payload):
        room_name_bytes = room_name.encode('utf-8')
        operation_payload_bytes = operation_payload.encode('utf-8')

        header = struct.pack('!B B B 29s', len(room_name_bytes), 1, 0, len(operation_payload_bytes).to_bytes(29, byteorder='big'))
        body = room_name_bytes + operation_payload_bytes
        self.tcp_sock.sendall(header + body)

        # print('in create tcp sock is: ', self.tcp_sock.getsockname())
        # print('in create udp sock is: ', self.udp_sock.getsockname())

        # ステート1の応答を待機
        response = self.tcp_sock.recv(2)
        operation, state = struct.unpack('!B B', response)
        if operation == 1 and state == 1:
            print("Server acknowledged the room creation request.")
        else:
            print("Failed to get acknowledgment from server.")
            return

        # ステート2の応答を待機
        response = self.tcp_sock.recv(257)  # 1 byte operation + 1 byte state + 255 bytes token
        operation, state, token = struct.unpack('!B B 255s', response)
        if operation == 1 and state == 2:
            self.token = token.decode('utf-8').strip('\x00')
            print("Room created successfully. Token:", self.token)
        else:
            print("Failed to create room.")


    def join_room(self, room_name, operation_code, operation_payload):
        room_name_bytes = room_name.encode('utf-8')
        operation_payload_bytes = operation_payload.encode('utf-8')

        # ヘッダをパック（1バイトルーム名サイズ、1バイト操作、1バイト状態、ユーザー名サイズ）
        header = struct.pack('!B B B 29s', len(room_name_bytes), operation_code, 0, len(operation_payload_bytes).to_bytes(29, byteorder='big'))
        body = room_name_bytes + operation_payload_bytes
        self.tcp_sock.sendall(header + body)

        # print('udp sock is: ', self.udp_sock.getsockname())


        # ステート1の応答を待機
        response = self.tcp_sock.recv(2)
        operation, state = struct.unpack('!B B', response)
        if operation == 2 and state == 1:
            print("Server acknowledged the room creation request.")
        else:
            print("Failed to get acknowledgment from server.")
            return

        # ステート2の応答を待機
        response = self.tcp_sock.recv(257)  # 1 byte operation + 1 byte state + 255 bytes token
        operation, state, token = struct.unpack('!B B 255s', response)
        if operation == 2 and state == 2:
            self.token = token.decode('utf-8').strip('\x00')
            print(f"You joined room:{room_name} successfully. Token:", self.token)
        else:
            print("Failed to create room.")


    def chat(self):
        print("You can start chatting now. Type 'exit' to leave chat.")
        # print('udp sock is: ', self.udp_sock.getsockname())

        # UDP接続が開始したら、1度だけUDPアドレスを送る(メッセージは空文字)
        room_name_bytes = self.room_name.encode('utf-8')
        token_bytes = self.token.encode('utf-8')
        header = struct.pack('!B B', len(room_name_bytes), len(token_bytes))
        body = room_name_bytes + token_bytes
        packet = header + body
        self.udp_sock.sendto(packet, (self.host, self.udp_port))


        while True:
            message = input("> ")
            if message.lower() == 'exit':
                break
                
            self.send_message(message)

    def send_message(self, message):
        room_name_bytes = self.room_name.encode('utf-8')
        token_bytes = self.token.encode('utf-8')
        message_bytes = message.encode('utf-8')

        header = struct.pack('!B B', len(room_name_bytes), len(token_bytes))
        body = room_name_bytes + token_bytes + message_bytes
        packet = header + body
        self.udp_sock.sendto(packet, (self.host, self.udp_port))
        self.last_activity_time = time.time() 

    # def receive_messages(self):
    #     while True:
    #         data, _ = self.udp_sock.recvfrom(4096)
    #         # ヘッダー
    #         room_name_size, user_name_size = struct.unpack('!B B', data[:2])
    #         # ボディ
    #         user_name = data[2:2 + room_name_size].decode()
    #         message = data[2 + room_name_size : 1 + user_name_size:].decode()

    #         room_name = data[2:2 + room_name_size].decode('utf-8')
    #         user_name = data[2 + room_name_size:2 + room_name_size + user_name_size].decode('utf-8')
    #         message = data[2 + room_name_size + user_name_size:].decode()

    #         print(f"{user_name} : {message} in {room_name}")

    def monitor_activity(self):
        while True:
            time.sleep(5)  # 10秒ごとにチェック
            if time.time() - self.last_activity_time > self.timeout_seconds:
                print("No activity detected. Disconnecting...")
                self.shutdown()
                break

    def remove_client(self, client_token):
        print(f"Starting to remove client {client_token}")
        if client_token in self.clients:
            del self.clients[client_token]
            print(f"Removed {client_token} from clients list.")
        for room_name, room_info in list(self.rooms.items()):
            if client_token in room_info['participants']:
                room_info['participants'].remove(client_token)
                print(f"Removed {client_token} from room {room_name}.")
                if not room_info['participants']:
                    del self.rooms[room_name]
                    print(f"Room {room_name} deleted because it is now empty.")
        print(f"Client {client_token} and all associated data have been removed.")

    def receive_messages(self):
        while True:
            try:
                print("Waiting for data...")
                data, _ = self.udp_sock.recvfrom(4096)
                if data:
                    print(f"受け取ったデータは: {data}")  # 受信データを表示
                    # ヘッダー
                    room_name_size, user_name_size = struct.unpack('!B B', data[:2])
                    room_name = data[2:2 + room_name_size].decode('utf-8')
                    user_name = data[2 + room_name_size:2 + room_name_size + user_name_size].decode('utf-8')
                    message = data[2 + room_name_size + user_name_size:].decode('utf-8')

                    print(f"受信した message: '{message}'")  # 受信メッセージの確認

                    # 特定の切断メッセージの確認
                    if data == b'DISCONNECT':
                        print("Server has disconnected the client.")
                        self.shutdown()
                        print("シャットダウン")
                        break

                    # 受信メッセージの表示
                    print(f"{user_name} : {message} in {room_name}")
            except Exception as e:
                print(f"Failed to receive message: {e}")
                if not self.active:
                    break

    def shutdown(self):
        print("Disconnecting from server...")
        try:
            self.active = False  # スレッドループを停止させる
            self.tcp_sock.close()
            self.udp_sock.close()
        except Exception as e:
            print(f"Error while closing sockets: {e}")
        finally:
            print("Client shutdown complete.")
            sys.exit(0)  # クライアントプログラムを終了

        

            
        


if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    client = ChatClient(HOST, TCP_PORT, UDP_PORT)
    client.start()

