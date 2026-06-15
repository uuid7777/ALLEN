"""
Allen 自建 TF-IDF 向量检索 — 语义级记忆召回
零外部依赖，纯 Python 实现

原理：
  1. 将记忆文本拆分为 token（中文按字 + 英文按词）
  2. 计算每个 token 的 TF-IDF 权重
  3. 文档表示为稀疏向量
  4. 查询时计算余弦相似度 → 返回最相关记忆
"""
import json
import re
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

TZ = timezone(timedelta(hours=8))
VECTOR_DIR = Path(__file__).resolve().parent.parent / "memory_data"
VOCAB_FILE = VECTOR_DIR / "vocab.json"
VECTORS_FILE = VECTOR_DIR / "vectors.json"

# ─── 分词器 ─────────────────────────────

class Tokenizer:
    """Allen 分词器：中文按字符 2-gram + 英文按单词"""

    def tokenize(self, text: str) -> list:
        """将文本拆分为 token 列表"""
        if not text:
            return []

        tokens = []

        # 提取中文部分 → 按 2-gram（字符重叠二元组）
        chinese_segments = re.findall(r'[\u4e00-\u9fff]+', text)
        for seg in chinese_segments:
            if len(seg) == 1:
                tokens.append(seg)
            else:
                # 2-gram + 3-gram + 单独字符（保留细粒度）
                for i in range(len(seg)):
                    tokens.append(seg[i])  # 单字
                for i in range(len(seg) - 1):
                    tokens.append(seg[i:i+2])  # 双字
                if len(seg) >= 3:
                    for i in range(len(seg) - 2):
                        tokens.append(seg[i:i+3])  # 三字

        # 提取英文/数字部分 → 按空格/标点分词
        eng_segments = re.findall(r'[a-zA-Z0-9\.\+\-\_]+', text)
        for seg in eng_segments:
            if len(seg) >= 2:
                tokens.append(seg.lower())

        return tokens


# ─── TF-IDF 向量化 ─────────────────────

