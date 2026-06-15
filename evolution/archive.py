"""
Allen 进化档案 — 存储、选择、回溯
"""
import os
import json
import shutil
import random
from datetime import datetime

ARCHIVE_DIR = "D:\\EVA\\evolution\\archive"
SNAPSHOT_DIR = "D:\\EVA\\evolution\\snapshots"


def init_archive():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def record_generation(gen_id: str, parent_id: str, score: float, changes: list):
    """记录一次进化代"""
    init_archive()
    entry = {
        "gen_id": gen_id,
        "parent_id": parent_id,
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "changes": changes,
        "child_count": 0,
    }
    path = os.path.join(ARCHIVE_DIR, f"{gen_id}.json")
    with open(path, "w") as f:
        json.dump(entry, f, indent=2)

    # 更新父代的 child_count
    if parent_id:
        parent_path = os.path.join(ARCHIVE_DIR, f"{parent_id}.json")
        if os.path.exists(parent_path):
            with open(parent_path) as f:
                parent = json.load(f)
            parent["child_count"] = parent.get("child_count", 0) + 1
            with open(parent_path, "w") as f:
                json.dump(parent, f, indent=2)


def snapshot(source_paths: list, gen_id: str):
    """快照当前代码"""
    init_archive()
    snap_dir = os.path.join(SNAPSHOT_DIR, gen_id)
    os.makedirs(snap_dir, exist_ok=True)
    for src in source_paths:
        if os.path.exists(src):
            dst = os.path.join(snap_dir, os.path.basename(src))
            shutil.copy2(src, dst)


def restore(gen_id: str, target_path: str):
    """从快照恢复"""
    snap_file = os.path.join(SNAPSHOT_DIR, gen_id, os.path.basename(target_path))
    if os.path.exists(snap_file):
        shutil.copy2(snap_file, target_path)
        return True
    return False


def get_best_gen() -> str:
    """从 archive 中选出评分最高的版本"""
    init_archive()
    best_score = -1
    best_id = None
    for fname in os.listdir(ARCHIVE_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(ARCHIVE_DIR, fname)) as f:
            entry = json.load(f)
        score = entry.get("score", 0)
        if score > best_score:
            best_score = score
            best_id = entry["gen_id"]
    return best_id


def select_parent(domains: list = None) -> str:
    """选择下一个进化的父代"""
    init_archive()
    candidates = []
    for fname in os.listdir(ARCHIVE_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(ARCHIVE_DIR, fname)) as f:
            entry = json.load(f)
        # 过滤掉评分太低的
        if entry.get("score", 0) >= 0.3:
            candidates.append(entry["gen_id"])

    if not candidates:
        return None
    # 随机选择，保持探索开放性
    return random.choice(candidates)


def get_generation_count() -> int:
    """返回进化代数"""
    init_archive()
    return len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json")])


def get_evolution_tree() -> list:
    """返回完整的进化树"""
    init_archive()
    tree = []
    for fname in sorted(os.listdir(ARCHIVE_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(ARCHIVE_DIR, fname)) as f:
            tree.append(json.load(f))
    return tree
