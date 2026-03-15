import torch
import os
import torch.nn as nn


# 假设模型类名为 MyModel，请根据实际情况替换

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(115, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, 5),
            nn.Softmax(dim=1)
        )
    def forward(self, features):
        x = self.flatten(features)
        logits = self.linear_relu_stack(x)
        return logits

# 获取当前脚本文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建 .pt 文件的完整路径
file_path = os.path.join(current_dir, 'mode1_new.pt')

# 加载模型参数
try:
    state_dict = torch.load(file_path)

    # 创建模型实例
    model = MyModel()

    # 加载状态字典到模型实例
    model.load_state_dict(state_dict)
    model.eval()

    # 打印模型结构
    print("Model structure:")
    print(model)

    # 打印模型参数
    print("\nModel parameters:")
    for name, param in model.named_parameters():
        if param.requires_grad:
            print(f"{name}: {param.data}")

except FileNotFoundError as e:
    print(f"File '{file_path}' not found. Please check the file path.")
except Exception as e:
    print(f"An error occurred: {e}")
