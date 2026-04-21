#!/usr/bin/env python3
"""
查询库存现存量数据，直接写入飞书电子表格

用法:
    python3 query_stock_to_sheet.py
    python3 query_stock_to_sheet.py --warehouse 仓库名称
    python3 query_stock_to_sheet.py --sku SKU编码

输出:
    - 飞书表格链接
    - 库存统计（行数/现存量合计/可用量合计）
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = str(Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)
from ys_client import YonSuiteClient


# 13列标准表头（含批次号）
HEADERS = [
    '物料编码', '物料名称', 'SKU编码', 'SKU名称',
    '仓库编码', '仓库名称', '库存组织', '单位编码', '单位名称',
    '现存量', '可用量', '批次号', '库存状态',
]


def query_and_format(warehouse: str = None, sku: str = None):
    """查询并格式化库存数据"""
    client = YonSuiteClient()
    result = client.query_current_stock(page_size=500)

    # 库存 API 返回：result['data'] 直接是 list
    raw_data = result.get('data', [])
    records = raw_data if isinstance(raw_data, list) else []

    if not records:
        print('⚠️  未找到库存数据')
        return None, None, None, None

    # 过滤
    if warehouse:
        records = [r for r in records if warehouse in str(r.get('warehouse_name', ''))]
    if sku:
        records = [r for r in records if sku in str(r.get('productsku_code', ''))]

    if not records:
        print(f'⚠️  未找到匹配的库存数据（仓库={warehouse}, SKU={sku}）')
        return None, None, None, None

    # ============================================================
    # 核心逻辑：按 仓库+SKU 聚合，但 SKU 为空时按 仓库+物料编码 聚合
    # （API 可能返回多条同物料不同批号的记录，需按此规则合并）
    # ============================================================
    aggregated = defaultdict(lambda: {
        'product_code': '',
        'product_name': '',
        'productsku_code': '',
        'productsku_name': '',
        'warehouse_code': '',
        'warehouse_name': '',
        'org_name': '',
        'unit_code': '',
        'unit_name': '',
        'current_qty': 0.0,
        'available_qty': 0.0,
        'batchno': '',
        'status': '合格',
    })

    for r in records:
        sku_code = str(r.get('productsku_code', '') or '').strip()
        mat_code = str(r.get('product_code', '') or '').strip()
        wh_code = str(r.get('warehouse_code', '') or '').strip()
        wh_name = str(r.get('warehouse_name', '') or '').strip()

        # 决定聚合 key：SKU 优先，否则用物料编码
        if sku_code:
            agg_key = (wh_name, sku_code)
        else:
            agg_key = (wh_name, mat_code)

        entry = aggregated[agg_key]

        # 只在首次写入时填充字段（同一 key 的多条记录字段值相同）
        if entry['productsku_code'] == '':
            entry['product_code'] = mat_code
            entry['product_name'] = str(r.get('product_name', '') or '')
            entry['productsku_code'] = sku_code if sku_code else '(无SKU)'
            entry['productsku_name'] = str(r.get('productsku_name', '') or '')
            entry['warehouse_code'] = wh_code
            entry['warehouse_name'] = wh_name
            entry['org_name'] = str(r.get('org_name', '') or '')
            entry['unit_code'] = str(r.get('product_unitCode', '') or '')
            entry['unit_name'] = str(r.get('product_unitName', '') or '')
            entry['status'] = str(r.get('stockStatusDoc_statusName', '') or '合格')
            entry['batchno'] = str(r.get('batchno', '') or '')

        entry['current_qty'] += float(r.get('currentqty', 0) or 0)
        entry['available_qty'] += float(r.get('availableqty', 0) or 0)

    # 转换为输出格式
    data_rows = []
    grand_current = 0.0
    grand_available = 0.0

    for key, entry in sorted(aggregated.items()):
        grand_current += entry['current_qty']
        grand_available += entry['available_qty']

        data_rows.append([
            entry['product_code'],          # 物料编码
            entry['product_name'],          # 物料名称
            entry['productsku_code'],       # SKU编码
            entry['productsku_name'],       # SKU名称
            entry['warehouse_code'],        # 仓库编码
            entry['warehouse_name'],        # 仓库名称
            entry['org_name'],             # 库存组织
            entry['unit_code'],             # 单位编码
            entry['unit_name'],            # 单位名称
            round(entry['current_qty'], 2),   # 现存量
            round(entry['available_qty'], 2), # 可用量
            entry['batchno'],               # 批次号
            entry['status'],               # 库存状态
        ])

    # 合计行
    data_rows.append([
        '合计', '', '', '', '', '', '', '', '', '',
        round(grand_current, 2),
        round(grand_available, 2),
        '', ''
    ])

    return data_rows, len(aggregated), grand_current, grand_available


def main():
    parser = argparse.ArgumentParser(description='查询库存现存量并写入飞书表格')
    parser.add_argument('--warehouse', help='仓库名称（模糊匹配）')
    parser.add_argument('--sku', help='SKU编码（模糊匹配）')
    parser.add_argument('--title', help='飞书表格标题')
    args = parser.parse_args()

    warehouse = args.warehouse
    sku = args.sku
    title = args.title or '库存查询'

    filter_desc = []
    if warehouse:
        filter_desc.append(f'仓库={warehouse}')
    if sku:
        filter_desc.append(f'SKU={sku}')
    filter_str = ' / '.join(filter_desc) if filter_desc else '全部'
    print(f'📦 查询条件: {filter_str}')

    result = query_and_format(warehouse=warehouse, sku=sku)
    if result[0] is None:
        sys.exit(1)

    data_rows, row_count, grand_current, grand_available = result

    print(f'✅ 查询完成: {row_count} 条（已按仓库+SKU聚合）')
    print(f'📦 现存量合计: {grand_current:,.2f}')
    print(f'🔓 可用量合计: {grand_available:,.2f}')
    print()
    print(f'表头({len(HEADERS)}列): {HEADERS}')
    print(f'数据({len(data_rows)}行): 前3行预览')
    for row in data_rows[:3]:
        print(f'  {row[:5]}...')

    # 输出 JSON
    output = {
        'title': title,
        'headers': HEADERS,
        'data': data_rows,
        'summary': {
            'warehouse': warehouse,
            'sku': sku,
            'row_count': row_count,
            'grand_current': grand_current,
            'grand_available': grand_available,
        }
    }

    out_dir = f'{SCRIPT_DIR}/output'
    import os
    os.makedirs(out_dir, exist_ok=True)
    json_path = f'{out_dir}/stock_result.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n📄 数据已保存: {json_path}')
    print('下一步: 调用 feishu_sheet create 创建表格，然后 write 写入数据')


if __name__ == '__main__':
    main()
