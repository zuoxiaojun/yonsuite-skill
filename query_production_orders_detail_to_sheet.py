#!/usr/bin/env python3
"""
查询指定日期的生产订单（通过详情接口），直接写入飞书电子表格

详情接口：/yonbip/mfg/productionorder/batchGet
特点：一主多子结构，每个订单返回一个嵌套的 orderProduct[] 数组

用法:
    python3 query_production_orders_detail_to_sheet.py 2026-04    # 查整月
    python3 query_production_orders_detail_to_sheet.py 2026-04-03 # 查某日
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
    '2': '已审批',
}
STOCK_STATUS_MAP = {
    0: '未入库',
    1: '部分入库',
    2: '全部入库',
}
FINISH_STATUS_MAP = {
    0: '未申请',
    1: '已申请',
    2: '已审批',
}
MATERIAL_STATUS_MAP = {
    0: '未领料',
    1: '部分领料',
    2: '已领料',
}
HOLD_MAP = {
    False: '正常',
    True: '挂起',
    'false': '正常',
    'true': '挂起',
}

# 24列标准表头
HEADERS = [
    '单据编号', '工厂', '交易类型', '单据日期', '创建时间',
    '创建人', '审核时间', '审批状态', '订单状态', '生产部门',
    '行号', '物料编码', '物料名称', '生产数量', '主计量',
    '生产件数', '已完工数量', '累计入库数量', '开工日期', '完工日期',
    '入库状态', '完工申报状态', '领料状态', '挂起状态',
]


def fmt_date(v):
    if not v:
        return ''
    v = str(v)
    return v[:10] if ' ' in v else v


def fmt_str(v, default=''):
    return str(v) if v else default


def query_and_format(date_filter: str):
    """通过详情接口查询并格式化生产订单数据"""
    client = YonSuiteClient()
    
    # Step 1: 先用列表接口获取所有订单（用于过滤日期）
    list_result = client.query_production_orders(page_size=500)
    all_records = list_result.get('data', {}).get('recordList', [])
    
    # 按日期过滤
    if len(date_filter) == 7:  # YYYY-MM
        filtered = [r for r in all_records if str(r.get('vouchdate', '')).startswith(date_filter)]
    else:  # YYYY-MM-DD
        filtered = [r for r in all_records if str(r.get('vouchdate', '')).startswith(date_filter)]
    
    if not filtered:
        print(f'⚠️  未找到 {date_filter} 的生产订单数据')
        return None, None, None, None
    
    # Step 2: 提取每个订单的 id（去重）
    order_ids = list({r.get('id') or r.get('orderProduct_id', '') for r in filtered})
    order_ids = [oid for oid in order_ids if oid]
    print(f'📦 共 {len(order_ids)} 个订单待查详情')
    
    # Step 3: 逐个调用详情接口
    all_order_details = []
    for i, oid in enumerate(order_ids, 1):
        try:
            detail = client.get_production_order_detail(str(oid))
            data = detail.get('data')
            if data:
                all_order_details.append(data)
            print(f'  [{i}/{len(order_ids)}] {oid}: OK')
        except Exception as e:
            print(f'  [{i}/{len(order_ids)}] {oid}: FAIL - {e}')
    
    # Step 4: 再次按日期过滤（detail接口没有vouchdate在顶层）
    # 用之前 filtered 的 code 集合做过滤
    valid_codes = {r.get('code') for r in filtered}
    all_order_details = [o for o in all_order_details if o.get('code') in valid_codes]
    
    # Step 5: 扁平化：一行 = 一个 orderProduct
    data_rows = []
    grand_qty = 0.0
    order_count = len(all_order_details)
    row_count = 0
    
    for order in all_order_details:
        code = order.get('code', '')
        order_products = order.get('orderProduct', [])
        
        for op in order_products:
            row_count += 1
            planned_qty = float(op.get('quantity') or 0)
            completed_qty = float(op.get('completedQuantity') or 0)
            incoming_qty = float(op.get('cfmIncomingQty') or op.get('incomingQuantity') or 0)
            grand_qty += planned_qty
            
            data_rows.append([
                fmt_str(code),                                  # 1 单据编号
                fmt_str(op.get('orgName')),                    # 2 工厂
                fmt_str(order.get('transTypeName')),            # 3 交易类型
                fmt_date(order.get('vouchdate')),              # 4 单据日期
                fmt_date(order.get('createTime')),             # 5 创建时间
                fmt_str(order.get('creator')),                 # 6 创建人
                fmt_date(order.get('auditTime')),              # 7 审核时间
                VERIFY_MAP.get(str(order.get('verifystate', '')), ''),  # 8 审批状态
                STATUS_MAP.get(str(order.get('status', '')), ''),  # 9 订单状态
                fmt_str(order.get('departmentName')),          # 10 生产部门
                int(float(op.get('lineNo') or 0)),            # 11 行号
                fmt_str(op.get('productCode')),               # 12 物料编码
                fmt_str(op.get('productName')),               # 13 物料名称
                round(planned_qty, 2),                       # 14 生产数量
                fmt_str(op.get('mainUnitName')),              # 15 主计量
                float(op.get('auxiliaryQuantity') or 0),      # 16 生产件数
                round(completed_qty, 2),                     # 17 已完工数量
                round(incoming_qty, 2),                      # 18 累计入库数量
                fmt_date(op.get('startDate')),               # 19 开工日期
                fmt_date(op.get('finishDate')),               # 20 完工日期
                STOCK_STATUS_MAP.get(int(op.get('stockStatus') or 0), '未入库'),  # 21 入库状态
                FINISH_STATUS_MAP.get(int(op.get('finishedWorkApplyStatus') or 0), '未申请'),  # 22 完工申报状态
                MATERIAL_STATUS_MAP.get(int(op.get('materialStatus') or 0), '未领料'),  # 23 领料状态
                HOLD_MAP.get(str(op.get('isHold')), '正常'),  # 24 挂起状态
            ])
    
    # 合计行
    data_rows.append([
        '合计', '', '', '', '', '', '', '', '', '',
        '', '', '', round(grand_qty, 2), '', '',
        '', '', '', '', '', '', '', '', ''
    ])
    
    return data_rows, order_count, row_count, grand_qty


def main():
    parser = argparse.ArgumentParser(description='通过详情接口查询生产订单并写入飞书表格')
    parser.add_argument('date', help='日期，如 2026-04-01 或 2026-04')
    parser.add_argument('--title', help='飞书表格标题，默认按日期生成')
    args = parser.parse_args()
    
    date_filter = args.date
    title = args.title or f'生产订单详情_{date_filter}'
    
    print(f'📅 查询日期: {date_filter}')
    print(f'🔍 使用详情接口: /yonbip/mfg/productionorder/batchGet')
    
    result = query_and_format(date_filter)
    if result[0] is None:
        sys.exit(1)
    
    data_rows, order_count, row_count, grand_qty = result
    
    print(f'✅ 查询完成: {order_count} 单 / {row_count} 行')
    print(f'🏭 生产数量合计: {grand_qty:,.2f}')
    print(f'表头({len(HEADERS)}列): {HEADERS}')
    print(f'数据({len(data_rows)}行): 前3行预览')
    for row in data_rows[:3]:
        print(f'  {row[:6]}...')
    
    # 输出 JSON
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
    
    json_path = f'{SCRIPT_DIR}/output/production_order_detail_result.json'
    import os
    os.makedirs(f'{SCRIPT_DIR}/output', exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\n📄 数据已保存: {json_path}')
    print('下一步: 调用 feishu_sheet create 创建表格，然后 write 写入数据')


if __name__ == '__main__':
    main()
