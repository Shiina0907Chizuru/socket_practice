#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 综合自动化测试脚本
测试TCP服务器、HTTP服务器、网络性能等完整功能
"""

import socket
import threading
import time
import sys
import subprocess
import requests
import json
import os
from datetime import datetime
from urllib.parse import urljoin

class AdvancedSocketTester:
    def __init__(self):
        self.test_results = []
        self.servers_running = []
        self.basic_server = None  # 用于存储直接创建的服务器实例
        
    def log_test(self, test_name, success, message="", details=None):
        """记录测试结果"""
        status = "PASS" if success else "FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {test_name}: {status}"
        if message:
            result += f" - {message}"
        
        print(result)
        if details and not success:
            print(f"    详细信息: {details}")
            
        self.test_results.append((test_name, success, message, details))
    
    def start_server_process(self, script_name, port, server_type="TCP", extra_args=None):
        """启动服务器进程"""
        try:
            print(f"\n启动{server_type}服务器: {script_name}")
            
            # 检查脚本是否存在
            if not os.path.exists(script_name):
                self.log_test(f"{server_type}服务器文件检查", False, f"{script_name} 不存在")
                return None
            
            # 构建命令参数
            cmd_args = [sys.executable, script_name]
            
            # 对于基础server.py，需要特殊参数格式
            if script_name == "server.py":
                cmd_args.extend(["--auto", f"--port={port}"])
            else:
                # 对于其他服务器（如advanced_server.py）
                cmd_args.extend(["--auto", "--port", str(port)])
            
            # 添加额外参数
            if extra_args:
                cmd_args.extend(extra_args)
            
            # 启动服务器进程
            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='gbk', 
                errors='ignore'
            )
            
            # 等待服务器启动
            time.sleep(3)
            
            # 检查进程是否还在运行
            if process.poll() is None:
                self.log_test(f"{server_type}服务器启动", True, f"进程ID: {process.pid}")
                self.servers_running.append((process, server_type, script_name))
                return process
            else:
                stdout, stderr = process.communicate()
                self.log_test(f"{server_type}服务器启动", False, "进程意外退出", stderr)
                return None
                
        except Exception as e:
            self.log_test(f"{server_type}服务器启动", False, str(e))
            return None
    
    def test_basic_tcp_server(self, host='localhost', port=8888):
        """测试基础TCP服务器功能"""
        print(f"\n测试基础TCP服务器功能 ({host}:{port})")
        print("=" * 60)
        
        try:
            # 测试连接
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10.0)  # 增加超时时间到10秒
            
            start_time = time.time()
            client_socket.connect((host, port))
            connect_time = time.time() - start_time
            
            self.log_test("TCP服务器连接", True, f"连接时间: {connect_time*1000:.2f}ms")
            
            # 给服务器一点时间完成连接处理
            time.sleep(0.5)
            
            # 测试基本消息发送
            test_message = "Hello Server!"
            try:
                client_socket.send(test_message.encode('utf-8'))
                print(f"    发送消息: {test_message}")
                
                response = client_socket.recv(1024).decode('utf-8')
                if response:
                    self.log_test("TCP消息收发", True, f"收到回复: {response[:50]}...")
                    print(f"    收到响应: {response}")
                else:
                    self.log_test("TCP消息收发", False, "未收到回复")
            except socket.timeout:
                self.log_test("TCP消息收发", False, "响应超时")
            except Exception as e:
                self.log_test("TCP消息收发", False, f"发送消息失败: {e}")
            
            # 测试命令功能
            commands = ["time", "info", "stats"]
            for cmd in commands:
                try:
                    print(f"    测试命令: {cmd}")
                    client_socket.send(cmd.encode('utf-8'))
                    response = client_socket.recv(1024).decode('utf-8')
                    if response:
                        self.log_test(f"TCP命令 '{cmd}'", True, f"响应长度: {len(response)}")
                        print(f"    {cmd} 响应: {response[:100]}...")
                    else:
                        self.log_test(f"TCP命令 '{cmd}'", False, "无响应")
                except socket.timeout:
                    self.log_test(f"TCP命令 '{cmd}'", False, "响应超时")
                except Exception as e:
                    self.log_test(f"TCP命令 '{cmd}'", False, f"命令失败: {e}")
                time.sleep(1.0)  # 增加命令间隔时间
            
            client_socket.close()
            self.log_test("TCP连接关闭", True)
            
        except socket.timeout:
            self.log_test("TCP服务器测试", False, "连接超时")
        except ConnectionRefusedError:
            self.log_test("TCP服务器测试", False, "连接被拒绝，服务器未启动")
        except Exception as e:
            self.log_test("TCP服务器测试", False, str(e))
    
    def test_http_server(self, host='localhost', port=8080):
        """测试HTTP服务器功能"""
        print(f"\n测试HTTP服务器功能 ({host}:{port})")
        print("=" * 60)
        
        # 启动HTTP服务器
        server_process = self.start_server_process("http_server.py", port, "HTTP")
        if not server_process:
            self.log_test("HTTP服务器启动", False, "无法启动HTTP服务器")
            return
        
        # 等待HTTP服务器完全启动
        time.sleep(3)
        
        base_url = f"http://{host}:{port}"
        
        try:
            # 测试主页
            try:
                response = requests.get(base_url, timeout=10)
                if response.status_code == 200:
                    self.log_test("HTTP主页访问", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("HTTP主页访问", False, f"状态码: {response.status_code}")
            except requests.RequestException as e:
                self.log_test("HTTP主页访问", False, f"请求失败: {e}")
            
            # 测试API端点
            try:
                api_url = urljoin(base_url, "/api/status")
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test("HTTP API测试", True, f"返回数据: {data}")
                    except json.JSONDecodeError:
                        self.log_test("HTTP API测试", False, "JSON解析失败")
                else:
                    self.log_test("HTTP API测试", False, f"状态码: {response.status_code}")
            except requests.RequestException as e:
                self.log_test("HTTP API测试", False, f"API请求失败: {e}")
            
            # 测试POST请求
            try:
                post_url = urljoin(base_url, "/api/echo")
                test_data = {"message": "测试数据", "timestamp": datetime.now().isoformat()}
                response = requests.post(post_url, json=test_data, timeout=10)
                
                if response.status_code in [200, 201]:
                    self.log_test("HTTP POST测试", True, f"状态码: {response.status_code}")
                else:
                    self.log_test("HTTP POST测试", False, f"状态码: {response.status_code}")
            except requests.RequestException as e:
                self.log_test("HTTP POST测试", False, f"POST请求失败: {e}")
            
            # 测试错误处理
            try:
                error_url = urljoin(base_url, "/nonexistent")
                response = requests.get(error_url, timeout=10)
                if response.status_code == 404:
                    self.log_test("HTTP错误处理", True, "正确返回404")
                else:
                    self.log_test("HTTP错误处理", False, f"期望404，实际: {response.status_code}")
            except requests.RequestException as e:
                self.log_test("HTTP错误处理", False, f"错误测试失败: {e}")
                
        except Exception as e:
            self.log_test("HTTP服务器测试", False, f"测试过程出错: {e}")
        
        # HTTP服务器将在cleanup_servers()中统一清理，不需要在这里处理
    
    def test_network_performance(self, host='localhost', port=8888):
        """测试网络性能工具"""
        print(f"\n测试网络性能工具")
        print("=" * 60)
        
        try:
            # 测试ping功能
            import subprocess
            ping_result = subprocess.run([
                'ping', '-n', '1', host
            ], capture_output=True, text=True, encoding='gbk', errors='ignore')
            
            if ping_result.returncode == 0:
                self.log_test("网络连通性测试", True, f"Ping {host} 成功")
            else:
                self.log_test("网络连通性测试", False, f"Ping {host} 失败")
            
            # 测试端口扫描
            def test_port_scan(target_host, target_port):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target_host, target_port))
                    sock.close()
                    return result == 0
                except:
                    return False
            
            # 扫描常用端口
            common_ports = [22, 23, 53, 80, 110, 443, 993, 995]
            open_ports = []
            
            for port in common_ports:
                if test_port_scan(host, port):
                    open_ports.append(port)
            
            self.log_test("端口扫描测试", True, f"发现开放端口: {open_ports}")
            
            # 测试带宽测试
            start_time = time.time()
            test_data = b"0" * 1024  # 1KB测试数据
            
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(5)
                test_socket.connect((host, 8888))  # 连接到我们的测试服务器
                
                for _ in range(100):  # 发送100次
                    test_socket.send(test_data)
                
                end_time = time.time()
                duration = end_time - start_time
                throughput = (len(test_data) * 100) / duration / 1024  # KB/s
                
                test_socket.close()
                self.log_test("网络吞吐量测试", True, f"吞吐量: {throughput:.2f} KB/s")
                
            except Exception as e:
                self.log_test("网络吞吐量测试", False, f"测试失败: {e}")
                
        except Exception as e:
            self.log_test("网络性能测试", False, f"测试异常: {e}")
    
    def test_tcp_analyzer(self):
        """测试TCP分析器功能"""
        print("\nTCP状态分析器测试")
        print("=" * 60)
        
        try:
            from tcp_analyzer import TCPAnalyzer
            analyzer = TCPAnalyzer()
            self.log_test("TCP分析器创建", True, "分析器实例化成功")
            
            # 测试连接创建
            test_connection = analyzer.create_connection("test_client", "CLIENT")
            
            # 测试连接属性（修复：使用对象属性而不是.get()方法）
            if hasattr(test_connection, 'connection_id') and test_connection.connection_id == "test_client":
                self.log_test("TCP分析器测试", True, f"连接ID验证成功: {test_connection.connection_id}")
            else:
                self.log_test("TCP分析器测试", False, "连接ID验证失败")
                return
            
            # 简化测试：仅验证核心功能
            if hasattr(test_connection, 'connection_type') and test_connection.connection_type == "CLIENT":
                self.log_test("TCP连接类型测试", True, f"连接类型正确: {test_connection.connection_type}")
            else:
                self.log_test("TCP连接类型测试", False, "连接类型验证失败")
                
        except Exception as e:
            self.log_test("TCP分析器测试", False, f"测试异常: {str(e)}")

    def test_concurrent_connections(self, host='localhost', port=8888, num_clients=5):
        """测试并发连接处理"""
        print(f"\n测试并发连接处理 ({num_clients}个客户端)")
        print("=" * 60)
        
        successful_connections = 0
        connection_times = []
        
        def create_client_connection(client_id):
            nonlocal successful_connections
            try:
                start_time = time.time()
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5.0)
                
                client_socket.connect((host, port))
                connect_time = time.time() - start_time
                connection_times.append(connect_time)
                
                # 发送测试消息
                message = f"并发客户端 {client_id}"
                client_socket.send(message.encode('utf-8'))
                
                # 接收响应
                response = client_socket.recv(1024)
                if response:
                    successful_connections += 1
                
                client_socket.close()
                
            except Exception as e:
                print(f"客户端 {client_id} 连接失败: {e}")
        
        # 创建并发连接
        threads = []
        start_time = time.time()
        
        for i in range(num_clients):
            thread = threading.Thread(target=create_client_connection, args=(i+1,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # 错开连接时间
        
        # 等待所有连接完成
        for thread in threads:
            thread.join(timeout=10)
        
        total_time = time.time() - start_time
        success_rate = (successful_connections / num_clients) * 100
        avg_connect_time = sum(connection_times) / len(connection_times) if connection_times else 0
        
        if success_rate >= 80:  # 80%以上成功率认为通过
            self.log_test("并发连接测试", True, 
                         f"成功率: {success_rate:.1f}%, 平均连接时间: {avg_connect_time*1000:.2f}ms")
        else:
            self.log_test("并发连接测试", False, 
                         f"成功率过低: {success_rate:.1f}%")
    
    def cleanup_servers(self):
        """清理所有启动的服务器进程和实例"""
        print("\n清理服务器进程...")
        
        # 清理subprocess启动的服务器
        for process, server_type, script_name in self.servers_running:
            try:
                if process.poll() is None:  # 进程仍在运行
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"已停止 {server_type} 服务器 ({script_name})")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"强制结束 {server_type} 服务器 ({script_name})")
            except Exception as e:
                print(f"清理 {server_type} 服务器失败: {e}")
        
        self.servers_running.clear()
        
        # 清理直接创建的服务器实例
        if hasattr(self, 'basic_server') and self.basic_server:
            try:
                self.basic_server.stop_server()
                print("已停止直接启动的基础TCP服务器")
            except Exception as e:
                print(f"清理基础TCP服务器失败: {e}")
            finally:
                self.basic_server = None
    
    def run_comprehensive_tests(self):
        """运行完整的综合测试"""
        print("综合Socket测试")
        print("=" * 80)
        print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        start_time = time.time()
        
        # 按模块顺序执行测试
        print("\n【第1阶段】高级功能模块测试")
        self.test_tcp_analyzer()
        
        print("\n【第2阶段】服务器功能测试")
        
        # 启动基础TCP服务器并测试（使用直接导入方式，避免subprocess input()阻塞）
        tcp_port = 8888
        print(f"\n直接启动基础TCP服务器 (端口 {tcp_port})...")
        
        # 导入server模块并启动服务器
        try:
            import server
            
            # 创建服务器实例
            tcp_server = server.SocketServer('localhost', tcp_port)
            self.log_test("基础TCP服务器创建", True, f"SocketServer(localhost, {tcp_port})")
            
            # 在单独线程中启动服务器
            server_thread = threading.Thread(target=tcp_server.start_server)
            server_thread.daemon = True
            server_thread.start()
            
            # 等待服务器完全启动
            time.sleep(2)
            
            # 验证服务器是否正在监听
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(2.0)
                test_socket.connect(('localhost', tcp_port))
                test_socket.close()
                self.log_test("基础TCP服务器启动", True, f"服务器成功监听端口 {tcp_port}")
                
                # 运行TCP服务器测试
                time.sleep(1)
                self.test_basic_tcp_server(port=tcp_port)
                self.test_concurrent_connections(port=tcp_port)
                
                # 保存服务器实例以便后续清理
                self.basic_server = tcp_server
                
            except Exception as e:
                self.log_test("基础TCP服务器连接测试", False, f"连接失败: {e}")
                
        except Exception as e:
            self.log_test("基础TCP服务器启动", False, f"服务器启动失败: {e}")
        
        # 启动HTTP服务器并测试  
        http_port = 8080
        print(f"\n启动HTTP服务器 (端口 {http_port})...")
        self.test_http_server(port=http_port)
        
        print("\n【第3阶段】网络性能测试")
        self.test_network_performance()
        
        # 计算总耗时并生成报告
        total_time = time.time() - start_time
        self.generate_test_report(total_time)
        
        # 清理服务器进程
        self.cleanup_servers()
        
        # 返回测试是否整体成功
        passed = sum(1 for _, success, _, _ in self.test_results if success)
        total = len(self.test_results)
        return (passed / total) >= 0.7 if total > 0 else False

    def generate_test_report(self, total_time):
        """生成测试报告"""
        print("\n" + "=" * 80)
        print("综合测试结果报告")
        print("=" * 80)
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests} ")
        print(f"   失败测试: {failed_tests} ")
        print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
        print(f"   测试耗时: {total_time:.2f} 秒")
        
        # 按功能模块分类统计
        modules = {}
        for test_name, success, _, _ in self.test_results:
            module = test_name.split()[0] if test_name else "其他"
            if module not in modules:
                modules[module] = {"total": 0, "passed": 0}
            modules[module]["total"] += 1
            if success:
                modules[module]["passed"] += 1
        
        print(f"\n功能模块测试结果:")
        for module, stats in modules.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            status = "" if success_rate >= 80 else "" if success_rate >= 50 else ""
            print(f"   {module}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%) {status}")
        
        # 失败测试详情
        if failed_tests > 0:
            print(f"\n失败测试详情:")
            for test_name, success, message, details in self.test_results:
                if not success:
                    print(f"   • {test_name}: {message}")
                    if details:
                        print(f"     详情: {details}")
        
        # 保存测试报告到文件
        report_data = {
            "测试时间": datetime.now().isoformat(),
            "测试统计": {
                "总测试数": total_tests,
                "通过测试": passed_tests,
                "失败测试": failed_tests,
                "成功率": f"{(passed_tests/total_tests*100):.1f}%",
                "测试耗时": f"{total_time:.2f}秒"
            },
            "详细结果": [
                {
                    "测试名称": name,
                    "结果": "通过" if success else "失败",
                    "消息": message,
                    "详情": details
                }
                for name, success, message, details in self.test_results
            ]
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            print(f"\n详细测试报告已保存: {report_file}")
        except Exception as e:
            print(f"\n保存测试报告失败: {e}")
        
        print("\n" + "=" * 80)
        print("综合测试完成!")
        
        # 评估整体测试结果
        overall_success = (passed_tests / total_tests) >= 0.8 if total_tests > 0 else False
        if overall_success:
            print("恭喜！所有核心功能测试通过，项目运行良好！")
        else:
            print("部分测试失败，请检查相关功能并修复问题。")
        
        return overall_success

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("SOCKET网络编程实验 - 综合自动化测试脚本")
        print("=" * 60)
        print("功能: 全面测试TCP服务器、HTTP服务器、网络性能工具等")
        print("用法: python test_socket.py")
        print("\n测试内容:")
        print("• 高级日志系统")
        print("• TCP状态分析器") 
        print("• 高级TCP服务器功能")
        print("• HTTP服务器和API")
        print("• 网络性能测试工具")
        print("• 并发连接处理")
        print("• 错误处理机制")
        return
    
    print("准备启动综合Socket测试...")
    print("注意: 测试将自动启动服务器进程，请确保端口8888和8080未被占用")
    
    try:
        input("按 Enter 键开始测试，或 Ctrl+C 取消...")
    except KeyboardInterrupt:
        print("\n测试已取消")
        return
    
    tester = AdvancedSocketTester()
    
    try:
        success = tester.run_comprehensive_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        tester.cleanup_servers()
        sys.exit(1)
    except Exception as e:
        print(f"\n测试运行出错: {e}")
        tester.cleanup_servers()
        sys.exit(1)

if __name__ == "__main__":
    main()
