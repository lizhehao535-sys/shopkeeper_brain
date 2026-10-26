import huggingface_hub
import importlib.metadata as m
import transformers

print("huggingface_hub 模块版本:", huggingface_hub.__version__)
print("huggingface-hub 元数据版本:", m.version("huggingface-hub"))
print("transformers 版本:", transformers.__version__)