const tcpClient = require('../js/tcpClient');

document.getElementById('createButton').addEventListener('click', () => {
    const roomName = document.getElementById('roomName').value;
    const userName = document.getElementById('userName').value;
    tcpClient.createRoom(roomName, userName);
});