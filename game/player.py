from typing import List, Optional
from dataclasses import dataclass, field

from game.card import Card, CardType


@dataclass
class Player:
    """玩家类"""
    player_id: str # 玩家ID，用于区分（如 "player1", "player2"）
    hand: List[Card] = field(default_factory=list)
    score_zone: List[Card] = field(default_factory=list)

    def draw_card(self, card: Card) -> None:
        """从牌库抽一张牌加入手牌"""
        self.hand.append(card)

    def play_card(self, card_id: int) -> Optional[Card]:
        """
        出牌：根据卡牌ID从手牌中移除并返回
        如果未找到该卡牌，则返回 None
        """
        for i, card in enumerate(self.hand):
            if card.id == card_id:
                return self.hand.pop(i)
        return None

    def add_to_score_zone(self, card: Card) -> None:
        """将卡牌加入得分区"""
        self.score_zone.append(card)

    def discard_card(self, card_id: int) -> Optional[Card]:
        """将某张卡牌从手牌移除（如释义错误时丢弃）"""
        for i, card in enumerate(self.hand):
            if card.id == card_id:
                return self.hand.pop(i)
        return None

    def has_counter_card(self) -> bool:
        """是否拥有可以反击的卡牌（🛡️）"""
        return any(card.has_counter_effect() for card in self.hand)

    def has_combo_card(self) -> bool:
        """是否拥有可以连击的卡牌（⚡）"""
        return any(card.has_combo_effect() for card in self.hand)

    def get_counter_cards(self) -> List[Card]:
        """获取所有反击卡牌"""
        return [card for card in self.hand if card.has_counter_effect()]

    def get_combo_cards(self) -> List[Card]:
        """获取所有连击卡牌"""
        return [card for card in self.hand if card.has_combo_effect()]

    def get_normal_cards(self) -> List[Card]:
        """获取所有普通卡牌"""
        return [card for card in self.hand if card.is_normal_card()]

    def get_hand_card_ids(self) -> List[int]:
        """获取当前所有手牌的 ID 列表"""
        return [card.id for card in self.hand]

    def score_count(self) -> int:
        """得分区卡牌数"""
        return len(self.score_zone)

    def hand_count(self) -> int:
        """手牌数"""
        return len(self.hand)

    def __str__(self) -> str:
        return f"{self.player_id}: 手牌({len(self.hand)}) 得分({len(self.score_zone)})"

    def summary(self) -> str:
        """简要状态概览"""
        hand_cards = ", ".join(str(card) for card in self.hand)
        return f"[{self.player_id}] 🖐️ 手牌: {hand_cards} | 🏆 得分区: {len(self.score_zone)} 张"

    def to_dict(self) -> dict:
        """将玩家状态转换为字典格式"""
        return {
            "player_id": self.player_id,
            "hand_count": self.hand_count(),
            "score_count": self.score_count(),
            "hand": [card.__dict__ for card in self.hand],
            "score_zone": [card.__dict__ for card in self.score_zone]
        }
