from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional

from game.card import Card
from game.player import Player


@dataclass
class GameState:
    """游戏状态类，维护全局信息"""
    deck: List[Card]                     # 牌库区
    discard_pile: List[Card] = field(default_factory=list)
    player1: Player = field(default_factory=lambda: Player("player1"))
    player2: Player = field(default_factory=lambda: Player("player2"))
    current_player_id: str = "player1"  # 当前轮到谁
    round_count: int = 1                # 当前回合数

    def reset(self, new_deck: Optional[List[Card]] = None):
        """重置游戏状态
        
        Args:
            new_deck: 可选的新牌库，如果不提供则保持当前牌库
        """
        if new_deck is not None:
            self.deck = new_deck
        self.discard_pile = []
        self.player1 = Player("player1")
        self.player2 = Player("player2")
        self.current_player_id = "player1"
        self.round_count = 1
        self.shuffle_deck()

    def get_current_player(self) -> Player:
        return self.player1 if self.current_player_id == "player1" else self.player2

    def get_opponent_player(self) -> Player:
        return self.player2 if self.current_player_id == "player1" else self.player1

    def switch_turn(self):
        """轮换玩家"""
        self.current_player_id = "player2" if self.current_player_id == "player1" else "player1"
        self.round_count += 1

    def draw_card(self, player: Player) -> Optional[Card]:
        """从牌库抽一张牌到指定玩家手牌"""
        if not self.deck:
            return None
        card = self.deck.pop(0)
        player.draw_card(card)
        return card

    def move_to_discard(self, card: Card):
        """将卡牌送入弃牌堆"""
        self.discard_pile.append(card)

    def is_game_over(self, max_score: int = 10) -> bool:
        """判断是否达到胜利条件或牌库耗尽"""
        return (
            self.player1.score_count() >= max_score
            or self.player2.score_count() >= max_score
            or len(self.deck) == 0
        )

    def get_zone_counts(self) -> Dict[str, int]:
        """获取所有区域卡牌数量（供裁定逻辑使用）"""
        return {
            "deck": len(self.deck),
            "discard": len(self.discard_pile),
            "player1": self.player1.hand_count(),
            "player2": self.player2.hand_count(),
            "score1": self.player1.score_count(),
            "score2": self.player2.score_count(),
        }

    def shuffle_deck(self):
        """洗牌"""
        random.shuffle(self.deck)

    def summary(self) -> str:
        """当前状态简报"""
        return (
            f"回合 {self.round_count} - 当前轮到: {self.current_player_id}\n"
            f"牌库剩余: {len(self.deck)} 张，弃牌区: {len(self.discard_pile)} 张\n"
            f"{self.player1.summary()}\n"
            f"{self.player2.summary()}"
        )

    def to_dict(self) -> dict:
        """将游戏状态转换为字典格式"""
        return {
            "deck_count": len(self.deck),
            "discard_count": len(self.discard_pile),
            "discard_pile": [card.__dict__ for card in self.discard_pile],
            "turn_count": self.round_count,
            "current_player_id": self.current_player_id,
            "player1": self.player1.to_dict(),
            "player2": self.player2.to_dict(),
            "is_over": self.is_game_over()
        }
