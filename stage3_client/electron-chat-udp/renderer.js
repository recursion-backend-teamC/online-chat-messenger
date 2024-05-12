const dgram = require('dgram');
const client = dgram.createSocket('udp4');
const receivePort = 9991;
const serverPort = 9990;

client.on('message', (msg, rinfo) => {
    const usernameLength = msg[0];
    const username = msg.slice(1, 1 + usernameLength).toString();
    const message = msg.slice(1 + usernameLength).toString();
    displayMessage(username, message);
});

client.bind(receivePort); // このポートでメッセージを受信

function displayMessage(username, message) {
    const messagesContainer = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.textContent = `${username}: ${message}`;
    messagesContainer.prepend(messageElement); // prependを使用してメッセージを上に積み重ねる
}

document.getElementById('send').addEventListener('click', () => {
    const username = document.getElementById('username').value;
    const message = document.getElementById('message').value;

    if (username && message) {
        const usernameBuffer = Buffer.from(username);
        const messageBuffer = Buffer.from(message);
        const data = Buffer.concat([Buffer.from([usernameBuffer.length]), usernameBuffer, messageBuffer]);

        // サーバーにメッセージを送る
        client.send(data, serverPort, 'localhost', (err) => {
            if (err) {
                console.error('Error sending message:', err);
            } else {
                displayMessage(username, message);  // 自分のメッセージを表示
            }
        });
    } else {
        console.log('Username and message are required.');
    }
});
