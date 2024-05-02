import socket
import struct
import threading

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.token = ''
        self.room_name = ''
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        self.tcp_sock.connect((self.host, self.port))
        print("Connected to server")
        while True:
            choice = input("Enter 'create' to create a new room or 'join' to join an existing room: ")
            self.room_name = input("Enter room name: ")
            if choice.lower() == 'create':
                self.send_tcp_request(1, self.room_name, '')
            elif choice.lower() == 'join':
                token = input("Enter room token: ")
                self.send_tcp_request(2, self.room_name, token)
            threading.Thread(target=self.receive_messages).start()
            self.chat()

    def send_tcp_request(self, operation, room_name, token):
        room_name_encoded = room_name.encode('utf-8')
        token_encoded = token.encode('utf-8')
        header = struct.pack('!B B', len(room_name_encoded), operation) + room_name_encoded + struct.pack('!B', len(token_encoded)) + token_encoded
        self.tcp_sock.send(header)
        if operation == 1:
            response = self.tcp_sock.recv(1024)
            self.token = response[1:].decode('utf-8')

    def chat(self):
        while True:
            message = input("Enter your message: ").encode('utf-8')
            room_name_encoded = self.room_name.encode('utf-8')
            token_encoded = self.token.encode('utf-8')
            header = struct.pack('!B B', len(room_name_encoded), len(token_encoded))
            packet = header + room_name_encoded + token_encoded + message
            self.udp_sock.sendto(packet, (self.host, self.port + 1))

    def receive_messages(self):
        while True:
            data, _ = self.udp_sock.recvfrom(4096)
            print("Received message:", data.decode('utf-8'))

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 9999
    client = ChatClient(HOST, PORT)
    client.start()
