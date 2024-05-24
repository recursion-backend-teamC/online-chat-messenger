const tcpClient = require('../js/tcpClient');

document.getElementById('joinButton').addEventListener('click', () => {
    const roomName = document.getElementById('roomName').value;
    const userName = document.getElementById('userName').value;
    tcpClient.joinRoom(roomName, userName);
});