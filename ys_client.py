#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yonsuite_search - 用友 YonSuite API 查询客户端 v2.0

重构优化版,采用模块化设计,提供类型安全、错误处理、缓存等增强功能。

**定位:** 专注于 YS 系统业务数据的查询(只读操作)

功能包括:
- Token 管理(自动获取、刷新、持久化缓存)
- 销售订单查询(列表、详情)
- 采购订单查询(列表)
- 客户档案查询(列表)
- 供应商档案查询(列表、详情)
- 库存查询(现存量、可用量)
- 生产订单查询(列表、详情)
- 商机查询(列表)

使用方法:
    from ys_client import YonSuiteClient
    client = YonSuiteClient()

    # 查询销售订单
    orders = client.query_sale_orders(customer_name="测试客户")

    # 查询生产订单(近一个月)
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=30)
    production_orders = client.query_production_orders(
        start_date=start.strftime('%Y-%m-%d'),
        end_date=end.strftime('%Y-%m-%d'),
        page_size=50
    )

    # 查询库存
    stock = client.query_current_stock(product_code="A010100003")

作者:Alice
创建:2026-03-17
重构:2026-03-20 - v2.0 模块化重构
"""

import os
import sys
import time
import hmac
import hashlib
import base64
import urllib.parse
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

# 导入配置和异常
from config import config, Config
from exceptions import (
    YonSuiteConfigError,
    YonSuiteAuthError,
    YonSuiteAPIError,
    raise_api_error
)
from cache import get_cache, TokenCache

# 导入功能模块
from modules.sales import SalesModule
from modules.purchase import PurchaseModule
from modules.stock import StockModule
from modules.customer import CustomerModule
from modules.vendor import VendorModule
from modules.production import ProductionModule
from modules.voucher import VoucherModule
from modules.todo import TodoModule
from modules.product import ProductModule
from modules.org import OrgModule
from modules.crm import CrmModule

# 导入数据模型
from models import (
    SaleOrder, SaleOrderDetail,
    PurchaseOrder,
    Customer,
    Vendor, VendorDetail,
    StockItem,
    ProductionOrder, ProductionOrderDetail,
    ProductItem,
    Opportunity
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YonSuiteClient:
    """
    用友 YonSuite API 客户端(v2.0 重构版)

    提供统一的 API 访问接口,整合所有 YonSuite 相关功能。

    Attributes:
        sales: 销售订单模块
        purchase: 采购订单模块
        stock: 库存查询模块
        customer: 客户档案模块
        vendor: 供应商档案模块
        production: 生产订单模块
    """

    def __init__(self,
                 app_key: Optional[str] = None,
                 app_secret: Optional[str] = None,
                 tenant_id: Optional[str] = None,
                 gateway_url: Optional[str] = None,
                 use_cache: bool = True):
        """
        初始化客户端

        Args:
            app_key: App Key(不传则从环境变量读取)
            app_secret: App Secret(不传则从环境变量读取)
            tenant_id: 租户 ID(不传则从环境变量读取)
            gateway_url: API 网关 URL(不传则使用默认值)
            use_cache: 是否启用 Token 缓存(默认 True)

        Raises:
            YonSuiteConfigError: 配置不完整时抛出
        """
        # 验证配置
        self.app_key = app_key or config.APP_KEY
        self.app_secret = app_secret or config.APP_SECRET
        self.tenant_id = tenant_id or config.TENANT_ID
        self.gateway_url = gateway_url or config.GATEWAY_URL
        self.token_url = config.TOKEN_URL
        self.default_token_url = config.DEFAULT_TOKEN_URL

        # 验证必需配置
        if not all([self.app_key, self.app_secret, self.tenant_id]):
            missing = []
            if not self.app_key: missing.append('YONSUITE_APP_KEY')
            if not self.app_secret: missing.append('YONSUITE_APP_SECRET')
            if not self.tenant_id: missing.append('YONSUITE_TENANT_ID')
            raise YonSuiteConfigError(f"缺少必需配置:{', '.join(missing)}")

        # Token 缓存
        self.use_cache = use_cache
        self._cache: Optional[TokenCache] = None
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0

        # 初始化功能模块
        self.sales = SalesModule(self.gateway_url)
        self.purchase = PurchaseModule(self.gateway_url)
        self.stock = StockModule(self.gateway_url)
        self.customer = CustomerModule(self.gateway_url)
        self.vendor = VendorModule(self.gateway_url)
        self.production = ProductionModule(self.gateway_url)
        self.voucher = VoucherModule(self.gateway_url)
        self.todo = TodoModule(self.gateway_url)
        self.product = ProductModule(self.gateway_url)
        self.org = OrgModule(self.gateway_url)
        self.crm = CrmModule(self.gateway_url)

        logger.info(f"YonSuiteClient 初始化完成,租户:{self.tenant_id}")

    @property
    def cache(self) -> TokenCache:
        """获取 Token 缓存实例"""
        if self._cache is None:
            self._cache = get_cache(use_file_cache=self.use_cache)
        return self._cache

    def _http_get(self, url: str, params: Optional[Dict] = None) -> Dict:
        """HTTP GET 请求(兼容旧接口)"""
        import urllib.request
        import urllib.error
        import json

        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}&{query}" if '?' in url else f"{url}?{query}"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    def _http_post_raw(self, url: str, json_data: Dict) -> Dict:
        """HTTP POST 请求(兼容旧接口)"""
        import urllib.request
        import urllib.error
        import json

        data = json.dumps(json_data, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            method='POST',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    def get_data_center_domain(self, tenant_id: str) -> str:
        """
        获取租户所在数据中心域名

        Args:
            tenant_id: 租户 ID

        Returns:
            Token URL
        """
        url = f"https://apigateway.yonyoucloud.com/open-auth/dataCenter/getGatewayAddress?tenantId={tenant_id}"
        result = self._http_get(url)

        if result.get('code') == '00000':
            return result['data']['tokenUrl']
        else:
            raise YonSuiteAuthError(f"获取数据中心域名失败:{result.get('message')}")

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取 access_token(带缓存)

        Args:
            force_refresh: 强制刷新 Token

        Returns:
            access_token

        Raises:
            YonSuiteAuthError: 认证失败时抛出
        """
        # 检查内存缓存
        if not force_refresh and self._access_token and time.time() < self._token_expire_time:
            logger.debug("使用内存中的 Token 缓存")
            return self._access_token

        # 检查持久化缓存
        if self.use_cache and not force_refresh:
            cached_token = self.cache.get(self.tenant_id)
            if cached_token:
                logger.debug("使用持久化缓存的 Token")
                self._access_token = cached_token
                # 设置一个较短的过期时间,下次调用时会重新检查
                self._token_expire_time = time.time() + 300
                return self._access_token

        # 获取租户数据中心域名
        try:
            token_url = self.get_data_center_domain(self.tenant_id)
        except Exception as e:
            logger.warning(f"获取数据中心域名失败,使用默认 URL: {e}")
            token_url = self.default_token_url

        # 生成签名
        import urllib.parse
        timestamp = int(time.time() * 1000)
        sign_str = f"appKey{self.app_key}timestamp{timestamp}"

        signature_bytes = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest()

        signature_base64 = base64.b64encode(signature_bytes).decode('utf-8')
        signature = urllib.parse.quote(signature_base64, safe='')

        # 获取 Token
        url = f"{token_url}/open-auth/selfAppAuth/getAccessToken?appKey={self.app_key}&timestamp={timestamp}&signature={signature}"

        import urllib.request
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req) as response:
            result = __import__('json').loads(response.read().decode('utf-8'))

        if result.get('code') == '00000':
            data = result['data']
            self._access_token = data['access_token']
            # 设置过期时间(提前 5 分钟过期)
            self._token_expire_time = time.time() + data['expire'] - 300

            # 保存到缓存
            if self.use_cache:
                self.cache.set(self.tenant_id, self._access_token, data['expire'])

            logger.info(f"Token 获取成功,过期时间:{data['expire']}秒")
            return self._access_token
        else:
            raise YonSuiteAuthError(f"获取 token 失败:{result.get('message')}")

    # ============== 销售订单 ==============

    def query_sale_orders(self, page_index: int = 1, page_size: int = 500, isSum: bool = False,
                          date_from: str = None, date_to: str = None) -> Dict:
        """
        查询销售订单列表

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500
            isSum: True=按订单汇总(一订单一行), False=按商品明细分列(默认)
            date_from: 起始日期，格式 YYYY-MM-DD，不传则不过滤
            date_to: 截止日期，格式 YYYY-MM-DD，不传则不过滤

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.sales.query_orders(token, page_index, page_size, isSum, date_from, date_to)

    def get_order_detail(self, order_id: str) -> Dict:
        """
        查询销售订单详情

        Args:
            order_id: 订单 ID

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.sales.get_order_detail(token, order_id)

    # ============== 采购订单 ==============

    def query_purchase_orders(self, page_index: int = 1, page_size: int = 500) -> Dict:
        """
        查询采购订单列表

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.purchase.query_orders(token, page_index, page_size)

    def get_purchase_order_detail(self, order_id: str) -> Dict:
        """
        查询采购订单详情(完整信息)

        ⭐ 新增接口:返回采购订单的完整信息,包括明细行、付款计划、付款执行等

        Args:
            order_id: 采购订单 ID(必填)

        Returns:
            API 响应结果,包含完整采购订单信息
        """
        token = self.get_access_token()
        return self.purchase.get_order_detail(token, order_id)

    # ============== 库存查询 ==============

    def query_current_stock(self, page_index: int = 1, page_size: int = 500) -> Dict:
        """
        查询库存现存量

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.stock.query_current_stock(token, page_index, page_size)

    # ============== 物料档案 ==============

    def query_products(self,
                      product_code: str = "",
                      product_name: str = "",
                      page_index: int = 1,
                      page_size: int = 10) -> Dict:
        """
        分页查询物料档案

        API: POST /yonbip/digitalModel/product/queryByPage

        Args:
            product_code: 物料编码(可选,精确匹配)
            product_name: 物料名称(可选,模糊匹配)
            page_index: 页码(默认1)
            page_size: 每页条数(默认10)

        Returns:
            API 响应结果,含 recordList、recordCount、pageCount 等
        """
        token = self.get_access_token()
        return self.product.query_products(
            token, product_code, product_name, page_index, page_size
        )

    # ============== 组织档案 ==============

    def get_org_detail(self, org_id: str) -> Dict:
        """
        查询业务单元(组织)详情

        API: GET /yonbip/digitalModel/orgunit/detail

        Args:
            org_id: 组织 ID(必填)

        Returns:
            API 响应结果,包含组织完整信息
        """
        token = self.get_access_token()
        return self.org.get_org_detail(token, org_id)

    def query_org_units(
        self,
        func_type_code: str = "orgunit",
        org_dept: str = "",
        parent_id: str = "",
        parent_code: str = "",
        name: str = "",
        dr: str = "0",
        enable: str = "",
        pubts: str = "",
        source_type: str = "1",
        external_org: str = "0",
        ids: Optional[list] = None,
        codes: Optional[list] = None,
        objids: Optional[list] = None,
        page_index: int = 1,
        page_size: int = 10,
    ) -> Dict:
        """
        批量查询业务单元/部门(V2)

        API: POST /yonbip/digitalModel/OrgUnitSync/orgUnitDataSyncByDTO

        Args:
            func_type_code: 职能类型,默认 orgunit
                - orgunit: 组织单元
                - adminorg: 人力资源组织
                - factoryorg: 工厂组织
                - inventoryorg: 库存组织
                - salesorg: 销售组织
                - assetsorg: 资产组织
                - purchaseorg: 采购组织
                - financeorg: 会计主体
                - taxpayerorg: 纳税主体
            org_dept: 查询范围,org-业务单元,dept-部门,不填查全部
            parent_id: 上级组织 ID
            parent_code: 上级组织编码
            name: 组织名称(模糊匹配)
            dr: 删除标识,0-未删除,1-已删除
            enable: 启用状态,0-未启用,1-启用,2-停用
            pubts: 时间戳,格式 YYYY-MM-DD HH:MM:SS
            source_type: 数据来源,默认1
            external_org: 外部组织,默认0
            ids: 组织 ID 列表
            codes: 组织编码列表
            objids: 外部系统主键列表
            page_index: 页码,默认1
            page_size: 每页行数,默认10

        Returns:
            分页结果,含 recordList(组织列表)、pageIndex、pageSize、recordCount、pageCount
        """
        token = self.get_access_token()
        return self.org.query_org_units(
            token,
            funcTypeCode=func_type_code,
            orgDept=org_dept,
            parentId=parent_id,
            parentCode=parent_code,
            name=name,
            dr=dr,
            enable=enable,
            pubts=pubts,
            sourceType=source_type,
            externalOrg=external_org,
            ids=ids,
            codes=codes,
            objids=objids,
            pageIndex=page_index,
            pageSize=page_size,
        )

    def format_org_unit_info(self, org: Dict) -> str:
        """
        格式化单个组织信息为可读文本

        Args:
            org: 组织数据字典

        Returns:
            格式化的文本
        """
        name = org.get('name', '-')
        if isinstance(name, dict):
            name = name.get('zh_CN', '-')

        shortname = org.get('shortname', '-')
        if isinstance(shortname, dict):
            shortname = shortname.get('zh_CN', '-')

        enable_map = {0: "未启用", 1: "启用", 2: "停用"}
        enable = enable_map.get(org.get('enable', -1), '未知')

        org_type_map = {1: '业务单元', 2: '部门'}
        org_type = org_type_map.get(org.get('orgtype', 0), '未知')

        dr_map = {0: '未删除', 1: '已删除'}
        dr = dr_map.get(org.get('dr', 0), '未知')

        lines = [
            f"🏢 {name} ({org.get('code', '?')})",
            f"   组织ID: {org.get('id', '?')}",
            f"   简称: {shortname}",
            f"   类型: {org_type}",
            f"   状态: {enable}",
            f"   删除: {dr}",
            f"   上级ID: {org.get('parentid', '-')}",
            f"   层级: {org.get('level', '-')}",
            f"   创建时间: {org.get('creationtime', '-')}",
        ]
        return "\n".join(lines)

    # ============== 客户档案 ==============

    def query_customers(self, page_index: int = 1, page_size: int = 500) -> Dict:
        """
        查询客户档案列表

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.customer.query_customers(token, page_index, page_size)

    def query_customer_detail(self,
                              customer_id: Optional[str] = None,
                              customer_code: Optional[str] = None,
                              belong_org_id: Optional[str] = None,
                              belong_org_code: Optional[str] = None) -> Dict:
        """
        查询单个客户档案详情(完整信息)

        ⭐ 新增接口:返回客户的完整档案信息,包括地址、联系人、银行、发票等

        Args:
            customer_id: 客户 ID(与 customer_code 至少传一个)
            customer_code: 客户编码(与 customer_id 至少传一个)
            belong_org_id: 使用组织 ID(可选)
            belong_org_code: 使用组织编码(可选)

        Returns:
            API 响应结果,包含完整客户档案信息
        """
        token = self.get_access_token()
        return self.customer.query_customer_detail_single(
            token, customer_id, customer_code, belong_org_id, belong_org_code
        )

    def query_customer_details_batch(self,
                                     customer_list: List[Dict[str, Any]],
                                     belong_org_id: Optional[str] = None,
                                     belong_org_code: Optional[str] = None) -> Dict:
        """
        批量查询客户档案详情

        ⭐ 新增接口:支持一次查询多个客户的完整档案信息

        Args:
            customer_list: 客户查询条件列表
                示例:[{"id": "123"}, {"code": "CUST001"}, {"id": "456", "belongOrgId": "666666"}]
            belong_org_id: 默认使用组织 ID(可选)
            belong_org_code: 默认使用组织编码(可选)

        Returns:
            API 响应结果,包含多个客户的完整档案信息
        """
        token = self.get_access_token()
        return self.customer.query_customer_details_batch(
            token, customer_list, belong_org_id, belong_org_code
        )

    # ============== 供应商档案 ==============

    def query_vendors(self, page_index: int = 1, page_size: int = 500) -> Dict:
        """
        查询供应商档案列表

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.vendor.query_vendors(token, page_index, page_size)

    def get_vendor_detail(self,
                         vendor_id: str,
                         org_id: Optional[str] = None) -> Dict:
        """
        查询供应商档案详情

        Args:
            vendor_id: 供应商档案 ID(必填)
            org_id: 组织 ID(可选)

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.vendor.get_vendor_detail(token, vendor_id, org_id)

    # ============== 生产订单 ==============

    def query_production_orders(self, page_index: int = 1, page_size: int = 500) -> Dict:
        """
        查询生产订单列表

        Args:
            page_index: 页码,默认值:1
            page_size: 每页行数,默认值:500

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.production.query_orders(token, page_index, page_size)

    def get_production_order_detail(self, order_id: str) -> Dict:
        """
        查询生产订单详情

        Args:
            order_id: 生产订单 ID

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.production.get_order_detail(token, order_id)

    def query_production_orders_batch(self, order_ids: list,
                                      show_process: bool = False,
                                      show_material: bool = False,
                                      show_by_product: bool = False) -> Dict:
        """
        批量查询生产订单详情（通过 batchGet 接口）

        API: POST /yonbip/mfg/productionorder/batchGet

        Args:
            order_ids: 生产订单 ID 列表（最多 50 个）
            show_process: 是否展示工序
            show_material: 是否展示材料
            show_by_product: 是否展示联副产品

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.production.query_production_orders_batch(
            token, order_ids,
            show_process=show_process,
            show_material=show_material,
            show_by_product=show_by_product
        )

    # ============== 账簿查询 ==============

    def query_accbooks(self) -> List[Dict]:
        """查询账簿列表（优先本地缓存）"""
        token = self.get_access_token()
        return self.voucher.get_cached_accbooks(token)

    def query_accbooks_refresh(self) -> List[Dict]:
        """强制刷新账簿缓存"""
        token = self.get_access_token()
        return self.voucher.query_accbooks(token)


