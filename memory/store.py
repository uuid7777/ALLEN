"""
Allen 记忆模块 — JSON 持久化 + 向量语义检索
使用自建 TF-IDF 做语义联想，零外部依赖
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory_data"
MEMORY_FILE = MEMORY_DIR / "memories.json"


def _ensure():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> list:
    _ensure()
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []


def _save(memories: list):
    _ensure()
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


async def store(content: str, mem_type: str = "learning",
                source: str = "", tags: list = None) -> int:
    """存入一条记忆，返回 ID。自动加入向量索引。"""
    memories = _load()
    mem_id = len(memories) + 1
    mem = {
        "id": mem_id,
        "time": datetime.now(TZ).isoformat(),
        "type": mem_type,
        "content": content,
        "source": source,
        "tags": tags or []
    }
    memories.append(mem)
    _save(memories)

    # 同步加入向量索引
    try:
        from memory.vector import vmem
        vmem.add(mem_id, content, mem_type, tags or [])
    except ImportError:
        pass  # 向量模块未就绪时静默跳过

    return mem_id


async def recall(stimulus: str, top_k: int = 5) -> list:
    """语义检索 + 关键词检索双召回，返回最相关记忆"""
    memories = _load()
    if not memories:
        return []

    results = []

    # 1. 向量语义检索
    try:
        from memory.vector import vmem
        vec_results = vmem.search(stimulus, top_k=top_k)
        for vr in vec_results:
            # 根据 ID 查找完整记忆
            for m in memories:
                if m["id"] == vr["id"]:
                    m_with_score = dict(m)
                    m_with_score["_score"] = vr["score"]
                    m_with_score["_method"] = "vector"
                    results.append(m_with_score)
                    break
    except ImportError:
        pass

    # 2. 关键词检索（后备 + 补充）
    keywords = re.findall(r'[\u4e00-\u9fff]{2,}|\b[a-zA-Z]{3,}\b', stimulus)
    seen_ids = {r["id"] for r in results}
    for m in memories:
        if m["id"] in seen_ids:
            continue
        content = m.get("content", "") + " ".join(m.get("tags", []))
        score = 0
        for kw in keywords:
            if kw.lower() in content.lower():
                score += 1
        if score > 0:
            m_with_score = dict(m)
            m_with_score["_score"] = score / max(len(keywords), 1)
            m_with_score["_method"] = "keyword"
            results.append(m_with_score)

    # 按分数排序
    results.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # 去除 _score / _method 字段再返回
    for r in results:
        r.pop("_score", None)
        r.pop("_method", None)

    return results[:top_k]


async def get_recent(limit: int = 20) -> list:
    """获取最近 N 条记忆"""
    memories = _load()
    return memories[-limit:]


async def get_stats() -> dict:
    """记忆统计"""
    memories = _load()
    types = {}
    for m in memories:
        t = m.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    vector_stats = {}
    try:
        from memory.vector import vmem
        vector_stats = vmem.stats()
    except ImportError:
        pass

    return {
        "total": len(memories),
        "types": types,
        "vector_indexed": vector_stats.get("indexed_memories", 0),
        "vocab_size": vector_stats.get("vocab_size", 0),
        "latest_time": memories[-1]["time"] if memories else "无",
        "latest_content": memories[-1]["content"][:150] if memories else "无"
    }


async def search_memories(query: str, limit: int = 10) -> list:
    """在记忆中搜索包含关键词的记录"""
    memories = _load()
    results = []
    q = query.lower()
    for m in reversed(memories):
        if q in m.get("content", "").lower():
            results.append(m)
            if len(results) >= limit:
                break
    return results


async def rebuild_vectors():
    """重建所有记忆的向量索引（当记忆库变更时调用）"""
    try:
        from memory.vector import vmem
        memories = _load()
        vmem.rebuild(memories)
        stats = vmem.stats()
        return f"[OK] 向量索引重建完成: {stats['indexed_memories']} 条记忆, {stats['vocab_size']} 个词汇"
    except ImportError as e:
        return f"[FAIL] 向量模块未就绪: {e}"