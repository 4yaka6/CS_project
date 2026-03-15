#服务器地址，训练轮数
import flwr as fl

fl.server.start_server(server_address='10.0.0.1:8080', config=fl.server.ServerConfig(num_rounds=10))

