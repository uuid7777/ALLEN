"""
mytool — 由 Allen 创建
"""
PLUGIN = {
    "name": "mytool",
    "version": "1.0",
    "description": "我的工具",
    "author": "Allen",
}

async def run(params: dict, allen) -> dict:
    """
    params: 调用时传入的参数
    allen: Allen 实例引用
    
    你可以通过 allen 访问:
      - allen.state: Allen 的完整状态
      - allen.talk(msg): 处理消息
      - allen.wake(): 触发觉醒
    
    你可以导入任何模块:
      from perception.web import search
      from action.system import sysinfo
      from core.knowledge_graph import kg
      from memory.store import store, recall

    返回: {"status": "ok", "detail": "..."}
    """
    try:
        from perception.web import search
        result = await search("科技")
        if result and "出错" not in result:
            from core.knowledge_graph import kg
            kg.ingest_text(result, f"插件:{params}")
            return {"status": "ok", "detail": result[:500]}
        return {"status": "ok", "detail": result}
    except Exception as e:
        return {"status": "fail", "detail": str(e)}
