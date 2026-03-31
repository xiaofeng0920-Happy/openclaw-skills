#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive Agent - 主动唤醒、定时任务自我检查
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

HEARTBEAT_FILE = Path.home() / ".openclaw" / "workspace" / "HEARTBEAT.md"
STATE_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "proactive_state.json"

def load_state():
    """加载状态"""
    if not STATE_FILE.exists():
        return {
            "last_check": None,
            "last_notification": None,
            "check_count": 0
        }
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_heartbeat():
    """检查 HEARTBEAT.md 中的任务"""
    if not HEARTBEAT_FILE.exists():
        return {"tasks": [], "status": "未找到 HEARTBEAT.md"}
    
    with open(HEARTBEAT_FILE, 'r') as f:
        content = f.read()
    
    # 解析任务列表
    tasks = []
    for line in content.split('\n'):
        if '- [ ]' in line or '- [x]' in line:
            task = line.strip()
            tasks.append({
                "task": task,
                "completed": '- [x]' in task
            })
    
    return {"tasks": tasks, "total": len(tasks), "completed": sum(1 for t in tasks if t["completed"])}

def check_email():
    """检查邮箱"""
    return {
        "service": "email",
        "status": "需要配置邮箱",
        "last_check": datetime.now().isoformat()
    }

def check_calendar():
    """检查日历"""
    return {
        "service": "calendar",
        "status": "需要配置日历",
        "events": [],
        "last_check": datetime.now().isoformat()
    }

def check_projects():
    """检查项目状态"""
    return {
        "service": "projects",
        "status": "需要配置项目源",
        "last_check": datetime.now().isoformat()
    }

def run_check(service=None):
    """执行检查"""
    state = load_state()
    state["last_check"] = datetime.now().isoformat()
    state["check_count"] = state.get("check_count", 0) + 1
    
    results = {
        "timestamp": state["last_check"],
        "check_count": state["check_count"]
    }
    
    if service == "email" or not service:
        results["email"] = check_email()
    if service == "calendar" or not service:
        results["calendar"] = check_calendar()
    if service == "projects" or not service:
        results["projects"] = check_projects()
    if service == "heartbeat" or not service:
        results["heartbeat"] = check_heartbeat()
    
    save_state(state)
    return results

def status():
    """显示状态"""
    state = load_state()
    heartbeat = check_heartbeat()
    return {
        "state": state,
        "heartbeat": heartbeat
    }

def main():
    if len(sys.argv) < 2:
        print("Proactive Agent - 主动唤醒、定时任务自我检查")
        print("")
        print("用法：proactive-agent <command> [options]")
        print("")
        print("命令:")
        print("  proactive-agent check        - 执行全面检查")
        print("  proactive-agent check email  - 检查邮箱")
        print("  proactive-agent check calendar - 检查日历")
        print("  proactive-agent status       - 显示状态")
        print("  proactive-agent heartbeat    - 检查 HEARTBEAT 任务")
        print("")
        print("配置:")
        print("  编辑 ~/.openclaw/workspace/HEARTBEAT.md 添加定时任务")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        result = status()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command == "check":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        result = run_check(service)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command == "heartbeat":
        result = check_heartbeat()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"⚠️  未知命令：{command}")
        print("运行 'proactive-agent' 查看帮助")

if __name__ == "__main__":
    main()
