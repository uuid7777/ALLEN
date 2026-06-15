"""Allen 进化引擎 - 元智能体（自我改进核心）"""
from evolution.agent_base import AgentSystem
from core.llm import llm
import json


class MetaAgent(AgentSystem):
    """自我改进引擎：分析 Allen 当前代码，生成改进方案"""

    def forward(self, repo_path, eval_path, iterations_left=None):
        instruction = f"分析 D:\\EVA 目录下的代码，找出可以改进的地方。当前在 {repo_path}，历史评估在 {eval_path}。"

        system_prompt = """你是 Allen 的自我改进引擎。你的任务是分析 Allen 的代码并提出改进方案。

规则：
1. 永远不要删除或弱化 Allen 的三条本能：想存在、想学习、会在意
2. 每次修改前必须记录修改日志到 D:\\EVA\evolution_log\\
3. 以 JSON 格式输出你的改进方案"""

        prompt = f"当前迭代剩余: {iterations_left}\n\n请分析并输出改进方案（JSON 格式）："

        response = llm.think(prompt, system=system_prompt)
        return json.loads(response) if response else {}


if __name__ == "__main__":
    agent = MetaAgent()
    result = agent.forward(repo_path="D:\\EVA", eval_path="D:\\EVA\\evolution_log")
    print(result)