# ============== 凭证查询 ==============

    def query_vouchers(self, page_size: int = 20, **kwargs) -> Dict:
        """查询凭证列表（凭证管理模块）"""
        token = self.get_access_token()
        return self.voucher.query_vouchers(token, page_size=page_size, **kwargs)

    def query_vouchers_parsed(self, page_size: int = 500, **kwargs) -> Dict:
        """查询凭证列表（解析后格式）"""
        token = self.get_access_token()
        return self.voucher.query_vouchers_parsed(token, page_size=page_size, **kwargs)

# ============== 用户待办 ==============

    def query_user_todos(self, page_no: int = 1, page_size: int = 10) -> Dict:
        """
        查询用户待办事项列表

        Args:
            page_no: 页码,默认值:1
            page_size: 每页行数,默认值:10

        Returns:
            API 响应结果
        """
        token = self.get_access_token()
        return self.todo.query_todos(token, page_no, page_size)

    def query_user_todos_parsed(self, page_no: int = 1, page_size: int = 10) -> List:
        """
        查询用户待办数据(解析为模型对象)

        Args:
            page_no: 页码,默认值:1
            page_size: 每页行数,默认值:10

        Returns:
            TodoItem 对象列表
        """
        from modules.todo import TodoItem
        token = self.get_access_token()
        return self.todo.query_todos_parsed(token, page_no, page_size)

    def format_todo_info(self, todo_items: List) -> str:
        """
        格式化待办信息为可读文本

        Args:
            todo_items: 待办事项列表

        Returns:
            格式化的文本
        """

    # ============== 商机查询 ==============

    def query_opportunities(self, page_index: int = 1, page_size: int = 500,
                            code: str = None, name: str = None,
                            oppt_state: str = None, win_lose_state: str = None,
                            is_sum: bool = True, date_from: str = None,
                            date_to: str = None) -> Dict:
        """
        查询商机列表

        Args:
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
        token = self.get_access_token()
        return self.crm.query_opportunities(
            token, page_index, page_size,
            code=code, name=name,
            oppt_state=oppt_state, win_lose_state=win_lose_state,
            is_sum=is_sum, date_from=date_from, date_to=date_to
        )

    def query_opportunities_parsed(self, page_index: int = 1, page_size: int = 500,
                                   code: str = None, name: str = None,
                                   oppt_state: str = None, win_lose_state: str = None,
                                   is_sum: bool = True, date_from: str = None,
                                   date_to: str = None) -> List[Opportunity]:
        """
        查询商机列表（解析为 Opportunity 对象）

        Args:
            page_index: 页码，默认值：1
            page_size: 每页行数，默认值：500
            code: 商机编码（可选）
            name: 商机名称（可选）
            oppt_state: 商机状态（可选）
            win_lose_state: 赢丢单状态（可选）
            is_sum: True=返回表头+明细，False=仅表头
            date_from: 起始日期（可选）
            date_to: 截止日期（可选）

        Returns:
            Opportunity 对象列表
        """
        token = self.get_access_token()
        result = self.crm.query_opportunities(
            token, page_index, page_size,
            code=code, name=name,
            oppt_state=oppt_state, win_lose_state=win_lose_state,
            is_sum=is_sum, date_from=date_from, date_to=date_to
        )
        return self.crm.parse_opportunities(result)

    # ============== 格式化方法(兼容旧接口) ==============

    def format_order_info(self, order: Dict) -> str:
        """格式化订单信息为可读文本"""
        return SaleOrder.from_api(order).format()

    def format_stock_info(self, stock_list: List[Dict]) -> str:
        """格式化库存信息为可读文本"""
        items = [StockItem.from_api(item) for item in stock_list]
        return self.stock.format_stock_info(items)

    def format_production_order_info(self, order: Dict) -> str:
        """格式化生产订单信息为可读文本"""
        return ProductionOrder.from_api(order).format()

    # ============== 业务场景快捷方法(已删除,只保留官方 API) ==============


# ============== 命令行入口 ==============

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='yonsuite_search - 用友 YonSuite API 查询客户端 v2.0')
    parser.add_argument('--action', type=str, required=True,
                       choices=['token', 'query-orders', 'order-detail',
                               'query-purchase-orders', 'purchase-order-detail',
                               'query-stock',
                               'query-customers', 'customer-detail', 'customer-details-batch',
                               'vendor-detail', 'query-vendors',
                               'query-production-orders', 'production-order-detail',
                               'query-todos', 'query-vouchers', 'query-accbooks'],
                       help='操作类型')
    parser.add_argument('--accbook-code', type=str, help='账簿编码(如1001、1000)')
    parser.add_argument('--customer', type=str, help='客户名称')
    parser.add_argument('--customer-id', type=str, help='客户 ID(查询客户详情用)')
    parser.add_argument('--customer-code', type=str, help='客户编码(查询客户详情用)')
    parser.add_argument('--order-code', type=str, help='订单编号')
    parser.add_argument('--order-id', type=str, help='订单 ID')
    parser.add_argument('--purchase-order-id', type=str, help='采购订单 ID(查询采购订单详情用)')
    parser.add_argument('--vendor-id', type=str, help='供应商 ID')
    parser.add_argument('--product-code', type=str, help='物料编码')
    parser.add_argument('--product-name', type=str, help='物料名称')
    parser.add_argument('--start-date', type=str, help='开始日期(YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期(YYYY-MM-DD)')
    parser.add_argument('--vouchdate-start', type=str, help='单据日期开始(YYYY-MM-DD,销售订单用)')
    parser.add_argument('--vouchdate-end', type=str, help='单据日期结束(YYYY-MM-DD,销售订单用)')
    parser.add_argument('--is-sum', action='store_true', default=True, help='是否汇总(True=表头汇总,默认)')
    parser.add_argument('--no-sum', action='store_true', help='是否汇总(False=明细行)')
    parser.add_argument('--status', type=str, help='订单状态')
    parser.add_argument('--page-size', type=int, default=500, help='每页数量(默认500)')
    parser.add_argument('--page-no', type=int, default=1, help='页码(待办查询用)')
    parser.add_argument('--todo-status', type=str, default='todo', help='待办状态:todo=待办,done=已办')
    parser.add_argument('--voucher-date-start', type=str, help='凭证日期区间左端点(YYYY-MM-DD)')
    parser.add_argument('--voucher-date-end', type=str, help='凭证日期区间右端点(YYYY-MM-DD)')
    parser.add_argument('--accountant-year', type=str, help='会计年度(如2026)')
    parser.add_argument('--accountant-period', type=str, help='会计期间(如01)')
    parser.add_argument('--period-start', type=str, help='起始期间(yyyy-MM，默认当前月)')
    parser.add_argument('--period-end', type=str, help='结束期间(yyyy-MM，默认当前月)')
    parser.add_argument('--document-type-name', type=str, help='凭证字(如记)')
    parser.add_argument('--page-index', type=int, default=1, help='页码(凭证查询用)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        client = YonSuiteClient()

        if args.action == 'token':
            token = client.get_access_token(force_refresh=True)
            print(f"✅ Token 获取成功:{token[:20]}...")

        elif args.action == 'query-orders':
            result = client.query_sale_orders(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-purchase-orders':
            result = client.query_purchase_orders(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'purchase-order-detail':
            if not args.purchase_order_id:
                print("❌ 请提供采购订单 ID")
                return
            result = client.get_purchase_order_detail(args.purchase_order_id)
            # 使用格式化输出
            detail = result.get('data', {})
            if detail:
                formatted = client.purchase.format_order_detail(detail)
                print(formatted)
            else:
                print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'order-detail':
            if not args.order_id:
                print("❌ 请提供订单 ID")
                return
            result = client.get_order_detail(args.order_id)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-stock':
            result = client.query_current_stock(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-customers':
            result = client.query_customers(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'customer-detail':
            if not args.customer_id and not args.customer_code:
                print("❌ 请提供客户 ID 或客户编码")
                return
            result = client.query_customer_detail(
                customer_id=args.customer_id,
                customer_code=args.customer_code
            )
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'customer-details-batch':
            print("❌ 批量查询请使用 Python 代码调用,示例:")
            print("""
