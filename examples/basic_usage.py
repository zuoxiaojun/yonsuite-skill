#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite API 客户端 - 基础使用示例

本示例展示如何使用 YonSuiteClient 进行常见操作。
"""

import sys
from pathlib import Path

# 添加技能目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ys_client import YonSuiteClient
from datetime import datetime, timedelta


def main():
    # 初始化客户端
    print("🚀 初始化 YonSuite 客户端...")
    client = YonSuiteClient()
    
    # ============== 1. 查询销售订单 ==============
    print("\n📋 查询销售订单...")
    orders = client.query_sale_orders(customer_name="测试", page_size=5)
    print(f"找到 {len(orders.get('data', []))} 个订单")
    
    # ============== 2. 查询订单详情 ==============
    if orders.get('data'):
        order_id = orders['data'][0]['id']
        print(f"\n📋 查询订单详情：{order_id}")
        detail = client.get_order_detail(order_id)
        print(f"订单状态：{detail.get('data', {}).get('nextStatusName', 'N/A')}")
    
    # ============== 3. 查询库存 ==============
    print("\n📦 查询库存...")
    stock = client.query_current_stock(product_code="A010100003")
    if stock.get('data'):
        for item in stock['data'][:3]:
            print(f"  - {item.get('product_name')}: {item.get('currentqty')} 件")
    
    # ============== 4. 查询客户档案 ==============
    print("\n👥 查询客户档案...")
    customers = client.query_customers(page_size=5)
    print(f"找到 {len(customers.get('data', []))} 个客户")
    
    # ============== 5. 查询供应商档案 ==============
    print("\n🏢 查询供应商档案...")
    vendors = client.query_vendors(page_size=5)
    print(f"找到 {len(vendors.get('data', []))} 个供应商")
    
    # ============== 6. 查询生产订单 ==============
    print("\n🏭 查询生产订单（近 7 天）...")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    production = client.query_production_orders(
        start_date=start_date,
        end_date=end_date,
        page_size=5
    )
    print(f"找到 {len(production.get('data', []))} 个生产订单")
    
    # ============== 7. 查询采购订单 ==============
    print("\n🛒 查询采购订单...")
    purchase = client.query_purchase_orders(page_size=5)
    print(f"找到 {len(purchase.get('data', []))} 个采购订单")
    
    # ============== 8. 查询客户详情（新增）⭐ ==============
    if customers.get('data'):
        customer_id = customers['data'][0]['id']
        print(f"\n👤 查询客户详情（新增功能）：{customer_id}")
        customer_detail = client.query_customer_detail(customer_id=customer_id)
        detail_data = customer_detail.get('data', {})
        if detail_data:
            print(f"  客户名称：{detail_data.get('name', {}).get('simplifiedName', 'N/A')}")
            print(f"  联系人：{detail_data.get('contactName', 'N/A')}")
            print(f"  电话：{detail_data.get('contactTel', 'N/A')}")
    
    # ============== 9. 查询采购订单详情（新增）⭐ ==============
    if purchase.get('data'):
        purchase_id = purchase['data'][0]['id']
        print(f"\n🛒 查询采购订单详情（新增功能）：{purchase_id}")
        purchase_detail = client.get_purchase_order_detail(purchase_id)
        detail_data = purchase_detail.get('data', {})
        if detail_data:
            print(f"  订单编号：{detail_data.get('code', 'N/A')}")
            print(f"  供应商：{detail_data.get('vendor_name', 'N/A')}")
            print(f"  含税金额：¥{detail_data.get('oriSum', 0):,.2f}")
            # 显示订单明细
            for item in detail_data.get('purchaseOrders', [])[:2]:
                print(f"    - {item.get('product_cName')}: {item.get('qty')} {item.get('unit_name')}")
    
    print("\n✅ 示例执行完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