class TfidfVectorizer:
    """
    自建 TF-IDF 向量化器
    支持增量构建（新文档加入时更新 IDF）
    """

    def __init__(self):
        self.tokenizer = Tokenizer()
        # 词汇表: token -> index
        self.vocab = {}
        # IDF: token -> idf value
        self.idf = {}
        # 文档总数
        self.doc_count = 0
        # 包含每个 token 的文档数
        self.df = defaultdict(int)

    def build(self, documents: list):
        """从文档列表构建词汇表和 IDF"""
        self.vocab = {}
        self.df = defaultdict(int)
        self.doc_count = len(documents)

        # 第一遍：统计 DF
        for doc in documents:
            tokens = self.tokenizer.tokenize(doc)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.df[t] += 1

        # 构建词汇表并计算 IDF
        self.vocab = {}
        idx = 0
        for t in sorted(self.df.keys()):
            if self.df[t] >= 1:  # 过滤掉只在 1 个文档出现的 token？先保留全部
                self.vocab[t] = idx
                idx += 1

        # 计算 IDF
        N = self.doc_count
        for t, df_t in self.df.items():
            self.idf[t] = math.log((N + 1) / (df_t + 1)) + 1  # 平滑

    def add_document(self, doc: str):
        """增量添加一个文档，更新词汇表和 IDF"""
        tokens = self.tokenizer.tokenize(doc)
        unique_tokens = set(tokens)

        # 更新 DF
        for t in unique_tokens:
            self.df[t] += 1

        self.doc_count += 1

        # 为新 token 分配索引
        for t in unique_tokens:
            if t not in self.vocab:
                self.vocab[t] = len(self.vocab)

        # 重新计算 IDF
        N = self.doc_count
        for t in self.df:
            self.idf[t] = math.log((N + 1) / (self.df[t] + 1)) + 1

    def transform(self, text: str) -> dict:
        """将文本转为稀疏向量 {index: weight}"""
        tokens = self.tokenizer.tokenize(text)
        if not tokens:
            return {}

        # 计算词频
        tf = Counter(tokens)

        # 计算 TF-IDF
        vector = {}
        max_tf = max(tf.values())
        for t, count in tf.items():
            if t in self.vocab:
                idx = self.vocab[t]
                # TF: 1 + log(count) ，归一化
                tf_weight = 1 + math.log(count) if count > 0 else 0
                # TF-IDF
                weight = tf_weight * self.idf.get(t, 1)
                vector[idx] = weight

        # L2 归一化
        norm = math.sqrt(sum(w * w for w in vector.values()))
        if norm > 0:
            for k in vector:
                vector[k] /= norm

        return vector

    def cosine_similarity(self, vec_a: dict, vec_b: dict) -> float:
        """计算两个稀疏向量的余弦相似度"""
        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0

        # 遍历 A
        for k, v in vec_a.items():
            norm_a += v * v
            if k in vec_b:
                dot += v * vec_b[k]

        # 遍历 B（只需要 norm_b）
        for v in vec_b.values():
            norm_b += v * v

        norm_a = math.sqrt(norm_a)
        norm_b = math.sqrt(norm_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def vocab_size(self) -> int:
        return len(self.vocab)

    def save(self):
        """保存词汇表和 IDF"""
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "vocab": self.vocab,
            "idf": {str(k): v for k, v in self.idf.items()},
            "df": {str(k): v for k, v in self.df.items()},
            "doc_count": self.doc_count,
        }
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> bool:
        """加载词汇表和 IDF"""
        if not VOCAB_FILE.exists():
            return False
        try:
            with open(VOCAB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.vocab = data.get("vocab", {})
            self.idf = {k: v for k, v in data.get("idf", {}).items()}
            self.df = defaultdict(int, {k: v for k, v in data.get("df", {}).items()})
            self.doc_count = data.get("doc_count", 0)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False


# ─── 向量记忆管理器 ─────────────────────

class VectorMemory:
    """
    向量记忆管理器
    每个记忆条目 = 文本 + 向量 + 元数据
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.vectorizer.load()
        # 记忆向量缓存: [{"id": int, "vector": {idx: weight}, "text": str, ...}]
        self._vectors = self._load_vectors()

    def _vectors_path(self) -> Path:
        return VECTORS_FILE

    def _load_vectors(self) -> list:
        """从磁盘加载向量缓存"""
        path = self._vectors_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 转换 key 为 int
                    for item in data:
                        item["vector"] = {int(k): v for k, v in item.get("vector", {}).items()}
                    return data
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return []

    def _save_vectors(self):
        """保存向量缓存到磁盘"""
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        # 转换 key 为 str
        data = []
        for item in self._vectors:
            vec_str = {str(k): v for k, v in item.get("vector", {}).items()}
            data.append({**item, "vector": vec_str})
        with open(self._vectors_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, mem_id: int, text: str, mem_type: str = "", tags: list = None):
        """
        添加一条记忆到向量索引
        自动更新 TF-IDF 词汇表
        """
        # 向量化
        vector = self.vectorizer.transform(text)

        # 增量更新 TF-IDF
        self.vectorizer.add_document(text)

        # 存储向量
        entry = {
            "id": mem_id,
            "vector": vector,
            "text_preview": text[:200],
            "mem_type": mem_type,
            "tags": tags or [],
            "added": datetime.now(TZ).isoformat(),
        }
        self._vectors.append(entry)
        self._save_vectors()
        self.vectorizer.save()

    def search(self, query: str, top_k: int = 10) -> list:
        """
        语义搜索记忆
        返回: [{"id": int, "score": float, "text": str, "mem_type": str, ...}]
        """
        if not self._vectors:
            return []

        query_vector = self.vectorizer.transform(query)
        if not query_vector:
            return []

        # 计算所有向量的余弦相似度
        scored = []
        for entry in self._vectors:
            score = self.vectorizer.cosine_similarity(query_vector, entry["vector"])
            if score > 0.01:  # 极低阈值过滤
                scored.append((score, entry))

        # 按相似度排序
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, entry in scored[:top_k]:
            results.append({
                "id": entry["id"],
                "score": round(score, 4),
                "text": entry["text_preview"],
                "mem_type": entry.get("mem_type", ""),
                "tags": entry.get("tags", []),
            })

        return results

    def rebuild(self, memories: list):
        """
        从记忆列表重建所有向量
        memories: [{"id": int, "content": str, "type": str, "tags": list}]
        """
        # 提取所有文本
        texts = [m.get("content", "") for m in memories if m.get("content")]

        # 重建 TF-IDF
        self.vectorizer = TfidfVectorizer()
        for t in texts:
            self.vectorizer.add_document(t)
        self.vectorizer.save()

        # 重建向量缓存
        self._vectors = []
        for m in memories:
            text = m.get("content", "")
            if not text:
                continue
            vector = self.vectorizer.transform(text)
            self._vectors.append({
                "id": m["id"],
                "vector": vector,
                "text_preview": text[:200],
                "mem_type": m.get("type", ""),
                "tags": m.get("tags", []),
                "added": datetime.now(TZ).isoformat(),
            })

        self._save_vectors()

    def stats(self) -> dict:
        """统计"""
        return {
            "indexed_memories": len(self._vectors),
            "vocab_size": self.vectorizer.vocab_size(),
            "doc_count": self.vectorizer.doc_count,
        }


# ─── 全局单例 ─────────────────────────────
vmem = VectorMemory()
