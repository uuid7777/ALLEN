"""
Allen LLM 引擎 — 调用本地 Ollama 多模型
Qwen 2.5 7B（主脑）+ MiniCPM-V（视觉）
支持自动重连和离线降级
"""
import json
import requests
import base64
import subprocess
import time
from pathlib import Path

OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_BIN = r"D:\Ollama\ollama.exe"
TIMEOUT = 300


class LLMEngine:
    """多模型 LLM 引擎"""

    MODELS = {
        "brain": "qwen2.5:7b",   # 主脑：7B，8GB显存流畅运行
        "fast": "qwen2.5:7b",    # 快速任务也用7B
        "vision": "minicpm-v",   # 视觉分析
    }

    def __init__(self):
        # 5分钟无对话自动卸载，释放7.6GB内存
        self._keep_alive = "5m"
        self._connection_ok = False       # 缓存上次连接结果
        self._last_check = 0.0            # 上次检查时间
        self._check_interval = 30         # 连接检查缓存秒数
        # 记录使用的模型名
        self._using_model = self.MODELS["brain"]

    # ─── 连接管理 ─────────────────────

    def check_connection(self) -> bool:
        """检查 Ollama 是否在线（结果缓存30秒，不频繁请求）"""
        now = time.time()
        if now - self._last_check < self._check_interval:
            return self._connection_ok
        self._last_check = now
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            self._connection_ok = r.status_code == 200
        except Exception:
            self._connection_ok = False
        return self._connection_ok

    @property
    def is_available(self) -> bool:
        """判断大脑是否在线"""
        return self.check_connection()

    def auto_repair(self) -> str:
        """尝试重新启动 Ollama 进程"""
        ollama_exe = OLLAMA_BIN
        if not Path(ollama_exe).exists():
            return "Ollama 未安装"

        try:
            # 先检查进程是否在跑
            r = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                capture_output=True, text=True, timeout=5,
            )
            if "ollama.exe" not in r.stdout:
                # 启动 Ollama
                subprocess.Popen(
                    [ollama_exe, "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)
                if self.check_connection():
                    return "大脑重新连接成功"
                return "已启动 Ollama，但尚未响应"
            else:
                # 进程在但无响应 → 杀进程重启
                subprocess.run(
                    ["taskkill", "/F", "/IM", "ollama.exe"],
                    capture_output=True, timeout=5,
                )
                time.sleep(1)
                subprocess.Popen(
                    [ollama_exe, "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)
                if self.check_connection():
                    return "大脑重新连接成功"
                return "已重启 Ollama，但尚未响应"
        except Exception as e:
            return f"自动修复失败: {e}"

    # ─── 基础调用 ─────────────────────

    def chat(self, model_key: str, messages: list, tools: list = None,
             stream: bool = False) -> dict:
        """调用 Ollama chat API"""
        # 连接检查
        if not self.check_connection():
            return {"error": "离线模式：大脑未连接", "offline": True}

        model = self.MODELS.get(model_key, model_key)
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 500,      # 回复长度适中，兼顾速度和完整性
            }
        }
        print(f"[LLM] 请求: model={model} tools={'yes' if tools else 'no'}", flush=True)
        # tools 分开发送（qwen27b 带 tools 时响应极慢，先试不带）
        if tools:
            payload["tools"] = tools
        if self._keep_alive:
            payload["keep_alive"] = self._keep_alive
        try:
            print(f"[LLM] POST {OLLAMA_HOST}/api/chat model={model}", flush=True)
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data
        except requests.exceptions.Timeout:
            print(f"[LLM] 超时: model={model}", flush=True)
            return {"error": f"模型 {model} 响应超时"}
        except requests.exceptions.ConnectionError:
            print(f"[LLM] 无法连接: {OLLAMA_HOST}", flush=True)
            return {"error": "无法连接 Ollama，请确认 Ollama 正在运行"}
        except Exception as e:
            print(f"[LLM] 错误: {e}", flush=True)
            return {"error": str(e)}

    def think(self, prompt: str, system: str = "", tools: list = None) -> str:
        """主脑思考：完整对话"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = self.chat("brain", messages, tools)
        if "error" in result:
            return result["error"]
        return result.get("message", {}).get("content", "")

    def quick(self, prompt: str, system: str = "") -> str:
        """快速任务：Gemma 处理"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        result = self.chat("fast", messages)
        if "error" in result:
            # 降级到主脑
            result = self.chat("brain", messages)
        return result.get("message", {}).get("content", "")

    def see(self, image_path: str, prompt: str = "描述这张图片的内容") -> str:
        """视觉分析：用 MiniCPM-V 看图片。自动压缩大图。"""
        try:
            path = Path(image_path)
            if not path.exists():
                return f"图片不存在: {image_path}"

            # 用 PIL 压缩图片
            try:
                from PIL import Image
                img = Image.open(path)
                max_dim = 640
                if img.width > max_dim or img.height > max_dim:
                    ratio = max_dim / max(img.width, img.height)
                    new_w = int(img.width * ratio)
                    new_h = int(img.height * ratio)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                import io
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            except ImportError:
                with open(path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")

            # Ollama 标准格式：images 字段
            payload = {
                "model": self.MODELS["vision"],
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [img_b64],
                    }
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 512},
            }
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json=payload,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"视觉分析失败: {e}"

    def extract_json(self, text: str) -> dict:
        """从 LLM 回复中提取 JSON（清理 markdown 包裹）"""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"error": "无法解析 JSON", "raw": text[:500]}


llm = LLMEngine()
