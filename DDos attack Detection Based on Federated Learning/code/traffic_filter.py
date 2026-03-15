from scapy.all import *
import sys
import csv

if len(sys.argv) < 2:
    print('Pass 1 argument: the pcap file')
    exit(1)


packets = rdpcap(sys.argv[1])


def filter_8080(packet):
    return packet.haslayer(TCP) and (packet[TCP].dport or packet[TCP].sport) == 8080#端口号可修改

print(packets)


filtered_packets = filter(filter_8080, packets)

print(filtered_packets)


wrpcap("output.pcap", filtered_packets)

headers = ["Time", "Source IP", "Destination IP", "Source MAC", "Destination MAC", "PacketLength"]

import pandas as pd

df = pd.read_csv("output.csv")


first_timestamp = df['frame.time_epoch'].iloc[0]


df['relative_time'] = df['frame.time_epoch'] - first_timestamp

print(df.head().to_string())

df.to_csv('data.csv', index=False)




