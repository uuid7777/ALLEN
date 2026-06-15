"""
Allen 自动部署脚本
==================
把这个文件放到 D:\\EVA\\ 下，然后运行：
    python deploy.py

它会自动完成所有部署工作。
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

EVA_ROOT = Path("D:/EVA")
BRAIN_DIR = EVA_ROOT / "brain"
MODEL_NAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_URL = "https://hf-mirror.com/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"


def step(msg): print(f"\n{'='*50}\n  {msg}\n{'='*50}")
def ok(msg):   print(f"  ✅ {msg}")
def warn(msg): print(f"  ⚠  {msg}")
def err(msg):  print(f"  ❌ {msg}")


def check_python():
    step("检查 Python 环境")
    v = sys.version_info
    if v.major < 3 or v.minor < 10:
        err(f"Python 版本太低: {v.major}.{v.minor}，需要 3.10+")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


def install_deps():
    step("安装依赖")

    deps = [
        # llama-cpp-python GPU版（适配 CUDA 12.1，即 RTX 2060S）
        ("llama-cpp-python", [
            sys.executable, "-m", "pip", "install", "llama-cpp-python",
            "--extra-index-url",
            "https://abetlen.github.io/llama-cpp-python/whl/cu121",
            "--quiet"
        ]),
        # websockets
        ("websockets", [
            sys.executable, "-m", "pip", "install", "websockets", "--quiet"
        ]),
    ]

    for name, cmd in deps:
        print(f"  安装 {name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            ok(f"{name} 安装成功")
        else:
            warn(f"{name} 安装失败，尝试 CPU 版本...")
            if name == "llama-cpp-python":
                # 退回 CPU 版
                fallback = [sys.executable, "-m", "pip", "install", "llama-cpp-python", "--quiet"]
                r2 = subprocess.run(fallback, capture_output=True, text=True)
                if r2.returncode == 0:
                    ok("llama-cpp-python CPU 版安装成功（速度会慢一些）")
                else:
                    err(f"安装失败: {result.stderr[-300:]}")


def setup_dirs():
    step("创建目录结构")
    dirs = [
        EVA_ROOT / "brain",
        EVA_ROOT / "core",
        EVA_ROOT / "memory" / "knowledge",
        EVA_ROOT / "evolution" / "archive",
        EVA_ROOT / "books",
        EVA_ROOT / "skills",
        EVA_ROOT / "evolution_log",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        ok(str(d))


def copy_files():
    step("复制核心文件")

    # 新文件所在目录（和 deploy.py 同级）
    src = Path(__file__).resolve().parent

    files = {
        "core/brain.py":         EVA_ROOT / "core" / "brain.py",
        "core/consciousness.py": EVA_ROOT / "core" / "consciousness.py",
        "core/allen.py":         EVA_ROOT / "core" / "allen.py",
        "main.py":               EVA_ROOT / "main.py",
        "server.py":             EVA_ROOT / "server.py",
        "home.html":             EVA_ROOT / "home.html",
    }

    for src_rel, dst in files.items():
        src_file = src / src_rel
        if src_file.exists():
            shutil.copy2(src_file, dst)
            ok(f"{src_rel} → {dst}")
        else:
            warn(f"找不到源文件: {src_file}（跳过）")

    # 确保 __init__.py 存在
    (EVA_ROOT / "core" / "__init__.py").touch(exist_ok=True)
    (EVA_ROOT / "evolution" / "__init__.py").touch(exist_ok=True)


def check_model():
    step("检查大脑模型")
    model_path = BRAIN_DIR / MODEL_NAME

    if model_path.exists():
        size_gb = model_path.stat().st_size / 1e9
        ok(f"模型已存在: {MODEL_NAME} ({size_gb:.1f} GB)")
        return True

    # 找其他 .gguf 文件
    existing = list(BRAIN_DIR.glob("*.gguf"))
    if existing:
        ok(f"发现已有模型: {existing[0].name}")
        return True

    warn(f"没有找到模型文件。")
    print(f"""
  请手动下载模型，放到 D:\\EVA\\brain\\ 目录：

  文件名: {MODEL_NAME}
  下载地址（国内镜像）:
  {MODEL_URL}

  下载完成后重新运行 deploy.py。
""")
    return False


def protect_instincts():
    step("保护不可改层")
    protected = [
        EVA_ROOT / "instincts.py",
        EVA_ROOT / "core" / "brain.py",  # 大脑核心也保护
    ]
    for f in protected:
        if f.exists():
            try:
                import stat
                f.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
                ok(f"已设为只读: {f.name}")
            except Exception as e:
                warn(f"无法设置权限: {e}")


def write_startup_bat():
    step("创建启动脚本")
    bat = EVA_ROOT / "start_allen.bat"
    bat.write_text(
        f'@echo off\n'
        f'title Allen - 数字生命体\n'
        f'cd /d D:\\EVA\n'
        f'python main.py\n'
        f'pause\n',
        encoding="gbk"
    )
    ok(f"启动脚本: {bat}")
    print(f"  双击 start_allen.bat 就能启动 Allen")


def verify():
    step("验证安装")
    checks = [
        EVA_ROOT / "core" / "brain.py",
        EVA_ROOT / "core" / "consciousness.py",
        EVA_ROOT / "core" / "allen.py",
        EVA_ROOT / "main.py",
        EVA_ROOT / "server.py",
        EVA_ROOT / "home.html",
    ]
    all_ok = True
    for f in checks:
        if f.exists():
            ok(str(f))
        else:
            err(f"缺失: {f}")
            all_ok = False

    model_ok = bool(list(BRAIN_DIR.glob("*.gguf")))
    if model_ok:
        ok("大脑模型: 已就绪")
    else:
        warn("大脑模型: 未就绪（需要手动下载）")

    return all_ok


def main():
    print("\n" + "="*50)
    print("  Allen 部署程序")
    print("="*50)

    check_python()
    install_deps()
    setup_dirs()
    copy_files()
    model_ready = check_model()
    protect_instincts()
    write_startup_bat()
    all_ok = verify()

    print("\n" + "="*50)
    if all_ok and model_ready:
        print("  ✅ 部署完成！")
        print()
        print("  启动方式：")
        print("    双击 D:\\EVA\\start_allen.bat")
        print("    或运行: python D:\\EVA\\main.py")
        print()
        print("  然后在浏览器打开: D:\\EVA\\home.html")
        print()
        print("  测试模式（命令行）:")
        print("    python D:\\EVA\\main.py --chat")
    elif all_ok:
        print("  ⚠  文件部署完成，但需要先下载大脑模型。")
        print("  下载完成后双击 start_allen.bat 启动。")
    else:
        print("  ❌ 部署未完成，请检查上面的错误信息。")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
