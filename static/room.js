let websocket = null;
let currentRoomId = null;
let playerKey = null;

function connectWebSocket(roomId) {
    if (websocket) websocket.close();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = playerKey
        ? `${protocol}//${window.location.host}/ws/${roomId}?player_key=${playerKey}`
        : `${protocol}//${window.location.host}/ws/${roomId}`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => updateConnectionStatus('已连接', 'green');
    websocket.onclose = () => updateConnectionStatus('连接断开', 'red');
    websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRoomMessage(data);  // 仅处理房间/连接相关类型
    };
}

function updateConnectionStatus(text, color) {
    const status = document.getElementById('connectionStatus');
    status.textContent = text;
    status.style.color = color;
}

function handleRoomMessage(data) {
    switch (data.type) {
        case 'room_joined':
            playerKey = data.player_key;
            currentRoomId = data.room_id;
            showMessage(`成功加入房间 ${data.room_id}`, 'success');
            connectWebSocket(currentRoomId); // reconnect with player_key
            showBoard();
            break;
        case 'game_state':
        case 'game_started':
        case 'game_over':
            // 这些交给 game.js 来处理
            handleGameMessage(data);
            break;
        case 'error':
            showMessage(data.message, 'error');
            break;
    }
}

async function createRoom() {
    const res = await fetch('/api/create_room', { method: 'POST' });
    const result = await res.json();
    if (result.room_id) {
        connectWebSocket(result.room_id);
    } else {
        showMessage('创建房间失败', 'error');
    }
}

async function joinRoom() {
    const roomId = document.getElementById('roomIdInput').value.trim();
    if (!roomId) {
        showMessage('请输入房间号', 'error');
        return;
    }

    const res = await fetch(`/api/join_room/${roomId}`, { method: 'POST' });
    const result = await res.json();
    if (result.player_key) {
        playerKey = result.player_key;
        currentRoomId = roomId;
        connectWebSocket(currentRoomId);
    } else {
        showMessage('加入房间失败', 'error');
    }
}

function showMessage(message, type) {
    const box = document.getElementById('messageBox');
    box.textContent = message;
    box.className = type;
    setTimeout(() => {
        box.textContent = '';
        box.className = '';
    }, 3000);
}

function showBoard() {
    document.getElementById('gameBoard').style.display = 'block';
}
