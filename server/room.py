from typing import Dict, Optional
from fastapi import WebSocket
import uuid

from data.v1 import get_all_cards
from game.game_state import GameState
from game.player import Player
from game.card import Card
from game.judge import Judge
from game.rules import GameRoundManager

class GameRoom:
    """游戏房间类，管理房间内的玩家、连接和游戏状态"""
    
    def __init__(self):
        self.room_id: str = str(uuid.uuid4())[:8]
        self.players: Dict[str, str] = {}  # player_key -> player_id mapping
        self.connections: Dict[str, WebSocket] = {}  # player_key -> websocket
        self.round_manager:Optional[GameRoundManager]=None
    
    @property
    def game_state(self) -> Optional[GameState]:
        """获取游戏状态，用于兼容性"""
        return self.round_manager.state if self.round_manager else None
    
    def add_player(self) -> tuple[str, str]:
        """添加新玩家到房间
        
        Returns:
            tuple[str, str]: (player_key, player_id)
        """
        if len(self.players) >= 2:
            raise ValueError("Room is full")
        
        player_key = str(uuid.uuid4())
        player_id = f"player{len(self.players) + 1}"
        self.players[player_key] = player_id
        return player_key, player_id
    
    def get_player_id(self, player_key: str) -> Optional[str]:
        """获取玩家ID"""
        return self.players.get(player_key)
    
    def is_full(self) -> bool:
        """检查房间是否已满"""
        return len(self.players) >= 2
    
    def has_player(self, player_key: str) -> bool:
        """检查玩家是否在房间中"""
        return player_key in self.players
    
    def remove_player(self, player_key: str):
        """从房间中移除玩家"""
        if player_key in self.players:
            del self.players[player_key]
        if player_key in self.connections:
            del self.connections[player_key]
    
    def add_connection(self, player_key: str, websocket: WebSocket):
        """添加WebSocket连接"""
        self.connections[player_key] = websocket
    
    def remove_connection(self, player_key: str):
        """移除WebSocket连接"""
        if player_key in self.connections:
            del self.connections[player_key]
    
    def get_connection(self, player_key: str) -> Optional[WebSocket]:
        """获取玩家的WebSocket连接"""
        return self.connections.get(player_key)
    
    def format_game_state(self, requesting_player_key: Optional[str] = None) -> dict:
        """格式化游戏状态为前端所需格式"""
        if not self.round_manager:
            return {
                "room_id": self.room_id,
                "state": "waiting",
                "players": {
                    key: {"key": key, "ready": True, "player_id": player_id} 
                    for key, player_id in self.players.items()
                }
            }
        
        # 获取基础游戏状态
        state = self.round_manager.state.to_dict()
        state["room_id"] = self.room_id
        state["state"] = "finished" if state.pop("is_over") else "playing"
        
        # 转换玩家信息格式
        players_state = {}
        for key, player_id in self.players.items():
            player_data = self.round_manager.state.player1.to_dict() if player_id == "player1" else self.round_manager.state.player2.to_dict()
            player_state = {
                "key": key,
                "ready": True,
                "player_id": player_id,
                "hand_count": player_data["hand_count"],
                "score_count": player_data["score_count"],
                "score_cards": player_data["score_zone"]
            }
            
            # 只向当前玩家展示手牌
            if key == requesting_player_key:
                player_state["hand_cards"] = player_data["hand"]
            
            players_state[key] = player_state
        
        state["players"] = players_state
        return state

    async def broadcast_game_state(self):
        """广播游戏状态到所有连接的客户端"""
        # 创建连接列表的副本进行迭代
        connections = list(self.connections.items())
        for player_key, websocket in connections:
            try:
                state = self.format_game_state(player_key)
                await websocket.send_json({
                    "type": "game_state",
                    "data": state
                })
            except Exception as e:
                # 如果发送失败，移除连接
                self.remove_connection(player_key)

class RoomManager:
    """房间管理器，管理所有游戏房间"""
    
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
    
    def create_room(self) -> GameRoom:
        """创建新房间"""
        room = GameRoom()
        self.rooms[room.room_id] = room
        return room
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """获取房间"""
        return self.rooms.get(room_id)
    
    def remove_room(self, room_id: str):
        """移除房间"""
        if room_id in self.rooms:
            del self.rooms[room_id]