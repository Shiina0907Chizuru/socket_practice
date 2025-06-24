#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版SOCKET服务器 - Advanced TCP Server
集成TCP状态分析、性能监控、智能日志管理
"""

import socket
import threading
import time
import json
import os
import sys
import argparse
from datetime import datetime
from advanced_logger import get_advanced_logger, create_new_session
from tcp_analyzer import TCPAnalyzer, TCPConnection

class AdvancedSocketServer:
    def __init__(self, host='localhost', port=8888):
        """
        初始化增强版服务器
        :param host: 服务器IP地址
        :param port: 服务器端口号
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # 存储客户端连接信息
        self.running = False
        self.connection_count = 0
        self.start_time = None
        
        # 初始化高级日志管理器
        self.logger = create_new_session("advanced_server")
        
        # 初始化TCP分析器
        self.tcp_analyzer = TCPAnalyzer()
        
        # 性能统计
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'total_messages': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'avg_response_time': 0
        }
        
        self.logger.info(f"增强版服务器初始化完成 - {host}:{port}")
    
    def start_server(self):
        """启动服务器并开始监听"""
        try:
            # 创建服务器套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)  # 支持更多并发连接
            
            self.running = True
            self.start_time = datetime.now()
            
            self.logger.info(f"增强版服务器启动成功")
            self.logger.info(f"监听地址: {self.host}:{self.port}")
            self.logger.info(f"最大并发连接数: 10")
            self.logger.info(f"TCP状态分析: 已启用")
            
            print(f"增强版SOCKET服务器启动成功！")
            print(f"监听地址: {self.host}:{self.port}")
            print(f"TCP状态分析已启用")
            print(f"日志目录: {self.logger.get_session_directory()}")
            print("=" * 60)
            
            # 开始接受连接
            self.accept_connections()
            
        except Exception as e:
            error_msg = f"服务器启动失败: {e}"
            self.logger.log_error("SERVER_START_ERROR", str(e))
            print(f"{error_msg}")
            raise
    
    def accept_connections(self):
        """接受客户端连接"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                
                # 生成连接ID
                self.connection_count += 1
                connection_id = f"CONN_{self.connection_count}"
                
                # 记录连接建立
                connection_info = {
                    'connection_id': connection_id,
                    'client_address': address,
                    'connect_time': datetime.now().isoformat(),
                    'socket': client_socket
                }
                
                self.clients[connection_id] = connection_info
                self.stats['total_connections'] += 1
                self.stats['active_connections'] += 1
                
                # 创建TCP连接分析
                tcp_conn = self.tcp_analyzer.create_connection(connection_id, "SERVER")
                tcp_conn.simulate_server_handshake()
                
                # 记录连接事件
                self.logger.log_connection_event("CLIENT_CONNECTED", {
                    'connection_id': connection_id,
                    'client_ip': address[0],
                    'client_port': address[1],
                    'total_connections': self.stats['total_connections']
                })
                
                self.logger.log_performance_metric("活跃连接数", self.stats['active_connections'])
                
                print(f"新客户端连接: {address} -> {connection_id}")
                print(f"当前活跃连接: {self.stats['active_connections']}")
                
                # 设置客户端socket超时，避免recv()阻塞
                client_socket.settimeout(30.0)  # 30秒超时
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, connection_id, address),
                    name=f"Client-{connection_id}"
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.log_error("CONNECTION_ACCEPT_ERROR", str(e))
                    print(f"接受连接时发生错误: {e}")
    
    def handle_client(self, client_socket, connection_id, address):
        """处理客户端连接 - 简化版本，专注于基本消息收发"""
        try:
            self.logger.info(f"开始处理客户端 {connection_id}")
            
            # 发送欢迎消息 - 与原始版本完全一致
            welcome_msg = f"欢迎连接到服务器！当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            client_socket.send(welcome_msg.encode('utf-8'))
            print(f"[{connection_id}] 发送欢迎消息: {welcome_msg}")
            
            while self.running:
                try:
                    # 接收客户端数据 - 简单直接的方式
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    message = data.decode('utf-8')
                    print(f"[{connection_id}] 收到: {message}")
                    
                    # 处理特殊命令 - 简化版本
                    if message.lower() == 'quit':
                        response = "再见！连接即将关闭。"
                        client_socket.send(response.encode('utf-8'))
                        break
                    elif message.lower() == 'time':
                        response = f"服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    elif message.lower() == 'info':
                        response = f"服务器信息 - 地址: {self.host}:{self.port}, 连接ID: {connection_id}"
                    elif message.lower() == 'stats':
                        response = f"服务器统计 - 活跃连接: {self.stats['active_connections']}, 总消息: {self.stats['total_messages']}"
                    else:
                        # 回声服务：将收到的消息返回给客户端
                        response = f"服务器回复[{connection_id}]: {message}"
                    
                    # 发送响应给客户端
                    client_socket.send(response.encode('utf-8'))
                    print(f"[{connection_id}] 发送: {response}")
                    
                    # 简单统计更新
                    self.stats['total_messages'] += 1
                    
                except socket.timeout:
                    continue
                except socket.error as e:
                    print(f"[{connection_id}] Socket错误: {e}")
                    break
                except UnicodeDecodeError:
                    print(f"[{connection_id}] 接收到非UTF-8数据，跳过")
                    continue
                    
        except Exception as e:
            print(f"[{connection_id}] 处理客户端时发生错误: {e}")
        finally:
            self.disconnect_client(client_socket, connection_id)
    
    def disconnect_client(self, client_socket, connection_id):
        """断开客户端连接"""
        try:
            # 模拟TCP四次挥手
            if connection_id in self.tcp_analyzer.connections:
                tcp_conn = self.tcp_analyzer.connections[connection_id]
                tcp_conn.simulate_server_teardown()
            
            client_socket.close()
            
            # 更新连接统计
            self.stats['active_connections'] -= 1
            
            # 记录断开连接事件
            if connection_id in self.clients:
                client_info = self.clients[connection_id]
                self.logger.log_connection_event("CLIENT_DISCONNECTED", {
                    'connection_id': connection_id,
                    'client_address': client_info.get('client_address'),
                    'active_connections': self.stats['active_connections']
                })
                
                # 移除客户端信息
                del self.clients[connection_id]
            
            print(f"[{connection_id}] 客户端已断开")
            print(f"当前活跃连接: {self.stats['active_connections']}")
            
        except Exception as e:
            self.logger.log_error("CLIENT_DISCONNECT_ERROR", str(e), connection_id)
    
    def shutdown_server(self):
        """关闭服务器"""
        print("\n正在关闭增强版服务器...")
        
        self.running = False
        
        # 关闭所有客户端连接
        for connection_id, client_info in self.clients.copy().items():
            if 'socket' in client_info:
                try:
                    client_info['socket'].close()
                except:
                    pass
        
        # 关闭服务器套接字
        if self.server_socket:
            self.server_socket.close()
        
        # 生成最终报告
        final_summary = self.generate_final_report()
        
        self.logger.info("增强版服务器已关闭")
        print("增强版服务器已安全关闭")
        
        return final_summary
    
    def generate_final_report(self):
        """生成服务器运行总结报告"""
        end_time = datetime.now()
        total_uptime = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        report = {
            "服务器运行总结": {
                "启动时间": self.start_time.isoformat() if self.start_time else None,
                "关闭时间": end_time.isoformat(),
                "总运行时间": f"{total_uptime:.2f} 秒",
                "统计信息": self.stats,
                "平均性能": {
                    "每秒连接数": f"{self.stats['total_connections'] / total_uptime:.2f}" if total_uptime > 0 else "0",
                    "每秒消息数": f"{self.stats['total_messages'] / total_uptime:.2f}" if total_uptime > 0 else "0",
                    "平均消息大小": f"{self.stats['total_bytes_received'] / self.stats['total_messages']:.2f} 字节" if self.stats['total_messages'] > 0 else "0"
                }
            }
        }
        
        # 保存到日志
        self.logger.log_connection_event("SERVER_SHUTDOWN", report)
        
        # 生成会话总结
        session_summary = self.logger.generate_session_summary()
        
        print(f"\n服务器运行总结:")
        print(f"   总运行时间: {total_uptime:.2f} 秒")
        print(f"   处理连接数: {self.stats['total_connections']}")
        print(f"   处理消息数: {self.stats['total_messages']}")
        print(f"   日志位置: {self.logger.get_session_directory()}")
        
        return report

def main():
    """主函数"""
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='增强版SOCKET服务器')
    parser.add_argument('--host', default='localhost', help='服务器IP地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=8888, help='服务器端口号 (默认: 8888)')
    parser.add_argument('--auto', action='store_true', help='自动模式，不需要用户输入')
    
    args = parser.parse_args()
    
    print("增强版SOCKET服务器")
    print("集成TCP状态分析、性能监控、智能日志")
    print("=" * 50)
    
    # 获取服务器配置
    try:
        if args.auto:
            # 自动模式，使用命令行参数或默认值
            host = args.host
            port = args.port
            print(f"自动启动模式: {host}:{port}")
        else:
            # 交互模式
            host = input("请输入服务器IP地址 (默认: localhost): ").strip()
            if not host:
                host = args.host
            
            port_input = input("请输入服务器端口号 (默认: 8888): ").strip()
            port = int(port_input) if port_input else args.port
        
        # 创建并启动增强版服务器
        server = AdvancedSocketServer(host, port)
        server.start_server()
        
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        if 'server' in locals():
            server.shutdown_server()
    except ValueError:
        print("端口号必须是数字")
    except Exception as e:
        print(f"服务器运行时发生错误: {e}")

if __name__ == "__main__":
    main()
