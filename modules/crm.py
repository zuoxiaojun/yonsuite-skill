#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRM 商机管理模块

提供商机查询等功能。
API: POST /yonbip/crm/oppt/bill/list
"""

import logging
import urllib.parse
from typing import Optional, List, Dict, Any

try:
    from .base import BaseAPIClient, retry_on_failure
    from ..models import Opportunity
    from ..exceptions import YonSuiteAPIError
except ImportError:
    from modules.base import BaseAPIClient, retry_on_failure
    from models import Opportunity
    from exceptions import YonSuiteAPIError

logger = logging.getLogger(__name__)


class CrmModule(BaseAPIClient):
    """CRM 商机管理模块"""

    def __init__(self, gateway_url: str = None):
        super().__init__(gateway_url=gateway_url)
        self.base_path = "/yonbip/crm/oppt"

    @retry_on_failure()
    def query_opportunities(self, access_token: str, page_index: int = 1, page_size: int = 500,
                            code: str = None, name: str = None,
                            oppt_state: str = None, win_lose_state: str = None,
                            is_sum: bool = True, date_from: str = None, date_to: str = None) -> Dict:
        """
        查询商机列表

        API: POST /yonbip/crm/oppt/bill/list

        Args:
            access_token: API 访问 Token
            page_index: 页码，默认值：1
            page_size: 每页行数，默认值：500
            code: 商机编码（可选）
            name: 商机名称（可选）
            oppt_state: 商机状态（可选）：0-进行中；1-暂停；2-作废；3-关闭
            win_lose_state: 赢丢单状态（可选）：0-赢单；1-丢单；2-未定；3-部分赢单
            is_sum: True=返回表头+明细，False=仅表头
            date_from: 起始日期，格式 YYYY-MM-DD（可选）
            date_to: 截止日期，格式 YYYY-MM-DD（可选）

        Returns:
            API 响应结果（含 data.recordList 商机组）
        """
        url = f"{self.gateway_url}{self.base_path}/bill/list?access_token={urllib.parse.quote(access_token)}"

        body = {
            "pageIndex": page_index,
            "pageSize": page_size,
            "isSum": is_sum,
        }

        # 可选过滤字段
        if code:
            body["code"] = code
        if name:
            body["name"] = name
        if oppt_state:
            body["opptState"] = oppt_state
        if win_lose_state:
            body["winLoseOrderState"] = win_lose_state

        # 日期范围过滤（通过 simpleVOs）
        if date_from or date_to:
            simple_vos = []
            if date_from or date_to:
                date_filter = {"field": "createTime", "op": "between"}
                date_filter["value1"] = date_from or "1900-01-01 00:00:00"
                date_filter["value2"] = date_to or "2099-12-31 23:59:59"
                simple_vos.append(date_filter)
            body["simpleVOs"] = simple_vos
        else:
            body["simpleVOs"] = []

        logger.info(f"查询商机列表，页码：{page_index}，每页：{page_size}，状态：{oppt_state}，赢丢单：{win_lose_state}")
        return self._http_post_raw(url, body)

    def parse_opportunities(self, result: Dict) -> List[Opportunity]:
        """
        解析商机查询结果为 Opportunity 对象列表

        Args:
            result: query_opportunities 返回的原始 API 结果

        Returns:
            Opportunity 对象列表
        """
        if str(result.get('code', '')) not in ('200', '0', '成功', ''):
            raise YonSuiteAPIError(f"API error: {result.get('message', 'Unknown error')}")

        data = result.get('data', {})
        records = data.get('recordList', [])
        return [Opportunity.from_api(r) for r in records]
