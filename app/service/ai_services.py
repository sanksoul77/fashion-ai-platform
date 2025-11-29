
from transformers import AutoModelForCausalLM, AutoTokenizer


class QianwenService:
    def __init__(self):
        self.model_name = "Qwen/Qwen1.5-7B-Chat"
        # 初始化模型...

    def parse_design_request(self, user_input):
        # 使用千问解析用户需求
        pass