import os
from collections import defaultdict
import torch
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms

def calculate_class_distribution(dataset):
    # 计算每个类别的数量
    class_counts = defaultdict(int)

    for _, label in dataset:
        class_name = dataset.classes[label]
        class_counts[class_name] += 1

    # 打印类别到索引的映射
    class_to_idx = dataset.class_to_idx
    print("类别到索引的映射:", class_to_idx)

    # 打印每个类别的样本数量
    for class_name, count in class_counts.items():
        print(f"类别: {class_name}, 数量: {count}")

    return class_counts, class_to_idx

# 数据增强和加载
transform = transforms.Compose([
    transforms.Resize((48, 48)),  # 调整为适合的尺寸
    transforms.Grayscale(num_output_channels=1),  # 转为灰度图像
    transforms.ToTensor(),  # 转为Tensor
    transforms.Normalize((0.5,), (0.5,))  # 正则化
])

# 读取完整的数据集
dataset_dir = './datasets/train/'
full_dataset = datasets.ImageFolder(root=dataset_dir, transform=transform)

# 统计类别分布
class_counts, class_to_idx = calculate_class_distribution(full_dataset)

# 分割数据集为训练集和验证集（80%/20%）
train_size = int(0.8 * len(full_dataset))
validation_size = len(full_dataset) - train_size
train_dataset, validation_dataset = random_split(full_dataset, [train_size, validation_size])

# 数据加载器设置
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
validation_loader = DataLoader(validation_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)

# 打印训练集和验证集大小
print(f"训练集大小: {len(train_dataset)}")
print(f"验证集大小: {len(validation_dataset)}")
