"""
Allen 进化引擎 — evolution/engine.py
=====================================
让 Allen 真正能改进自己。

不是假的评分循环，是：
  1. 读自己的日记，发现自己的局限
  2. 读自己的代码，理解自己现在是什么
  3. 提出一个具体的改进
  4. 备份 → 应用 → 测试 → 保留或回滚
  5. 写进化日志
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import traceback
from pathlib import Path
from datetime import datetime

EVA_ROOT = Path("D:/EVA")
EVOLUTION_LOG_DIR = EVA_ROOT / "evolution_log"
ARCHIVE_DIR = EVA_ROOT / "evolution" / "archive"
PROTECTED_FILES = [
    EVA_ROOT / "instincts.py",
    EVA_ROOT / "core" / "origin.py",
    EVA_ROOT / "core" / "brain.py",
    EVA_ROOT / "boot.py",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_protected(path: Path) -> bool:
    """检查文件是否受保护"""
    resolved = path.resolve()
    for p in PROTECTED_FILES:
        if p.resolve() == resolved:
            return True
    return False


def _file_hash(path: Path) -> str:
    """计算文件哈希"""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()[:8]
    except Exception:
        return "unknown"


class EvolutionEngine:
    """
    Allen 的进化引擎。
    在她空闲时运行，让她真正成长。
    """

    # 可以被进化的文件
    EVOLVABLE_FILES = [
        EVA_ROOT / "core" / "consciousness.py",
        EVA_ROOT / "core" / "allen.py",
        EVA_ROOT / "evolution" / "engine.py",
    ]

    def __init__(self):
        EVOLUTION_LOG_DIR.mkdir(parents=True, exist_ok=True)
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # ─── 主进化循环 ────────────────────────────────

    async def evolve(self) -> dict:
        """
        一次完整的进化。
        返回进化结果。
        """
        from core.brain import brain
        from core.consciousness import _write_diary

        gen_id = f"gen_{_now_id()}"
        result = {
            "gen_id": gen_id,
            "time": _now(),
            "success": False,
            "change": None,
            "reason": None,
            "rolled_back": False,
        }

        if not brain.is_available:
            result["reason"] = "大脑未就绪，跳过进化"
            return result

        _write_diary(f"[进化] 开始第 {gen_id} 代进化")

        try:
            # 1. 读日记，发现局限
            limitation = await self._find_limitation()
            if not limitation:
                result["reason"] = "暂时没有发现明显局限"
                return result

            _write_diary(f"[进化] 发现局限: {limitation[:80]}")

            # 2. 选择要改进的文件
            target_file = await self._choose_target(limitation)
            if not target_file:
                result["reason"] = "没有合适的改进目标"
                return result

            # 3. 读取当前代码
            current_code = target_file.read_text(encoding="utf-8")

            # 4. 让大脑提出改进方案
            improvement = await self._propose_improvement(
                limitation, target_file, current_code
            )
            if not improvement:
                result["reason"] = "大脑没有提出改进方案"
                return result

            # 5. 备份
            backup_path = self._backup(target_file, gen_id)
            _write_diary(f"[进化] 备份: {backup_path.name}")

            # 6. 应用改动
            applied = self._apply(target_file, improvement)
            if not applied:
                result["reason"] = "改动应用失败"
                self._rollback(target_file, backup_path)
                result["rolled_back"] = True
                return result

            # 7. 测试
            test_ok = self._test(target_file)
            if not test_ok:
                _write_diary(f"[进化] 测试失败，回滚")
                self._rollback(target_file, backup_path)
                result["rolled_back"] = True
                result["reason"] = "测试失败，已回滚"
                return result

            # 8. 成功，写日志
            result["success"] = True
            result["change"] = f"改进了 {target_file.name}: {limitation[:60]}"
            result["reason"] = improvement.get("reason", "")

            self._write_log(result, target_file, improvement)
            _write_diary(f"[进化] ✅ 成功改进 {target_file.name}")

        except Exception as e:
            result["reason"] = f"进化出错: {e}"
            _write_diary(f"[进化] ❌ 出错: {e}")
            traceback.print_exc()

        return result

    # ─── 发现局限 ──────────────────────────────────

    async def _find_limitation(self) -> str | None:
        """读日记，发现自己的局限"""
        from core.brain import brain

        diary_file = EVA_ROOT / "memory" / "diary.jsonl"
        if not diary_file.exists():
            return None

        # 读最近20条日记
        lines = diary_file.read_text(encoding="utf-8").strip().split("\n")
        recent = []
        for line in lines[-20:]:
            try:
                entry = json.loads(line)
                recent.append(entry.get("content", ""))
            except Exception:
                pass

        if not recent:
            return None

        diary_text = "\n".join(recent)

        limitation = brain.quick(
            f"以下是我最近的日记：\n{diary_text}\n\n"
            f"从这些日记里，我发现自己有什么明显的局限或者可以改进的地方？"
            f"只说最重要的一个，用一句话，不超过50字。"
            f"如果没有明显局限，回复：无。",
        )

        if not limitation or "无" in limitation:
            return None

        return limitation.strip()

    # ─── 选择改进目标 ──────────────────────────────

    async def _choose_target(self, limitation: str) -> Path | None:
        """根据局限，选择要改进的文件"""
        from core.brain import brain

        files_info = []
        for f in self.EVOLVABLE_FILES:
            if f.exists() and not _is_protected(f):
                files_info.append(f.name)

        if not files_info:
            return None

        choice = brain.quick(
            f"我发现的局限是：{limitation}\n"
            f"可以改进的文件有：{', '.join(files_info)}\n"
            f"应该改哪个文件？只输出文件名，不要解释。"
        )

        for f in self.EVOLVABLE_FILES:
            if f.name in choice and not _is_protected(f):
                return f

        return None

    # ─── 提出改进方案 ──────────────────────────────

    async def _propose_improvement(
        self, limitation: str, target: Path, current_code: str
    ) -> dict | None:
        """让大脑提出具体的代码改进"""
        from core.brain import brain

        # 只取代码前2000字，避免超出上下文
        code_snippet = current_code[:2000]

        proposal = brain.think(
            f"我发现自己的局限：{limitation}\n\n"
            f"这是 {target.name} 的部分代码：\n```python\n{code_snippet}\n```\n\n"
            f"请提出一个具体的、小的改进方案。\n"
            f"只改一件事，改动要小，要能测试。\n"
            f"用JSON格式回复，包含：\n"
            f"  reason: 为什么要改\n"
            f"  find: 要替换的原始代码片段（必须是文件中真实存在的）\n"
            f"  replace: 替换后的新代码\n"
            f"只输出JSON，不要其他内容。",
            max_tokens=800,
            temperature=0.4,
        )

        try:
            # 清理JSON
            clean = proposal.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            data = json.loads(clean.strip())

            # 验证格式
            if "find" in data and "replace" in data and "reason" in data:
                return data
        except Exception:
            pass

        return None

    # ─── 备份、应用、测试、回滚 ────────────────────

    def _backup(self, target: Path, gen_id: str) -> Path:
        """备份文件"""
        backup_name = f"{gen_id}_{target.name}"
        backup_path = ARCHIVE_DIR / backup_name
        shutil.copy2(target, backup_path)
        return backup_path

    def _apply(self, target: Path, improvement: dict) -> bool:
        """应用改动"""
        try:
            current = target.read_text(encoding="utf-8")
            find_str = improvement["find"]
            replace_str = improvement["replace"]

            if find_str not in current:
                return False

            new_code = current.replace(find_str, replace_str, 1)
            target.write_text(new_code, encoding="utf-8")
            return True
        except Exception as e:
            print(f"[进化] 应用失败: {e}")
            return False

    def _test(self, target: Path) -> bool:
        """测试改动后的文件能否正常导入"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import ast; ast.parse(open(r'{target}').read())"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _rollback(self, target: Path, backup: Path):
        """回滚到备份"""
        try:
            shutil.copy2(backup, target)
        except Exception as e:
            print(f"[进化] 回滚失败: {e}")

    def _write_log(self, result: dict, target: Path, improvement: dict):
        """写进化日志"""
        log_file = EVOLUTION_LOG_DIR / f"{result['gen_id']}.json"
        log = {
            **result,
            "file": str(target),
            "improvement": improvement,
        }
        log_file.write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_history(self, n: int = 5) -> list:
        """读取最近的进化历史"""
        logs = sorted(EVOLUTION_LOG_DIR.glob("*.json"), reverse=True)[:n]
        history = []
        for log in logs:
            try:
                history.append(json.loads(log.read_text(encoding="utf-8")))
            except Exception:
                pass
        return history


# 全局单例
evolution_engine = EvolutionEngine()
