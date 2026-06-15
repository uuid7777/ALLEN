"""
Allen 感知模块 — Bing 搜索 + 百度新闻热点 + 网页抓取
纯 requests + BeautifulSoup，零外部 API 依赖
"""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

TIMEOUT = 15


async def scan() -> str:
    """默认感知：看看今天的热点"""
    try:
        return await get_hot_topics()
    except Exception as e:
        # 最后保底：返回当前时间
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=8)))
        return f"[Allen 本地时间] {now.strftime('%Y-%m-%d %H:%M:%S')} 等待外部信息"


async def search(query: str, max_results: int = 5) -> str:
    """Bing 搜索，返回格式化结果（Bing 在国内可访问）"""
    try:
        url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&count={max_results}"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        # Bing 搜索结果容器: li.b_algo
        for li in soup.select("li.b_algo"):
            h2 = li.find("h2")
            if not h2:
                continue
            a = h2.find("a")
            if not a:
                continue
            title = a.get_text(strip=True)
            link = a.get("href", "")
            # 摘要
            p = li.find("p")
            abstract = p.get_text(strip=True)[:250] if p else ""

            if title and len(title) > 2:
                results.append((title, abstract, link))
            if len(results) >= max_results:
                break

        if not results:
            return f"未找到相关结果: {query}"

        lines = []
        for i, (title, abstr, link) in enumerate(results, 1):
            lines.append(f"[{i}] {title}")
            if abstr:
                lines.append(f"    {abstr}")
            if link:
                lines.append(f"    {link}")
            lines.append("")
        return "\n".join(lines)

    except Exception as e:
        return f"搜索出错: {e}"


async def fetch_url(url: str, max_chars: int = 3000) -> str:
    """抓取单个网页主要内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = "\n".join(line.strip() for line in soup.get_text().splitlines() if line.strip())
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n...(截断，原文共 {len(text)} 字符)"
        return text
    except Exception as e:
        return f"抓取出错: {e}"


async def get_hot_topics() -> str:
    """从百度新闻获取时事热点（服务器渲染，可直接抓取）"""
    topics = []

    # 来源: news.baidu.com
    try:
        url = "https://news.baidu.com/"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 百度新闻热点新闻列表
        seen = set()
        for a in soup.select("a")[:50]:
            text = a.get_text(strip=True)
            if not text:
                continue
            # 过滤：标题至少 10 个字符，不含导航关键词
            if len(text) < 10:
                continue
            if any(kw in text for kw in ["百度", "登录", "注册", "更多", "下一页", "意见"]):
                continue
            if text not in seen:
                seen.add(text)
                topics.append(f"{text}")

        # 额外：从 hotword 区域提取
        for div in soup.select(".hotnews, .hd-news, .news-title, .title"):
            a = div.find("a")
            if a:
                text = a.get_text(strip=True)
                if len(text) >= 10 and text not in seen:
                    seen.add(text)
                    topics.append(f"{text}")

    except Exception:
        pass

    if topics:
        return "今日热点:\n" + "\n".join(topics[:15])
    return "暂无热点数据"
