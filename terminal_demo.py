from game.card import Card, CardType
from game.player import Player
from game.game_state import GameState
from game.judge import Judge
from game.rules import GameRoundManager
from data.v1 import get_all_cards, get_card_by_id


def print_player_status(player: Player):
    """打印玩家状态"""
    print(f"\n{player.player_id} 的状态:")
    print(f"手牌({len(player.hand)}): {' '.join(str(card) for card in player.hand)}")
    print(f"得分区({len(player.score_zone)}): {' '.join(str(card) for card in player.score_zone)}")


def get_card_choice(player: Player, valid_types: list[CardType] = None) -> Card:
    """获取玩家选择的卡牌"""
    while True:
        print(f"\n{player.player_id} 的手牌:")
        for i, card in enumerate(player.hand):
            print(f"{i + 1}. {card}")
        
        try:
            choice = input("请选择要使用的卡牌编号（输入0放弃）: ").strip()
            if choice == '0':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(player.hand):
                card = player.hand[idx]
                if valid_types and card.card_type not in valid_types:
                    print(f"❌ 当前只能使用以下类型的卡牌: {[t.value for t in valid_types]}")
                    continue
                return card
        except (ValueError, IndexError):
            pass
        print("❌ 无效的选择，请重试")


def main():
    # 初始化游戏
    game = GameRoundManager()
    game.initialize_game_state()
    game.deal_phase()
    
    print("\n=== 游戏开始 ===")
    print(game.state.summary())
    
    # 主游戏循环
    while not game.state.is_game_over():
        current_player = game.state.get_current_player()
        opponent = game.state.get_opponent_player()
        
        # 准备阶段：抽牌
        game.prepare_phase()
        print_player_status(current_player)
        print_player_status(opponent)
        
        # 出牌阶段
        print(f"\n[主攻] {current_player.player_id} 的回合")
        main_card = get_card_choice(current_player)
        if not main_card:
            print("放弃出牌")
            game.state.switch_turn()
            continue
            
        current_player.play_card(main_card.id)
        print(f"[主攻] {current_player.player_id} 打出 {main_card}")
        
        # 反击阶段
        response_card = None
        if opponent.has_counter_card():
            print(f"\n[反击] {opponent.player_id} 可以使用反击卡")
            response_card = get_card_choice(opponent, [CardType.COUNTER])
            if response_card:
                opponent.play_card(response_card.id)
                print(f"[反击] {opponent.player_id} 使用 {response_card} 进行反击")
        
        # 连击阶段
        combo_card = None
        if not response_card and current_player.has_combo_card():
            print(f"\n[连击] {current_player.player_id} 可以使用连击卡")
            combo_card = get_card_choice(current_player, [CardType.COMBO])
            if combo_card:
                current_player.play_card(combo_card.id)
                print(f"[连击] {current_player.player_id} 追加 {combo_card}")
        
        # 结算阶段
        game.run_one_turn(main_card, response_card, combo_card)
        
        print("\n当前游戏状态:")
        print(game.state.summary())
    
    # 游戏结束
    print("\n=== 游戏结束 ===")
    p1_score = game.state.player1.score_count()
    p2_score = game.state.player2.score_count()
    print(f"Player 1 得分: {p1_score}")
    print(f"Player 2 得分: {p2_score}")
    
    if p1_score > p2_score:
        print("Player 1 获胜！")
    elif p2_score > p1_score:
        print("Player 2 获胜！")
    else:
        print("平局！")


if __name__ == "__main__":
    main()