"""
Allen 视觉感知模块 — 截图 + 鼠标键盘控制
纯 Python，利用 pyautogui 实现"看屏幕"和"操作电脑"
"""
import os
import time
from pathlib import Path
from PIL import Image

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.2
    _HAS_GUI = True
except ImportError:
    _HAS_GUI = False

# 截图保存目录
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def screenshot(resize: int = 1280) -> str:
    """
    截取当前屏幕，保存为 PNG。
    resize: 最长边限制（像素），None 为原尺寸
    返回: 文件路径
    """
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装，无法截图"

    path = str(SCREENSHOT_DIR / f"screen_{int(time.time())}.png")
    img = pyautogui.screenshot()
    if resize and (img.width > resize or img.height > resize):
        ratio = resize / max(img.width, img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    img.save(path)
    return f"[OK] 截图已保存: {path} ({img.width}x{img.height})"


async def screen_info() -> str:
    """获取屏幕基本信息"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    w, h = pyautogui.size()
    x, y = pyautogui.position()
    return f"[SCREEN] 分辨率 {w}x{h}，鼠标位置 ({x},{y})"


async def click(x: int, y: int, button: str = "left") -> str:
    """点击屏幕坐标"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.click(x, y, button=button)
    return f"[CLICK] ({x},{y}) {button}"


async def double_click(x: int, y: int) -> str:
    """双击"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.doubleClick(x, y)
    return f"[DOUBLE_CLICK] ({x},{y})"


async def type_text(text: str) -> str:
    """键盘输入文字"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.write(text, interval=0.02)
    return f"[TYPE] '{text[:50]}' ({len(text)} 字符)"


async def press_key(key: str) -> str:
    """按键"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.press(key)
    return f"[KEY] {key}"


async def hotkey(*keys: str) -> str:
    """组合键"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.hotkey(*keys)
    return f"[HOTKEY] {'+'.join(keys)}"


async def mouse_pos() -> str:
    """获取鼠标位置"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    x, y = pyautogui.position()
    return f"[POS] 鼠标: ({x}, {y})"


async def scroll(clicks: int) -> str:
    """滚动"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.scroll(clicks)
    return f"[SCROLL] {clicks}"


async def drag(x1: int, y1: int, x2: int, y2: int) -> str:
    """拖动"""
    if not _HAS_GUI:
        return "[ERROR] pyautogui 未安装"
    pyautogui.moveTo(x1, y1)
    pyautogui.drag(x2 - x1, y2 - y1, duration=0.3)
    return f"[DRAG] ({x1},{y1}) -> ({x2},{y2})"


def is_available() -> bool:
    """检查 GUI 操作是否可用"""
    return _HAS_GUI
