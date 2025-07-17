from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Optional
import json

from server.api import StartGameRequest, PlayCardRequest
from server.room import RoomManager
from game.rules import GameRoundManager

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局房间管理器
room_manager = RoomManager()

@app.get("/")
async def root():
    return {"message": "Welcome to SummerQuest 2025 Game Server"}

@app.post("/api/create_room")
async def create_room():
    room = room_manager.create_room()
    return {"success": True, "room_id": room.room_id}

@app.post("/api/join_room/{room_id}")
async def join_room(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.is_full():
        raise HTTPException(status_code=400, detail="Room is full")
    player_key, player_id = room.add_player()
    print(len(room.players))
    return {
        "success": True,
        "key": player_key,
        "player_count": len(room.players)
    }

@app.post("/api/start_game/{room_id}")
async def start_game(room_id: str, request: StartGameRequest):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room.has_player(request.key):
        raise HTTPException(status_code=403, detail="Not a player in this room")
    if len(room.players) < 2:
        raise HTTPException(status_code=400, detail="Need two players to start")
    room.round_manager=GameRoundManager()
    room.round_manager.initialize_game_state()
    room.round_manager.deal_phase()
    await room.broadcast_game_state()
    return {"success": True,"game_state":room.format_game_state()}



@app.get("/api/game_state/{room_id}")
async def get_game_state(room_id: str, player_key: Optional[str] = None):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {"success": True, "game_state": room.format_game_state(player_key)}

@app.post("/api/play_card/{room_id}")
async def play_card(room_id: str, request: PlayCardRequest):
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if not room.has_player(request.key):
        raise HTTPException(status_code=403, detail="Not a player in this room")
    
    if not room.round_manager:
        raise HTTPException(status_code=400, detail="Game not started")
    
    # 获取玩家ID和游戏状态
    player_id = room.get_player_id(request.key)
    game_state = room.round_manager.state
    
    # 验证是否轮到该玩家
    if game_state.current_player_id != player_id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # 获取玩家对象
    player = game_state.get_current_player()
    
    # 验证卡牌是否在手牌中
    if not player.has_card_id(request.card_id):
        raise HTTPException(status_code=400, detail="Card not in hand")
    
    # 从手牌中移除并打出卡牌
    card = player.play_card(request.card_id)
    
    # 使用GameRoundManager处理回合
    room.round_manager.run_one_turn(card)
    
    # 广播游戏状态
    await room.broadcast_game_state()
    
    return {"status": "success"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_key: Optional[str] = None):
    """WebSocket连接用于实时更新"""
    room = room_manager.get_room(room_id)
    if not room:
        await websocket.close(code=4000, reason="Room not found")
        return
    
    if player_key and not room.has_player(player_key):
        await websocket.close(code=4001, reason="Invalid player key")
        return
    
    connection_id = f"{room_id}_{id(websocket)}"

    await websocket.accept()
    
    # 更新连接信息
    if player_key:
        room.add_connection(player_key, websocket)
        # 立即发送当前游戏状态
    try:
        state = room.format_game_state(player_key)
        await websocket.send_json({
            "type": "game_state",
            "data": state
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    
    try:
        while True:
            data = await websocket.receive_text()
            # 处理WebSocket消息
            message = json.loads(data)
            if message.get("type") == "refresh":
                await room.broadcast_game_state()
    except WebSocketDisconnect:
        if player_key:
            room.remove_connection(player_key)
    except Exception as e:
        if player_key:
            room.remove_connection(player_key)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)