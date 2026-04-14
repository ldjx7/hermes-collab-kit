#!/usr/bin/env python3
"""
PM 系统测试脚本
"""
import sys
import os

sys.path.insert(0, '/root/vibecoding/hermes-collab-kit')

from skills.pm import ProjectManager, Task

print("="*70)
print("测试 Phase 1 PM 系统")
print("="*70)

# 初始化 PM
print("\n1. 初始化 ProjectManager...")
pm = ProjectManager(workspace_path='/root/vibecoding/hermes-collab-kit')
print("✓ PM 初始化成功")

# 测试需求 intake
print("\n2. 测试需求 intake...")
request = "实现一个用户登录功能，包含注册、登录、JWT 认证"
print(f"需求：{request}")

result = pm.handle_request(request)
print(f"✓ 处理结果：{result['status']}")
print(f"  消息：{result['message']}")

# 显示路由结果
if result['status'] == 'success':
    print("\n3. 任务路由结果:")
    for task_id, info in result.get('data', {}).items():
        print(f"  Task ID: {task_id}")
        print(f"    标题：{info['task_title']}")
        print(f"    分配给：{info['assigned_agent']}")
        print(f"    状态：{info['status']}")

# 测试上下文
print("\n4. 测试上下文管理...")
context = pm.context_manager.get('project_name', 'Unknown')
print(f"  项目名称：{context}")

print("\n" + "="*70)
print("✅ Phase 1 PM 系统测试通过！")
print("="*70)
