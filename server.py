#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 服务器端
基于TCP协议的C/S架构服务器实现
"""

import socket
import threading
import time
import logging
from datetime import datetime

class SocketServer:
    def __init__(self, host='localhost', port=8888):
        """
        初始化服务器
        :param host: 服务器IP地址
        :param port: 服务器端口号
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []  # 存储连接的客户端
        self.running = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_server(self):
        """启动服务器"""
        try:
            # 1. 创建TCP套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置socket选项，允许地址重用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 2. 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            
            # 3. 设置为监听模式
            self.server_socket.listen(5)  # 最大连接数为5
            
            self.running = True
            self.logger.info(f"服务器启动成功，监听地址: {self.host}:{self.port}")
            self.logger.info("等待客户端连接...")
            
            while self.running:
                try:
                    # 4. 接受客户端连接
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"新客户端连接: {client_address}")
                    
                    # 为每个客户端创建新线程处理
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"接受连接时出错: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket, client_address):
        """
        处理客户端连接
        :param client_socket: 客户端套接字
        :param client_address: 客户端地址
        """
        self.clients.append(client_socket)
        
        try:
            # 发送欢迎消息
            welcome_msg = f"欢迎连接到服务器！当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            client_socket.send(welcome_msg.encode('utf-8'))
            
            while self.running:
                try:
                    # 5. 接收客户端数据
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    message = data.decode('utf-8')
                    self.logger.info(f"收到来自 {client_address} 的消息: {message}")
                    
                    # 处理特殊命令
                    if message.lower() == 'quit':
                        break
                    elif message.lower() == 'time':
                        response = f"服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    elif message.lower() == 'info':
                        response = f"服务器信息 - 地址: {self.host}:{self.port}, 在线客户端: {len(self.clients)}"
                    else:
                        # 回声服务：将收到的消息返回给客户端
                        response = f"服务器回复: {message}"
                    
                    # 6. 发送响应给客户端
                    client_socket.send(response.encode('utf-8'))
                    
                except socket.timeout:
                    continue
                except socket.error as e:
                    self.logger.error(f"处理客户端 {client_address} 时出错: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"客户端处理异常: {e}")
        finally:
            # 7. 关闭客户端连接
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            self.logger.info(f"客户端 {client_address} 断开连接")
    
    def stop_server(self):
        """停止服务器"""
        self.running = False
        
        # 关闭所有客户端连接
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("服务器已停止")

def main():
    """主函数"""
    print("=== SOCKET网络编程实验 - 服务器端 ===")
    print("支持命令:")
    print("- time: 获取服务器时间")
    print("- info: 获取服务器信息")
    print("- quit: 断开连接")
    print("- 其他消息: 回声服务")
    print("=" * 40)
    
    # 获取服务器配置
    try:
        host = input("请输入服务器IP地址 (默认: localhost): ").strip()
        if not host:
            host = 'localhost'
        
        port_input = input("请输入服务器端口号 (默认: 8888): ").strip()
        port = int(port_input) if port_input else 8888
        
        # 创建并启动服务器
        server = SocketServer(host, port)
        
        try:
            server.start_server()
        except KeyboardInterrupt:
            print("\n接收到中断信号，正在关闭服务器...")
            server.stop_server()
            
    except ValueError:
        print("端口号必须是整数！")
    except Exception as e:
        print(f"服务器运行出错: {e}")

if __name__ == "__main__":
    main()
