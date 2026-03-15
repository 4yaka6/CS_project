import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn import preprocessing
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, ConfusionMatrixDisplay
from sklearn.utils import Bunch
from sklearn.neural_network import MLPClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from datetime import datetime
import os

# 导入数据集
def read_csv_files(path_name):
    df_ori = pd.read_csv(path_name)
    return df_ori


df_processed = read_csv_files("../../new_dataset/new_client1.csv")


#拆分数据帧以对每个客户端进行训练和测试，训练比例为80%，测试比例为20%

df_client_train_ori, df_client_test_ori = train_test_split(df_processed, train_size=0.8, random_state=42, stratify=df_processed['target'])

df_client_test = df_client_test_ori.reset_index(drop=True)



df_client_train = df_client_train_ori[df_client_train_ori['target'] != 0].reset_index(drop=True)


plt.subplot(2, 2, 1)
plt.title("Train label distribution client1", fontsize=10)
df_client_train.groupby('target').size().plot(kind='pie', autopct='%.2f', figsize=(10,10))
plt.subplots_adjust(left=0.1, right=1.0, top=0.9, bottom=0.1)

plt.subplot(2, 2, 2)
plt.title("Test label distribution client1", fontsize=10)
df_client_test.groupby('target').size().plot(kind='pie', autopct='%.2f', figsize=(5,5))

# 创建自己的数据集
import torch
class build_torch_dataset:
    def __init__(self, data, targets):
        self.data = data
        self.targets = targets

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        current_sample = self.data[idx, :]
        current_target = self.targets[idx]
        return (torch.tensor(current_sample, dtype=torch.float), torch.tensor(current_target, dtype=torch.long))

# 转化为torch数据集,使得更好的用与pytorch模型的训练
def covert_df_to_torch_dataset(df):


    df_data = df.iloc[:, 0: len(df.columns) - 1]
    df_target= df.iloc[:, len(df.columns) - 1: len(df.columns)]


    ds_torch_data = df_data.to_numpy()
    ds_torch_target = df_target.to_numpy()
    

    ds_torch_target_list = ds_torch_target.tolist()
    ds_torch_target_1D = []
    for i in range(len(ds_torch_target_list)):
        ds_torch_target_1D = np.append(ds_torch_target_1D, ds_torch_target_list[i][0])

    ds_torch = build_torch_dataset(ds_torch_data, ds_torch_target_1D)
    return ds_torch

ds_torch_train_client = covert_df_to_torch_dataset(df=df_client_train)
ds_torch_test_client = covert_df_to_torch_dataset(df=df_client_test)


#加载数据
train_loader_client = torch.utils.data.DataLoader(ds_torch_train_client, batch_size = 12, drop_last=True)
test_loader_client = torch.utils.data.DataLoader(ds_torch_test_client, batch_size = 12, drop_last=True)



#多层感知器
import torch.nn as nn
class NeuralNetwork(nn.Module):
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

print(NeuralNetwork().to('cpu'))

# 基于混淆矩阵对每个模型进行评估的函数
def evaluation(confmat_glb):


    print(confmat_glb)

    # 良性
    tp_benign = confmat_glb[0, 0].item()
    fn_benign = confmat_glb[0, 1].item() + confmat_glb[0, 2].item() + confmat_glb[0, 3].item() + confmat_glb[0, 4].item()
    fp_benign = confmat_glb[1, 0].item() + confmat_glb[2, 0].item() + confmat_glb[3, 0].item() + confmat_glb[4, 0].item()

    # ACK
    tp_ack = confmat_glb[1, 1].item()
    fn_ack = confmat_glb[1, 0].item() + confmat_glb[1, 2].item() + confmat_glb[1, 3].item() + confmat_glb[1, 4].item()
    fp_ack = confmat_glb[0, 1].item() + confmat_glb[2, 1].item() + confmat_glb[3, 1].item() + confmat_glb[4, 1].item()

    # Scan
    tp_scan = confmat_glb[2, 2].item()
    fn_scan = confmat_glb[2, 0].item() + confmat_glb[2, 1].item() + confmat_glb[2, 3].item() + confmat_glb[2, 4].item()
    fp_scan = confmat_glb[0, 2].item() + confmat_glb[1, 2].item() + confmat_glb[3, 2].item() + confmat_glb[4, 2].item()

    # SYN
    tp_syn = confmat_glb[3, 3].item()
    fn_syn= confmat_glb[3, 0].item() + confmat_glb[3, 1].item() + confmat_glb[3, 2].item() + confmat_glb[3, 4].item()
    fp_syn = confmat_glb[0, 3].item() + confmat_glb[1, 3].item() + confmat_glb[2, 3].item() + confmat_glb[4, 3].item()

    # UDP
    tp_udp = confmat_glb[4, 4].item()
    fn_udp= confmat_glb[4, 0].item() + confmat_glb[4, 1].item() + confmat_glb[4, 2].item() + confmat_glb[4, 3].item()
    fp_udp = confmat_glb[0, 4].item() + confmat_glb[1, 4].item() + confmat_glb[2, 4].item() + confmat_glb[3, 4].item()

    # 分别计算每个标签的召回率、精确度和f1分数
    recall_benign, precision_benign, f1_score_benign = evaluation_helper(tp_benign, fn_benign, fp_benign)
    recall_ack, precision_ack, f1_score_ack = evaluation_helper(tp_ack, fn_ack, fp_ack)
    recall_scan, precision_scan, f1_score_scan = evaluation_helper(tp_scan, fn_scan, fp_scan)
    recall_syn, precision_syn, f1_score_syn = evaluation_helper(tp_syn, fn_syn, fp_syn)
    recall_udp, precision_udp, f1_score_udp = evaluation_helper(tp_udp, fn_udp, fp_udp)

    # 二维化
    return [[recall_benign, precision_benign, f1_score_benign], [ recall_ack, precision_ack, f1_score_ack],
            [recall_scan, precision_scan, f1_score_scan], [recall_syn, precision_syn, f1_score_syn], [recall_udp, precision_udp, f1_score_udp]]

