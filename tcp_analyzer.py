#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCP状态分析器 - TCP State Analyzer
实时监控和分析TCP三次握手、四次挥手过程
"""

import socket
import time
import threading
from datetime import datetime
from enum import Enum
from advanced_logger import get_advanced_logger

class TCPState(Enum):
    """TCP连接状态枚举"""
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RCVD = "SYN_RCVD"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"

class TCPConnection:
    """TCP连接状态跟踪"""
    
    def __init__(self, connection_id, connection_type="CLIENT"):
        self.connection_id = connection_id
        self.connection_type = connection_type  # CLIENT 或 SERVER
        self.current_state = TCPState.CLOSED
        self.state_history = []
        self.handshake_steps = []
        self.teardown_steps = []
        self.start_time = datetime.now()
        self.logger = get_advanced_logger()
        
        # 记录初始状态
        self._change_state(TCPState.CLOSED, "连接初始化")
    
    def _change_state(self, new_state, reason=""):
        """改变TCP状态并记录"""
        old_state = self.current_state
        self.current_state = new_state
        timestamp = datetime.now()
        
        state_change = {
            "timestamp": timestamp,
            "old_state": old_state.value if old_state else "NONE",
            "new_state": new_state.value,
            "reason": reason
        }
        
        self.state_history.append(state_change)
        
        # 记录到日志
        self.logger.log_tcp_state_change(
            self.connection_id,
            old_state.value if old_state else "NONE",
            new_state.value,
            reason
        )
        
        print(f"🔄 TCP[{self.connection_id}] {old_state.value if old_state else 'NONE'} -> {new_state.value} ({reason})")
    
    def start_handshake_analysis(self):
        """开始三次握手分析"""
        print(f"\n🤝 开始分析TCP三次握手过程 - Connection[{self.connection_id}]")
        self.handshake_steps = []
    
    def log_handshake_step(self, step_number, description, packet_type=""):
        """记录握手步骤"""
        timestamp = datetime.now()
        step_info = {
            "step": step_number,
            "timestamp": timestamp.isoformat(),
            "description": description,
            "packet_type": packet_type
        }
        
        self.handshake_steps.append(step_info)
        
        self.logger.log_handshake_analysis(
            self.connection_id,
            "THREE_WAY_HANDSHAKE",
            step_number,
            timestamp.isoformat(),
            description
        )
        
        print(f"   步骤{step_number}: {description} [{packet_type}]")
    
    def simulate_client_handshake(self):
        """模拟客户端三次握手过程"""
        self.start_handshake_analysis()
        
        # 步骤1: 客户端发送SYN
        self._change_state(TCPState.SYN_SENT, "客户端发送SYN包")
        self.log_handshake_step(1, "客户端发送SYN包到服务器，seq=x", "SYN")
        time.sleep(0.1)  # 模拟网络延迟
        
        # 步骤2: 收到服务器的SYN+ACK
        self.log_handshake_step(2, "收到服务器SYN+ACK包，seq=y, ack=x+1", "SYN+ACK")
        time.sleep(0.1)
        
        # 步骤3: 客户端发送ACK
        self._change_state(TCPState.ESTABLISHED, "连接建立成功")
        self.log_handshake_step(3, "客户端发送ACK包，ack=y+1，握手完成", "ACK")
        
        print("✅ 三次握手完成，连接建立！")
    
    def simulate_server_handshake(self):
        """模拟服务器端三次握手过程"""
        self.start_handshake_analysis()
        
        # 服务器监听状态
        self._change_state(TCPState.LISTEN, "服务器监听状态")
        self.log_handshake_step(1, "服务器处于监听状态，等待客户端连接", "LISTEN")
        time.sleep(0.01)  # 减少延迟
        
        # 收到客户端SYN
        self._change_state(TCPState.SYN_RCVD, "收到客户端SYN包")
        self.log_handshake_step(2, "收到客户端SYN包，seq=x", "SYN")
        time.sleep(0.01)  # 减少延迟
        
        # 服务器发送SYN+ACK
        self.log_handshake_step(3, "服务器发送SYN+ACK包，seq=y, ack=x+1", "SYN+ACK")
        time.sleep(0.01)  # 减少延迟
        
        # 收到客户端ACK，连接建立
        self._change_state(TCPState.ESTABLISHED, "连接建立成功")
        self.log_handshake_step(4, "收到客户端ACK包，ack=y+1，握手完成", "ACK")
        
        print("✅ 服务器端三次握手完成，连接建立！")
    
    def start_teardown_analysis(self):
        """开始四次挥手分析"""
        print(f"\n👋 开始分析TCP四次挥手过程 - Connection[{self.connection_id}]")
        self.teardown_steps = []
    
    def log_teardown_step(self, step_number, description, packet_type=""):
        """记录挥手步骤"""
        timestamp = datetime.now()
        step_info = {
            "step": step_number,
            "timestamp": timestamp.isoformat(),
            "description": description,
            "packet_type": packet_type
        }
        
        self.teardown_steps.append(step_info)
        
        self.logger.log_handshake_analysis(
            self.connection_id,
            "FOUR_WAY_TEARDOWN",
            step_number,
            timestamp.isoformat(),
            description
        )
        
        print(f"   步骤{step_number}: {description} [{packet_type}]")
    
    def simulate_client_teardown(self):
        """模拟客户端发起的四次挥手"""
        self.start_teardown_analysis()
        
        # 步骤1: 客户端发送FIN
        self._change_state(TCPState.FIN_WAIT_1, "客户端发送FIN包")
        self.log_teardown_step(1, "客户端发送FIN包，请求关闭连接", "FIN")
        time.sleep(0.1)
        
        # 步骤2: 收到服务器ACK
        self._change_state(TCPState.FIN_WAIT_2, "等待服务器FIN")
        self.log_teardown_step(2, "收到服务器ACK确认", "ACK")
        time.sleep(0.1)
        
        # 步骤3: 收到服务器FIN
        self.log_teardown_step(3, "收到服务器FIN包", "FIN")
        self._change_state(TCPState.TIME_WAIT, "进入TIME_WAIT状态")
        time.sleep(0.1)
        
        # 步骤4: 发送最后的ACK
        self.log_teardown_step(4, "发送最后的ACK确认", "ACK")
        time.sleep(0.2)  # 模拟TIME_WAIT等待
        
        self._change_state(TCPState.CLOSED, "连接关闭完成")
        print("✅ 四次挥手完成，连接关闭！")
    
    def simulate_server_teardown(self):
        """模拟服务器响应的四次挥手"""
        self.start_teardown_analysis()
        
        # 步骤1: 收到客户端FIN
        self.log_teardown_step(1, "收到客户端FIN包，开始挥手过程", "FIN")
        self._change_state(TCPState.CLOSE_WAIT, "收到FIN，进入CLOSE_WAIT")
        time.sleep(0.01)  # 减少延迟
        
        # 步骤2: 服务器发送ACK确认
        self.log_teardown_step(2, "服务器发送ACK确认客户端FIN", "ACK")
        time.sleep(0.01)  # 减少延迟
        
        # 步骤3: 服务器发送FIN
        self.log_teardown_step(3, "服务器发送FIN包，准备关闭连接", "FIN")
        self._change_state(TCPState.LAST_ACK, "发送FIN，等待最后ACK")
        time.sleep(0.01)  # 减少延迟
        
        # 步骤4: 收到客户端最后的ACK
        self.log_teardown_step(4, "收到客户端最后ACK，挥手完成", "ACK")
        self._change_state(TCPState.CLOSED, "连接完全关闭")
        
        print("✅ 服务器端四次挥手完成，连接关闭！")
    
    def get_connection_summary(self):
        """获取连接总结信息"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            "connection_id": self.connection_id,
            "connection_type": self.connection_type,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "final_state": self.current_state.value,
            "total_state_changes": len(self.state_history),
            "handshake_steps": len(self.handshake_steps),
            "teardown_steps": len(self.teardown_steps),
            "state_history": self.state_history,
            "handshake_details": self.handshake_steps,
            "teardown_details": self.teardown_steps
        }
        
        return summary

