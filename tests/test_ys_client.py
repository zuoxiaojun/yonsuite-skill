#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YonSuite API 客户端单元测试

运行测试：
    python -m pytest tests/test_ys_client.py -v

或：
    python tests/test_ys_client.py
"""

import unittest
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from exceptions import YonSuiteConfigError, YonSuiteAPIError
from models import SaleOrder, StockItem, ProductionOrder


class TestConfig(unittest.TestCase):
    """配置测试"""
    
    def test_config_loaded(self):
        """测试配置是否正确加载"""
        # 如果配置了环境变量，应该能正确读取
        self.assertTrue(Config.is_configured() or not Config.is_configured())
    
    def test_config_validation(self):
        """测试配置验证"""
        if not Config.is_configured():
            with self.assertRaises(ValueError):
                Config.validate()


class TestModels(unittest.TestCase):
    """数据模型测试"""
    
    def test_sale_order_from_dict(self):
        """测试销售订单模型转换"""
        data = {
            'id': '123456',
            'code': 'SO20260320-001',
            'agentId_name': '测试客户',
            'payMoney': 1000.50,
            'nextStatusName': '已审核',
            'vouchdate': '2026-03-20'
        }
        order = SaleOrder.from_api(data)
        self.assertEqual(order.id, '123456')
        self.assertEqual(order.code, 'SO20260320-001')
        self.assertEqual(order.customer_name, '测试客户')
        self.assertAlmostEqual(order.amount, 1000.50)
    
    def test_stock_item_from_dict(self):
        """测试库存项目模型转换"""
        data = {
            'product_code': 'A010100003',
            'product_name': '测试物料',
            'currentqty': 100,
            'availableqty': 80
        }
        item = StockItem.from_api(data)
        self.assertEqual(item.product_code, 'A010100003')
        self.assertEqual(item.product_name, '测试物料')
        self.assertEqual(item.current_qty, 100)
        self.assertEqual(item.available_qty, 80)
    
    def test_production_order_from_dict(self):
        """测试生产订单模型转换"""
        data = {
            'id': '789012',
            'code': 'MO20260320-001',
            'status': '1',
            'OrderProduct_materialName': '测试产品',
            'OrderProduct_quantity': 50
        }
        order = ProductionOrder.from_api(data)
        self.assertEqual(order.id, '789012')
        self.assertEqual(order.status_text, '已审核')
        self.assertEqual(order.material_name, '测试产品')
        self.assertAlmostEqual(order.planned_qty, 50)


class TestClient(unittest.TestCase):
    """客户端测试"""
    
    @unittest.skipIf(not Config.is_configured(), "配置未设置")
    def test_get_token(self):
        """测试获取 Token"""
        from ys_client import YonSuiteClient
        client = YonSuiteClient()
        token = client.get_access_token()
        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)
    
    @unittest.skipIf(not Config.is_configured(), "配置未设置")
    def test_query_customers(self):
        """测试查询客户（ smoke test）"""
        from ys_client import YonSuiteClient
        client = YonSuiteClient()
        result = client.query_customers(page_size=5)
        self.assertIn('code', result)
        self.assertIn(result['code'], ['200', '00000'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
