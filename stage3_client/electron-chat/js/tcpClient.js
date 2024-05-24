const net = require('net');
const serverHost = 'localhost';
const tcpPort = 9998;

// TCPクライアントの作成
const client = new net.Socket();

// サーバーへの接続
client.connect(tcpPort, serverHost, () => {
    console.log('Connected to server on TCP');
});


// データ受信イベント
client.on('data', (data) => {
    const operation = data.readUInt8(0);
    const state = data.readUInt8(1);

    console.log('in once: ', operation)
    console.log(state)

    // ルーム作成
    if (operation === 1 && state === 1) {
        console.log("Server acknowledged the room creation request.");
        // サーバーが応答を認めた後のトークン取得
        const token = data.slice(2).toString('utf8').trim();
        console.log("Room created successfully. Token:", token);
        localStorage.setItem('chatToken', token);
        if (typeof window !== 'undefined') {
            window.location.href = '../views/chat.html'; // チャットページへ遷移
        }
    }
    // ルーム参加
    else if (operation === 2 && state === 1) {
        console.log("Server acknowledged the room join request.");
        const token = data.slice(2).toString('utf8').trim();
        console.log("Joined room successfully. Token:", token);
        localStorage.setItem('chatToken', token);
        window.location.href = '../views/chat.html'; // チャットページへ遷移
    
    } else {
        console.log("Failed to get acknowledgment from server.");
    }
});

// エラーイベント
client.on('error', (err) => {
    console.error('Error:', err);
});

// サーバーからの切断イベント
client.on('close', () => {
    console.log('Connection closed');
});

// チャットルーム作成要求
function createRoom(roomName, operationPayload) {
    const roomNameBuffer = Buffer.from(roomName, 'utf-8');
    const operationPayloadBuffer = Buffer.from(operationPayload, 'utf-8');
    
    const header = Buffer.alloc(32);
    header.writeUInt8(roomNameBuffer.length, 0); // ルーム名の長さ
    header.writeUInt8(1, 1); // 操作コード: 1 (部屋作成)
    header.writeUInt8(0, 2); // ステート: 0 (初期リクエスト)
    operationPayloadBuffer.length.toString().padEnd(29, '\0').split('').forEach((char, index) => {
        header.writeUInt8(char.charCodeAt(0), 3 + index); // ペイロードサイズ（29バイト固定）
    });
    
    const message = Buffer.concat([header, roomNameBuffer, operationPayloadBuffer]);
    client.write(message);

    // todo エラー処理を入れるべき
    localStorage.setItem('roomName', roomName); // ルーム名を保存
    localStorage.setItem('userName', operationPayload); // ユーザー名を保存

}

// チャットルーム参加要求
function joinRoom(roomName, userName) {
    const roomNameBuffer = Buffer.from(roomName);
    const userNameBuffer = Buffer.from(userName);
    const header = Buffer.alloc(32);
    header.writeUInt8(roomNameBuffer.length, 0);
    header.writeUInt8(2, 1); // Operation: Join Room
    header.writeUInt8(0, 2); // State: Initial request
    header.writeUInt32BE(userNameBuffer.length, 28);
    const message = Buffer.concat([header, roomNameBuffer, userNameBuffer]);
    client.write(message);

    // todo エラー処理を入れるべき
    localStorage.setItem('roomName', roomName); // ルーム名を保存
    localStorage.setItem('userName', userName); // ユーザー名を保存
}

module.exports = {
    createRoom,
    joinRoom
};
