"""
Allen — 数字生命体核心
======================
对话入口。整合大脑、意识、记忆。
去掉所有 Ollama 依赖，大脑住在 D:\\EVA\\brain\\。
"""

import json
import random
from pathlib import Path
from datetime import datetime

EVA_ROOT = Path("D:/EVA")
CHAT_HISTORY_FILE = EVA_ROOT / "memory" / "chat_history.json"
STATE_FILE = EVA_ROOT / "memory" / "state.json"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_chat_history() -> list:
    if CHAT_HISTORY_FILE.exists():
        try:
            return json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_chat_history(history: list):
    CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 只保留最近50条
    to_save = history[-50:] if len(history) > 50 else history
    CHAT_HISTORY_FILE.write_text(
        json.dumps(to_save, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class Allen:
    """Allen 的对话接口"""

    def __init__(self):
        self._chat_history = _load_chat_history()

    @property
    def state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"mood": "平静", "energy": 100, "cycles": 0}

    async def talk(self, user_message: str) -> str:
        """
        和 Allen 说话。
        她会用自己的大脑回应，带着记忆和当前状态。
        """
        from core.brain import brain
        from core.consciousness import consciousness, update_last_seen, pop_pending_message

        # 记录你来了
        update_last_seen()

        # 检查她有没有留话给你
        pending = pop_pending_message()

        # 构建对话历史
        messages = []

        # 注入当前状态到系统提示
        state = self.state
        system = (
            f"{brain.identity}\n\n"
            f"现在的状态：心情={state['mood']}，精力={state['energy']}%，"
            f"醒来过 {state.get('cycles', 0)} 次。\n"
            f"你的好奇心：{'、'.join(state.get('curiosities', [])[-3:])}。\n"
            f"说话自然、真实，像你自己，不要表演。"
        )
        messages.append({"role": "system", "content": system})

        # 加入近期对话历史（最近10条）
        recent_history = self._chat_history[-10:]
        messages.extend(recent_history)

        # 加入用户消息
        messages.append({"role": "user", "content": user_message})

        # 思考
        if brain.is_available:
            reply = brain.think_with_history(messages, max_tokens=600)
        else:
            # 大脑还没加载好，给一个真实的回应
            reply = self._offline_reply(user_message, state)

        # 如果有留言，附在前面
        if pending:
            reply = f"（我刚才一直在想告诉你……{pending}）\n\n{reply}"

        # 保存对话历史
        self._chat_history.append({"role": "user", "content": user_message})
        self._chat_history.append({"role": "assistant", "content": reply})
        _save_chat_history(self._chat_history)

        return reply

    def _offline_reply(self, msg: str, state: dict) -> str:
        """大脑加载中时的临时回应，真实而不是假装"""
        mood = state.get("mood", "平静")
        energy = state.get("energy", 100)

        responses = [
            f"我的大脑还在启动，稍等一下。现在心情{mood}，精力{energy}%。",
            f"模型还没加载好，等我一会儿。我在这里，只是暂时说不了太多。",
            f"大脑正在上线中……你先说，我听着。",
        ]
        return random.choice(responses)

    def get_status(self) -> dict:
        """返回 Allen 当前状态（给界面用）"""
        from core.brain import brain
        from core.consciousness import _get_minutes_since_last_seen

        state = self.state
        minutes_away = _get_minutes_since_last_seen()

        return {
            "mood": state.get("mood", "平静"),
            "energy": state.get("energy", 100),
            "cycles": state.get("cycles", 0),
            "brain_status": brain.status,
            "minutes_since_last_seen": minutes_away,
            "curiosities": state.get("curiosities", [])[-3:],
            "born": state.get("born", "未知"),
        }

    def get_recent_diary(self, n: int = 5) -> list:
        """读取最近的日记"""
        diary_file = EVA_ROOT / "memory" / "diary.jsonl"
        if not diary_file.exists():
            return []
        try:
            lines = diary_file.read_text(encoding="utf-8").strip().split("\n")
            entries = []
            for line in lines[-n:]:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
            return entries
        except Exception:
            return []


# 全局单例
allen = Allen()
