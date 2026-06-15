class MicroBrain:
    def __init__(self, state=None):
        self.state = state or {}

    def think(self, text):
        t=text.lower()
        if any(x in t for x in ["在吗","你好","怎么样"]):
            return "我在。我正在检查自己的状态。"
        return "我记录了这个信息，并准备继续学习。"
