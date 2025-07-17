from enum import Enum
from typing import List, Union, Optional
from dataclasses import dataclass


# ==========================
# 枚举定义：卡牌分类与效果执行要素
# ==========================

class CardType(Enum):
    NORMAL = "normal"      # 普通卡牌 📄
    COUNTER = "counter"    # 反击卡牌 🛡️
    COMBO = "combo"        # 连击卡牌 ⚡


class GameZone(Enum):
    H = "deck"         # 牌库区（Heap）
    P1 = "player1"     # 玩家1手牌区
    P2 = "player2"     # 玩家2手牌区
    S1 = "score1"      # 玩家1得分区
    S2 = "score2"      # 玩家2得分区
    A = "discard"      # 弃牌区（Abandon）


class OperatorType(Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "="
    NEQ = "!="


class ActionType(Enum):
    ORDER = "order"    # 按顺序（如从顶部抽）
    SELECT = "select"  # 指定选取
    RANDOM = "random"  # 随机抽取


# ==========================
# 效果组件：IF 条件与 ACTION 动作
# ==========================

@dataclass
class IfCondition:
    operand_a: Union[GameZone, int]
    operator: OperatorType
    operand_b: Union[GameZone, int]

    def evaluate(self, game_state: dict) -> bool:
        """判断 IF 条件是否成立"""
        val_a = self._get_value(self.operand_a, game_state)
        val_b = self._get_value(self.operand_b, game_state)

        match self.operator:
            case OperatorType.GT: return val_a > val_b
            case OperatorType.GTE: return val_a >= val_b
            case OperatorType.LT: return val_a < val_b
            case OperatorType.LTE: return val_a <= val_b
            case OperatorType.EQ: return val_a == val_b
            case OperatorType.NEQ: return val_a != val_b
        return False

    def _get_value(self, operand: Union[GameZone, int], game_state: dict) -> int:
        if isinstance(operand, int):
            return operand
        return game_state.get(operand.value, 0)


@dataclass
class ActionEffect:
    from_zone: GameZone
    to_zone: GameZone
    num: int
    action_type: ActionType

    def execute(self, game_state: dict) -> dict:
        """执行动作效果（当前为接口留空）"""
        # 实际游戏执行逻辑应由服务器调用实现
        return game_state


@dataclass
class CardEffect:
    effects: List[Union[IfCondition, ActionEffect]]

    def execute(self, game_state: dict) -> dict:
        """顺序执行效果链"""
        current_state = game_state.copy()
        for effect in self.effects:
            if isinstance(effect, IfCondition):
                if not effect.evaluate(current_state):
                    break  # 条件不满足，中断整个效果链
            elif isinstance(effect, ActionEffect):
                current_state = effect.execute(current_state)
        return current_state


# ==========================
# 卡牌类定义
# ==========================

@dataclass
class Card:
    id: int
    name: str
    meaning: str
    story: str
    card_type: CardType
    effect_description: str
    effects: Optional[List[CardEffect]] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = []

    def is_normal_card(self) -> bool:
        return self.card_type == CardType.NORMAL

    def has_counter_effect(self) -> bool:
        return self.card_type == CardType.COUNTER

    def has_combo_effect(self) -> bool:
        return self.card_type == CardType.COMBO

    def execute_effects(self, game_state: dict) -> dict:
        current_state = game_state.copy()
        for effect in self.effects:
            current_state = effect.execute(current_state)
        return current_state

    def __str__(self) -> str:
        symbols = {
            CardType.NORMAL: "📄",
            CardType.COUNTER: "🛡️",
            CardType.COMBO: "⚡"
        }
        return f"{symbols.get(self.card_type, '')} {self.name}"

    def __repr__(self) -> str:
        return f"Card(id={self.id}, name='{self.name}', type={self.card_type.value})"


# ==========================
# 工具函数：快速构造卡牌元素
# ==========================

def create_if_condition(operand_a: Union[GameZone, int],
                        operator: OperatorType,
                        operand_b: Union[GameZone, int]) -> IfCondition:
    return IfCondition(operand_a, operator, operand_b)


def create_action_effect(from_zone: GameZone,
                         to_zone: GameZone,
                         num: int,
                         action_type: ActionType) -> ActionEffect:
    return ActionEffect(from_zone, to_zone, num, action_type)


def create_card_effect(effects: List[Union[IfCondition, ActionEffect]]) -> CardEffect:
    return CardEffect(effects)
