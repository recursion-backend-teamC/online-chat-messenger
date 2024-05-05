# online-chat-messenger

### 実行方法(Macの場合)

1. 以下を実行(クライアントごとに異なるIPアドレスを振り分けるための前処理)
sh set_loopback.sh

2. プログラムを実行(それぞれ別のターミナルで)
ターミナル1: python3 server.py (サーバーを実行)
ターミナル2: python3 client.py (1人目のクライアントを実行)
ターミナル3: python3 client.py (1人目のクライアントを実行)

