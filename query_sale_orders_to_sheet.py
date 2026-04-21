#!/usr/bin/env python3
"""
查询指定日期的销售订单，直接写入飞书电子表格

用法:
    python3 query_sale_orders_to_sheet.py 2026-04-01
    python3 query_sale_orders_to_sheet.py 2026-04    # 查整月

输出:
    - 飞书表格链接
    - 订单统计（单数/行数/含税总金额/税额合计）
"""

import sys
import json
import argparse
from collections import defaultdict

from pathlib import Path
SCRIPT_DIR = str(Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)
from ys_client import YonSuiteClient


def round2(v):
    """保留两位小数"""
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


# ---------- 字段映射 ----------
STATUS_MAP = {
    'CONFIRMORDER': '开立',
    'DELIVERY_PART': '部分发货',
    'DELIVERY_TAKE_PART': '部分发货待收货',
    'DELIVERGOODS': '待发货',
    'TAKEDELIVERY': '待收货',
    'ENDORDER': '已完成',
    'OPPOSE': '已取消',
    'APPROVING': '审批中',
}

# 29列标准表头（销售订单）- 官方文档字段顺序
HEADERS = [
    '单据编号', '单据日期', '审批日期', '销售组织', '交易类型',
    '客户', '销售部门', '销售业务员', '订单状态',
    '行号', '物料编码', '物料名称', '销售数量', '销售单位',
    '数量', '主计量', '币种',
    '含税成交价', '含税金额', '税率', '表体税额',
    '计划发货日期', '库存组织', '发货仓库',
    '累计已发货数量', '累计出库金额', '累计开票数量', '累计开票含税金额',
    '累计出库确认数量'
]


def query_and_format(date_filter: str):
    """查询并格式化销售订单数据"""
    client = YonSuiteClient()
    result = client.query_sale_orders(page_size=500)
    records = result.get('data', {}).get('recordList', [])

    if len(date_filter) == 7:
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]
    else:
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]

    if not filtered:
        print(f'⚠️  未找到 {date_filter} 的销售订单数据')
        return None, None, None, None, None

    by_code = defaultdict(list)
    for o in filtered:
        by_code[o.get('code', '')].append(o)

    data_rows = []
    grand_total = 0.0
    grand_tax = 0.0
    order_count = len(by_code)
    row_count = 0

    for code in sorted(by_code.keys()):
        rows = by_code[code]
        first = rows[0]

        sale_status = first.get('nextStatus', '') or ''
        status_str = STATUS_MAP.get(sale_status, sale_status)

        for r in rows:
            row_count += 1
            lineno = int(float(r.get('lineno', 0) or 0))
            ori_sum = float(r.get('oriSum', 0) or 0)
            ori_unit_price = float(r.get('oriTaxUnitPrice', 0) or 0)
            tax_rate_val = float(r.get('taxRate', 0) or 0)
            calc_tax = ori_sum / (1 + tax_rate_val / 100) * (tax_rate_val / 100) if tax_rate_val > 0 else 0.0

            grand_total += round2(ori_sum)
            grand_tax += round2(calc_tax)

            # 币种嵌套在 orderPrices 下
            order_prices = first.get('orderPrices', {}) or {}
            currency_name = order_prices.get('originalName', '') or ''

            data_rows.append([
                code,                                               # 1 单据编号
                r.get('vouchdate', '')[:10],                       # 2 单据日期
                str(first.get('auditDate', '') or '')[:10],         # 3 审批日期
                first.get('salesOrgId_name', ''),                   # 4 销售组织
                first.get('transactionTypeId_name', ''),            # 5 交易类型
                first.get('agentId_name', ''),                       # 6 客户
                first.get('saleDepartmentId_name', ''),             # 7 销售部门
                first.get('corpContactUserName', ''),               # 8 销售业务员
                status_str,                                         # 9 订单状态
                lineno,                                             # 10 行号
                r.get('skuCode', ''),                               # 11 物料编码
                r.get('skuName', ''),                               # 12 物料名称
                round2(float(r.get('qty', 0) or 0)),               # 13 销售数量
                r.get('productUnitName', ''),                       # 14 销售单位
                round2(float(r.get('qty', 0) or 0)),               # 15 数量（主计量单位）
                r.get('qtyName', ''),                               # 16 主计量
                currency_name or 'CNY',                             # 17 币种
                round2(ori_unit_price),                             # 18 含税成交价
                round2(ori_sum),                                    # 19 含税金额
                str(r.get('taxRate', '')),                          # 20 税率
                round2(calc_tax),                                   # 21 表体税额
                str(first.get('sendDate', '') or '')[:10],          # 22 计划发货日期
                first.get('stockOrgId_name', ''),                   # 23 库存组织
                first.get('stockName', '') or '—',                  # 24 发货仓库（API可能为null）
                round2(float(r.get('sendQty', 0) or 0)),            # 25 累计已发货数量
                round2(float(r.get('totalOutStockOriMoney', 0) or 0)),  # 26 累计出库金额
                round2(float(r.get('invoiceQty', 0) or 0)),          # 27 累计开票数量
                round2(float(r.get('invoiceOriSum', 0) or 0)),        # 28 累计开票含税金额
                round2(float(r.get('totalOutStockQuantity', 0) or 0)),  # 29 累计出库确认数量
            ])

    # 合计行
    data_rows.append([
        '合计', '', '', '', '', '', '',
        '', '', '', '', '', '',
        round2(grand_total), '', round2(grand_tax),
        '', '', '', '', '', '',
        '', '', '', '', '', '', '', ''
    ])

    return data_rows, order_count, row_count, grand_total, grand_tax


def main():
    parser = argparse.ArgumentParser(description='查询销售订单并写入飞书表格')
    parser.add_argument('date', help='日期，如 2026-04-01 或 2026-04')
    parser.add_argument('--title', help='飞书表格标题，默认按日期生成')
    args = parser.parse_args()

    date_filter = args.date
    title = args.title or f'销售订单_{date_filter}'

    print(f'📅 查询日期: {date_filter}')

    result = query_and_format(date_filter)
    if result[0] is None:
        sys.exit(1)

    data_rows, order_count, row_count, grand_total, grand_tax = result

    print(f'✅ 查询完成: {order_count} 单 / {row_count} 行')
    print(f'💰 含税总金额: ¥{grand_total:,.2f}')
    print(f'🧾 税额合计: ¥{grand_tax:,.2f}')

    output = {
        'title': title,
        'headers': HEADERS,
        'data': data_rows,
        'summary': {
            'date': date_filter,
            'order_count': order_count,
            'row_count': row_count,
            'grand_total': grand_total,
            'grand_tax': grand_tax
        }
    }

    json_path = f'{SCRIPT_DIR}/output/sale_order_result.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'📄 数据已保存: {json_path}')
    print('下一步: 调用 feishu_sheet create 创建表格，然后 write 写入数据')


if __name__ == '__main__':
    main()
