from enum import Enum
from typing import List, Union, Optional,TYPE_CHECKING
from dataclasses import dataclass
if TYPE_CHECKING:
    from game.game_state import GameState


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

    def evaluate(self, game_state: 'GameState') -> bool:
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

    def _get_value(self, operand: Union[GameZone, int], game_state: 'GameState') -> int:
        if isinstance(operand, int):
            return operand
        match operand:
            case GameZone.H: return len(game_state.deck)
            case GameZone.P1: return game_state.player1.hand_count()
            case GameZone.P2: return game_state.player2.hand_count()
            case GameZone.S1: return game_state.player1.score_count()
            case GameZone.S2: return game_state.player2.score_count()
            case GameZone.A: return len(game_state.discard_pile)
        return 0


@dataclass
class ActionEffect:
    from_zone: GameZone
    to_zone: GameZone
    num: int
    action_type: ActionType

    def execute(self, game_state: 'GameState') -> 'GameState':
        """执行动作效果，直接修改 GameState 对象"""
        # 获取源区域和目标区域的卡牌列表引用
        from_cards = self._get_zone_cards(game_state, self.from_zone)
        if not from_cards:
            return game_state

        # 根据动作类型选择卡牌
        cards_to_move = []
        match self.action_type:
            case ActionType.ORDER:
                # 从顶部开始取指定数量
                cards_to_move = from_cards[:min(self.num, len(from_cards))]
            case ActionType.RANDOM:
                # 随机选择指定数量
                if len(from_cards) > self.num:
                    cards_to_move = random.sample(from_cards, self.num)
                else:
                    cards_to_move = from_cards.copy()
            case ActionType.SELECT:
                # 暂不支持指定选取
                return game_state

        # 从源区域移除卡牌
        for card in cards_to_move:
            from_cards.remove(card)

        # 将卡牌添加到目标区域
        self._add_to_zone(game_state, self.to_zone, cards_to_move)

        return game_state

    def _get_zone_cards(self, game_state: 'GameState', zone: GameZone) -> List['Card']:
        """获取指定区域的卡牌列表引用"""
        match zone:
            case GameZone.H: return game_state.deck
            case GameZone.P1: return game_state.player1.hand
            case GameZone.P2: return game_state.player2.hand
            case GameZone.S1: return game_state.player1.score_zone
            case GameZone.S2: return game_state.player2.score_zone
            case GameZone.A: return game_state.discard_pile
        return []

    def _add_to_zone(self, game_state: 'GameState', zone: GameZone, cards: List['Card']):
        """将卡牌添加到指定区域"""
        match zone:
            case GameZone.H: game_state.deck.extend(cards)
            case GameZone.P1: 
                for card in cards:
                    game_state.player1.draw_card(card)
            case GameZone.P2:
                for card in cards:
                    game_state.player2.draw_card(card)
            case GameZone.S1:
                for card in cards:
                    game_state.player1.add_to_score_zone(card)
            case GameZone.S2:
                for card in cards:
                    game_state.player2.add_to_score_zone(card)
            case GameZone.A: game_state.discard_pile.extend(cards)


@dataclass
class CardEffect:
    effects: List[Union[IfCondition, ActionEffect]]

    def execute(self, game_state: 'GameState') -> 'GameState':
        """顺序执行效果链"""
        for effect in self.effects:
            if isinstance(effect, IfCondition):
                if not effect.evaluate(game_state):
                    break  # 条件不满足，中断整个效果链
            elif isinstance(effect, ActionEffect):
                game_state = effect.execute(game_state)
        return game_state


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

    def execute_effects(self, game_state: 'GameState') -> 'GameState':
        """执行卡牌的所有效果"""
        for effect in self.effects:
            game_state = effect.execute(game_state)
        return game_state

    def __str__(self) -> str:
        symbols = {
            CardType.NORMAL: "📄",
            CardType.COUNTER: "🛡️",
            CardType.COMBO: "⚡"
        }
        effect_text = f"------{self.effect_description}" if self.effect_description else ""
        return f"\n{symbols.get(self.card_type, '')} {self.name}{effect_text}\n"

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
