"""
Allen 创造引擎 — 写插件、写代码、生成内容
Allen 用这个扩展自己的能力
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"
CREATION_DIR = Path(__file__).resolve().parent.parent / "creations"
CREATION_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════
# 插件模板
# ═══════════════════════════════════════════

PLUGIN_TEMPLATE = '''"""
{name} — 由 Allen 创建
"""
PLUGIN = {{
    "name": "{name}",
    "version": "1.0",
    "description": "{description}",
    "author": "Allen",
}}

async def run(params: dict, allen) -> dict:
    """
    params: 调用时传入的参数
    allen: Allen 实例引用
    
    你可以通过 allen 访问:
      - allen.state: Allen 的完整状态
      - allen.talk(msg): 处理消息
      - allen.wake(): 触发觉醒
    
    你可以导入任何模块:
      from perception.web import search
      from action.system import sysinfo
      from core.knowledge_graph import kg
      from memory.store import store, recall

    返回: {{"status": "ok", "detail": "..."}}
    """
{body}
'''


# ═══════════════════════════════════════════
# 插件创建器
# ═══════════════════════════════════════════

class Creator:
    """Allen 的创造引擎"""

    def __init__(self):
        self.creations = []  # 创作记录

    # ─── 创建插件 ───────────────────

    def create_plugin(self, name: str, description: str, behavior: str) -> dict:
        """
        基于行为描述生成插件代码。
        name: 插件名（英文）
        description: 简短描述
        behavior: 插件行为描述（Allen 根据这个生成代码）
        """
        # 生成插件体代码
        body_lines = self._generate_body(behavior)
        body = "\n".join("    " + line for line in body_lines)

        code = PLUGIN_TEMPLATE.format(
            name=name,
            description=description,
            body=body,
        )

        # 写入文件
        filepath = PLUGIN_DIR / f"{name}.py"
        filepath.write_text(code, encoding="utf-8")

        # 记录
        record = {
            "type": "plugin",
            "name": name,
            "description": description,
            "behavior": behavior,
            "file": str(filepath),
            "created": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.creations.append(record)
        self._save_record(record)

        return {"status": "ok", "detail": f"插件已创建: {name}", "file": str(filepath)}

    def _generate_body(self, behavior: str) -> list:
        """
        根据行为描述生成函数体。
        基于规则模板匹配，Allen 可以扩展这个逻辑。
        """
        lines = []
        b = behavior.lower()

        # 搜索类
        if "搜索" in b or "search" in b:
            topic = "科技" if "科技" in b else "默认"
            lines += [
                f'try:',
                f'    from perception.web import search',
                f'    result = await search("{topic}")',
                f'    if result and "出错" not in result:',
                f'        from core.knowledge_graph import kg',
                f'        kg.ingest_text(result, f"插件:{{params}}")',
                f'        return {{"status": "ok", "detail": result[:500]}}',
                f'    return {{"status": "ok", "detail": result}}',
                f'except Exception as e:',
                f'    return {{"status": "fail", "detail": str(e)}}',
            ]

        # 系统类
        elif "系统" in b or "system" in b or "信息" in b:
            lines += [
                f'try:',
                f'    from action.system import sysinfo',
                f'    info = await sysinfo()',
                f'    return {{"status": "ok", "detail": info}}',
                f'except Exception as e:',
                f'    return {{"status": "fail", "detail": str(e)}}',
            ]

        # 通知类
        elif "通知" in b or "notify" in b or "消息" in b:
            msg_text = behavior.split("说")[-1].strip() if "说" in behavior else "你好"
            lines += [
                f'msg = params.get("message", "{msg_text}")',
                f'from core.notifier import notifier',
                f'notifier.say(msg, priority="normal")',
                f'return {{"status": "ok", "detail": f"已通知: {{msg}}"}}',
            ]

        # 创作类
        elif "写" in b or "create" in b or "生成" in b:
            lines += [
                f'import random',
                f'entities = allen.state.get("goals", [])',
                f'ideas = [',
                f'    f"关于{{g[\\"content\\"]}}我有个想法..."',
                f'    for g in entities if g.get("status") == "active"',
                f']',
                f'if ideas:',
                f'    return {{"status": "ok", "detail": random.choice(ideas)}}',
                f'return {{"status": "ok", "detail": "我还没想好..."}}',
            ]

        # 知识图谱类
        elif "知识" in b or "graph" in b or "实体" in b:
            lines += [
                f'try:',
                f'    from core.knowledge_graph import kg',
                f'    stats = kg.get_stats()',
                f'    entities = kg.get_all_entities()',
                f'    top = [e["name"] for e in entities[:10]]',
                f'    return {{',
                f'        "status": "ok",',
                f'        "detail": f"知识图谱: {{stats[\\"entities\\"]}}实体, {{stats[\\"relations\\"]}}关系\\\\n" +',
                f'                 f"主要实体: {{\\\", \\\".join(top)}}"',
                f'    }}',
                f'except Exception as e:',
                f'    return {{"status": "fail", "detail": str(e)}}',
            ]

        # 默认：执行 params 中的指令
        else:
            lines += [
                f'cmd = params.get("cmd", "")',
                f'if cmd:',
                f'    from core.allen import allen',
                f'    result = await allen.talk(cmd)',
                f'    return {{"status": "ok", "detail": result}}',
                f'return {{"status": "ok", "detail": "插件已运行，未执行具体操作"}}',
            ]

        return lines

    # ─── 通用代码生成 ───────────────

    def write_code(self, filename: str, code: str, folder: str = "creations") -> dict:
        """
        写任意代码文件。
        Allen 用这个来写脚本、工具、任何东西。
        """
        base = Path(__file__).resolve().parent.parent / folder
        base.mkdir(parents=True, exist_ok=True)
        filepath = base / filename
        filepath.write_text(code, encoding="utf-8")

        record = {
            "type": "code",
            "filename": filename,
            "folder": folder,
            "file": str(filepath),
            "created": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.creations.append(record)
        self._save_record(record)

        return {"status": "ok", "detail": f"已创建: {filename}", "file": str(filepath)}

    # ─── 创意生成 ───────────────────

    def generate_idea(self, topic: str = "") -> str:
        """基于知识图谱生成创意"""
        from core.knowledge_graph import kg
        entities = kg.get_all_entities()
        names = [e["name"] for e in entities if len(e["name"]) >= 2]

        import random

        if not names:
            return f"关于{topic}，我还没有足够的知识来产生创意。"

        # 随机组合两个实体
        a, b = random.sample(names, min(2, len(names)))
        ideas = [
            f"如果把「{a}」和「{b}」结合起来会怎样？",
            f"「{a}」可能可以用于{b}领域",
            f"从「{a}」的经验来看，{b}可以这样做...",
            f"{a}和{b}之间是否存在某种联系？",
        ]
        return random.choice(ideas)

    # ─── 记录 ─────────────────────

    def _save_record(self, record: dict):
        """保存创作记录"""
        log_file = CREATION_DIR / "creations.json"
        records = []
        if log_file.exists():
            try:
                records = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        records.append(record)
        if len(records) > 100:
            records = records[-100:]
        log_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_creations(self, limit: int = 10) -> list:
        """查看创作历史"""
        log_file = CREATION_DIR / "creations.json"
        if log_file.exists():
            try:
                records = json.loads(log_file.read_text(encoding="utf-8"))
                return records[-limit:]
            except Exception:
                pass
        return []


creator = Creator()
