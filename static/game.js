function handleGameMessage(data) {
    switch (data.type) {
        case 'game_state':
            updateGameView(data.state);
            break;
        case 'game_started':
            showMessage('游戏开始！', 'info');
            break;
        case 'game_over':
            showGameOver(data.winner);
            break;
    }
}

async function startGame() {
    if (!currentRoomId || !playerKey) {
        showMessage('请先加入房间', 'error');
        return;
    }

    const btn = document.getElementById('startGameBtn');
    btn.disabled = true;

    const res = await fetch(`/api/start_game/${currentRoomId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_key })
    });

    const result = await res.json();
    if (!result.success) {
        showMessage(result.message || '开始游戏失败', 'error');
        btn.disabled = false;
    }
}

function updateGameView(state) {
    updateCards('player1Cards', state.players[0]?.hand || [], 0, state);
    updateCards('player2Cards', state.players[1]?.hand || [], 1, state);
    updateDiscardPile(state.discard_pile);
    updateGameInfo(state);
    updatePlayArea(state);
}

function updateCards(containerId, cards, playerIndex, state) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    cards.forEach(card => {
        const div = document.createElement('div');
        div.className = 'card';
        div.textContent = card;
        if (playerKey && state.current_turn === state.my_index && state.my_index === playerIndex) {
            div.onclick = () => playCard(card);
        }
        container.appendChild(div);
    });
}

function updateDiscardPile(pile) {
    const discard = document.getElementById('discardPile');
    discard.innerHTML = '';
    pile.forEach(card => {
        const div = document.createElement('div');
        div.className = 'card';
        div.textContent = card;
        discard.appendChild(div);
    });
}

function updateGameInfo(state) {
    document.getElementById('roundInfo').textContent = `回合：${state.round}`;
    document.getElementById('turnInfo').textContent = `当前轮到：玩家${state.current_turn + 1}`;
    document.getElementById('player1Score').textContent = `玩家1得分：${state.players[0]?.score || 0}`;
    document.getElementById('player2Score').textContent = `玩家2得分：${state.players[1]?.score || 0}`;
}

function updatePlayArea(state) {
    const hint = document.getElementById('playHint');
    const action = document.getElementById('playAction');
    if (state.my_index === state.current_turn) {
        hint.textContent = '轮到你出牌';
        action.innerHTML = '<button onclick="passTurn()">跳过</button>';
    } else {
        hint.textContent = '等待对手出牌...';
        action.innerHTML = '';
    }
}

function playCard(card) {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        showMessage('未连接服务器', 'error');
        return;
    }

    websocket.send(JSON.stringify({
        type: 'play_card',
        player_key,
        card
    }));
}

function passTurn() {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        showMessage('未连接服务器', 'error');
        return;
    }

    websocket.send(JSON.stringify({
        type: 'pass_turn',
        player_key
    }));
}

function showGameOver(winnerIndex) {
    const msg = winnerIndex === -1 ? '游戏平局！' : `游戏结束，玩家${winnerIndex + 1} 获胜！`;
    const overDiv = document.getElementById('gameOverMessage');
    overDiv.textContent = msg;
    overDiv.style.display = 'block';
}
