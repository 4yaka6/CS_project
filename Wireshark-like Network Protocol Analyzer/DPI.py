import matplotlib.pyplot as plt
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, UDP
from collections import defaultdict
from datetime import datetime
import numpy as np

# 服务类型常量
LowLatency = "LowLatency"
GuaranteedLatency = "GuaranteedLatency"
GuaranteedDelivery = "GuaranteedDelivery"
BestEffortDelivery = "BestEffortDelivery"


class ServiceStats:
    def __init__(self):
        self.hosts = set()  # 通信主机集合
        self.total_length = 0  # 总流量大小
        self.packet_count = 0  # 数据包数量
        self.first_time = None  # 第一个数据包的时间戳
        self.last_time = None  # 最后一个数据包的时间戳

    def update(self, packet):
        if packet.haslayer(IP):
            ip = packet[IP]
            self.hosts.update([ip.src, ip.dst])

        self.total_length += len(packet)
        self.packet_count += 1

        # 将 packet.time 转换为 float 类型，避免 'EDecimal' 错误
        timestamp = datetime.fromtimestamp(float(packet.time))

        if self.first_time is None or timestamp < self.first_time:
            self.first_time = timestamp
        if self.last_time is None or timestamp > self.last_time:
            self.last_time = timestamp

    def calculate_metrics(self, total_packets):
        """
        计算统计信息：
        - 主机数量
        - 流量包占比
        - 平均速率
        """
        host_count = len(self.hosts)
        packet_ratio = self.packet_count / total_packets if total_packets > 0 else 0
        duration = (self.last_time - self.first_time).total_seconds() if self.first_time and self.last_time else 1
        avg_speed = self.total_length / duration if duration > 0 else 0
        return host_count, packet_ratio, avg_speed

# 分类逻辑
def get_service_type(packet):
    # 检查是否是 TCP 包
    if packet.haslayer(TCP):
        tcp = packet[TCP]

        # SSH 流量，尽最大努力交付（例如管理协议）
        if tcp.sport == 22 or tcp.dport == 22:
            return BestEffortDelivery

        # HTTP 或 HTTPS 流量，保证延时
        if tcp.sport in [80, 443] or tcp.dport in [80, 443]:
            return GuaranteedLatency

        # 其他 TCP 流量，保证交付
        return GuaranteedDelivery

    # 检查是否是 UDP 包
    if packet.haslayer(UDP):
        udp = packet[UDP]

        # SIP 流量，低延时
        if udp.sport in [5060, 5061] or udp.dport in [5060, 5061]:
            return LowLatency

        # RTP 流量，低延时（通常用于语音、视频流）
        if udp.sport in range(16384, 32768) or udp.dport in range(16384, 32768):  # RTP 动态端口范围
            return LowLatency

        # DNS 查询，尽最大努力交付
        if udp.sport == 53 or udp.dport == 53:
            return BestEffortDelivery
        
        # TFTP 用于文件共享，尽最大努力交付
        if udp.sport == 69 or udp.dport == 69:
            return BestEffortDelivery

        # 其他 UDP 流量，保证交付
        return GuaranteedDelivery

    # 默认流量类型为保证交付
    return GuaranteedDelivery



# 绘图

def plot_service_stats(service_stats, total_packets):
    service_types = list(service_stats.keys())
    host_counts = []
    packet_ratios = []
    average_speeds = []

    # 计算每种服务类型的统计信息
    for stats in service_stats.values():
        host_count, packet_ratio, avg_speed = stats.calculate_metrics(total_packets)
        host_counts.append(host_count)
        packet_ratios.append(packet_ratio)
        average_speeds.append(avg_speed)

    # 确保所有可能的服务类型都占位，即使没有统计数据（值为0）
    all_service_types = [LowLatency, GuaranteedLatency, GuaranteedDelivery, BestEffortDelivery]
    for service_type in all_service_types:
        if service_type not in service_types:
            service_types.append(service_type)
            host_counts.append(0)
            packet_ratios.append(0)
            average_speeds.append(0)

    x = range(len(service_types))

    plt.figure(figsize=(12, 6))

    # 绘制条形图
    bar_width = 0.2
    bars1 = plt.bar(x, host_counts, width=bar_width, label="Host Count", color='b', align='center')
    bars2 = plt.bar([i + bar_width for i in x], packet_ratios, width=bar_width, label="Packet Ratio", color='g', align='center')
    bars3 = plt.bar([i + 2 * bar_width for i in x], average_speeds, width=bar_width, label="Average Speed (bytes/s)", color='r', align='center')

    # 添加顶部标注值
    def add_labels(bars, values):
        for bar, value in zip(bars, values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{value:.2f}" if isinstance(value, float) else f"{value}",
                ha='center', va='bottom', fontsize=9
            )

    add_labels(bars1, host_counts)
    add_labels(bars2, [v * 100 for v in packet_ratios])  # 转换为百分比
    add_labels(bars3, average_speeds)

    # 设置 X 轴刻度和标签
    plt.xticks([i + bar_width for i in x], service_types)
    plt.xlabel("Service Types")
    plt.ylabel("Values")
    plt.title("Service Statistics")
    plt.legend()

    # 保存和展示图表
    plt.savefig("service_stats.png")
    plt.show()


def main():
    packets = rdpcap("packet.pcap")    # 文件名和路径在此修改####################################
    service_stats = defaultdict(ServiceStats)
    total_packets = 0

    for packet in packets:
        total_packets += 1
        service_type = get_service_type(packet)
        service_stats[service_type].update(packet)

        if total_packets == 27000:  # 限制处理数据包数量
            break

    plot_service_stats(service_stats, total_packets)


if __name__ == "__main__":
    main()
