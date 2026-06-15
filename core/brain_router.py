class BrainRouter:
    def __init__(self, llm=None, micro=None):
        self.llm = llm
        self.micro = micro

    def decide(self, text):
        complexity = len(text) / 100
        if complexity < 0.5 and self.micro:
            return self.micro.think(text)
        if self.llm:
            return self.llm.chat(text)
        return "我正在核心模式运行。"

    def think(self, msg):
        """Omega 升级：简单思考接口"""
        result = self.decide(msg)
        return result if result != "我正在核心模式运行。" else f"我收到：{msg}\n（核心模式运行，等待接入模型）"
