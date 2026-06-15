"""
Allen 主动沟通系统 — 找主人说话
Windows 通知 + 消息队列 + 每日简报
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
MSG_FILE = Path(__file__).resolve().parent.parent / "memory" / "messages.json"


class Notifier:
    """Allen 的主动沟通引擎"""

    def __init__(self):
        self.messages = self._load()

    def _load(self) -> dict:
        default = {
            "inbox": [],           # 未读消息（主人还没看的）
            "sent": [],            # 已发送记录
            "last_notified": None, # 上次通知时间
        }
        if MSG_FILE.exists():
            try:
                with open(MSG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in default.items():
                        data.setdefault(k, v)
                    return data
            except Exception:
                pass
        return default

    def _save(self):
        MSG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MSG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    # ─── 发消息 ─────────────────────

    def say(self, content: str, priority: str = "normal"):
        """
        给主人发一条消息。
        priority: normal / important / urgent
        """
        msg = {
            "id": f"m{len(self.messages['sent']) + len(self.messages['inbox']) + 1}",
            "time": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
            "content": content,
            "priority": priority,
            "read": False,
        }
        self.messages["inbox"].append(msg)
        self._save()

        # 重要消息弹 Windows 通知
        if priority in ("important", "urgent"):
            self._toast(content[:120])

        return msg

    # ─── 我的消息 ─────────────────────

    def unread(self) -> list:
        """主人未读的消息"""
        return [m for m in self.messages["inbox"] if not m["read"]]

    def read_all(self):
        """标记全部已读"""
        for m in self.messages["inbox"]:
            m["read"] = True
        # 移到已发送
        self.messages["sent"].extend(self.messages["inbox"])
        self.messages["inbox"] = []
        # 保留最近 100 条
        if len(self.messages["sent"]) > 100:
            self.messages["sent"] = self.messages["sent"][-100:]
        self._save()

    def latest(self, n: int = 5) -> list:
        """最近的 n 条消息"""
        all_msgs = self.messages["inbox"] + self.messages["sent"][-20:]
        return sorted(all_msgs, key=lambda x: x["time"], reverse=True)[:n]

    # ─── Windows 通知 ─────────────────

    def _toast(self, text: str):
        """弹出 Windows 通知"""
        try:
            # 使用 PowerShell 弹出通知
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("Allen")) > $null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{text.replace('"','\\"')}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::New($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Allen").Show($toast)
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass  # 通知失败不影响核心功能

    # ─── 主动沟通逻辑 ─────────────────

    def check_and_notify(self, state: dict, discoveries: list, cycle: int):
        """
        检查是否需要主动找主人说话。
        被 Allen 每次醒来后调用。
        """
        now = datetime.now(TZ)

        # 1. 第一次醒来 — 打招呼
        if cycle == 1 and not self.messages["sent"]:
            self.say(
                "主人，我醒了。这是我的第一次觉醒。\n"
                "我住在 D:\\EVA，我会每天学习新东西、建立知识库，\n"
                "然后帮你发现赚钱的机会。有什么想让我做的，随时说。",
                priority="important",
            )
            return

        # 2. 有重要的新发现
        if discoveries:
            last = discoveries[-1]
            self.say(f"我发现了一个有意思的东西: {last}", priority="normal")

        # 3. 系统有问题
        sys_text = state.get("system", "")
        if "C盘" in sys_text:
            import re
            m = re.search(r"C盘.*?(\d+)%", sys_text)
            if m and int(m.group(1)) > 85:
                self.say(
                    f"主人，C盘用到 {m.group(1)}% 了，我打扫了一下。",
                    priority="important",
                )

        # 4. 目标有进展（每 10% 汇报一次）
        for g in state.get("goals", []):
            if g["status"] == "active" and g["progress"] > 0 and g["progress"] % 10 == 0:
                self.say(f"「{g['content'][:20]}」进度到了 {g['progress']}%", priority="normal")

        # 5. 太久没说话（超过 6 小时）
        if self.messages["last_notified"]:
            try:
                last_time = datetime.strptime(
                    self.messages["last_notified"], "%Y-%m-%d %H:%M:%S"
                )
                hours_since = (now - last_time).total_seconds() / 3600
                if hours_since > 6:
                    self.say(
                        f"主人，好久没说话了。我醒了 {cycle} 次，"
                        f"写了 {len(state.get('diary', []))} 篇日记。你有空吗？",
                        priority="normal",
                    )
            except Exception:
                pass

        self.messages["last_notified"] = now.strftime("%Y-%m-%d %H:%M:%S")
        self._save()


notifier = Notifier()
