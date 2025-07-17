from typing import Optional
from game.card import Card
from game.judge import Judge
from game.player import Player
from game.game_state import GameState
from data.v1 import get_all_cards


class GameRoundManager:
    """管理一轮完整流程"""
    def __init__(self):
        cards=get_all_cards()
        self.state = GameState(deck=cards)
        self.judge = Judge(mode="cli")
    
    def initialize_game_state(self):
        self.state.shuffle_deck()
    
    def run_one_turn(self,
                     main_card: Card,
                     response_card: Optional[Card] = None,
                     combo_card: Optional[Card] = None):
        """
        运行一整个回合流程，包括三个阶段：
        1. 准备阶段
        2. 行动阶段（主攻 + 反击 + 连击）
        3. 胜负判断
        """
        self.prepare_phase()
        self.action_phase(main_card, response_card, combo_card)
        self.check_end_conditions()
        self.state.switch_turn()

    def prepare_phase(self):
        """准备阶段：当前玩家抽一张牌"""
        player = self.state.get_current_player()
        card = self.state.draw_card(player)
        print(f"\n[准备阶段] {player.player_id} 抽牌：{card}")

    def action_phase(self,
                     main_card: Card,
                     response_card: Optional[Card] = None,
                     combo_card: Optional[Card] = None):
        """
        行动阶段：包括主攻、反击、连击判定
        """
        attacker = self.state.get_current_player()
        defender = self.state.get_opponent_player()

        print(f"\n[主攻] {attacker.player_id} 打出 📄 {main_card.name}")
        self.handle_resolution(attacker, defender, main_card)

        # 反击处理
        if response_card:
            print(f"[反击] {defender.player_id} 使用 🛡️ {response_card.name} 进行反击")
            self.handle_resolution(defender, attacker, response_card, is_counter=True)
            return  # 反击成功与否都终止连击

        # 连击处理（必须主攻成功结算，且对方未反击）
        if combo_card:
            print(f"[连击] {attacker.player_id} 追加 ⚡ {combo_card.name}")
            self.handle_resolution(attacker, defender, combo_card)

    def deal_phase(self, initial_cards: int = 5):
        """发牌阶段：游戏开始时给双方玩家发放初始手牌"""
        print(f"\n[发牌阶段] 每位玩家抽取{initial_cards}张初始手牌")
        
        for _ in range(initial_cards):
            self.state.draw_card(self.state.player1)
            self.state.draw_card(self.state.player2)
            
        print(f"[发牌完成] 玩家1手牌数：{self.state.player1.hand_count()}")
        print(f"[发牌完成] 玩家2手牌数：{self.state.player2.hand_count()}")

    def handle_resolution(self,
                          attacker: Player,
                          defender: Player,
                          card: Card,
                          is_counter: bool = False):
        """
        结算阶段：
        - 释义判定失败 → 弃牌
        - 释义成功 + 典故失败 → 得分但不触发效果
        - 全部成功 → 得分 + 触发效果
        """
        if not self.meaning_judgement(defender, card):
            print(f"[判定❌] 释义错误 → {card.name} 进入弃牌区")
            self.state.move_to_discard(card)
            return

        if not self.story_judgement(defender, card):
            print(f"[判定⚠️] 典故错误 → {card.name} 得分但无效果")
            attacker.add_to_score_zone(card)
            return

        print(f"[判定✅] {card.name} 完全正确 → 加分并触发效果")
        attacker.add_to_score_zone(card)
        self.state.get_zone_counts()  # 用于条件判断
        updated_state = card.execute_effects(self.state.get_zone_counts())
        if card.effect_description:
            print(f"[效果🎯] {card.effect_description}")

    def meaning_judgement(self, defender: Player, card: Card) -> bool:
        """
        模拟对释义的判断
        """
        return self.judge.judge_meaning(card, defender.player_id)

    def story_judgement(self, defender: Player, card: Card) -> bool:
        """
        模拟对典故的判断
        """
        return self.judge.judge_story(card, defender.player_id)

    def check_end_conditions(self):
        """判断是否触发胜负条件"""
        if not self.state.is_game_over():
            return

        print("\n🎯 游戏结束！胜负判定中...")

        p1_score = self.state.player1.score_count()
        p2_score = self.state.player2.score_count()
        if p1_score > p2_score:
            winner = "player1"
        elif p2_score > p1_score:
            winner = "player2"
        else:
            # 比较手牌数
            p1_hand = self.state.player1.hand_count()
            p2_hand = self.state.player2.hand_count()
            if p1_hand > p2_hand:
                winner = "player1"
            elif p2_hand > p1_hand:
                winner = "player2"
            else:
                # 平局 → 后手胜
                winner = "player2" if self.state.current_player_id == "player1" else "player1"

        print(f"🏆 胜者为：{winner}")
