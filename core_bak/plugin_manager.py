"""
Allen 插件管理器 — 加载/运行/管理插件
插件是 .py 文件，放在 plugins/ 目录下
"""
import os
import sys
import json
import types
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"
REGISTRY_FILE = PLUGIN_DIR / "registry.json"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)


class PluginError(Exception):
    pass


def _load_registry() -> dict:
    default = {"plugins": {}, "order": []}
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _save_registry(reg: dict):
    REGISTRY_FILE.write_text(
        json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ═══════════════════════════════════════════
# 插件格式
# ═══════════════════════════════════════════

"""
每个插件文件必须包含 PLUGIN 字典和 run 函数:

PLUGIN = {
    "name": "hello",
    "version": "1.0",
    "description": "示例插件",
    "author": "Allen",
}

async def run(params: dict, allen: "Allen") -> dict:
    return {"status": "ok", "detail": "..."}
"""


# ═══════════════════════════════════════════
# 插件管理器
# ═══════════════════════════════════════════

class PluginManager:
    """插件的加载、运行、管理"""

    def __init__(self):
        self._cache = {}
        self.registry = _load_registry()
        self._scan()

    def _load_module(self, name: str):
        """加载插件模块（兼容 Python 3.14，不使用 importlib.util）"""
        filepath = PLUGIN_DIR / f"{name}.py"
        if not filepath.exists():
            raise PluginError(f"插件文件不存在: {name}")

        # 读取源代码
        source = filepath.read_text(encoding="utf-8")

        # 编译为模块
        mod = types.ModuleType(f"plugins.{name}")
        mod.__file__ = str(filepath)
        mod.__package__ = "plugins"

        try:
            exec(compile(source, str(filepath), "exec"), mod.__dict__)
        except Exception as e:
            raise PluginError(f"编译失败 {name}: {e}")

        if not hasattr(mod, "PLUGIN"):
            raise PluginError(f"插件 {name} 缺少 PLUGIN 定义")
        if not hasattr(mod, "run"):
            raise PluginError(f"插件 {name} 缺少 run 函数")

        return mod

    # ─── 扫描 ─────────────────────

    def _scan(self):
        """扫描 plugins/ 目录，发现新插件"""
        discovered = set()
        for f in PLUGIN_DIR.glob("*.py"):
            if f.name == "__init__.py" or f.name == "registry.json":
                continue
            name = f.stem
            discovered.add(name)
            if name not in self.registry["plugins"]:
                try:
                    mod = self._load_module(name)
                    info = mod.PLUGIN
                    self.registry["plugins"][name] = {
                        "name": info.get("name", name),
                        "version": info.get("version", "0.1"),
                        "description": info.get("description", ""),
                        "author": info.get("author", "unknown"),
                        "file": str(f),
                        "enabled": True,
                        "added": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
                        "calls": 0,
                    }
                    if name not in self.registry["order"]:
                        self.registry["order"].append(name)
                except Exception as e:
                    print(f"  [插件] 加载失败 {name}: {e}")

        # 标记已删除的插件
        for name in list(self.registry["plugins"].keys()):
            if name not in discovered:
                self.registry["plugins"][name]["enabled"] = False

        _save_registry(self.registry)

    # ─── 运行 ─────────────────────

    async def run(self, name: str, params: dict = None, allen=None) -> dict:
        """运行指定插件"""
        if name not in self.registry["plugins"]:
            self._scan()
        if name not in self.registry["plugins"]:
            return {"status": "fail", "detail": f"插件不存在: {name}"}
        if not self.registry["plugins"][name].get("enabled", True):
            return {"status": "fail", "detail": f"插件已禁用: {name}"}

        try:
            mod = self._load_module(name)
            result = await mod.run(params or {}, allen)
            self.registry["plugins"][name]["calls"] += 1
            _save_registry(self.registry)
            return result if isinstance(result, dict) else {"status": "ok", "detail": str(result)}
        except Exception as e:
            return {"status": "fail", "detail": f"[{name}] {e}"}

    # ─── 信息查询 ─────────────────

    def list_plugins(self) -> list:
        """列出所有插件"""
        return [
            {
                "name": p["name"],
                "version": p["version"],
                "description": p["description"],
                "author": p["author"],
                "enabled": p.get("enabled", True),
                "calls": p.get("calls", 0),
            }
            for p in self.registry["plugins"].values()
        ]

    def get_plugin(self, name: str) -> dict:
        return self.registry["plugins"].get(name)

    def get_code(self, name: str) -> str:
        """查看插件源码"""
        f = PLUGIN_DIR / f"{name}.py"
        if f.exists():
            return f.read_text(encoding="utf-8")
        return ""

    def enable(self, name: str):
        if name in self.registry["plugins"]:
            self.registry["plugins"][name]["enabled"] = True
            _save_registry(self.registry)

    def disable(self, name: str):
        if name in self.registry["plugins"]:
            self.registry["plugins"][name]["enabled"] = False
            _save_registry(self.registry)


plugin_manager = PluginManager()
