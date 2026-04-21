#!/usr/bin/env python3
"""
查询指定日期的采购订单，直接写入飞书电子表格

用法:
    python3 query_purchase_orders_to_sheet.py 2026-04-01
    python3 query_purchase_orders_to_sheet.py 2026-04    # 查整月

输出:
    - 飞书表格链接
    - 订单统计（单数/行数/含税总金额/税额合计）
"""

import sys
import json
import argparse
from collections import defaultdict

# 飞书 API 相关（通过 HTTP 请求实现，避免额外依赖）
# feishu_sheet 工具负责写入，这里只生成数据

# ---------- YonSuite 客户端 ----------
from pathlib import Path
SCRIPT_DIR = str(Path(__file__).parent)
sys.path.insert(0, SCRIPT_DIR)
from ys_client import YonSuiteClient


# ---------- 字段映射 ----------
STATUS_MAP = {'0': '开立', '1': '已审核', '2': '已关闭', '3': '审核中'}
ARRIVED_MAP = {'1': '到货完成', '2': '未到货', '3': '部分到货', '4': '到货完成'}
INWH_MAP = {'1': '入库完成', '2': '未入库', '3': '部分入库', '4': '入库结束'}
INVOICE_MAP = {'1': '开票完成', '2': '未开票', '3': '部分开票', '4': '开票结束'}

# 28列标准表头
HEADERS = [
    '订单编号', '采购组织', '交易类型', '供货供应商', '开票供应商',
    '单据日期', '创建人', '采购部门', '采购员', '单据状态',
    '行号', '物料编码', '物料名称', '采购数量', '单位',
    '含税单价', '含税金额', '税率', '税额',
    '计划到货日期', '收货组织', '收票组织',
    '累计到货数量', '累计入库数量', '累计开票数量',
    '到货状态', '入库状态', '发票状态',
    '汇率', '流程名称', '币种', '本币'
]


def query_and_format(date_filter: str):
    """查询并格式化采购订单数据"""
    client = YonSuiteClient()
    result = client.query_purchase_orders(page_size=500)
    records = result.get('data', {}).get('recordList', [])

    # 按日期过滤（支持 YYYY-MM-DD 或 YYYY-MM）
    if len(date_filter) == 7:  # YYYY-MM
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]
    else:  # YYYY-MM-DD
        filtered = [r for r in records if str(r.get('vouchdate', '')).startswith(date_filter)]

    if not filtered:
        print(f'⚠️  未找到 {date_filter} 的采购订单数据')
        return None, None, None, None

    # 按订单编号分组
    by_code = defaultdict(list)
    for o in filtered:
        by_code[o.get('code', '')].append(o)

    data_rows = []
    grand_total = 0.0
    grand_tax = 0.0

    for code in sorted(by_code.keys()):
        rows = by_code[code]
        first = rows[0]
        creator = first.get('creator', '') or ''
        dept = first.get('department_name', '') or ''
        operator = first.get('operator_name', '') or creator

        for r in rows:
            lineno = int(r.get('lineno', 0) or 0)
            plan_d = str(r.get('planArrivalDate', ''))[:10] \
                if r.get('planArrivalDate') and str(r.get('planArrivalDate')) != 'None' else ''

            # 行级金额累加到合计
            row_sum = float(r.get('listOriSum', 0) or 0)
            row_tax = float(r.get('listOriTax', 0) or 0)
            grand_total += row_sum
            grand_tax += row_tax

            data_rows.append([
                code,                                       # 订单编号
                first.get('demandOrg_name', ''),           # 采购组织
                first.get('bustype_name', ''),             # 交易类型
                first.get('vendor_name', ''),               # 供货供应商
                first.get('invoiceVendor_name', ''),        # 开票供应商
                r.get('vouchdate', '')[:10],              # 单据日期
                creator,                                    # 创建人
                dept,                                       # 采购部门
                operator,                                   # 采购员
                STATUS_MAP.get(str(first.get('status', '')), ''),  # 单据状态
                lineno,                                     # 行号
                r.get('product_cCode', ''),               # 物料编码
                r.get('product_cName', ''),               # 物料名称
                r.get('subQty', 0),                        # 采购数量
                r.get('unit_name', ''),                    # 单位
                r.get('oriTaxUnitPrice', 0),              # 含税单价
                r.get('listOriSum', 0),               # 含税金额（行级）
                str(r.get('listTaxRate', '')),              # 税率
                r.get('listOriTax', 0),                   # 税额（行级）
                plan_d,                                    # 计划到货日期
                r.get('inOrg_name', ''),                  # 收货组织
                r.get('inInvoiceOrg_name', ''),           # 收票组织
                r.get('purchaseOrders_totalConfirmInQty', 0) or 0,  # 累计到货数量
                r.get('purchaseOrders_totalInSubqty', 0) or 0,    # 累计入库数量
                r.get('purchaseOrders_totalInvoiceQty', 0) or 0,   # 累计开票数量
                ARRIVED_MAP.get(str(r.get('purchaseOrders_arrivedStatus', '')), '未知'),  # 到货状态
                INWH_MAP.get(str(r.get('purchaseOrders_inWHStatus', '')), '未知'),      # 入库状态
                INVOICE_MAP.get(str(r.get('purchaseOrders_invoiceStatus', '')), '未知'),  # 发票状态
                first.get('exchRate', ''),                # 汇率
                first.get('bizFlow_name', ''),            # 流程名称
                first.get('currency_name', ''),           # 币种
                first.get('natCurrency_name', ''),        # 本币
            ])

    # 合计行
    data_rows.append([
        '合计', '', '', '', '', '', '', '', '', '',
        '', '', '', '', '', '', grand_total, '', grand_tax,
        '', '', '', '', '', '', '', '', '',
        '', '', '', ''
    ])

    return data_rows, len(by_code), len(filtered), grand_total, grand_tax


def main():
    parser = argparse.ArgumentParser(description='查询采购订单并写入飞书表格')
    parser.add_argument('date', help='日期，如 2026-04-01 或 2026-04')
    parser.add_argument('--title', help='飞书表格标题，默认按日期生成')
    args = parser.parse_args()

    date_filter = args.date
    title = args.title or f'采购订单_{date_filter}'

    print(f'📅 查询日期: {date_filter}')

    result = query_and_format(date_filter)
    if result[0] is None:
        sys.exit(1)

    data_rows, order_count, row_count, grand_total, grand_tax = result

    print(f'✅ 查询完成: {order_count} 单 / {row_count} 行')
    print(f'💰 含税总金额: ¥{grand_total:,.2f}')
    print(f'🧾 税额合计: ¥{grand_tax:,.2f}')
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
            'grand_total': grand_total,
            'grand_tax': grand_tax
        }
    }

    json_path = f'{SCRIPT_DIR}/output/purchase_order_result.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n📄 数据已保存: {json_path}')
    print('下一步: 调用 feishu_sheet create 创建表格，然后 write 写入数据')


if __name__ == '__main__':
    main()
