#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite 配置管理模块

从环境变量读取配置，支持 .env 文件加载。

配置项：
- YONSUITE_APP_KEY: App Key
- YONSUITE_APP_SECRET: App Secret
- YONSUITE_TENANT_ID: 租户 ID
- YONSUITE_GATEWAY_URL: API 网关 URL（可选）
- YONSUITE_TOKEN_URL: Token URL（可选）
- YONSUITE_LOG_LEVEL: 日志级别（可选，默认 INFO）
- YONSUITE_CACHE_DIR: Token 缓存目录（可选）
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 自动加载 .env 文件（从当前文件所在目录向上查找）
def find_env_file() -> Optional[Path]:
    """查找 .env 文件"""
    current = Path(__file__).resolve()
    # 优先查找技能目录的 .env
    skill_env = current.parent / '.env'
    if skill_env.exists():
        return skill_env
    
    # 查找 ~/.openclaw/.env
    home_env = Path.home() / '.openclaw' / '.env'
    if home_env.exists():
        return home_env
    
    # 查找当前工作目录的 .env
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists():
        return cwd_env
    
    return None

# 加载环境变量
env_file = find_env_file()
if env_file:
    load_dotenv(env_file)


class Config:
    """YonSuite 配置类"""
    
    # 必需配置
    APP_KEY: str = os.getenv('YONSUITE_APP_KEY', '')
    APP_SECRET: str = os.getenv('YONSUITE_APP_SECRET', '')
    TENANT_ID: str = os.getenv('YONSUITE_TENANT_ID', '')
    
    # 可选配置（有默认值）
    GATEWAY_URL: str = os.getenv('YONSUITE_GATEWAY_URL', 'https://c2.yonyoucloud.com/iuap-api-gateway')
    TOKEN_URL: str = os.getenv('YONSUITE_TOKEN_URL', 'https://c2.yonyoucloud.com/iuap-api-auth')
    DEFAULT_TOKEN_URL: str = os.getenv('YONSUITE_DEFAULT_TOKEN_URL', 'https://c2.yonyoucloud.com/iuap-api-auth')
    
    # 日志配置
    LOG_LEVEL: str = os.getenv('YONSUITE_LOG_LEVEL', 'INFO')
    
    # 缓存配置
    CACHE_DIR: str = os.getenv('YONSUITE_CACHE_DIR', str(Path(__file__).parent))
    
    # Token 缓存提前过期时间（秒）
    TOKEN_REFRESH_BUFFER: int = int(os.getenv('YONSUITE_TOKEN_REFRESH_BUFFER', '300'))
    
    # HTTP 超时（秒）
    HTTP_TIMEOUT: int = int(os.getenv('YONSUITE_HTTP_TIMEOUT', '30'))
    
    # 重试配置
    MAX_RETRIES: int = int(os.getenv('YONSUITE_MAX_RETRIES', '3'))
    RETRY_DELAY: float = float(os.getenv('YONSUITE_RETRY_DELAY', '1.0'))
    
    @classmethod
    def validate(cls) -> None:
        """验证必需配置是否存在"""
        missing = []
        if not cls.APP_KEY:
            missing.append('YONSUITE_APP_KEY')
        if not cls.APP_SECRET:
            missing.append('YONSUITE_APP_SECRET')
        if not cls.TENANT_ID:
            missing.append('YONSUITE_TENANT_ID')
        
        if missing:
            raise ValueError(f"缺少必需的配置项：{', '.join(missing)}\n"
                           f"请在 {env_file or '~/.openclaw/.env'} 中配置")
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查配置是否完整"""
        return bool(cls.APP_KEY and cls.APP_SECRET and cls.TENANT_ID)


# 快捷访问
config = Config()
