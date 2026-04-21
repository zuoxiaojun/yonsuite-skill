#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite 数据模型模块

使用 dataclass 定义结构化数据模型，提供类型安全和更好的 IDE 支持。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== 基础模型 ==============

@dataclass
class BaseModel:
    """基础模型类，提供通用的转换方法"""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建模型实例"""
        # 获取 dataclass 的字段
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        # 只提取匹配的字段
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__.values()}


# ============== 认证相关 ==============

@dataclass
class TokenInfo(BaseModel):
    """Token 信息"""
    access_token: str
    expire_in: int  # 秒
    expire_time: float = field(default=0)  # 过期时间戳
    tenant_id: str = ''
    
    def is_valid(self, buffer: int = 300) -> bool:
        """检查 Token 是否有效（考虑缓冲时间）"""
        return self.expire_time > (time.time() + buffer) if self.expire_time else False


# ============== 销售订单相关 ==============

@dataclass
class SaleOrder(BaseModel):
    """销售订单 - 按28字段格式展示"""
    # 单据信息（1-9）
    id: str = ''                    # 单据ID
    code: str = ''                  # 单据编号
    vouchdate: str = ''             # 单据日期
    approvetime: str = ''           # 审批日期
    sales_org_id: str = ''          # 销售组织ID
    sales_org_name: str = ''        # 销售组织
    transaction_type: str = ''      # 交易类型
    transaction_type_id: str = ''   # 交易类型ID
    customer_id: str = ''           # 客户ID
    customer_name: str = ''         # 客户
    dept_id: str = ''               # 销售部门ID
    dept_name: str = ''             # 销售部门
    salesman_id: str = ''           # 销售业务员ID
    salesman_name: str = ''         # 销售业务员
    status: str = ''                # 订单状态
    bill_status: str = ''           # 单据状态
    # 商品明细（10-12）
    rowno: int = 0                  # 行号
    material_id: str = ''           # 商品ID
    material_code: str = ''        # 商品编码
    material_name: str = ''        # 商品名称
    # 数量计量（13-16）
    salenum: float = 0.0            # 销售数量
    saleunit: str = ''              # 销售单位
    qty: float = 0.0               # 数量（主计量）
    unit: str = ''                  # 主计量
    # 财务信息（17-21）
    currency_id: str = ''          # 币种ID
    currency_name: str = ''         # 币种
    price: float = 0.0             # 含税成交价
    taxrate: float = 0.0           # 税率
    oriSum: float = 0.0             # 含税金额
    tax: float = 0.0               # 表体税额
    # 执行进度（22-28）
    plan_send_date: str = ''        # 计划发货日期
    stock_org_id: str = ''          # 库存组织ID
    stock_org_name: str = ''        # 库存组织
    warehouse_id: str = ''          # 发货仓库ID
    warehouse_name: str = ''        # 发货仓库
    total_sendnum: float = 0.0     # 累计已发货数量
    total_outamount: float = 0.0   # 累计出库金额
    total_invoicenum: float = 0.0  # 累计开票数量
    total_invoicesum: float = 0.0  # 累计开票含税金额
    # 附加信息
    memo: str = ''                  # 备注
    created_time: str = ''
    modified_time: str = ''
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'SaleOrder':
        """从 API 响应创建实例"""
        def safe_str(v, default=''):
            return str(v) if v else default
        
        def safe_float(v, default=0.0):
            try:
                return float(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(v, default=0):
            try:
                return int(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def fmt_date(v):
            """格式化日期"""
            if not v:
                return ''
            v = str(v)
            if ' ' in v:
                return v.split(' ')[0]
            return v
        
        def get_detail_price(key, default=None):
            """从 orderDetailPrices 获取嵌套数据"""
            detail = data.get('orderDetailPrices', {})
            if isinstance(detail, dict):
                return detail.get(key, default)
            elif isinstance(detail, str):
                try:
                    import json
                    detail = json.loads(detail)
                    return detail.get(key, default)
                except:
                    return default
            return default
        
        # YonSuite recordList 数据结构（明细数据在根级别扁平化）
        tax = get_detail_price('natTax') or get_detail_price('oriTax') or 0
        tax = safe_float(tax)
        
        return cls(
            id=safe_str(data.get('id')),
            code=safe_str(data.get('code')),
            vouchdate=fmt_date(data.get('vouchdate')),
            approvetime=fmt_date(data.get('auditTime') or data.get('pubts')),
            sales_org_id=safe_str(data.get('salesOrgId')),
            sales_org_name=safe_str(data.get('salesOrgId_name')),
            transaction_type=safe_str(data.get('transactionTypeId_name', data.get('bizFlow_name'))),
            transaction_type_id=safe_str(data.get('transactionTypeId')),
            customer_id=safe_str(data.get('agentId')),
            customer_name=safe_str(data.get('agentId_name')),
            dept_id=safe_str(data.get('saleDepartmentId')),
            dept_name=safe_str(data.get('saleDepartmentId_name')),
            salesman_id=safe_str(data.get('salesmanId')),
            salesman_name=safe_str(data.get('salesmanId_name')),
            status=safe_str(data.get('nextStatusName') or data.get('statusCode')),
            bill_status=safe_str(data.get('billStatus')),
            rowno=safe_int(data.get('lineno') or data.get('rowno') or 1),
            material_id=safe_str(data.get('productId')),
            material_code=safe_str(data.get('productCode') or data.get('skuCode')),
            material_name=safe_str(data.get('productName') or data.get('skuName')),
            salenum=safe_float(data.get('priceQty') or data.get('subQty') or data.get('salenum')),
            saleunit=safe_str(data.get('productUnitName') or data.get('purUOM_Code') or data.get('qtyName')),
            qty=safe_float(data.get('qty')),
            unit=safe_str(data.get('unit_name') or data.get('qtyName')),
            currency_id=safe_str(data.get('currency')),
            currency_name=safe_str(data.get('originalName', '人民币')),
            price=safe_float(data.get('oriTaxUnitPrice') or data.get('taxprice') or data.get('salePrice')),
            taxrate=safe_float(data.get('taxRate', 0) / 100 if data.get('taxRate') else 0),
            oriSum=safe_float(data.get('oriSum') or data.get('payMoney')),
            tax=tax,
            plan_send_date=fmt_date(data.get('sendDate')),
            stock_org_id=safe_str(data.get('stockOrgId')),
            stock_org_name=safe_str(data.get('stockOrgId_name')),
            warehouse_id=safe_str(data.get('warehouseId')),
            warehouse_name=safe_str(data.get('warehouseId_name')),
            total_sendnum=safe_float(data.get('sendQty')),
            total_outamount=safe_float(data.get('totalOutStockOriMoney')),
            total_invoicenum=safe_float(data.get('invoiceQty')),
            total_invoicesum=safe_float(data.get('invoiceOriSum')),
            memo=safe_str(data.get('memo')),
            created_time=safe_str(data.get('createTime')),
            modified_time=safe_str(data.get('modifyTime'))
        )
    
    def format(self) -> str:
        """格式化为可读文本 - 28字段格式"""
        def fmt(v):
            if isinstance(v, float):
                return f"{v:,.2f}"
            return str(v) if v else "-"
        
        lines = [
            f"{'单据编号':<14}：{self.code}",
            f"{'单据日期':<14}：{self.vouchdate}",
            f"{'审批日期':<14}：{self.approvetime or '-'}",
            f"{'销售组织':<14}：{self.sales_org_name}",
            f"{'交易类型':<14}：{self.transaction_type}",
            f"{'客户':<14}：{self.customer_name}",
            f"{'销售部门':<14}：{self.dept_name}",
            f"{'销售业务员':<14}：{self.salesman_name}",
            f"{'订单状态':<14}：{self.status}",
            f"{'行号':<14}：{self.rowno}",
            f"{'商品编码':<14}：{self.material_code}",
            f"{'商品名称':<14}：{self.material_name}",
            f"{'销售数量':<14}：{fmt(self.salenum)} {self.saleunit}",
            f"{'销售单位':<14}：{self.saleunit}",
            f"{'数量':<14}：{fmt(self.qty)} {self.unit}",
            f"{'主计量':<14}：{self.unit}",
            f"{'币种':<14}：{self.currency_name}",
            f"{'含税成交价':<14}：{fmt(self.price)}",
            f"{'含税金额':<14}：{fmt(self.oriSum)}",
            f"{'税率':<14}：{fmt(self.taxrate * 100) if self.taxrate else '-'}%",
            f"{'表体税额':<14}：{fmt(self.tax)}",
            f"{'计划发货日期':<14}：{self.plan_send_date}",
            f"{'库存组织':<14}：{self.stock_org_name}",
            f"{'发货仓库':<14}：{self.warehouse_name}",
            f"{'累计已发货数量':<14}：{fmt(self.total_sendnum)}",
            f"{'累计出库金额':<14}：{fmt(self.total_outamount)}",
            f"{'累计开票数量':<14}：{fmt(self.total_invoicenum)}",
            f"{'累计开票含税金额':<14}：{fmt(self.total_invoicesum)}",
        ]
        return "\n".join(lines)
    
    def to_table_row(self) -> Dict[str, Any]:
        """转换为表格行数据 - 28字段"""
        return {
            '单据编号': self.code,
            '单据日期': self.vouchdate,
            '审批日期': self.approvetime or '-',
            '销售组织': self.sales_org_name,
            '交易类型': self.transaction_type,
            '客户': self.customer_name,
            '销售部门': self.dept_name,
            '销售业务员': self.salesman_name,
            '订单状态': self.status,
            '行号': self.rowno,
            '商品编码': self.material_code,
            '商品名称': self.material_name,
            '销售数量': f"{self.salenum:,.2f}" if self.salenum else '-',
            '销售单位': self.saleunit,
            '数量': f"{self.qty:,.2f}" if self.qty else '-',
            '主计量': self.unit,
            '币种': self.currency_name,
            '含税成交价': f"{self.price:,.2f}" if self.price else '-',
            '含税金额': f"{self.oriSum:,.2f}" if self.oriSum else '-',
            '税率': f"{self.taxrate * 100:.1f}%" if self.taxrate else '-',
            '表体税额': f"{self.tax:,.2f}" if self.tax else '-',
            '计划发货日期': self.plan_send_date,
            '库存组织': self.stock_org_name,
            '发货仓库': self.warehouse_name,
            '累计已发货数量': f"{self.total_sendnum:,.2f}" if self.total_sendnum else '-',
            '累计出库金额': f"{self.total_outamount:,.2f}" if self.total_outamount else '-',
            '累计开票数量': f"{self.total_invoicenum:,.2f}" if self.total_invoicenum else '-',
            '累计开票含税金额': f"{self.total_invoicesum:,.2f}" if self.total_invoicesum else '-',
        }


@dataclass
class SaleOrderDetail(SaleOrder):
    """销售订单详情（包含明细行）"""
    items: List[Dict[str, Any]] = field(default_factory=list)
    status_tracking: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'SaleOrderDetail':
        """从 API 响应创建实例"""
        instance = super().from_api(data)
        instance.items = data.get('entries', [])
        instance.status_tracking = data.get('statusTracking', [])
        return instance


# ============== 采购订单相关 ==============

@dataclass
class PurchaseOrder(BaseModel):
    """采购订单 - 按25字段格式展示"""
    # 单据信息（1-10）
    id: str = ''                      # 订单ID
    code: str = ''                    # 订单编号
    purchase_org_id: str = ''         # 采购组织ID
    purchase_org_name: str = ''       # 采购组织
    transaction_type: str = ''        # 交易类型
    transaction_type_id: str = ''    # 交易类型ID
    vendor_id: str = ''               # 供货供应商ID
    vendor_name: str = ''             # 供货供应商
    invoice_vendor_id: str = ''      # 开票供应商ID
    invoice_vendor_name: str = ''    # 开票供应商
    vouchdate: str = ''               # 单据日期
    creator_name: str = ''            # 创建人
    creator_id: str = ''              # 创建人ID
    dept_id: str = ''                 # 采购部门ID
    dept_name: str = ''               # 采购部门
    purchaser_id: str = ''            # 采购员ID
    purchaser_name: str = ''          # 采购员
    bill_status: str = ''             # 单据状态
    status: str = ''                  # 订单状态
    # 商品明细（11-13）
    rowno: int = 0                    # 行号
    material_id: str = ''             # 物料ID
    material_code: str = ''          # 物料编码
    material_name: str = ''          # 物料名称
    # 数量金额（14-19）
    purchase_qty: float = 0.0        # 采购数量
    qty: float = 0.0                # 数量（主计量）
    unit: str = ''                    # 单位
    unit_name: str = ''               # 单位名称
    price: float = 0.0              # 含税单价
    oriSum: float = 0.0             # 含税金额
    taxrate: float = 0.0             # 税率
    tax: float = 0.0                 # 税额
    # 执行进度（20-25）
    plan_arrive_date: str = ''        # 计划到货日期
    receive_org_id: str = ''          # 收货组织ID
    receive_org_name: str = ''       # 收货组织
    invoice_org_id: str = ''         # 收票组织ID
    invoice_org_name: str = ''       # 收票组织
    total_arrivenum: float = 0.0     # 累计到货数量
    total_stockinnum: float = 0.0   # 累计入库数量
    total_invoicenum: float = 0.0    # 累计开票数量
    # 附加信息
    memo: str = ''                    # 备注
    created_time: str = ''
    modified_time: str = ''
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'PurchaseOrder':
        """从 API 响应创建实例"""
        def safe_str(v, default=''):
            return str(v) if v else default
        
        def safe_float(v, default=0.0):
            try:
                return float(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(v, default=0):
            try:
                return int(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def fmt_date(v):
            """格式化日期"""
            if not v:
                return ''
            v = str(v)
            if ' ' in v:
                return v.split(' ')[0]
            return v
        
        def get_purchase_field(prefix, key, default=None):
            """从 purchaseOrders_* 嵌套字段获取数据"""
            full_key = f'purchaseOrders_{key}'
            return data.get(full_key, default)
        
        # YonSuite recordList 数据结构（采购订单明细扁平化）
        return cls(
            id=safe_str(data.get('id')),
            code=safe_str(data.get('code')),
            purchase_org_id=safe_str(data.get('org') or data.get('purchaseOrgId')),
            purchase_org_name=safe_str(data.get('org_name') or data.get('purchaseOrgId_name')),
            transaction_type=safe_str(data.get('bustype_name')),
            transaction_type_id=safe_str(data.get('bustype')),
            vendor_id=safe_str(data.get('vendor')),
            vendor_name=safe_str(data.get('vendor_name')),
            invoice_vendor_id=safe_str(data.get('invoiceVendor')),
            invoice_vendor_name=safe_str(data.get('invoiceVendor_name')),
            vouchdate=fmt_date(data.get('vouchdate')),
            creator_name=safe_str(data.get('submitter_username') or data.get('creator')),
            creator_id=safe_str(data.get('submitter') or data.get('creator')),
            dept_id=safe_str(data.get('deptId')),
            dept_name=safe_str(data.get('deptId_name')),
            purchaser_id=safe_str(data.get('purchaserId')),
            purchaser_name=safe_str(data.get('purchaserId_name')),
            bill_status=safe_str(data.get('status')),
            status=safe_str(data.get('bizstatus')),
            rowno=safe_int(data.get('lineno')),
            material_id=safe_str(data.get('product') or data.get('productsku')),
            material_code=safe_str(data.get('productsku_cCode') or data.get('product_cCode')),
            material_name=safe_str(data.get('productsku_cName') or data.get('product_cName')),
            purchase_qty=safe_float(get_purchase_field('purchaseOrders', 'priceQty') or data.get('priceQty') or data.get('purchaseOrders_priceQty')),
            qty=safe_float(data.get('qty') or data.get('purchaseOrders_subQty')),
            unit=safe_str(data.get('unit')),
            unit_name=safe_str(data.get('unit_name') or data.get('purUOM_Name')),
            price=safe_float(data.get('oriTaxUnitPrice')),
            oriSum=safe_float(data.get('oriSum') or data.get('listOriSum')),
            taxrate=safe_float(data.get('taxRate', 0) / 100 if data.get('taxRate') else 0),
            tax=safe_float(data.get('oriTax') or data.get('listOriTax') or data.get('purchaseOrders_natTax')),
            plan_arrive_date=fmt_date(data.get('planArriveDate')),
            receive_org_id=safe_str(data.get('inOrg') or data.get('receiveOrgId')),
            receive_org_name=safe_str(data.get('inOrg_name') or data.get('receiveOrgId_name')),
            invoice_org_id=safe_str(data.get('inInvoiceOrg')),
            invoice_org_name=safe_str(data.get('inInvoiceOrg_name')),
            total_arrivenum=safe_float(data.get('purchaseOrders_arrivedStatus')),
            total_stockinnum=safe_float(data.get('purchaseOrders_inWHStatus')),
            total_invoicenum=safe_float(data.get('purchaseOrders_invStatus') or data.get('purchaseOrders_invoiceStatus')),
            memo=safe_str(data.get('memo')),
            created_time=safe_str(data.get('createTime')),
            modified_time=safe_str(data.get('modifyTime'))
        )
    
    def format(self) -> str:
        """格式化为可读文本 - 25字段格式"""
        def fmt(v):
            if isinstance(v, float):
                return f"{v:,.2f}"
            return str(v) if v else "-"
        
        lines = [
            f"{'订单编号':<14}：{self.code}",
            f"{'采购组织':<14}：{self.purchase_org_name}",
            f"{'交易类型':<14}：{self.transaction_type}",
            f"{'供货供应商':<14}：{self.vendor_name}",
            f"{'开票供应商':<14}：{self.invoice_vendor_name}",
            f"{'单据日期':<14}：{self.vouchdate}",
            f"{'创建人':<14}：{self.creator_name}",
            f"{'采购部门':<14}：{self.dept_name}",
            f"{'采购员':<14}：{self.purchaser_name}",
            f"{'单据状态':<14}：{self.bill_status or self.status}",
            f"{'行号':<14}：{self.rowno}",
            f"{'物料编码':<14}：{self.material_code}",
            f"{'物料名称':<14}：{self.material_name}",
            f"{'采购数量':<14}：{fmt(self.purchase_qty)} {self.unit_name}",
            f"{'数量':<14}：{fmt(self.qty)} {self.unit_name}",
            f"{'含税单价':<14}：{fmt(self.price)}",
            f"{'含税金额':<14}：{fmt(self.oriSum)}",
            f"{'税率':<14}：{fmt(self.taxrate * 100) if self.taxrate else '-'}%",
            f"{'税额':<14}：{fmt(self.tax)}",
            f"{'计划到货日期':<14}：{self.plan_arrive_date}",
            f"{'收货组织':<14}：{self.receive_org_name}",
            f"{'收票组织':<14}：{self.invoice_org_name}",
            f"{'累计到货数量':<14}：{fmt(self.total_arrivenum)}",
            f"{'累计入库数量':<14}：{fmt(self.total_stockinnum)}",
            f"{'累计开票数量':<14}：{fmt(self.total_invoicenum)}",
        ]
        return "\n".join(lines)
    
    def to_table_row(self) -> Dict[str, Any]:
        """转换为表格行数据 - 25字段"""
        return {
            '订单编号': self.code,
            '采购组织': self.purchase_org_name,
            '交易类型': self.transaction_type,
            '供货供应商': self.vendor_name,
            '开票供应商': self.invoice_vendor_name,
            '单据日期': self.vouchdate,
            '创建人': self.creator_name,
            '采购部门': self.dept_name,
            '采购员': self.purchaser_name,
            '单据状态': self.bill_status or self.status,
            '行号': self.rowno,
            '物料编码': self.material_code,
            '物料名称': self.material_name,
            '采购数量': f"{self.purchase_qty:,.2f}" if self.purchase_qty else '-',
            '数量': f"{self.qty:,.2f}" if self.qty else '-',
            '含税单价': f"{self.price:,.2f}" if self.price else '-',
            '含税金额': f"{self.oriSum:,.2f}" if self.oriSum else '-',
            '税率': f"{self.taxrate * 100:.1f}%" if self.taxrate else '-',
            '税额': f"{self.tax:,.2f}" if self.tax else '-',
            '计划到货日期': self.plan_arrive_date,
            '收货组织': self.receive_org_name,
            '收票组织': self.invoice_org_name,
            '累计到货数量': f"{self.total_arrivenum:,.2f}" if self.total_arrivenum else '-',
            '累计入库数量': f"{self.total_stockinnum:,.2f}" if self.total_stockinnum else '-',
            '累计开票数量': f"{self.total_invoicenum:,.2f}" if self.total_invoicenum else '-',
        }


@dataclass
class Customer(BaseModel):
    """客户档案"""
    id: str = ''
    code: str = ''  # 客户编码
    name: str = ''  # 客户名称
    customer_class: str = ''  # 客户分类
    contact_person: str = ''  # 联系人
    phone: str = ''  # 电话
    email: str = ''  # 邮箱
    address: str = ''  # 地址
    status: str = ''  # 状态
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Customer':
        """从 API 响应创建实例"""
        return cls(
            id=str(data.get('id', '')),
            code=str(data.get('code', '')),
            name=str(data.get('name', '')),
            customer_class=str(data.get('customerClassName', '')),
            contact_person=str(data.get('personOfContact', '')),
            phone=str(data.get('mobilePhone', '') or data.get('telephone', '')),
            email=str(data.get('email', '')),
            address=str(data.get('address', '')),
            status=str(data.get('status', ''))
        )


# ============== 供应商档案相关 ==============

@dataclass
class Vendor(BaseModel):
    """供应商档案"""
    id: str = ''
    code: str = ''  # 供应商编码
    name: str = ''  # 供应商名称
    vendor_class: str = ''  # 供应商分类
    contact_person: str = ''  # 联系人
    phone: str = ''  # 电话
    email: str = ''  # 邮箱
    address: str = ''  # 地址
    bank_name: str = ''  # 开户行
    bank_account: str = ''  # 银行账号
    status: str = ''  # 状态
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Vendor':
        """从 API 响应创建实例"""
        return cls(
            id=str(data.get('id', '')),
            code=str(data.get('code', '')),
            name=str(data.get('name', '')),
            vendor_class=str(data.get('vendorClassName', '')),
            contact_person=str(data.get('personOfContact', '')),
            phone=str(data.get('mobilePhone', '') or data.get('telephone', '')),
            email=str(data.get('email', '')),
            address=str(data.get('address', '')),
            bank_name=str(data.get('bankName', '')),
            bank_account=str(data.get('bankAccount', '')),
            status=str(data.get('status', ''))
        )


@dataclass
class VendorDetail(Vendor):
    """供应商档案详情（包含更多信息）"""
    qualifications: List[Dict[str, Any]] = field(default_factory=list)  # 资质信息
    contacts: List[Dict[str, Any]] = field(default_factory=list)  # 联系信息
    addresses: List[Dict[str, Any]] = field(default_factory=list)  # 地址信息
    bank_accounts: List[Dict[str, Any]] = field(default_factory=list)  # 银行账户
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'VendorDetail':
        """从 API 响应创建实例"""
        instance = super().from_api(data)
        instance.qualifications = data.get('qualifications', [])
        instance.contacts = data.get('contacts', [])
        instance.addresses = data.get('addresses', [])
        instance.bank_accounts = data.get('bankAccounts', [])
        return instance


# ============== 库存相关 ==============

@dataclass
class StockItem(BaseModel):
    """库存项目"""
    product_code: str = ''  # 物料编码
    product_name: str = ''  # 物料名称
    productsku_code: str = ''  # SKU 编码
    productsku_name: str = ''  # SKU 名称
    warehouse_id: str = ''  # 仓库 ID
    warehouse_name: str = ''  # 仓库名称
    current_qty: float = 0.0  # 现存量
    available_qty: float = 0.0  # 可用量
    planned_qty: float = 0.0  # 计划可用量
    unit_code: str = ''  # 单位编码
    unit_name: str = ''  # 单位名称
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'StockItem':
        """从 API 响应创建实例"""
        return cls(
            product_code=str(data.get('product_code', '')),
            product_name=str(data.get('product_name', '')),
            productsku_code=str(data.get('productsku_code', '')),
            productsku_name=str(data.get('productsku_name', '')),
            warehouse_id=str(data.get('warehouse', '')),
            warehouse_name=str(data.get('warehouse_name', '')),
            current_qty=float(data.get('currentqty', 0) or 0),
            available_qty=float(data.get('availableqty', 0) or 0),
            planned_qty=float(data.get('plannedqty', 0) or 0),
            unit_code=str(data.get('stockUnitId_code', '')),
            unit_name=str(data.get('stockUnitId_name', ''))
        )
    
    def format(self) -> str:
        """格式化为可读文本"""
        lines = [
            f"📦 {self.product_name} ({self.product_code})",
            f"   SKU: {self.productsku_code}",
            f"   仓库：{self.warehouse_name}",
            f"   现存量：{self.current_qty} {self.unit_name}",
            f"   可用量：{self.available_qty} {self.unit_name}",
        ]
        return "\n".join(lines)


# ============== 生产订单相关 ==============

@dataclass
class ProductionOrder(BaseModel):
    """生产订单 - 按27字段格式展示"""
    # 单据信息（1-6）
    id: str = ''                      # 订单ID
    code: str = ''                    # 生产订单号
    vouchdate: str = ''               # 单据日期
    trans_type: str = ''              # 交易类型
    trans_type_id: str = ''           # 交易类型ID
    org_id: str = ''                  # 工厂ID
    org_name: str = ''                # 工厂
    dept_id: str = ''                 # 生产部门ID
    dept_name: str = ''               # 生产部门
    status: str = ''                  # 订单状态码
    status_text: str = ''             # 订单状态文本
    # 商品明细（7-10）
    rowno: int = 0                    # 行号
    material_id: str = ''             # 物料ID
    material_code: str = ''           # 物料编码
    material_name: str = ''           # 物料名称
    free_chars: str = ''              # 自由项特征组
    # 生产数量（11-15）
    planned_qty: float = 0.0          # 生产数量
    main_unit: str = ''                # 主计量
    auxiliary_qty: float = 0.0         # 生产件数
    production_unit: str = ''          # 生产单位
    net_qty: float = 0.0              # 净算量
    # 日期信息（16-17）
    start_date: str = ''              # 开工日期
    finish_date: str = ''             # 完工日期
    # 其他信息（18-22）
    memo: str = ''                    # 备注
    creator: str = ''                 # 创建人
    creator_id: str = ''              # 创建人ID
    create_time: str = ''             # 创建时间
    auditor: str = ''                 # 审核人
    auditor_id: str = ''             # 审核人ID
    audit_time: str = ''             # 审核时间
    # 来源单据（23-26）
    first_upcode: str = ''            # 来源单据号（销售订单）
    first_lineno: int = 0             # 来源单据行号
    upcode: str = ''                  # 源头单据号（计划订单）
    # 执行进度（27）
    total_stockin_qty: float = 0.0   # 累计入库数量
    # BOM信息
    bom_id: str = ''                  # BOM版本ID
    bom_unit: str = ''                # BOM单位
    # 完工相关
    completed_qty: float = 0.0        # 已完工数量
    qualified_qty: float = 0.0         # 合格数量
    scrap_qty: float = 0.0            # 报废数量
    
    # 状态映射
    STATUS_MAP = {
        "0": "开立",
        "1": "已审核",
        "2": "已关闭",
        "3": "审核中",
        "4": "已锁定",
        "5": "已开工"
    }
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ProductionOrder':
        """从 API 响应创建实例"""
        def safe_str(v, default=''):
            return str(v) if v else default
        
        def safe_float(v, default=0.0):
            try:
                return float(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(v, default=0):
            try:
                return int(v) if v else default
            except (ValueError, TypeError):
                return default
        
        def fmt_date(v):
            """格式化日期"""
            if not v:
                return ''
            v = str(v)
            if ' ' in v:
                return v.split(' ')[0]
            return v
        
        def get_op(key, default=None):
            """从 OrderProduct_* 前缀获取嵌套数据"""
            return data.get(f'OrderProduct_{key}', default)
        
        # 获取状态文本
        status = safe_str(data.get('status'))
        status_text = cls.STATUS_MAP.get(status, status)
        
        return cls(
            id=safe_str(data.get('id')),
            code=safe_str(data.get('code')),
            vouchdate=fmt_date(data.get('vouchdate')),
            trans_type=safe_str(data.get('transTypeName')),
            trans_type_id=safe_str(data.get('transType')),
            org_id=safe_str(data.get('org')),
            org_name=safe_str(get_op('orgName')) or safe_str(data.get('orgName')),
            dept_id=safe_str(data.get('departmentId')),
            dept_name=safe_str(data.get('departmentName')),
            status=status,
            status_text=status_text,
            rowno=safe_int(get_op('lineNo')),
            material_id=safe_str(get_op('productId')),
            material_code=safe_str(get_op('productCode')),
            material_name=safe_str(get_op('productName')),
            free_chars=safe_str(get_op('propCharacteristics')) if isinstance(get_op('propCharacteristics'), str) else '',
            planned_qty=safe_float(get_op('quantity')),
            main_unit=safe_str(get_op('mainUnitName')),
            auxiliary_qty=safe_float(get_op('auxiliaryQuantity')),
            production_unit=safe_str(get_op('productUnitName')),
            net_qty=safe_float(get_op('netQuantity')),
            start_date=fmt_date(get_op('startDate')),
            finish_date=fmt_date(get_op('finishDate')),
            memo=safe_str(data.get('memo')),
            creator=safe_str(data.get('creator')),
            creator_id=safe_str(data.get('creatorId')),
            create_time=fmt_date(data.get('createTime')),
            auditor=safe_str(data.get('auditor')),
            auditor_id=safe_str(data.get('auditorId')),
            audit_time=fmt_date(data.get('auditTime')),
            # 来源单据（23-26）
            first_upcode=safe_str(get_op('firstupcode')),
            first_lineno=safe_int(get_op('firstlineno')),
            upcode=safe_str(get_op('upcode')),
            # 执行进度（27）
            total_stockin_qty=safe_float(data.get('cfmIncomingQty')),
            # BOM信息
            bom_id=safe_str(get_op('bomId')),
            bom_unit=safe_str(get_op('bomUnitName')),
            # 完工相关
            completed_qty=safe_float(get_op('completedQuantity')),
        )
    
    def format(self) -> str:
        """格式化为可读文本 - 27字段格式"""
        def fmt(v):
            if isinstance(v, float):
                return f"{v:,.2f}"
            return str(v) if v else "-"
        
        lines = [
            f"{'工厂':<12}：{self.org_name}",
            f"{'生产订单号':<12}：{self.code}",
            f"{'单据日期':<12}：{self.vouchdate}",
            f"{'交易类型':<12}：{self.trans_type}",
            f"{'生产部门':<12}：{self.dept_name}",
            f"{'订单状态':<12}：{self.status_text}",
            f"{'行号':<12}：{self.rowno}",
            f"{'物料编码':<12}：{self.material_code}",
            f"{'物料名称':<12}：{self.material_name}",
            f"{'自由项特征组':<12}：{self.free_chars or '-'}",
            f"{'生产数量':<12}：{fmt(self.planned_qty)} {self.main_unit}",
            f"{'主计量':<12}：{self.main_unit}",
            f"{'生产件数':<12}：{fmt(self.auxiliary_qty)}",
            f"{'生产单位':<12}：{self.production_unit}",
            f"{'净算量':<12}：{fmt(self.net_qty)}",
            f"{'开工日期':<12}：{self.start_date}",
            f"{'完工日期':<12}：{self.finish_date}",
            f"{'备注':<12}：{self.memo or '-'}",
            f"{'创建人':<12}：{self.creator}",
            f"{'创建时间':<12}：{self.create_time}",
            f"{'审核人':<12}：{self.auditor}",
            f"{'审核时间':<12}：{self.audit_time}",
            f"{'来源单据号':<12}：{self.first_upcode or '-'}",
            f"{'来源单据行号':<12}：{self.first_lineno or '-'}",
            f"{'源头单据号':<12}：{self.upcode or '-'}",
            f"{'累计入库数量':<12}：{fmt(self.total_stockin_qty)}",
        ]
        return "\n".join(lines)
    
    def to_table_row(self) -> Dict[str, Any]:
        """转换为表格行数据 - 27字段"""
        return {
            '工厂': self.org_name,
            '生产订单号': self.code,
            '单据日期': self.vouchdate,
            '交易类型': self.trans_type,
            '生产部门': self.dept_name,
            '订单状态': self.status_text,
            '行号': self.rowno,
            '物料编码': self.material_code,
            '物料名称': self.material_name,
            '自由项特征组': self.free_chars or '-',
            '生产数量': f"{self.planned_qty:,.2f}" if self.planned_qty else '-',
            '主计量': self.main_unit,
            '生产件数': f"{self.auxiliary_qty:,.2f}" if self.auxiliary_qty else '-',
            '生产单位': self.production_unit,
            '净算量': f"{self.net_qty:,.2f}" if self.net_qty else '-',
            '开工日期': self.start_date,
            '完工日期': self.finish_date,
            '备注': self.memo or '-',
            '创建人': self.creator,
            '创建时间': self.create_time,
            '审核人': self.auditor,
            '审核时间': self.audit_time,
            '来源单据号': self.first_upcode or '-',
            '来源单据行号': self.first_lineno or '-',
            '源头单据号': self.upcode or '-',
            '累计入库数量': f"{self.total_stockin_qty:,.2f}" if self.total_stockin_qty else '-',
        }


@dataclass
class ProductionOrderDetail(ProductionOrder):
    """生产订单详情（包含工序、材料等）"""
    processes: List[Dict[str, Any]] = field(default_factory=list)  # 工序
    materials: List[Dict[str, Any]] = field(default_factory=list)  # 材料
    by_products: List[Dict[str, Any]] = field(default_factory=list)  # 联副产品
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ProductionOrderDetail':
        """从 API 响应创建实例"""
        instance = super().from_api(data)
        instance.processes = data.get('processes', [])
        instance.materials = data.get('materials', [])
        instance.by_products = data.get('byProducts', [])
        return instance


# ============== 通用响应模型 ==============

@dataclass
class APIResponse(BaseModel):
    """API 响应包装器"""
    success: bool
    code: str = ''
    message: str = ''
    data: Any = None
    page_index: int = 1
    page_size: int = 0
    total_count: int = 0
    
    @classmethod
    def from_api(cls, result: Dict[str, Any]) -> 'APIResponse':
        """从 API 响应创建实例"""
        return cls(
            success=result.get('code') in ('200', '00000', 200),
            code=str(result.get('code', '')),
            message=result.get('message', result.get('errorMsg', '')),
            data=result.get('data'),
            page_index=result.get('pageIndex', 1),
            page_size=result.get('pageSize', 0),
            total_count=result.get('pageInfo', {}).get('totalCount', 0)
        )


# ============== 用户待办相关 ==============

@dataclass
class TodoItem(BaseModel):
    """用户待办事项"""
    tenant_id: str = ""
    user_id: str = ""
    primary_id: str = ""
    app_id: str = ""
    business_key: str = ""
    title: str = ""
    content: str = ""
    rich_text: str = ""
    m_url: str = ""
    web_url: str = ""
    done_status: int = 0  # 0=待办，1=已办
    approve_source: str = ""
    form_id: str = ""
    service_code: str = ""
    group_id: str = ""
    org_id: str = ""
    commit_user_id: str = ""
    commit_ts_long: int = 0
    create_ts_long: int = 0
    update_ts_long: int = 0
    finish_ts_long: int = 0
    msg_ts_long: int = 0
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TodoItem':
        """从 API 响应创建待办事项对象"""
        return cls(
            tenant_id=data.get('tenantId', ''),
            user_id=data.get('userId', ''),
            primary_id=data.get('primaryId', ''),
            app_id=data.get('appId', ''),
            business_key=data.get('businessKey', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            rich_text=data.get('richText', ''),
            m_url=data.get('mUrl', ''),
            web_url=data.get('webUrl', ''),
            done_status=data.get('doneStatus', 0),
            approve_source=data.get('approveSource', ''),
            form_id=data.get('formId', ''),
            service_code=data.get('serviceCode', ''),
            group_id=data.get('groupId', ''),
            org_id=data.get('orgid', ''),
            commit_user_id=data.get('commitUserId', ''),
            commit_ts_long=data.get('commitTsLong', 0),
            create_ts_long=data.get('createTsLong', 0),
            update_ts_long=data.get('updateTsLong', 0),
            finish_ts_long=data.get('finishTsLong', 0),
            msg_ts_long=data.get('msgTsLong', 0),
        )
    
    def format(self) -> str:
        """格式化为可读文本"""
        status = "✅ 已办" if self.done_status == 1 else "⏳ 待办"
        lines = [
            f"标题：{self.title}",
            f"状态：{status}",
            f"内容：{self.content}",
            f"来源：{self.approve_source}",
            f"表单：{self.form_id}",
        ]
        if self.web_url:
            lines.append(f"链接：{self.web_url[:100]}...")
        return "\n  ".join(lines)
    
    @property
    def is_todo(self) -> bool:
        """是否为待办（未完成）"""
        return self.done_status == 0
    
    @property
    def is_done(self) -> bool:
        """是否为已办（已完成）"""
        return self.done_status == 1


# ============== 物料档案相关 ==============

@dataclass
class ProductItem(BaseModel):
    """物料档案"""
    id: str = ''
    code: str = ''  # 物料编码
    name: str = ''  # 物料名称
    model: str = ''  # SKU 型号
    product_class: str = ''  # 物料分类
    manage_class: str = ''  # 物料分类ID
    product_line: str = ''  # 产品线
    brand: str = ''  # 品牌
    unit: str = ''  # 主计量单位
    unit_name: str = ''  # 主计量单位名称
    real_product_attribute: str = ''  # 物料类型：1=实物物料，2=虚拟物料
    has_specs: str = ''  # 是否包含属性
    enable_assist_unit: str = ''  # 启用辅计量
    status: str = ''  # 平台处理商家物料状态
    create_time: str = ''  # 创建时间
    modify_time: str = ''  # 修改时间
    org_id: str = ''  # 组织id
    creator: str = ''  # 创建人
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'ProductItem':
        """从 API 响应创建实例"""
        # realProductAttribute 格式："1:实物物料、2:虚拟物料、"
        return cls(
            id=str(data.get('id', '')),
            code=str(data.get('code', '')),
            name=str(data.get('name', '')),
            model=str(data.get('model', '')),
            product_class=str(data.get('manageClassName', '') or data.get('productClass', '')),
            manage_class=str(data.get('manageClass', '')),
            product_line=str(data.get('productLine', '')),
            brand=str(data.get('brand', '')),
            unit=str(data.get('unitId', '') or data.get('unit', '')),
            unit_name=str(data.get('unitName', '') or data.get('unit_name', '')),
            real_product_attribute=str(data.get('realProductAttribute', '')),
            has_specs=str(data.get('hasSpecs', '')),
            enable_assist_unit=str(data.get('enableAssistUnit', '')),
            status=str(data.get('stopStatus', '')),
            create_time=str(data.get('createTime', '') or data.get('create_date', '')),
            modify_time=str(data.get('modifyTime', '') or data.get('modifyDate', '')),
            org_id=str(data.get('createOrgId', '') or data.get('orgId', '')),
            creator=str(data.get('creator', ''))
        )
    
    def format(self) -> str:
        """格式化为可读文本"""
        attr_text = self.real_product_attribute or '—'
        stop_text = '停用' if str(self.status) == 'true' else '启用'
        lines = [
            f"🏷️ {self.name} ({self.code})",
            f"   ID: {self.id}",
            f"   物料类型：{attr_text}",
            f"   主单位：{self.unit_name or self.unit or '—'}",
            f"   物料分类：{self.product_class or '—'}",
            f"   型号：{self.model or '—'}",
            f"   规格属性：{'是' if self.has_specs == 'true' else '否'}",
            f"   辅计量：{'是' if self.enable_assist_unit == 'true' else '否'}",
            f"   停用状态：{stop_text}",
            f"   创建时间：{self.create_time or '—'}",
        ]
        return "\n".join(lines)


# =============================================================================
# CRM 商机模型
# =============================================================================

@dataclass
class Opportunity:
    """
    商机数据模型（v5.9 修正版）

    来源：POST /yonbip/crm/oppt/bill/list
    API 返回字段为 camelCase（实测），注意区分。
    """
    id: str                          # 商机ID
    code: str                        # 商机编码
    name: str                        # 商机名称
    oppt_state: int                  # 商机状态：0-进行中；1-暂停；2-作废；3-关闭
    oppt_state_name: str             # 商机状态名称
    win_lose_order_state: int        # 赢丢单状态：0-赢单；1-丢单；2-未定；3-部分赢单
    win_lose_order_state_name: str   # 赢丢单状态名称
    expect_sign_money: float         # 预计签约金额（进行中商机）
    win_order_money: float           # 赢单实际金额（赢单后有值）
    win_order_date: str              # 赢单日期
    winning_rate: int                # 赢单概率 0-100
    customer_name: str              # 客户名称
    customer_code: str              # 客户编码
    ower_name: str                 # 业务员名称（API字段：ower_name）
    dept_name: str                 # 部门名称
    org_name: str                  # 销售组织名称
    oppt_stage_name: str           # 商机阶段名称（API字段：opptStage_name）
    create_date: str              # 创建日期（API字段：createDate）
    create_time: str              # 创建时间（API字段：createTime）
    oppt_date: str              # 商机日期（API字段：opptDate）
    details: List[Dict]         # 明细行列表（is_sum=True 时返回）

    @classmethod
    def from_api(cls, data: Dict) -> 'Opportunity':
        return cls(
            id=str(data.get('id', '')),
            code=str(data.get('code', '')),
            name=str(data.get('name', '')),
            oppt_state=int(data.get('opptState', 0) or 0),
            oppt_state_name=str(data.get('opptState_name', '')),
            win_lose_order_state=int(data.get('winLoseOrderState', 2) or 2),
            win_lose_order_state_name=str(data.get('winLoseOrderState_name', '')),
            expect_sign_money=float(data.get('expectSignMoney') or 0),
            win_order_money=float(data.get('winOrderMoney') or 0),
            win_order_date=str(data.get('winOrderDate', '')),
            winning_rate=int(data.get('winningRate') or 0),
            customer_name=str(data.get('customer_name', '')),
            customer_code=str(data.get('customer', '')),
            ower_name=str(data.get('ower_name', '')),
            dept_name=str(data.get('dept_name', '')),
            org_name=str(data.get('org_name', '')),
            oppt_stage_name=str(data.get('opptStage_name', '')),
            create_date=str(data.get('createDate', '')),
            create_time=str(data.get('createTime', '')),
            oppt_date=str(data.get('opptDate', '')),
            details=data.get('details', []),
        )

    def format(self) -> str:
        """格式化为可读文本"""
        state_map = {0: '进行中', 1: '暂停', 2: '作废', 3: '关闭'}
        win_map = {0: '赢单', 1: '丢单', 2: '未定', 3: '部分赢单'}

        # 金额：进行中用 expectSignMoney，赢单用 winOrderMoney
        amount = self.win_order_money if self.win_lose_order_state == 0 else self.expect_sign_money

        lines = [
            f"🏷️ {self.name} ({self.code})",
            f"   商机ID：{self.id}",
            f"   商机状态：{state_map.get(self.oppt_state, '未知')} → {self.oppt_state_name}",
            f"   赢丢单：{win_map.get(self.win_lose_order_state, '未知')} → {self.win_lose_order_state_name}",
            f"   商机金额：{amount:,.2f}（预计 {self.expect_sign_money:,.2f} / 赢单 {self.win_order_money:,.2f}）",
            f"   客户：{self.customer_name}（{self.customer_code}）",
            f"   业务员：{self.ower_name}",
            f"   部门：{self.dept_name}",
            f"   销售组织：{self.org_name}",
            f"   商机阶段：{self.oppt_stage_name}",
            f"   赢单概率：{self.winning_rate}%",
            f"   商机日期：{self.oppt_date}",
            f"   创建时间：{self.create_time}",
        ]
        return "\n".join(lines)

