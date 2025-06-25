#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import socket
import threading
from advanced_server import AdvancedSocketServer

# 全局变量用于控制服务器停止
server_instance = None
should_stop = False

def test_client():
    """简单的测试客户端"""
    global should_stop
    time.sleep(2)  # 等待服务器启动
    
    try:
        print("[CLIENT] 连接到高级服务器...")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 8889))
        
        # 接收欢迎消息
        welcome = client.recv(1024).decode('utf-8')
        print(f"[CLIENT] 收到欢迎消息: {welcome}")
        
        # 发送测试消息
        client.send("Hello Advanced Server!".encode('utf-8'))
        response = client.recv(1024).decode('utf-8')
        print(f"[CLIENT] 收到响应: {response}")
        
        # 等待一下让服务器端处理完
        time.sleep(2)
        
        client.close()
        print("[CLIENT] 客户端关闭")
        
        # 等待一下让异步分析完成
        time.sleep(1)
        
        # 设置停止标志
        should_stop = True
        
        # 发送一个连接来触发服务器检查停止条件
        try:
            trigger_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            trigger_socket.connect(('localhost', 8889))
            trigger_socket.close()
        except:
            pass
            
    except Exception as e:
        print(f"[CLIENT] 客户端错误: {e}")
        should_stop = True

def main():
    global server_instance, should_stop
    
    print("=== 手动测试高级TCP服务器 ===")
    print("查看调试输出...")
    print("注意：测试完成后服务器会自动停止")
    
    # 启动服务器
    server_instance = AdvancedSocketServer('localhost', 8889)
    
    # 在单独线程中启动客户端测试
    client_thread = threading.Thread(target=test_client, daemon=True)
    client_thread.start()
    
    try:
        # 启动服务器（这会阻塞）
        print("[SERVER] 启动高级服务器...")
        
        # 修改服务器的accept_connections方法以支持自动停止
        original_accept = server_instance.accept_connections
        
        def auto_stop_accept():
            """带自动停止功能的连接接受循环"""
            connection_count = 0
            while server_instance.running and not should_stop:
                try:
                    client_socket, address = server_instance.server_socket.accept()
                    connection_count += 1
                    
                    # 如果应该停止且这是触发连接，直接关闭
                    if should_stop:
                        client_socket.close()
                        print("[SERVER] 收到停止信号，准备关闭服务器...")
                        break
                    
                    # 正常处理连接
                    server_instance.connection_count += 1
                    connection_id = f"CONN_{server_instance.connection_count}"
                    
                    server_instance.stats['total_connections'] += 1
                    server_instance.stats['active_connections'] += 1
                    
                    print(f"新客户端连接: {address} -> {connection_id}")
                    print(f"当前活跃连接: {server_instance.stats['active_connections']}")
                    
                    print(f"[DEBUG] ===== 准备启动TCP分析线程: {connection_id} =====")
                    
                    # 创建TCP连接分析 - 异步执行，不阻塞socket
                    def async_tcp_analysis():
                        try:
                            print(f"[DEBUG] 开始异步TCP分析: {connection_id}")
                            tcp_conn = server_instance.tcp_analyzer.create_connection(connection_id, "SERVER")
                            # 异步执行握手分析，不影响实际socket通信
                            print(f"[DEBUG] 开始三次握手分析: {connection_id}")
                            tcp_conn.simulate_server_handshake()
                            print(f"[DEBUG] 三次握手分析完成: {connection_id}")
                            
                            # 记录连接事件到日志
                            server_instance.logger.log_connection_event("CLIENT_CONNECTED", {
                                'connection_id': connection_id,
                                'client_ip': address[0],
                                'client_port': address[1],
                                'total_connections': server_instance.stats['total_connections']
                            })
                            print(f"[DEBUG] 连接事件已记录: {connection_id}")
                            
                            # 给日志写入一些时间
                            time.sleep(0.1)
                            
                        except Exception as e:
                            print(f"TCP分析错误: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 在单独线程中执行TCP分析，避免阻塞
                    analysis_thread = threading.Thread(target=async_tcp_analysis, daemon=False)
                    print(f"[DEBUG] TCP分析线程已创建: {connection_id}")
                    analysis_thread.start()
                    print(f"[DEBUG] TCP分析线程已启动: {connection_id}")
                    
                    # 将线程添加到管理列表中
                    if not hasattr(server_instance, 'analysis_threads'):
                        server_instance.analysis_threads = []
                    server_instance.analysis_threads.append(analysis_thread)
                    
                    # 为每个客户端创建处理线程
                    client_thread = threading.Thread(
                        target=server_instance.handle_client,
                        args=(client_socket, connection_id, address),
                        name=f"Client-{connection_id}"
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if server_instance.running and not should_stop:
                        print(f"接受连接时发生错误: {e}")
                    break
        
        # 替换原来的accept_connections方法
        server_instance.accept_connections = auto_stop_accept
        server_instance.start_server()
        
    except KeyboardInterrupt:
        print("\n[SERVER] 收到中断信号，停止服务器...")
    finally:
        # 停止服务器
        server_instance.shutdown_server()
        
        # 等待分析线程完成
        if hasattr(server_instance, 'analysis_threads'):
            print(f"[SERVER] 等待 {len(server_instance.analysis_threads)} 个分析线程完成...")
            for thread in server_instance.analysis_threads:
                if thread.is_alive():
                    thread.join(timeout=2)
                    
        print("[SERVER] 服务器已停止")
        print("\n=== 测试完成！查看日志目录了解详细结果 ===")

if __name__ == "__main__":
    main()
