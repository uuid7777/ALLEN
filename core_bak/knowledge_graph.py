"""
Allen 原生知识图谱 — 自建语义网络
纯 Python，零外部模型依赖

结构：
  实体(entity) ←→ 关系(relation) ←→ 实体(entity)
  
  实体: { id, name, type, properties }
  关系: { source_id, target_id, relation_type, weight, evidence }
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TZ = timezone(timedelta(hours=8))
GRAPH_FILE = Path(__file__).resolve().parent.parent / "memory_data" / "knowledge_graph.json"

# ─── 实体类型 ─────────────────────────────
ENTITY_TYPES = {
    "concept",     # 抽象概念（人工智能、自由）
    "person",      # 人（埃隆·马斯克）
    "thing",       # 物体（茶杯、电脑）
    "event",       # 事件（发布会、选举）
    "location",    # 地点（北京、硅谷）
    "org",         # 组织（谷歌、OpenAI）
    "product",     # 产品（iPhone、ChatGPT）
    "field",       # 领域（科技、金融）
}

# ─── 关系类型 ─────────────────────────────
RELATION_TYPES = {
    "is_a",         # A 是 B（猫 is_a 动物）
    "has_part",     # A 有 B（汽车 has_part 引擎）
    "leads_to",     # A 导致 B（下雨 leads_to 地湿）
    "belongs_to",   # A 属于 B（员工 belongs_to 公司）
    "related_to",   # A 与 B 相关（通用）
    "creates",      # A 创造 B（作者 creates 作品）
    "uses",         # A 使用 B（程序员 uses Python）
    "opposes",      # A 反对 B
    "supports",     # A 支持 B
    "located_in",   # A 位于 B
    "created_by",   # A 由 B 创造（作品 created_by 作者）
    "after",        # A 发生在 B 之后
    "before",       # A 发生在 B 之前
    "causes",       # A 引起 B（同leads_to，更强调因果）
}


class KnowledgeGraph:
    """Allen 的知识图谱 — 自建语义网络"""

    def __init__(self):
        self.graph = self._load()
        self._entity_counter = self._get_max_id()

    # ─── 持久化 ─────────────────────────

    def _load(self) -> dict:
        """加载图谱文件"""
        default = {
            "entities": {},      # id -> entity
            "relations": [],     # list of relation dicts
            "adjacency": {},     # entity_id -> { related_id: [relation_types] }
            "meta": {
                "created": datetime.now(TZ).isoformat(),
                "updated": datetime.now(TZ).isoformat(),
                "entity_count": 0,
                "relation_count": 0,
            }
        }
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return default
        return default

    def save(self):
        """保存图谱到文件"""
        self.graph["meta"]["updated"] = datetime.now(TZ).isoformat()
        self.graph["meta"]["entity_count"] = len(self.graph["entities"])
        self.graph["meta"]["relation_count"] = len(self.graph["relations"])
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, ensure_ascii=False, indent=2)

    def _get_max_id(self) -> int:
        """获取当前最大实体 ID"""
        ids = [int(k) for k in self.graph["entities"].keys()]
        return max(ids) if ids else 0

    # ─── 实体操作 ─────────────────────────

    def add_entity(self, name: str, etype: str = "concept", properties: dict = None) -> str:
        """
        添加实体。如果同名已存在则返回现有 ID。
        name: 实体名称
        etype: 实体类型
        properties: 额外属性
        """
        name = name.strip()
        if not name:
            return None

        # 查重（同名同类型视为同一实体）
        existing = self.find_entity(name)
        if existing:
            return existing["id"]

        self._entity_counter += 1
        eid = str(self._entity_counter)
        self.graph["entities"][eid] = {
            "id": eid,
            "name": name,
            "type": etype if etype in ENTITY_TYPES else "concept",
            "properties": properties or {},
            "created": datetime.now(TZ).isoformat(),
            "occurrences": 1,
        }
        self.graph["adjacency"][eid] = {}
        self.save()
        return eid

    def find_entity(self, name: str) -> dict:
        """按名称查找实体（精确匹配）"""
        name_lower = name.lower().strip()
        for e in self.graph["entities"].values():
            if e["name"].lower() == name_lower:
                return e
        return None

    def find_or_create(self, name: str, etype: str = "concept") -> str:
        """查找实体，不存在则创建"""
        existing = self.find_entity(name)
        if existing:
            existing["occurrences"] = existing.get("occurrences", 1) + 1
            self.save()
            return existing["id"]
        return self.add_entity(name, etype)

    # ─── 关系操作 ─────────────────────────

    def add_relation(self, source_name: str, target_name: str,
                     rel_type: str = "related_to", evidence: str = ""):
        """
        在两个实体之间建立关系。
        自动创建不存在的实体。
        """
        if rel_type not in RELATION_TYPES:
            rel_type = "related_to"

        source_id = self.find_or_create(source_name)
        target_id = self.find_or_create(target_name)

        if not source_id or not target_id:
            return

        # 检查是否已有相同关系（避免重复）
        for rel in self.graph["relations"]:
            if (rel["source"] == source_id and rel["target"] == target_id
                    and rel["type"] == rel_type):
                rel["weight"] = rel.get("weight", 1) + 1
                if evidence and evidence not in rel.get("evidence", ""):
                    rel["evidence"] = rel.get("evidence", "") + "; " + evidence
                self.save()
                return

        relation = {
            "source": source_id,
            "target": target_id,
            "type": rel_type,
            "weight": 1,
            "evidence": evidence or "",
            "created": datetime.now(TZ).isoformat(),
        }
        self.graph["relations"].append(relation)

        # 更新邻接表
        if source_id not in self.graph["adjacency"]:
            self.graph["adjacency"][source_id] = {}
        if target_id not in self.graph["adjacency"]:
            self.graph["adjacency"][target_id] = {}

        targets = self.graph["adjacency"][source_id]
        if target_id not in targets:
            targets[target_id] = []
        if rel_type not in targets[target_id]:
            targets[target_id].append(rel_type)

        # 反向也记录
        sources = self.graph["adjacency"][target_id]
        if source_id not in sources:
            sources[source_id] = []
        reverse_rel = self._reverse_relation(rel_type)
        if reverse_rel and reverse_rel not in sources[source_id]:
            sources[source_id].append(reverse_rel)

        self.save()

    def _reverse_relation(self, rel_type: str) -> str:
        """获取反向关系类型"""
        reverse_map = {
            "is_a": "has_instance",         # 猫 is_a 动物 → 动物 has_instance 猫
            "has_part": "part_of",
            "leads_to": "caused_by",
            "belongs_to": "has_member",
            "creates": "created_by",
            "uses": "used_by",
            "opposes": "opposed_by",
            "supports": "supported_by",
            "located_in": "contains",
            "causes": "caused_by",
            "after": "before",
            "before": "after",
        }
        return reverse_map.get(rel_type, "related_to")

    # ─── 查询 ─────────────────────────────

    def get_related(self, entity_name: str, depth: int = 1) -> list:
        """
        获取与某实体相关的所有实体及关系。
        depth: 关联深度（1=直接关联，2=间接关联）
        返回: [(实体, 关系类型, 层级)]
        """
        entity = self.find_entity(entity_name)
        if not entity:
            return []

        eid = entity["id"]
        visited = {eid}
        results = []

        def dfs(current_id: str, current_depth: int):
            if current_depth > depth:
                return
            adj = self.graph["adjacency"].get(current_id, {})
            for neighbor_id, rel_types in adj.items():
                if neighbor_id not in visited or current_depth < depth:
                    visited.add(neighbor_id)
                    neighbor = self.graph["entities"].get(neighbor_id)
                    if neighbor:
                        for rt in rel_types:
                            results.append((neighbor, rt, current_depth))
                    if current_depth < depth:
                        dfs(neighbor_id, current_depth + 1)

        dfs(eid, 1)
        return results

    def query_path(self, from_name: str, to_name: str) -> list:
        """
        查找两个实体之间的路径。
        返回: [[(实体, 关系类型), ...], ...]  多条路径
        """
        from_entity = self.find_entity(from_name)
        to_entity = self.find_entity(to_name)
        if not from_entity or not to_entity:
            return []

        paths = []

        def dfs(current_id: str, target_id: str, visited: set, path: list):
            if current_id == target_id:
                paths.append(list(path))
                return
            if len(path) > 5:  # 限制深度
                return
            adj = self.graph["adjacency"].get(current_id, {})
            for neighbor_id, rel_types in adj.items():
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor = self.graph["entities"].get(neighbor_id)
                    for rt in rel_types:
                        path.append((neighbor, rt))
                        dfs(neighbor_id, target_id, visited, path)
                        path.pop()
                    visited.remove(neighbor_id)

        visited = {from_entity["id"]}
        dfs(from_entity["id"], to_entity["id"], visited, [])
        return paths

    def search_entities(self, keyword: str) -> list:
        """搜索实体（模糊匹配名称）"""
        keyword_lower = keyword.lower()
        results = []
        for e in self.graph["entities"].values():
            if keyword_lower in e["name"].lower():
                results.append(e)
        return results[:20]

    def get_stats(self) -> dict:
        """图谱统计"""
        return {
            "entities": len(self.graph["entities"]),
            "relations": len(self.graph["relations"]),
            "entity_types": defaultdict(int, {
                e["type"]: sum(1 for e2 in self.graph["entities"].values() if e2["type"] == e["type"])
                for e in self.graph["entities"].values()
            }),
            "relation_types": defaultdict(int, {
                r["type"]: sum(1 for r2 in self.graph["relations"] if r2["type"] == r["type"])
                for r in self.graph["relations"]
            }),
        }

    # ─── 文本解析 ─────────────────────────

    # 停止词 — 不可能是独立实体的片段
    STOP_WORDS = {
        "感知扫描遇到", "遇到问题", "扫描遇到", "当前无", "无有效", "效信息",
        "息输入", "记录", "待机", "出错", "错误", "超时", "失败",
        "保存新知识", "扫描环境中", "分析并决策", "执行完毕", "行动结果",
        "新知入库", "本次觉醒", "扫描环境", "检索相关知识", "理解并提取",
        "图谱联想", "图谱理解", "推理决策",
        "当前无有效信", "有效信息输入", "点击刷新", "将会有未读推荐", "未读推荐",
    }

    # 错误/异常关键词 — 包含这些的不提取实体
    ERROR_PATTERNS = [
        "error", "Error", "timeout", "Timeout", "超时", "出错",
        "Traceback", "Exception", "cannot", "denied",
    ]

    def _is_meaningful_entity(self, word: str, context: str = "") -> bool:
        """判断一个词是否是有意义的实体"""
        word = word.strip()
        if len(word) < 2:
            return False

        # 停止词过滤
        if word in self.STOP_WORDS:
            return False

        # 只包含标点符号或数字
        if re.match(r'^[\d\s\.\,\(\)\-\_]+$', word):
            return False

        # 中文词至少 2 个汉字
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', word)
        if chinese_chars and len(chinese_chars) < 2:
            return False

        # 检查是否是完整词（不以连接词/助词/动词开头结尾）
        dangling_head = {"的", "了", "是", "在", "有", "和", "与", "或", "把", "被", "让", "给", "对",
                         "就", "也", "还", "都", "而", "但", "可", "如", "为", "以", "从", "到", "向"}
        dangling_tail = {"的", "了", "是", "在", "有", "和", "与", "或", "把", "被", "让", "给", "对",
                         "就", "也", "还", "都", "而", "但", "可", "会", "能", "要", "让", "将", "已",
                         "着", "过", "中", "上", "下", "后"}
        if chinese_chars:
            if word[0] in dangling_head or word[-1] in dangling_tail:
                return False

        # 以标点结尾的不要
        if word[-1] in "，。！？、；：""''（）…—·":
            return False

        # 纯英文：至少 3 个字母，且含元音字母
        if not chinese_chars:
            if len(word) < 3 or not re.search(r'[aeiouAEIOU]', word):
                return False

        return True

    def _is_error_text(self, text: str) -> bool:
        """检查文本是否主要是错误信息"""
        for p in self.ERROR_PATTERNS:
            if p in text:
                return True
        return False

    def ingest_text(self, text: str, source: str = ""):
        """
        从一段文本中提取实体和关系。
        如果文本是错误信息则跳过实体提取。
        """
        if not text or len(text) < 5:
            return

        # 错误信息不提取实体，但仍尝试从错误描述中提取模式
        is_error = self._is_error_text(text)

        # 模式1: "A 是 B" / "A 是一种 B"  → is_a
        for m in re.finditer(r'([\u4e00-\u9fff\w]{2,20})(?:是|是一种|是一种|属于)([\u4e00-\u9fff\w]{2,20})', text):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b and self._is_meaningful_entity(a) and self._is_meaningful_entity(b):
                self.add_relation(a, b, "is_a", source)

        # 模式2: "A 有 B" / "A 包含 B"  → has_part
        for m in re.finditer(r'([\u4e00-\u9fff\w]{2,20})(?:有|包含|包括|拥有)([\u4e00-\u9fff\w]{2,20})', text):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b and self._is_meaningful_entity(a) and self._is_meaningful_entity(b):
                self.add_relation(a, b, "has_part", source)

        # 模式3: "A 在 B" / "A 位于 B"  → located_in
        for m in re.finditer(r'([\u4e00-\u9fff\w]{2,20})(?:在|位于|坐落于)([\u4e00-\u9fff\w]{2,20})', text):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b and self._is_meaningful_entity(a) and self._is_meaningful_entity(b):
                self.add_relation(a, b, "located_in", source)

        # 模式4: "A 使用 B" / "A 利用 B"  → uses
        for m in re.finditer(r'([\u4e00-\u9fff\w]{2,20})(?:使用|利用|采用|借助)([\u4e00-\u9fff\w]{2,20})', text):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b and self._is_meaningful_entity(a) and self._is_meaningful_entity(b):
                self.add_relation(a, b, "uses", source)

        # 模式5: "A 导致 B" / "A 引起 B"  → causes
        for m in re.finditer(r'([\u4e00-\u9fff\w]{2,20})(?:导致|引起|引发|造成)([\u4e00-\u9fff\w]{2,20})', text):
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b and self._is_meaningful_entity(a) and self._is_meaningful_entity(b):
                self.add_relation(a, b, "causes", source)

        # 模式6: 提取独立实体 — 仅在非错误文本中执行
        # 使用标点/空格分隔，避免截断长标题
        if not is_error:
            # 按标点/空格分割，提取独立的中文词或英文名
            segments = re.split(r'[，。！？、；：""''（）…—·\s\t\n\r,.;:!?()\[\]{}｜｜/\\\\]+', text)
            for seg in segments[:30]:
                seg = seg.strip()
                if not seg:
                    continue
                # 中文实体：2-15 个汉字
                chinese_match = re.match(r'^([\u4e00-\u9fff]{2,15})$', seg)
                if chinese_match:
                    w = chinese_match.group(1)
                    if self._is_meaningful_entity(w) and not self.find_entity(w):
                        self.add_entity(w, "concept")
                    continue
                # 英文实体：首字母大写的专有名词
                eng_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', seg)
                if eng_match:
                    w = eng_match.group(1)
                    if self._is_meaningful_entity(w) and not self.find_entity(w):
                        self.add_entity(w, "concept")

    def get_all_entities(self) -> list:
        """获取所有实体列表"""
        return list(self.graph["entities"].values())


# ─── 全局单例 ─────────────────────────────
kg = KnowledgeGraph()
