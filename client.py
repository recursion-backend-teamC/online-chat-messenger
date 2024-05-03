import socket
import struct
import threading

class ChatClient:
    def __init__(self, host, tcp_port, udp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.token = ''
        self.user_name = ''
        self.room_name = ''


    def start(self):
        self.tcp_sock.connect((self.host, self.tcp_port))
        print("Connected to server")
        threading.Thread(target=self.receive_messages).start()

        while True:
            self.user_name =  input("Enter your name: ")
            choice = input("Enter 'create' to create a new room or 'join' to join an existing room: ")
            self.room_name = input("Enter room name: ")

            if choice.lower() == 'create':
                # self.send_tcp_request(1, self.room_name)
                self.create_room(self.room_name, self.user_name)
            elif choice.lower() == 'join':
                # self.send_tcp_request(2, self.room_name)
                self.join_room(self.room_name, 2, self.user_name)

            self.chat()

    def create_room(self, room_name, operation_payload):
        room_name_bytes = room_name.encode('utf-8')
        operation_payload_bytes = operation_payload.encode('utf-8')

        header = struct.pack('!B B B 29s', len(room_name_bytes), 1, 0, len(operation_payload_bytes).to_bytes(29, byteorder='big'))
        body = room_name_bytes + operation_payload_bytes
        self.tcp_sock.sendall(header + body)

        # ステート1の応答を待機
        response = self.tcp_sock.recv(3)
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

        # ステート1の応答を待機
        response = self.tcp_sock.recv(3)
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
        while True:
            message = input("> ")
            if message.lower() == 'exit':
                break
            self.send_message(message)

    def send_message(self, message):
        message_encoded = message.encode('utf-8')
        room_name_encoded = self.room_name.encode('utf-8')
        token_encoded = self.token.encode('utf-8')
        header = struct.pack('!B B', len(room_name_encoded), len(token_encoded))
        packet = header + room_name_encoded + token_encoded + message_encoded
        self.udp_sock.sendto(packet, (self.host, self.udp_port))

    def receive_messages(self):
        while True:
            data, _ = self.udp_sock.recvfrom(4096)
            print("Received message:", data.decode('utf-8'))
        


if __name__ == "__main__":
    HOST = 'localhost'
    TCP_PORT = 9998
    UDP_PORT = 9999
    client = ChatClient(HOST, TCP_PORT, UDP_PORT)
    client.start()
