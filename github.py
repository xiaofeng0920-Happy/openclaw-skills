#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Skill - GitHub 代码库管理
"""

import os
import sys
import json
import subprocess

def check_gh_auth():
    """检查 GitHub CLI 认证状态"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return {"authenticated": True, "status": "已认证"}
        else:
            return {"authenticated": False, "status": "未认证", "setup": "运行 'gh auth login'"}
    except FileNotFoundError:
        return {
            "authenticated": False,
            "status": "未安装 gh CLI",
            "setup": "访问 https://cli.github.com 安装"
        }

def issue_list(limit=10, state="open"):
    """查看 Issues"""
    auth = check_gh_auth()
    if not auth["authenticated"]:
        return auth
    
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--limit", str(limit), "--state", state],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"issues": result.stdout, "raw": result.returncode}
    except Exception as e:
        return {"error": str(e)}

def pr_list(limit=10, state="open"):
    """查看 Pull Requests"""
    auth = check_gh_auth()
    if not auth["authenticated"]:
        return auth
    
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--limit", str(limit), "--state", state],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"prs": result.stdout, "raw": result.returncode}
    except Exception as e:
        return {"error": str(e)}

def run_list(repo=None):
    """查看 CI/CD 构建"""
    auth = check_gh_auth()
    if not auth["authenticated"]:
        return auth
    
    try:
        cmd = ["gh", "run", "list", "--limit", "10"]
        if repo:
            cmd.extend(["--repo", repo])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {"runs": result.stdout, "raw": result.returncode}
    except Exception as e:
        return {"error": str(e)}

def auth():
    """执行认证"""
    print("🔐 GitHub CLI 认证")
    print("")
    print("运行以下命令完成认证：")
    print("  gh auth login")
    print("")
    print("按照提示选择认证方式（HTTPS/SSH）并登录 GitHub 账号")

def main():
    if len(sys.argv) < 2:
        print("GitHub Skill - GitHub 代码库管理")
        print("")
        print("用法：github <command> [options]")
        print("")
        print("命令:")
        print("  github auth        - 执行认证")
        print("  github status      - 检查认证状态")
        print("  github issues      - 查看 Issues")
        print("  github prs         - 查看 Pull Requests")
        print("  github runs        - 查看 CI/CD 构建")
        print("")
        print("示例:")
        print("  github issues --limit 5")
        print("  github prs --state all")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "auth":
        auth()
    elif command == "status":
        result = check_gh_auth()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command in ["issues", "issue"]:
        result = issue_list()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command in ["prs", "pr"]:
        result = pr_list()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif command in ["runs", "run"]:
        result = run_list()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"⚠️  未知命令：{command}")
        print("运行 'github' 查看帮助")

if __name__ == "__main__":
    main()
