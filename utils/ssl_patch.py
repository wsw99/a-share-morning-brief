"""
工具函数: SSL 兼容 (国内金融数据源自签名证书)
"""
import ssl
import urllib3

# 禁用 SSL 证书校验 (仅用于访问国内金融数据源, 如 SSE/新浪财经)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
