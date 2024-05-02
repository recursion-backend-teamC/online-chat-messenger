import socket
import struct
import threading
import uuid

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.rooms = {}  # key: room_name, value: {'token': token, 'participants': set()}
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tcp_sock.bind((self.host, self.port))
        self.udp_sock.bind((self.host, self.port - 1))
        self.tcp_sock.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        threading.Thread(target=self.listen_udp).start()

    def start(self):
        while True:
            client_sock, addr = self.tcp_sock.accept()
            threading.Thread(target=self.handle_client, args=(client_sock, addr)).start()

    def handle_client(self, client_sock, addr):
        try:
            data = client_sock.recv(1024)
            room_name_len, operation = struct.unpack('!B B', data[:2])
            room_name = data[2:2 + room_name_len].decode('utf-8')
            if operation == 1:  # Create room
                token = str(uuid.uuid4())
                self.rooms[room_name] = {'token': token, 'participants': set([addr])}
                response = struct.pack('!B', len(token)) + token.encode('utf-8')
                client_sock.send(response)
            elif operation == 2:  # Join room
                token_len = data[2 + room_name_len]
                token = data[3 + room_name_len:3 + room_name_len + token_len].decode('utf-8')
                if self.rooms.get(room_name, {}).get('token') == token:
                    self.rooms[room_name]['participants'].add(addr)
                    client_sock.send(b'\x01')  # Success
                else:
                    client_sock.send(b'\x00')  # Failure
        finally:
            client_sock.close()

    def listen_udp(self):
        while True:
            data, addr = self.udp_sock.recvfrom(4096)
            room_name_size, token_size = struct.unpack('!B B', data[:2])
            room_name = data[2:2 + room_name_size].decode('utf-8')
            token = data[2 + room_name_size:2 + room_name_size + token_size].decode('utf-8')
            message = data[2 + room_name_size + token_size:]
            if self.rooms.get(room_name, {}).get('token') == token:
                for participant in self.rooms[room_name]['participants']:
                    if participant != addr:
                        self.udp_sock.sendto(data, participant)

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 9999
    server = ChatServer(HOST, PORT)
    server.start()
