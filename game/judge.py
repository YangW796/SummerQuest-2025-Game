from difflib import SequenceMatcher
from  game.card import Card


class Judge:
    """裁定器：判断玩家描述是否符合成语释义/典故"""

    def __init__(self, mode: str = "cli"):
        """
        mode: 'cli' 表示从命令行输入判断；'auto' 可接入 AI 判断或全自动模式。
        """
        self.mode = mode

    def judge_meaning(self, card: Card, player_id: str) -> bool:
        """
        判断释义正确性（默认 CLI 输入）
        Returns:
            True 表示正确，False 表示错误
        """
        if self.mode == "cli":
            answer = input(f"🧠 [{player_id}] 请口述成语『{card.name}』的释义: ").strip()
            return self._fuzzy_match(answer, card.meaning)
        elif self.mode == "auto":
            return True  # 后续可接 AI 模型判断
        else:
            raise ValueError("未知 Judge 模式")

    def judge_story(self, card: Card, player_id: str) -> bool:
        """
        判断典故正确性
        """
        if self.mode == "cli":
            answer = input(f"📚 [{player_id}] 请简述『{card.name}』的典故: ").strip()
            return self._fuzzy_match(answer, card.story)
        elif self.mode == "auto":
            return True
        else:
            raise ValueError("未知 Judge 模式")

    def _fuzzy_match(self, user_input: str, target: str, threshold: float = 0.6) -> bool:
        """
        使用 difflib 进行模糊匹配
        """
        score = SequenceMatcher(None, user_input, target).ratio()
        print(f"🔍 匹配度: {score:.2f}")
        return score >= threshold
