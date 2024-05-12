import socket
import threading
import time

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = {} # クライアントのアドレスを格納する辞書
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDPソケットの作成
        self.sock.bind((self.host, self.port)) # ソケットを指定したホストとポートにバインド

    # クライアントからのメッセージを処理するメソッド
    def handle_client(self, data, addr):
        username_len = data[0]
        username = data[1:username_len+1].decode()
        message = data[username_len+1:].decode()
        print(f"Received message from {username}: {message}")
        # print(addr)
        # print(data)
        self.broadcast(data, addr)

    # 受信したメッセージを他のクライアントに転送するメソッド
    def broadcast(self, data, sender_addr):
        # print(self.clients)
        # print(sender_addr)
        for client_addr in self.clients:
            if client_addr != sender_addr:
                # print(f"send to {client_addr}")
                self.sock.sendto(data, client_addr)

    # サーバの起動メソッド
    def start(self):
        print("Server started...")
        while True:
            data, addr = self.sock.recvfrom(4096) # メッセージを受信
            # print('1', data, addr)
            if addr not in self.clients:
                self.clients[addr] = {"last_active_time": time.time()}  # 新しいクライアントを辞書に追加
                print(f"New client connected: {addr}")

            threading.Thread(target=self.handle_client, args=(data, addr)).start() # クライアントを処理するスレッドを開始

            # クライアントの状態を確認し、一定期間アクティブでないクライアントを削除
            # self.remove_inactive_clients()

    # 一定期間メッセージが送信されていないクライアントを削除するメソッド
    # def remove_inactive_clients(self):
    #     current_time = time.time()
    #     inactive_clients = [addr for addr, info in self.clients.items() if current_time - info["last_active_time"] > 60]  # 1分間アクティブでないクライアントを検出
    #     for addr in inactive_clients:
    #         del self.clients[addr]  # クライアントを削除
    #         print(f"Client {addr} removed due to inactivity.")

if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 9990
    server = ChatServer(HOST, PORT)
    server.start()