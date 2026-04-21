#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite API 客户端 - 新功能演示示例（v2.1）

本示例展示 v2.1 版本新增的功能：
1. 客户档案详情批量查询
2. 采购订单详情查询
"""

import sys
from pathlib import Path

# 添加技能目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ys_client import YonSuiteClient


def demo_customer_detail():
    """演示客户详情查询功能"""
    print("\n" + "="*70)
    print("👤 客户档案详情查询功能演示")
    print("="*70)
    
    client = YonSuiteClient()
    
    # 示例 1：查询单个客户详情
    print("\n【示例 1】查询单个客户详情")
    print("-" * 70)
    
    # 使用之前查询到的客户 ID（南京宝生源食品有限公司）
    customer_id = "2499405494493380612"
    print(f"查询客户 ID: {customer_id}")
    
    detail = client.query_customer_detail(customer_id=customer_id)
    data = detail.get('data', {})
    
    if data:
        # 基本信息
        print("\n📋 基本信息")
        print(f"  客户编码：{data.get('code', 'N/A')}")
        print(f"  客户名称：{data.get('name', {}).get('simplifiedName', 'N/A')}")
        print(f"  客户简称：{data.get('shortname', {}).get('simplifiedName', 'N/A')}")
        print(f"  客户类型：{data.get('transTypeCode', 'N/A')} - {data.get('transTypeName', 'N/A')}")
        
        # 资质信息
        print("\n📄 资质信息")
        license_types = {0: '统一社会信用代码', 1: '营业执照', 2: '其他证照'}
        print(f"  证照类型：{license_types.get(data.get('licenseType'), 'N/A')}")
        print(f"  证照号码：{data.get('creditCode', 'N/A')}")
        print(f"  法人代表：{data.get('leaderName', 'N/A')}")
        print(f"  成立时间：{data.get('buildTime', 'N/A')}")
        print(f"  注册资金：{data.get('money', 'N/A')} {data.get('currencyCode', 'N/A')}")
        
        # 联系信息
        print("\n📞 联系信息")
        print(f"  联系电话：{data.get('contactTel', 'N/A')}")
        print(f"  电子邮箱：{data.get('email', 'N/A')}")
        print(f"  地址：{data.get('address', {}).get('simplifiedName', 'N/A')}")
        
        # 地址信息
        address_infos = data.get('merchantAddressInfos', [])
        if address_infos:
            print(f"\n📍 地址信息（共{len(address_infos)}条）")
            for i, addr in enumerate(address_infos[:2], 1):
                print(f"  {i}. {addr.get('address', 'N/A')}")
                print(f"     联系人：{addr.get('receiver', 'N/A')} {addr.get('mobile', 'N/A')}")
        
        # 银行信息
        financial_infos = data.get('merchantAgentFinancialInfos', [])
        if financial_infos:
            print(f"\n🏦 银行信息（共{len(financial_infos)}条）")
            for i, fin in enumerate(financial_infos[:2], 1):
                print(f"  {i}. {fin.get('bankName', 'N/A')}")
                print(f"     账号：{fin.get('bankAccount', 'N/A')}")
        
        # 发票信息
        invoice_infos = data.get('merchantAgentInvoiceInfos', [])
        if invoice_infos:
            print(f"\n🧾 发票信息（共{len(invoice_infos)}条）")
            for i, inv in enumerate(invoice_infos[:2], 1):
                print(f"  {i}. {inv.get('title', 'N/A')}")
                print(f"     税号：{inv.get('taxNo', 'N/A')}")
    
    # 示例 2：批量查询客户详情
    print("\n\n【示例 2】批量查询客户详情")
    print("-" * 70)
    
    # 先查询客户列表获取多个客户 ID
    customers = client.query_customers(page_size=3)
    customer_list = customers.get('data', [])
    
    if customer_list:
        print(f"准备查询 {len(customer_list)} 个客户的详情...")
        
        batch_params = [{"id": cust['id']} for cust in customer_list]
        result = client.query_customer_details_batch(batch_params)
        
        batch_data = result.get('data', [])
        print(f"成功查询 {len(batch_data)} 个客户详情\n")
        
        for i, cust in enumerate(batch_data[:3], 1):
            print(f"{i}. {cust.get('name', {}).get('simplifiedName', 'N/A')}")
            print(f"   编码：{cust.get('code', 'N/A')}")
            print(f"   联系人：{cust.get('contactName', 'N/A')}")
            print(f"   电话：{cust.get('contactTel', 'N/A')}")
            print()


def demo_purchase_order_detail():
    """演示采购订单详情查询功能"""
    print("\n" + "="*70)
    print("🛒 采购订单详情查询功能演示")
    print("="*70)
    
    client = YonSuiteClient()
    
    # 先查询采购订单列表
    print("\n【步骤 1】查询采购订单列表")
    print("-" * 70)
    
    orders = client.query_purchase_orders(page_size=5)
    order_list = orders.get('data', [])
    
    if not order_list:
        print("未找到采购订单")
        return
    
    print(f"找到 {len(order_list)} 个采购订单")
    for i, order in enumerate(order_list[:3], 1):
        print(f"  {i}. {order.get('code', 'N/A')} - {order.get('vendor_name', 'N/A')}")
    
    # 查询第一个订单的详情
    if order_list:
        order_id = order_list[0]['id']
        print(f"\n【步骤 2】查询订单详情：{order_id}")
        print("-" * 70)
        
        detail = client.get_purchase_order_detail(order_id)
        data = detail.get('data', {})
        
        if data:
            # 基本信息
            print("\n📋 基本信息")
            print(f"  订单编号：{data.get('code', 'N/A')}")
            print(f"  交易类型：{data.get('bustype_name', 'N/A')}")
            print(f"  采购组织：{data.get('org_name', 'N/A')}")
            print(f"  采购员：{data.get('operator_name', 'N/A')}")
            print(f"  单据日期：{data.get('vouchdate', 'N/A')}")
            print(f"  希望到货日期：{data.get('expectDate', 'N/A')}")
            
            # 供应商信息
            print("\n🏭 供应商信息")
            print(f"  供应商：{data.get('vendor_name', 'N/A')}")
            print(f"  供应商编码：{data.get('vendor_code', 'N/A')}")
            print(f"  联系人：{data.get('contact', 'N/A')}")
            print(f"  联系电话：{data.get('contactTel', 'N/A')}")
            
            # 金额信息
            print("\n💰 金额信息")
            print(f"  含税金额：¥{data.get('oriSum', 0):,.2f}")
            print(f"  无税金额：¥{data.get('oriMoney', 0):,.2f}")
            print(f"  税额：¥{data.get('oriTax', 0):,.2f}")
            print(f"  币种：{data.get('currency_name', 'N/A')}")
            
            # 状态信息
            print("\n📊 状态信息")
            status_map = {'0': '开立', '1': '已审核', '2': '已关闭', '3': '审核中'}
            bizstatus_map = {
                '0': '未提交', '1': '已提交', '2': '已关闭', 
                '3': '待入库', '4': '已完成'
            }
            print(f"  单据状态：{bizstatus_map.get(data.get('bizstatus'), data.get('bizstatus', 'N/A'))}")
            print(f"  审核状态：{status_map.get(data.get('status'), data.get('status', 'N/A'))}")
            print(f"  审核人：{data.get('auditor', 'N/A')}")
            print(f"  审核时间：{data.get('auditTime', 'N/A')}")
            
            # 执行情况
            print("\n📦 执行情况")
            print(f"  累计到货：¥{data.get('allTotalArrivedTaxMoney', 0):,.2f}")
            print(f"  累计入库：¥{data.get('allTotalInTaxMoney', 0):,.2f}")
            print(f"  累计开票：¥{data.get('allTotalInvoiceMoney', 0):,.2f}")
            print(f"  累计付款：¥{data.get('totalPayMoney', 0):,.2f}")
            
            # 订单明细
            purchase_orders = data.get('purchaseOrders', [])
            if purchase_orders:
                print(f"\n📋 订单明细（共{len(purchase_orders)}行）")
                for i, item in enumerate(purchase_orders[:5], 1):
                    print(f"  {i}. {item.get('product_cName', 'N/A')} ({item.get('product_model', 'N/A')})")
                    print(f"     数量：{item.get('qty', 0)} {item.get('unit_name', 'N/A')}")
                    print(f"     单价：¥{item.get('oriUnitPrice', 0):,.2f}")
                    print(f"     金额：¥{item.get('oriSum', 0):,.2f}")
                    print(f"     到货状态：{item.get('arrivedStatus', 'N/A')} | "
                          f"入库状态：{item.get('inWHStatus', 'N/A')}")
            
            # 付款计划
            payment_schedules = data.get('paymentSchedules', [])
            if payment_schedules:
                print(f"\n💳 付款计划（共{len(payment_schedules)}期）")
                for i, schedule in enumerate(payment_schedules[:3], 1):
                    print(f"  {i}. {schedule.get('name', 'N/A')} - {schedule.get('payRatio', 0)}%")
                    print(f"     金额：¥{schedule.get('amount', 0):,.2f}")
                    print(f"     日期：{schedule.get('startDateTime', 'N/A')}")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🎉 YonSuite v2.1 新功能演示")
    print("="*70)
    
    try:
        # 演示客户详情查询
        demo_customer_detail()
        
        # 演示采购订单详情查询
        demo_purchase_order_detail()
        
        print("\n" + "="*70)
        print("✅ 所有演示完成！")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