class TCPAnalyzer:
    """TCP分析器主类"""
    
    def __init__(self):
        self.connections = {}
        self.logger = get_advanced_logger()
        
    def create_connection(self, connection_id, connection_type="CLIENT"):
        """创建新的TCP连接跟踪"""
        if connection_id in self.connections:
            print(f"⚠️  警告：连接 {connection_id} 已存在")
        
        connection = TCPConnection(connection_id, connection_type)
        self.connections[connection_id] = connection
        
        self.logger.log_connection_event("CONNECTION_CREATED", {
            "connection_id": connection_id,
            "type": connection_type,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"🆕 创建TCP连接跟踪: {connection_id} ({connection_type})")
        return connection
    
    def analyze_full_connection_cycle(self, connection_id, connection_type="CLIENT"):
        """分析完整的TCP连接周期（握手 + 数据传输 + 挥手）"""
        print(f"\n🔍 开始完整TCP连接周期分析")
        print("=" * 60)
        
        connection = self.create_connection(connection_id, connection_type)
        
        # 模拟三次握手
        if connection_type == "CLIENT":
            connection.simulate_client_handshake()
        else:
            connection.simulate_server_handshake()
        
        # 模拟数据传输阶段
        print(f"\n📊 数据传输阶段...")
        time.sleep(1)  # 模拟数据传输
        
        self.logger.log_performance_metric("数据传输时间", "1.0", "秒", "模拟数据传输")
        
        # 模拟四次挥手
        if connection_type == "CLIENT":
            connection.simulate_client_teardown()
        else:
            connection.simulate_server_teardown()
        
        # 生成连接总结
        summary = connection.get_connection_summary()
        
        print(f"\n📋 连接总结:")
        print(f"   连接ID: {summary['connection_id']}")
        print(f"   连接类型: {summary['connection_type']}")
        print(f"   持续时间: {summary['duration_seconds']:.2f} 秒")
        print(f"   状态变化次数: {summary['total_state_changes']}")
        print(f"   握手步骤: {summary['handshake_steps']} 步")
        print(f"   挥手步骤: {summary['teardown_steps']} 步")
        
        return summary
    
    def demonstrate_concurrent_connections(self):
        """演示并发连接分析"""
        print(f"\n🌐 并发连接演示")
        print("=" * 60)
        
        # 创建多个连接
        connections = []
        for i in range(3):
            conn_id = f"CONN_{i+1}"
            conn_type = "CLIENT" if i % 2 == 0 else "SERVER"
            
            def analyze_connection(cid, ctype):
                time.sleep(i * 0.2)  # 错开启动时间
                self.analyze_full_connection_cycle(cid, ctype)
            
            thread = threading.Thread(target=analyze_connection, args=(conn_id, conn_type))
            connections.append(thread)
            thread.start()
        
        # 等待所有连接完成
        for thread in connections:
            thread.join()
        
        print(f"\n✅ 并发连接演示完成，共分析了 {len(connections)} 个连接")

def main():
    """主函数 - TCP分析器演示"""
    print("🚀 TCP状态分析器启动")
    print("实时监控TCP三次握手和四次挥手过程")
    print("=" * 60)
    
    analyzer = TCPAnalyzer()
    
    try:
        # 演示单个客户端连接
        print("\n1️⃣ 客户端连接演示:")
        analyzer.analyze_full_connection_cycle("CLIENT_DEMO", "CLIENT")
        
        time.sleep(2)
        
        # 演示单个服务器连接
        print("\n2️⃣ 服务器连接演示:")
        analyzer.analyze_full_connection_cycle("SERVER_DEMO", "SERVER")
        
        time.sleep(2)
        
        # 演示并发连接
        print("\n3️⃣ 并发连接演示:")
        analyzer.demonstrate_concurrent_connections()
        
        # 生成最终报告
        logger = get_advanced_logger()
        summary = logger.generate_session_summary()
        
        print(f"\n📊 实验会话总结:")
        print(f"   日志目录: {logger.get_session_directory()}")
        print(f"   总连接数: {summary['total_connections']}")
        print(f"   状态变化数: {summary['tcp_state_changes']}")
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断分析")
    except Exception as e:
        print(f"\n❌ 分析过程中发生错误: {e}")
    
    print("\n🏁 TCP分析器演示完成！")

if __name__ == "__main__":
    main()
