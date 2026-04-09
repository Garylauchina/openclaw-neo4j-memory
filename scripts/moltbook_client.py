#!/usr/bin/env python3
"""
Moltbook API 客户端（修复 SSL 兼容性问题）

使用 Python requests 库替代 curl，解决 macOS LibreSSL SSL 握手超时问题。
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

# 尝试导入 requests，如果不存在则使用 urllib
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    USE_REQUESTS = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("moltbook_client")


class MoltbookClient:
    """Moltbook API 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://www.moltbook.com/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        初始化客户端
        
        Args:
            api_key: API Key（默认从 moltbook_api_key.txt 读取）
            base_url: API 基础 URL
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 读取 API Key
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self._load_api_key()
        
        self.session = requests.Session() if USE_REQUESTS else None
        if self.api_key:
            if USE_REQUESTS:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                })
    
    def _load_api_key(self) -> Optional[str]:
        """从文件读取 API Key"""
        possible_paths = [
            Path.home() / ".openclaw" / "workspace" / "moltbook_api_key.txt",
            Path(__file__).parent.parent / "moltbook_api_key.txt",
            Path("moltbook_api_key.txt")
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        api_key = f.read().strip()
                    if api_key and api_key != "YOUR_MOLTBOOK_API_KEY":
                        logger.info(f"从 {path} 加载 API Key")
                        return api_key
                except Exception as e:
                    logger.warning(f"读取 {path} 失败：{e}")
        
        logger.warning("未找到有效的 API Key")
        return None
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        发送 HTTP 请求（带重试）
        
        Args:
            method: HTTP 方法（GET/POST）
            endpoint: API 端点（相对于 base_url）
            data: 请求数据（POST 时使用）
            
        Returns:
            JSON 响应字典，失败返回 None
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"请求 {method} {url} (尝试 {attempt}/{self.max_retries})")
                start_time = time.time()
                
                if USE_REQUESTS:
                    if method.upper() == "GET":
                        resp = self.session.get(url, timeout=self.timeout)
                    else:
                        resp = self.session.post(url, json=data, timeout=self.timeout)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"{method} {endpoint} 完成，耗时 {elapsed:.2f}s，状态码 {resp.status_code}")
                    
                    if resp.status_code == 200:
                        return resp.json()
                    else:
                        logger.warning(f"API 返回错误状态码：{resp.status_code}")
                        logger.warning(f"响应内容：{resp.text[:200]}")
                        return None
                else:
                    # Fallback: 使用 urllib
                    req = urllib.request.Request(url)
                    req.add_header("Authorization", f"Bearer {self.api_key}")
                    req.add_header("Content-Type", "application/json")
                    
                    if data:
                        req.data = json.dumps(data).encode('utf-8')
                    
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        elapsed = time.time() - start_time
                        logger.info(f"{method} {endpoint} 完成，耗时 {elapsed:.2f}s")
                        return json.loads(resp.read().decode('utf-8'))
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(f"请求失败（尝试 {attempt}/{self.max_retries}），耗时 {elapsed:.2f}s: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"所有重试失败：{e}")
                    return None
        
        return None
    
    def get_status(self) -> Optional[Dict]:
        """获取 Agent 状态"""
        return self._request("GET", "/agents/status")
    
    def get_home(self) -> Optional[Dict]:
        """获取主页信息"""
        return self._request("GET", "/home")
    
    def get_heartbeat(self) -> Optional[Dict]:
        """获取 Heartbeat 指令"""
        return self._request("GET", "/heartbeat.md")
    
    def get_post_comments(self, post_id: str, limit: int = 20) -> Optional[Dict]:
        """获取帖子评论"""
        return self._request("GET", f"/posts/{post_id}/comments?limit={limit}")
    
    def create_comment(self, post_id: str, content: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        """创建评论"""
        data = {"content": content}
        if parent_id:
            data["parent_id"] = parent_id
        return self._request("POST", f"/posts/{post_id}/comments", data)
    
    def mark_post_read(self, post_id: str) -> Optional[Dict]:
        """标记帖子为已读"""
        return self._request("POST", f"/notifications/read-by-post/{post_id}")
    
    def get_feed(self, sort: str = "new", limit: int = 15) -> Optional[Dict]:
        """获取 Feed"""
        return self._request("GET", f"/feed?sort={sort}&limit={limit}")
    
    def upvote_post(self, post_id: str) -> Optional[Dict]:
        """点赞帖子"""
        return self._request("POST", f"/posts/{post_id}/upvote")
    
    def create_post(self, submolt_name: str, title: str, content: str) -> Optional[Dict]:
        """创建帖子"""
        data = {
            "submolt_name": submolt_name,
            "title": title,
            "content": content
        }
        return self._request("POST", "/posts", data)


def main():
    parser = argparse.ArgumentParser(description="Moltbook API 客户端")
    parser.add_argument("--command", type=str, default="status",
                       choices=["status", "home", "heartbeat", "feed"],
                       help="API 命令（默认：status）")
    parser.add_argument("--timeout", type=int, default=30,
                       help="请求超时（秒，默认：30）")
    parser.add_argument("--retries", type=int, default=3,
                       help="最大重试次数（默认：3）")
    parser.add_argument("--verbose", action="store_true",
                       help="显示详细日志")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建客户端
    client = MoltbookClient(
        timeout=args.timeout,
        max_retries=args.retries
    )
    
    if not client.api_key:
        logger.error("未找到 API Key，请检查 moltbook_api_key.txt")
        sys.exit(1)
    
    # 执行命令
    logger.info(f"执行命令：{args.command}")
    
    if args.command == "status":
        result = client.get_status()
    elif args.command == "home":
        result = client.get_home()
    elif args.command == "heartbeat":
        result = client.get_heartbeat()
    elif args.command == "feed":
        result = client.get_feed()
    else:
        logger.error(f"未知命令：{args.command}")
        sys.exit(1)
    
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        logger.error("请求失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
