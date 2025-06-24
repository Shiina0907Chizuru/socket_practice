#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络性能测试工具 - Network Performance Tester
测试TCP连接的延迟、吞吐量、并发性能等关键指标
"""

import socket
import threading
import time
import statistics
from datetime import datetime
import json
from advanced_logger import get_advanced_logger, create_new_session

class NetworkPerformanceTester:
    def __init__(self, target_host='localhost', target_port=8888):
        """
        初始化网络性能测试器
        :param target_host: 目标服务器地址
        :param target_port: 目标服务器端口
        """
        self.target_host = target_host
        self.target_port = target_port
        self.logger = create_new_session("network_performance_test")
        
        # 测试结果存储
        self.test_results = {
            'latency_tests': [],
            'throughput_tests': [],
            'concurrent_tests': [],
            'connection_tests': []
        }
        
        self.logger.info(f"网络性能测试器初始化 - 目标: {target_host}:{target_port}")
    
    def test_connection_latency(self, num_tests=10):
        """测试连接延迟（RTT - Round Trip Time）"""
        print(f"\n🏓 连接延迟测试 (目标: {self.target_host}:{self.target_port})")
        print(f"执行 {num_tests} 次连接测试...")
        print("=" * 60)
        
        latencies = []
        successful_connections = 0
        
        for i in range(num_tests):
            try:
                start_time = time.time()
                
                # 建立连接
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)  # 5秒超时
                
                connect_start = time.time()
                sock.connect((self.target_host, self.target_port))
                connect_end = time.time()
                
                # 发送测试数据
                test_message = "PING_TEST"
                sock.send(test_message.encode('utf-8'))
                
                # 接收响应
                response = sock.recv(1024).decode('utf-8')
                end_time = time.time()
                
                # 关闭连接
                sock.close()
                
                # 计算延迟
                total_latency = (end_time - start_time) * 1000  # 毫秒
                connect_latency = (connect_end - connect_start) * 1000  # 毫秒
                
                latencies.append(total_latency)
                successful_connections += 1
                
                print(f"测试 {i+1:2d}: 总延迟 {total_latency:6.2f}ms, 连接延迟 {connect_latency:6.2f}ms ✅")
                
                # 记录到日志
                self.logger.log_performance_metric(f"延迟测试{i+1}", f"{total_latency:.2f}", "毫秒")
                
                time.sleep(0.1)  # 避免过于频繁的连接
                
            except Exception as e:
                print(f"测试 {i+1:2d}: 连接失败 - {e} ❌")
                self.logger.log_error("LATENCY_TEST_ERROR", str(e))
        
        # 统计分析
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            results = {
                "测试名称": "连接延迟测试",
                "目标地址": f"{self.target_host}:{self.target_port}",
                "测试次数": num_tests,
                "成功连接": successful_connections,
                "成功率": f"{(successful_connections/num_tests)*100:.1f}%",
                "平均延迟": f"{avg_latency:.2f} ms",
                "最小延迟": f"{min_latency:.2f} ms",
                "最大延迟": f"{max_latency:.2f} ms",
                "标准差": f"{std_dev:.2f} ms",
                "原始数据": latencies
            }
            
            self.test_results['latency_tests'].append(results)
            
            print(f"\n📊 延迟测试结果:")
            print(f"   成功率: {results['成功率']}")
            print(f"   平均延迟: {results['平均延迟']}")
            print(f"   延迟范围: {results['最小延迟']} ~ {results['最大延迟']}")
            print(f"   标准差: {results['标准差']}")
            
            return results
        else:
            print("❌ 所有连接测试都失败了")
            return None
    
    def test_throughput(self, data_size_kb=100, num_iterations=5):
        """测试网络吞吐量"""
        print(f"\n📈 网络吞吐量测试")
        print(f"数据大小: {data_size_kb} KB, 测试次数: {num_iterations}")
        print("=" * 60)
        
        throughput_results = []
        test_data = "X" * (data_size_kb * 1024)  # 生成测试数据
        
        for i in range(num_iterations):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10.0)
                
                # 连接到服务器
                connect_start = time.time()
                sock.connect((self.target_host, self.target_port))
                connect_time = time.time() - connect_start
                
                # 发送大量数据
                send_start = time.time()
                
                # 分块发送数据
                chunk_size = 4096
                bytes_sent = 0
                for j in range(0, len(test_data), chunk_size):
                    chunk = test_data[j:j+chunk_size]
                    sock.send(chunk.encode('utf-8'))
                    bytes_sent += len(chunk.encode('utf-8'))
                
                send_end = time.time()
                
                # 接收响应确认
                response = sock.recv(1024)
                receive_time = time.time()
                
                sock.close()
                
                # 计算吞吐量
                send_duration = send_end - send_start
                total_duration = receive_time - send_start
                
                send_throughput = (bytes_sent / send_duration) / (1024 * 1024)  # MB/s
                total_throughput = (bytes_sent / total_duration) / (1024 * 1024)  # MB/s
                
                throughput_results.append({
                    'iteration': i + 1,
                    'bytes_sent': bytes_sent,
                    'send_duration': send_duration,
                    'total_duration': total_duration,
                    'send_throughput_mbps': send_throughput,
                    'total_throughput_mbps': total_throughput,
                    'connect_time': connect_time
                })
                
                print(f"测试 {i+1}: 发送 {bytes_sent/1024:.0f}KB, "
                      f"吞吐量 {send_throughput:.2f}MB/s, "
                      f"连接时间 {connect_time*1000:.1f}ms ✅")
                
                self.logger.log_performance_metric(f"吞吐量测试{i+1}", f"{send_throughput:.2f}", "MB/s")
                
            except Exception as e:
                print(f"测试 {i+1}: 失败 - {e} ❌")
                self.logger.log_error("THROUGHPUT_TEST_ERROR", str(e))
        
        # 统计分析
        if throughput_results:
            send_throughputs = [r['send_throughput_mbps'] for r in throughput_results]
            avg_throughput = statistics.mean(send_throughputs)
            max_throughput = max(send_throughputs)
            min_throughput = min(send_throughputs)
            
            results = {
                "测试名称": "网络吞吐量测试",
                "数据大小": f"{data_size_kb} KB",
                "测试次数": num_iterations,
                "平均吞吐量": f"{avg_throughput:.2f} MB/s",
                "最大吞吐量": f"{max_throughput:.2f} MB/s",
                "最小吞吐量": f"{min_throughput:.2f} MB/s",
                "详细结果": throughput_results
            }
            
            self.test_results['throughput_tests'].append(results)
            
            print(f"\n📊 吞吐量测试结果:")
            print(f"   平均吞吐量: {results['平均吞吐量']}")
            print(f"   吞吐量范围: {results['最小吞吐量']} ~ {results['最大吞吐量']}")
            
            return results
        
        return None
    
    def test_concurrent_connections(self, max_connections=20, connection_duration=2):
        """测试并发连接性能"""
        print(f"\n🌐 并发连接测试")
        print(f"最大并发连接数: {max_connections}, 每个连接持续: {connection_duration}秒")
        print("=" * 60)
        
        successful_connections = 0
        failed_connections = 0
        connection_times = []
        active_connections = 0
        max_active = 0
        
        def create_connection(conn_id):
            nonlocal successful_connections, failed_connections, active_connections, max_active
            
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                
                # 连接到服务器
                sock.connect((self.target_host, self.target_port))
                connect_time = time.time() - start_time
                connection_times.append(connect_time)
                
                active_connections += 1
                max_active = max(max_active, active_connections)
                
                print(f"连接 {conn_id:2d}: 建立成功 ({connect_time*1000:.1f}ms) - 活跃连接: {active_connections}")
                
                # 发送测试消息
                sock.send(f"CONCURRENT_TEST_{conn_id}".encode('utf-8'))
                response = sock.recv(1024)
                
                # 保持连接指定时间
                time.sleep(connection_duration)
                
                sock.close()
                active_connections -= 1
                successful_connections += 1
                
                self.logger.log_connection_event("CONCURRENT_CONNECTION", {
                    'connection_id': conn_id,
                    'connect_time_ms': connect_time * 1000,
                    'duration': connection_duration,
                    'success': True
                })
                
            except Exception as e:
                failed_connections += 1
                active_connections = max(0, active_connections - 1)
                print(f"连接 {conn_id:2d}: 失败 - {e}")
                
                self.logger.log_error("CONCURRENT_CONNECTION_ERROR", str(e), f"connection_{conn_id}")
        
        # 启动并发连接
        threads = []
        start_time = time.time()
        
        for i in range(max_connections):
            thread = threading.Thread(target=create_connection, args=(i + 1,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # 稍微错开连接时间
        
        # 等待所有连接完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 统计结果
        success_rate = (successful_connections / max_connections) * 100
        avg_connect_time = statistics.mean(connection_times) if connection_times else 0
        
        results = {
            "测试名称": "并发连接测试",
            "目标连接数": max_connections,
            "成功连接数": successful_connections,
            "失败连接数": failed_connections,
            "成功率": f"{success_rate:.1f}%",
            "最大同时活跃连接": max_active,
            "平均连接时间": f"{avg_connect_time*1000:.2f} ms",
            "总测试时间": f"{total_time:.2f} 秒"
        }
        
        self.test_results['concurrent_tests'].append(results)
        
        print(f"\n📊 并发连接测试结果:")
        print(f"   成功率: {results['成功率']}")
        print(f"   最大同时连接: {results['最大同时活跃连接']}")
        print(f"   平均连接时间: {results['平均连接时间']}")
        
        return results
    
    def test_connection_stability(self, test_duration=30, message_interval=1):
        """测试连接稳定性"""
        print(f"\n🔗 连接稳定性测试")
        print(f"测试时长: {test_duration}秒, 消息间隔: {message_interval}秒")
        print("=" * 60)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            # 建立长连接
            start_time = time.time()
            sock.connect((self.target_host, self.target_port))
            
            messages_sent = 0
            messages_received = 0
            errors = 0
            response_times = []
            
            test_start = time.time()
            
            while (time.time() - test_start) < test_duration:
                try:
                    # 发送心跳消息
                    message = f"HEARTBEAT_{messages_sent + 1}"
                    send_time = time.time()
                    
                    sock.send(message.encode('utf-8'))
                    messages_sent += 1
                    
                    # 接收响应
                    response = sock.recv(1024).decode('utf-8')
                    receive_time = time.time()
                    
                    if response:
                        messages_received += 1
                        response_time = (receive_time - send_time) * 1000
                        response_times.append(response_time)
                        
                        print(f"消息 {messages_sent}: 响应时间 {response_time:.2f}ms ✅")
                    
                    time.sleep(message_interval)
                    
                except socket.timeout:
                    errors += 1
                    print(f"消息 {messages_sent}: 超时 ⏰")
                except Exception as e:
                    errors += 1
                    print(f"消息 {messages_sent}: 错误 - {e} ❌")
            
            sock.close()
            
            # 统计结果
            total_time = time.time() - test_start
            success_rate = (messages_received / messages_sent) * 100 if messages_sent > 0 else 0
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            results = {
                "测试名称": "连接稳定性测试",
                "测试时长": f"{total_time:.2f} 秒",
                "发送消息数": messages_sent,
                "接收消息数": messages_received,
                "错误次数": errors,
                "成功率": f"{success_rate:.1f}%",
                "平均响应时间": f"{avg_response_time:.2f} ms"
            }
            
            self.test_results['connection_tests'].append(results)
            
            print(f"\n📊 稳定性测试结果:")
            print(f"   消息成功率: {results['成功率']}")
            print(f"   平均响应时间: {results['平均响应时间']}")
            print(f"   错误次数: {results['错误次数']}")
            
            return results
            
        except Exception as e:
            print(f"❌ 稳定性测试失败: {e}")
            self.logger.log_error("STABILITY_TEST_ERROR", str(e))
            return None
    
    def run_comprehensive_test(self):
        """运行综合性能测试"""
        print("🚀 开始综合网络性能测试")
        print("=" * 80)
        
        test_start_time = time.time()
        
        # 1. 连接延迟测试
        latency_result = self.test_connection_latency(15)
        time.sleep(2)
        
        # 2. 吞吐量测试
        throughput_result = self.test_throughput(50, 3)
        time.sleep(2)
        
        # 3. 并发连接测试
        concurrent_result = self.test_concurrent_connections(15, 3)
        time.sleep(2)
        
        # 4. 连接稳定性测试
        stability_result = self.test_connection_stability(20, 1)
        
        total_test_time = time.time() - test_start_time
        
        # 生成综合报告
        comprehensive_report = {
            "测试概述": {
                "目标服务器": f"{self.target_host}:{self.target_port}",
                "测试开始时间": datetime.fromtimestamp(test_start_time).isoformat(),
                "总测试时间": f"{total_test_time:.2f} 秒"
            },
            "测试结果": {
                "延迟测试": latency_result,
                "吞吐量测试": throughput_result,
                "并发连接测试": concurrent_result,
                "连接稳定性测试": stability_result
            }
        }
        
        # 保存报告到文件
        report_file = f"{self.logger.get_session_directory()}/comprehensive_performance_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
        
        print(f"\n🏁 综合测试完成！")
        print(f"📊 总测试时间: {total_test_time:.2f} 秒")
        print(f"📁 详细报告已保存: {report_file}")
        
        # 生成会话总结
        session_summary = self.logger.generate_session_summary()
        
        return comprehensive_report

def main():
    """主函数"""
    print("🔬 网络性能测试工具")
    print("测试TCP连接的延迟、吞吐量、并发性能")
    print("=" * 50)
    
    try:
        # 获取测试目标
        host = input("请输入测试目标IP地址 (默认: localhost): ").strip()
        if not host:
            host = 'localhost'
        
        port_input = input("请输入测试目标端口号 (默认: 8888): ").strip()
        port = int(port_input) if port_input else 8888
        
        # 创建性能测试器
        tester = NetworkPerformanceTester(host, port)
        
        print(f"\n🎯 测试目标: {host}:{port}")
        print("请确保目标服务器正在运行...")
        
        input("按 Enter 键开始测试...")
        
        # 运行综合测试
        results = tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except ValueError:
        print("❌ 端口号必须是数字")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()
