#!/usr/bin/env python3
"""
查询指定日期的生产订单，直接写入飞书电子表格

用法:
    python3 query_production_orders_to_sheet.py 2026-04-01
    python3 query_production_orders_to_sheet.py 2026-04    # 查整月

输出:
    - 飞书表格链接
    - 订单统计（单数/行数/生产数量合计）
"""

import sys
import json
import argparse
from collections import defaultdict

from pathlib import Path
SCRIPT_DIR = str(Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)
from ys_client import YonSuiteClient


# ---------- 状态映射 ----------
STATUS_MAP = {
    '0': '开立',
    '1': '已审核',
    '2': '已关闭',
    '3': '审核中',
    '4': '已锁定',
    '5': '已开工',
    '6': '生产完工',
}
VERIFY_MAP = {
    '0': '待审批',
    '1': '已审批',
}
STOCK_STATUS_MAP = {
    '0': '未入库',
    '1': '部分入库',
    '2': '全部入库',
}
FINISH_STATUS_MAP = {
    '0': '未申请',
    '1': '已申请',
    '2': '已审批',
}
MATERIAL_STATUS_MAP = {
    '0': '未领料',
    '1': '部分领料',
    '2': '已领料',
}
HOLD_MAP = {
    '0': '正常',
    '1': '挂起',
}

# 24列标准表头（SKU编码/SKU名称/自由项特征组已移除）
HEADERS = [
    '单据编号', '工厂', '交易类型', '单据日期', '创建时间',
    '创建人', '审核时间', '审批状态', '订单状态', '生产部门',
    '行号', '物料编码', '物料名称', '生产数量', '主计量',
    '生产件数', '已完工数量', '累计入库数量', '开工日期',
    '完工日期', '入库状态', '完工申报状态', '领料状态', '挂起状态',
]


def get_op(r, key, default=None):
    """从 OrderProduct_* 前缀获取嵌套数据"""
    return r.get(f'OrderProduct_{key}', default)


def query_and_format(date_filter: str):
    """查询并格式化生产订单数据"""
    client = YonSuiteClient()
    result = client.query_production_orders(page_size=500)
    records = result.get('data', {}).get('recordList', [])

    # 按日期过滤（支持 YYYY-MM-DD 或 YYYY-MM）
    if len(date_filter) == 7:  # YYYY-MM
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]
    else:  # YYYY-MM-DD
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]

    if not filtered:
        print(f'⚠️  未找到 {date_filter} 的生产订单数据')
        return None, None, None, None

    # 按订单编号分组
    by_code = defaultdict(list)
    for o in filtered:
        by_code[o.get('code', '')].append(o)

    data_rows = []
    grand_qty = 0.0
    order_count = len(by_code)
    row_count = 0

    for code in sorted(by_code.keys()):
        rows = by_code[code]
        first = rows[0]

        for r in rows:
            row_count += 1
            planned_qty = float(get_op(r, 'quantity') or 0)
            completed_qty = float(get_op(r, 'completedQuantity') or 0)
            incoming_qty = float(get_op(r, 'incomingQuantity') or 0) or float(r.get('cfmIncomingQty', 0) or 0)

            grand_qty += planned_qty

            # 自由项特征组
            def fmt_date(v):
                if not v:
                    return ''
                v = str(v)
                return v[:10] if ' ' in v else v

            def fmt_str(v, default=''):
                return str(v) if v else default

            data_rows.append([
                fmt_str(code),                                 # 1 单据编号
                fmt_str(get_op(r, 'orgName')) or fmt_str(r.get('orgName')),  # 2 工厂
                fmt_str(first.get('transTypeName')),           # 3 交易类型
                fmt_date(first.get('vouchdate')),             # 4 单据日期
                fmt_date(first.get('createTime')),            # 5 创建时间
                fmt_str(first.get('creator')),                 # 6 创建人
                fmt_date(first.get('auditTime')),              # 7 审核时间
                VERIFY_MAP.get(str(first.get('verifystate', '')), ''),  # 8 审批状态
                STATUS_MAP.get(str(first.get('status', '')), ''),  # 9 订单状态
                fmt_str(first.get('departmentName')),           # 10 生产部门
                int(float(get_op(r, 'lineNo') or 0)),          # 11 行号
                fmt_str(get_op(r, 'productCode')),             # 12 物料编码（API可能null）
                fmt_str(get_op(r, 'productName')),             # 13 物料名称（API可能null）
                round(planned_qty, 2),                        # 14 生产数量
                fmt_str(get_op(r, 'mainUnitName')),           # 15 主计量
                float(get_op(r, 'auxiliaryQuantity') or 0),   # 16 生产件数
                round(completed_qty, 2),                      # 17 已完工数量
                round(incoming_qty, 2),                       # 18 累计入库数量
                fmt_date(get_op(r, 'startDate')),             # 19 开工日期
                fmt_date(get_op(r, 'finishDate')),            # 20 完工日期
                STOCK_STATUS_MAP.get(str(get_op(r, 'stockStatus') or '0'), '未入库'),  # 21 入库状态
                FINISH_STATUS_MAP.get(str(get_op(r, 'finishedWorkApplyStatus') or '0'), '未申请'),  # 22 完工申报状态
                MATERIAL_STATUS_MAP.get(str(get_op(r, 'materialStatus') or '0'), '未领料'),  # 23 领料状态
                HOLD_MAP.get(str(get_op(r, 'isHold') or '0'), '正常'),  # 24 挂起状态
            ])

    # 合计行
    data_rows.append([
        '合计', '', '', '', '', '', '', '', '', '',
        '', '', '', '', '', '',
        round(grand_qty, 2), '', '',
        '', '', '', '', '', '', '', ''
    ])

    return data_rows, order_count, row_count, grand_qty


def main():
    parser = argparse.ArgumentParser(description='查询生产订单并写入飞书表格')
    parser.add_argument('date', help='日期，如 2026-04-01 或 2026-04')
    parser.add_argument('--title', help='飞书表格标题，默认按日期生成')
    args = parser.parse_args()

    date_filter = args.date
    title = args.title or f'生产订单_{date_filter}'

    print(f'📅 查询日期: {date_filter}')

    result = query_and_format(date_filter)
    if result[0] is None:
        sys.exit(1)

    data_rows, order_count, row_count, grand_qty = result

    print(f'✅ 查询完成: {order_count} 单 / {row_count} 行')
    print(f'🏭 生产数量合计: {grand_qty:,.2f}')
    print()
    print(f'表头({len(HEADERS)}列): {HEADERS}')
    print(f'数据({len(data_rows)}行): 前3行预览')
    for row in data_rows[:3]:
        print(f'  {row[:6]}...')

    # 输出 JSON 供 feishu_sheet 工具使用
    output = {
        'title': title,
        'headers': HEADERS,
        'data': data_rows,
        'summary': {
            'date': date_filter,
            'order_count': order_count,
            'row_count': row_count,
            'grand_qty': grand_qty,
        }
    }

    json_path = f'{SCRIPT_DIR}/output/production_order_result.json'
    import os
    os.makedirs(f'{SCRIPT_DIR}/output', exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n📄 数据已保存: {json_path}')
    print('下一步: 调用 feishu_sheet create 创建表格，然后 write 写入数据')


if __name__ == '__main__':
    main()
