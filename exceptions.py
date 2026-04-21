#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite 自定义异常模块

定义所有 YonSuite API 相关的异常类。
"""

from typing import Optional, Dict, Any


class YonSuiteError(Exception):
    """YonSuite 基础异常类"""
    pass


class YonSuiteConfigError(YonSuiteError):
    """配置错误"""
    pass


class YonSuiteAuthError(YonSuiteError):
    """认证/授权错误"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class YonSuiteAPIError(YonSuiteError):
    """API 调用错误"""
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 http_status: Optional[int] = None, raw_response: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.http_status = http_status
        self.raw_response = raw_response


class YonSuiteNotFoundError(YonSuiteAPIError):
    """资源未找到错误（404）"""
    pass


class YonSuitePermissionError(YonSuiteAPIError):
    """权限不足错误（403）"""
    pass


class YonSuiteRateLimitError(YonSuiteAPIError):
    """请求频率限制错误（429）"""
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class YonSuiteDataError(YonSuiteError):
    """数据错误（参数验证失败等）"""
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.field = field


class YonSuiteNetworkError(YonSuiteError):
    """网络错误"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class YonSuiteCacheError(YonSuiteError):
    """缓存错误"""
    pass


# 异常映射（HTTP 状态码 -> 异常类）
HTTP_ERROR_MAP = {
    403: YonSuitePermissionError,
    404: YonSuiteNotFoundError,
    429: YonSuiteRateLimitError,
}


def raise_api_error(result: Dict[str, Any], http_status: Optional[int] = None) -> None:
    """
    根据 API 响应结果抛出适当的异常
    
    Args:
        result: API 响应结果
        http_status: HTTP 状态码（如果有）
    
    Raises:
        YonSuiteAPIError 或其子类
    """
    code = result.get('code', '')
    message = result.get('message', result.get('errorMsg', '未知错误'))
    
    # 检查是否是成功响应
    if code in ('200', '00000', 200):
        return
    
    # 根据 HTTP 状态码选择异常类
    if http_status and http_status in HTTP_ERROR_MAP:
        exc_class = HTTP_ERROR_MAP[http_status]
        raise exc_class(message, error_code=code, http_status=http_status, raw_response=result)
    
    # 根据错误码选择异常类
    if code == '403' or 'permission' in message.lower():
        raise YonSuitePermissionError(message, error_code=code, http_status=http_status, raw_response=result)
    elif code == '404' or 'not found' in message.lower():
        raise YonSuiteNotFoundError(message, error_code=code, http_status=http_status, raw_response=result)
    elif code == '429' or 'rate limit' in message.lower():
        raise YonSuiteRateLimitError(message, error_code=code, http_status=http_status, raw_response=result)
    else:
        raise YonSuiteAPIError(message, error_code=code, http_status=http_status, raw_response=result)
