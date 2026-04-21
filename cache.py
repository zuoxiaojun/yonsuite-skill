#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 缓存模块

支持内存缓存和文件持久化缓存。
"""

import pickle
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock

from config import config
from exceptions import YonSuiteCacheError


class TokenCache:
    """Token 缓存管理器"""
    
    def __init__(self, cache_dir: Optional[str] = None, use_file_cache: bool = True):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存文件目录（默认使用配置中的 CACHE_DIR）
            use_file_cache: 是否启用文件缓存（默认 True）
        """
        self.cache_dir = Path(cache_dir or config.CACHE_DIR)
        self.use_file_cache = use_file_cache
        self.cache_file = self.cache_dir / '.yonsuite_token_cache'
        
        # 内存缓存
        self._memory_cache: Dict[str, Any] = {}
        self._lock = Lock()
        
        # 尝试加载文件缓存
        if self.use_file_cache:
            self._load_from_file()
    
    def _load_from_file(self) -> None:
        """从文件加载缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    # 检查是否过期
                    if data.get('expire_time', 0) > time.time():
                        self._memory_cache = data
        except Exception as e:
            # 文件缓存加载失败不影响使用
            pass
    
    def _save_to_file(self) -> None:
        """保存缓存到文件"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self._memory_cache, f)
        except Exception as e:
            # 文件缓存保存失败不影响使用
            pass
    
    def get(self, key: str) -> Optional[str]:
        """
        获取缓存的 Token
        
        Args:
            key: 缓存键（通常是 tenant_id）
            
        Returns:
            Token 字符串，如果不存在或已过期则返回 None
        """
        with self._lock:
            cache_key = f"token_{key}"
            if cache_key in self._memory_cache:
                data = self._memory_cache[cache_key]
                # 检查是否过期
                if data.get('expire_time', 0) > time.time():
                    return data.get('token')
                else:
                    # 已过期，删除
                    del self._memory_cache[cache_key]
            return None
    
    def set(self, key: str, token: str, expire_in: int) -> None:
        """
        设置 Token 缓存
        
        Args:
            key: 缓存键（通常是 tenant_id）
            token: Token 字符串
            expire_in: 过期时间（秒）
        """
        with self._lock:
            cache_key = f"token_{key}"
            # 提前 buffer 时间过期
            actual_expire_in = max(expire_in - config.TOKEN_REFRESH_BUFFER, 60)
            
            self._memory_cache[cache_key] = {
                'token': token,
                'expire_time': time.time() + actual_expire_in,
                'created_at': time.time()
            }
            
            # 保存到文件
            if self.use_file_cache:
                self._save_to_file()
    
    def delete(self, key: str) -> None:
        """
        删除缓存的 Token
        
        Args:
            key: 缓存键
        """
        with self._lock:
            cache_key = f"token_{key}"
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                if self.use_file_cache:
                    self._save_to_file()
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._memory_cache.clear()
            if self.use_file_cache and self.cache_file.exists():
                self.cache_file.unlink()
    
    def is_valid(self, key: str) -> bool:
        """
        检查 Token 是否有效
        
        Args:
            key: 缓存键
            
        Returns:
            True 如果 Token 存在且未过期
        """
        return self.get(key) is not None
    
    def get_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取 Token 缓存信息
        
        Args:
            key: 缓存键
            
        Returns:
            包含 token、expire_time 等信息的字典，如果不存在则返回 None
        """
        with self._lock:
            cache_key = f"token_{key}"
            if cache_key in self._memory_cache:
                data = self._memory_cache[cache_key].copy()
                data['remaining_time'] = max(0, data.get('expire_time', 0) - time.time())
                return data
            return None


# 全局缓存实例
_global_cache: Optional[TokenCache] = None


def get_cache(use_file_cache: bool = True) -> TokenCache:
    """
    获取全局缓存实例
    
    Args:
        use_file_cache: 是否启用文件缓存
        
    Returns:
        TokenCache 实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = TokenCache(use_file_cache=use_file_cache)
    return _global_cache
