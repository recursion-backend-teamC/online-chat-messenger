import socket
import threading

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.username = input("Enter your username: ")
        self.sock.sendto(bytes([len(self.username)]) + self.username.encode(), (self.host, self.port))

        # スレッドを開始して他のクライアントからのメッセージを受信する
        threading.Thread(target=self.receive_messages).start()

    def send_message(self):
        while True:
            message = input("Enter message: ")
            if message.lower() == "quit":
                break
            self.sock.sendto(bytes([len(self.username)]) + self.username.encode() + message.encode(), (self.host, self.port))


    def receive_messages(self):
        while True:
            data, addr = self.sock.recvfrom(4096)
            username_len = data[0]
            username = data[1:username_len+1].decode()
            message = data[username_len+1:].decode()
            print(f"{username}: {message}")

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 9990
    client = ChatClient(HOST, PORT)
    client.send_message()