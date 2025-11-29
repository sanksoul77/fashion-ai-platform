import json

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class QianwenService:
    def __init__(self):
        self.model_name = "Qwen/Qwen1.5-7B-Chat"
        # 加载模型和tokenizer（注意：7B模型需要足够显存，可先测试小模型如Qwen/Qwen1.5-0.5B-Chat）
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto"  # 自动分配设备（CPU/GPU）
        )
        # 创建文本生成管道
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer
        )

    def parse_design_request(self, user_input: str, garment_type: str) -> dict:
        """解析用户需求，生成设计规格"""
        prompt = f"""
        请根据用户需求生成服装设计规格：
        - 用户需求：{user_input}
        - 服装类型：{garment_type}
        请返回包含风格（style）、颜色（colors，列表）、细节描述（details）的JSON格式。
        """
        # 模型推理
        response = self.generator(
            prompt,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True
        )
        # 解析结果（简化处理，实际需加格式校验）
        result = response[0]["generated_text"].split(prompt)[-1].strip()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # 若解析失败，返回默认值
            return {
                "style": "现代简约",
                "colors": ["黑色", "灰色"],
                "details": "根据需求生成的设计"
            }