#计算回归精度和f1分数的辅助函数
def evaluation_helper(tp, fn, fp):
    if tp == 0:
        recall = 0
        precision = 0
        f1_score = 0
    else:
        recall = round((tp)/(tp + fn), 4)
        precision = round((tp)/(tp + fp), 4)
        f1_score = round(2 * ((precision * recall)/(precision + recall)), 4)


    return recall, precision, f1_score

def display_evaluation(eval_list):
    print()
    print("The display will followed by format: Type: [Recall, precision, f1_score]")
    for i in range(len(eval_list)):
        if i == 0:
            print('benign:', end = ' ')
        if i == 1:
            print('ack:', end = ' ')
        if i == 2:
            print('scan:', end = ' ')
        if i == 3:
            print('syn:', end = ' ')
        if i == 4:
            print('udp:', end = ' ')
        
        print(eval_list[i])

# 训练模型
def train(dataloader, model, loss_fn, optimizer, epoch):
    for i in range(epoch):
        model.train()  # 设置模型为训练模式

        # 遍历数据加载器提供的所有批次数据
        for tup in dataloader:
            X = tup[0]  # 输入数据
            y = tup[1]  # 真实标签

            pred = model(X)  # 前向传播，获取模型预测值
            loss = loss_fn(pred, y)  # 计算损失

            optimizer.zero_grad()  # 清零梯度
            loss.backward()  # 反向传播，计算梯度
            optimizer.step()  # 更新模型参数


# 测试模型
from torchmetrics import Recall, ConfusionMatrix


def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    model.eval()  # 设置模型为评估模式，关闭dropout等训练时特有的操作
    test_loss, total = 0, 0
    recall_glb = 0.0
    recall_model = Recall(task="multiclass", average='macro', num_classes=5)
    confmat_glb = torch.zeros(5, 5, dtype=torch.int64)  # 初始化全局混淆矩阵
    with torch.no_grad():  # 关闭梯度计算，加速和节省内存
        for tup in datloader:
            X = tup[0]  # 获取输入数据
            y = tup[1]  # 获取目标标签

            pred = model(X)  # 预测输出

            test_loss += loss_fn(pred, y).item()  # 累加测试损失

            pred_int = pred.argmax(1)  # 获取每个样本的预测类别
            recall_local = recall_model(pred_int, y)  # 计算本批次的召回率

            recall_glb += recall_local  # 累加全局召回率

            total += y.size(0)  # 累加样本数量

            confmat = ConfusionMatrix(task="multiclass", num_classes=5)  # 初始化本批次的混淆矩阵

            confmat_local = confmat(pred_int, y)  # 计算本批次的混淆矩阵
            confmat_glb += confmat_local  # 累加全局混淆矩阵

    recall_glb /= size  # 计算平均召回率
    recall_glb = recall_glb * 12  # 调整召回率
    test_loss /= size  # 计算平均损失

    eval_list = evaluation(confmat_glb)  # 使用混淆矩阵进行其他评估
    display_evaluation(eval_list)  # 显示评估结果

    return test_loss, recall_glb  # 返回测试损失和召回率

def train_test_itr(epochs, train_loader, test_loader):
    loss_fn = nn.CrossEntropyLoss()
    model_dnn = NeuralNetwork()
    optimizer = torch.optim.SGD(model_dnn.parameters(), lr=1e-3)
    for t in range(epochs):
        print(f"Epoch {t + 1}\n----------------------------------------------")
        train(train_loader, model_dnn, loss_fn, optimizer, epoch=5)
        test(test_loader, model_dnn, loss_fn)




from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10



import flwr as fl

def get_parameters(net):
    return [val.cpu().numpy() for _, val in net.state_dict().items()]

def set_parameters(net, parameters):
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)


class FlowerClient(fl.client.NumPyClient):
    def __init__(self, net, trainloader, valloader, loss_func, optimizer, epoch):
        self.net = net
        self.trainloader = trainloader
        self.valloader = valloader
        self.loss_func = loss_func
        self.optimizer = optimizer
        self.epoch = epoch

    def get_parameters(self, config):
        return get_parameters(self.net)

    def fit(self, parameters, config):
        set_parameters(self.net, parameters)
        train(self.trainloader, self.net, self.loss_func, self.optimizer, self.epoch)
        return get_parameters(self.net), len(self.trainloader), {}

    def evaluate(self, parameters, config):
        set_parameters(self.net, parameters)
        torch.save(self.net.state_dict(), 'mode1_new.pt')
        loss, accuracy = test(self.valloader, self.net, self.loss_func)
        return float(loss), len(self.valloader), {"accuracy": float(accuracy)}

trainloader = train_loader_client
valloader = test_loader_client
loss_fun = nn.CrossEntropyLoss()
model_dnn = NeuralNetwork()
optimizer = torch.optim.SGD(model_dnn.parameters(), lr=1e-3)

client1 = FlowerClient(model_dnn, trainloader, valloader, loss_fun, optimizer, epoch=10)


fl.client.start_numpy_client(
    server_address = "10.0.0.1:8080",
    client=client1,
)
