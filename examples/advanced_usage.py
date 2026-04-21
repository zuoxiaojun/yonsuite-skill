#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite API 客户端 - 高级使用示例

展示模块化调用、数据模型使用、错误处理等高级功能。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ys_client import YonSuiteClient
from models import SaleOrder, StockItem, ProductionOrder
from exceptions import YonSuiteAPIError, YonSuiteAuthError


def example_module_usage():
    """示例：直接使用功能模块"""
    print("\n=== 示例：模块化调用 ===\n")
    
    client = YonSuiteClient()
    token = client.get_access_token()
    
    # 直接使用销售模块
    orders = client.sales.query_orders_parsed(token, customer_name="测试", page_size=3)
    print(f"📋 销售订单（模型对象）：{len(orders)} 个")
    for order in orders:
        print(f"  - {order.code}: ¥{order.amount:,.2f}")
    
    # 直接使用库存模块
    stock_items = client.stock.query_stock_parsed(token, product_code="A010100003")
    print(f"\n📦 库存记录（模型对象）：{len(stock_items)} 条")
    for item in stock_items:
        print(f"  - {item.product_name}: {item.current_qty} 件 (可用：{item.available_qty})")


def example_error_handling():
    """示例：错误处理"""
    print("\n=== 示例：错误处理 ===\n")
    
    client = YonSuiteClient()
    
    try:
        # 查询不存在的订单
        detail = client.get_order_detail("invalid_id")
    except YonSuiteAPIError as e:
        print(f"⚠️  API 错误：{e}")
        print(f"   错误码：{e.error_code}")
        print(f"   HTTP 状态：{e.http_status}")
    except Exception as e:
        print(f"⚠️  其他错误：{e}")


def example_formatted_output():
    """示例：格式化输出"""
    print("\n=== 示例：格式化输出 ===\n")
    
    client = YonSuiteClient()
    
    # 查询并格式化销售订单
    result = client.query_sale_orders(page_size=3)
    if result.get('data'):
        orders = [SaleOrder.from_api(item) for item in result['data']]
        print(client.sales.format_orders_list(orders))
    
    # 查询并格式化库存
    result = client.query_current_stock(product_name="测试")
    if result.get('data'):
        items = [StockItem.from_api(item) for item in result['data']]
        print(client.stock.format_stock_info(items))


def example_production_order():
    """示例：生产订单查询"""
    print("\n=== 示例：生产订单 ===\n")
    
    from datetime import datetime, timedelta
    
    client = YonSuiteClient()
    
    # 查询近 30 天的生产订单
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    result = client.query_production_orders(
        start_date=start,
        end_date=end,
        page_size=5
    )
    
    if result.get('data'):
        orders = [ProductionOrder.from_api(item) for item in result['data']]
        print(client.production.format_orders_list(orders))


def main():
    """运行所有示例"""
    print("🚀 YonSuite API 客户端 - 高级使用示例\n")
    print("=" * 60)
    
    try:
        example_module_usage()
        example_error_handling()
        example_formatted_output()
        example_production_order()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例执行完成！")
    
    except Exception as e:
        print(f"\n❌ 示例执行失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