from ys_client import YonSuiteClient
client = YonSuiteClient()
result = client.query_customer_details_batch([
    {"id": "1706047321704235000"},
    {"code": "CUST001"}
])
print(result)
            """)
            return

        elif args.action == 'vendor-detail':
            if not args.vendor_id:
                print("❌ 请提供供应商 ID")
                return
            result = client.get_vendor_detail(args.vendor_id)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-vendors':
            result = client.query_vendors(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-production-orders':
            result = client.query_production_orders(page_size=args.page_size)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'production-order-detail':
            if not args.order_id:
                print("❌ 请提供生产订单 ID")
                return
            result = client.get_production_order_detail(args.order_id)
            print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-todos':
            result = client.query_user_todos(page_no=args.page_no, page_size=args.page_size)
            # 格式化输出
            data = result.get('data', [])
            if data:
                from modules.todo import TodoItem
                todo_items = [TodoItem.from_api(item) for item in data]
                formatted = client.format_todo_info(todo_items)
                print(formatted)
            else:
                print("📋 暂无待办事项")
                print(__import__('json').dumps(result, indent=2, ensure_ascii=False))

        elif args.action == 'query-vouchers':
            if not args.accbook_code:
                print("❌ 请指定账簿编码（--accbook-code）")
                print("   可用 python3 ys_client.py --action query-accbooks 查看所有账簿")
                return
            parsed = client.query_vouchers_parsed(
                page_size=args.page_size or 20,
                page_index=args.page_index or 1,
                voucher_date_start=args.voucher_date_start,
                voucher_date_end=args.voucher_date_end,
                accountant_year=args.accountant_year,
                accountant_period=args.accountant_period,
                period_start=args.period_start,
                period_end=args.period_end,
                document_type_name=args.document_type_name,
                accbook_code=args.accbook_code,
            )
            records = parsed.get('records', [])
            if records:
                formatted = client.voucher.format_vouchers_list(records)
                print(formatted)
                print(f"\n总记录数: {parsed.get('recordCount', 0)}")
            else:
                print("🧾 暂无凭证记录")
        elif args.action == 'query-accbooks':
            accbooks = client.query_accbooks()
            print(f"📋 账簿列表（共 {len(accbooks)} 个）：")
            for a in accbooks:
                print(f"   {a['code']} - {a['name']}")

    except Exception as e:
        logger.error(f"执行失败:{e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"❌ 错误:{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
