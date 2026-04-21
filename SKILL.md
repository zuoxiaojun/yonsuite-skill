---
name: yonsuite-skill
title: yonsuite-skill
description: YS系统业务数据查询技能（销售/采购/生产订单、库存、分析报表）
---

# yonsuite-skill - 用友 YonSuite 系统综合技能

**定位：** YS 系统业务数据查询 + 分析报表生成，支持销售/采购/生产订单、库存、客户、供应商等核心模块。

**版本：** v5.10（2026-04-21 修复：CRM商机字段名全部更新为 camelCase 实测版；v5.9 优化：data-analysis 强制加载流程 + 新增 metric-contracts.md 到必读清单；2026-04-21 新增：CRM商机查询模块 + Opportunity模型）

---

## ⚡ 执行前强制确认（不做这步 = 白干）

> **每次接到 YS 相关任务，必须先完成以下确认，再动手查数据。**

| 序号 | 问题 | 判断标准 | 下一步 |
|------|------|---------|--------|
| 1 | 用户指的是哪种？ | 「飞书任务」→ lark-cli task<br>「YS业务单据状态」→ query_*_orders 脚本<br>「YS待办中心/审批」→ client.query_user_todos() | 确认后才能继续 |
| 2 | 要不要生成 HTML？ | **是**，YS待办和分析报表的 HTML 是默认输出格式，<br>**不是**等用户说了才做 | 走本节 HTML 规范 |
| 3 | 要不要分析洞察？ | 分析类任务（销售/采购/生产报表）<br>→ 必须调用 data-analysis skill，**禁止 LLM 直接推理** | 走第366行强制流程 |

**⚠️ 跳过这几步被公子抓到的后果：重做 + 记录到本次复盘。**

---

## ⚠️ 重要澄清："YS待办"与飞书任务的区别

用户问"YS待办"时，必须先确认是指什么：

| 类型 | 查询方式 | 说明 |
|------|---------|------|
| **飞书任务中心** | `lark-cli task +get-my-tasks --complete=false` | 飞书原生待办/任务，存储在飞书任务系统 |
| **YS业务单据状态** | `query_*_orders` 脚本 + 状态过滤 | YS里的生产/采购/销售订单状态（如"待发货""已开工"），**不是**飞书任务 |
| **YS待办中心** | `client.query_user_todos()` | YS系统内的审批/待办任务，如销售订单审批、报销单、项目活动通知等 |

**查询 YS 待办中心：**
```python
# ⚠️ 执行前必读上方 Checklist 第1行 — 确认用户指的是YS待办中心，不是飞书任务或业务单据
# ⚠️ HTML 是默认输出 — 本节结束后请生成 HTML（见第107行规范），不是可选项
import sys, re
sys.path.insert(0, '/Users/zuoxiaojun/.hermes/skills/yonsuite-skill')
from ys_client import YonSuiteClient
client = YonSuiteClient()
result = client.query_user_todos(page_no=1, page_size=50)  # 返回 dict，含 data[]
items = result['data']  # 接口只返回待处理（doneStatus==0），无法获取已处理数据

# 清洗 richText 富文本（去除 HTML 标签）
for item in items:
    if item.get('richText'):
        item['richText'] = re.sub(r'<[^>]+>', '', item['richText']).strip()
```

**⚠️ 重要：接口只返回待处理数据。** `doneStatus==0` 为待处理，`doneStatus==1` 为已处理，但接口默认只返回待处理数据，不返回已处理数据。

**approveSource → 单据类型映射：**
```python
mapping = {
    'SCMSA': '销售订单',
    'SACT':  '销售合同',
    'RBSM':  '报销单',
    'PGRM':  '项目管理',
}
if '项目活动' in title:
    label = '项目活动'
```

**⚠️ approveSource 字段不是所有待办都有（重要 Gotcha）**

接口返回的待办中，`approveSource` 字段**并非所有记录都有**。实测发现：

| 待办类型 | approveSource | 判断方式 |
|---------|--------------|---------|
| 销售订单/报销单/销售合同 | ✅ 有（如 SCMSA、SACT、RBSM） | 用 `approveSource` 映射 |
| **iKM** | ❌ 没有 | 用 `typeName == 'iKM'` 或 `title contains 'iKM'` |

**正确的类型判断函数：**
```python
# ⚠️ approveSource 不是所有待办都有 — iKM类型无此字段，必须用 typeName 或 title 判断
def get_type_label(item):
    src = item.get('approveSource', '')
    title = item.get('title', '')
    type_name = item.get('typeName', '')
    if type_name == 'iKM' or 'iKM' in title:
        return 'iKM知识申请'
    if src in mapping:
        return mapping[src]
    sc = item.get('serviceCode', '') or ''
    if 'expense' in sc or 'znbzbx' in sc:
        return '报销单'
    if 'order' in sc:
        return '销售订单'
    if 'salescontract' in sc:
        return '销售合同'
    return title or src  # 兜底
```

同时，`businessData.taskName` 在 iKM 类型中为空字符串，应在 UI 层做 `-` 展示。

**query_user_todos() 返回字段（实测）：**
| 字段 | 说明 |
|------|------|
| `title` | 待办标题，如"销售订单SO1001260410-077" |
| `content` | 文本内容，含发起人/时间/部门（制表符分隔） |
| `richText` | HTML格式富文本内容，需 `re.sub(r'<[^>]+>', ' ', text)` 清洗 |
| `doneStatus` | 0=待处理，1=已处理（接口只返回0） |
| `commitTsLong` | 提交时间（毫秒时间戳），`datetime.fromtimestamp(int(str(ts)[:10]))` |
| `commitUserName` | 提交人姓名 |
| `approveSource` | 审批来源系统，如 SCMSA/SACT/RBSM/PGRM |
| `businessData.taskName` | 当前审批环节名称，如"普通环节1" |
| `mUrl` | 手机端审批链接 |
| `webUrl` | PC端审批链接（HTML展示用这个） |
| `buttons` | 操作按钮列表，含 `callBackExecType`（agree/reject） |

**常见误区：** 用 `query_sale_orders` 查"待发货"订单后误以为找到了"待办"，实际上这是 YS 业务数据，与飞书任务中心无关。

**查询飞书任务中心的正确命令：**
```bash
lark-cli task +get-my-tasks --complete=false --page-all --format pretty
```

**待办 HTML 生成规范（YS待办专用）：**
- 风格：白底用友品牌风（`yonyou-html-presentation` skill 规范）
- **Logo：** 右上角放置用友 Logo（从 `yonsuite-skill/assets/logo/current-logo.png` 读取并 base64 嵌入 HTML）
- 右下角品牌位：仅文字 `YonSuite · 用友网络科技股份有限公司`，不放 Logo
- 顶部三色装饰线：`linear-gradient(90deg, #E60012, #FF6A00, #0071E3)`
- **不展示决策简报**，纯数据展示
- 布局：Hero区（标题+全部待办数+单据类型数）+ KPI卡片（**按单据类型直接计数**，不加混合分组如"销售订单+合同"）+ 分组明细表格
- 分组表格：每种单据类型一个分组，带红色数量标签，展开独立滚动表格
- 表格结构：**表头sticky固定 + 内容区独立滚动**（`max-height: 280px; overflow-y: auto`）
- 表头列及列宽：标题 200px | 环节 56px | 内容摘要 340px | 提交人 80px | 时间 140px | 链接 80px
- **必须用 `<colgroup>` 指定列宽**：`table-layout:fixed` 下 thead 和 tbody 是两个独立表格，仅靠 CSS `width` 无法同步列宽。正确做法是在 `<table>` 内加 `<colgroup><col style="width:200px"><col style="width:56px"><col style="width:340px"><col style="width:80px"><col style="width:140px"><col style="width:80px"></colgroup>`，thead 和 tbody 两个 table 都要加。
- **审批链接（webUrl）：** 直接用 `webUrl` 字段，点击蓝色按钮「审批」直接跳转审批页面（`<a href="{webUrl}" target="_blank" class="url-link">审批</a>`），不做 JS toggle 或展开隐藏
- ⚠️ **每次生成 HTML 前必须重新查询 API 获取真实 webUrl**：`client.query_user_todos()` 返回的 webUrl 是实时审批链接，旧数据/硬编码的链接会失效（ID 可能变化）
- 不展示"操作按钮"列（buttons字段），只展示 webUrl 链接

---

## ⚠️ 核心概念：主子表结构（必须理解）

所有三种订单（销售/采购/生产）均为**主子表结构**：

| 层级 | 说明 | 举例 |
|-----|------|-----|
| **主表**（每订单一条） | 订单头信息，字段值在每行重复 | `code`、`vouchdate`、`salesOrgId_name` |
| **明细表**（`orderDetails[]`） | 每行商品一条，字段值各行不同 | `skuCode`、`qty`、`oriSum` |

**重要规则：**
- `oriSum`（含税金额）、`oriTaxUnitPrice`（含税单价）在**明细行顶层**，无需进嵌套
- `oriTax`（税额）在明细行**返回 null**，需用公式计算：`税额 = 含税金额 ÷ (1 + 税率%) × 税率%`
- 币种在 `orderPrices.originalName`（嵌套），可能为 null

---

## ⚠️ 日期过滤（⚠️ 旧版 Bug，已修复，保留参考）

**历史问题（v4.2 之前）：** `date_from/date_to` 参数**不会传递给 API**，底层只排序不过滤，返回全量历史数据。

**症状：** 查询4月份数据，却返回2月、3月的历史订单（49条而非26条）。

**修复状态：** `v4.2+` 版本已在客户端层（`modules/sales.py`）正确将 `date_from/date_to` 传给 `simpleVOs + op:"between"`，**Bug 已修复**，可直接使用：
```python
result = client.query_sale_orders(page_index=1, page_size=500, isSum=True, date_from='2026-04-01', date_to='2026-04-30')
records = result['data']['recordList']
```

**旧版绕路（仅历史参考，不再需要）：**
如需自定义过滤条件，才用 `_http_post_raw`（见下）。

**⚠️ 采购订单日期过滤（重要 Gotcha）**

**`query_purchase_orders` 不支持 `date_from/date_to` 参数**，只支持 `page_index` + `page_size`。

如需按日期过滤采购订单，必须用 `client.purchase._http_post_raw`（不是 `client._http_post_raw`）：

```python
import sys, urllib.parse
sys.path.insert(0, '/Users/zuoxiaojun/.hermes/skills/yonsuite-skill')
from ys_client import YonSuiteClient
client = YonSuiteClient()
token = client.get_access_token()

body = {
    "pageIndex": 1, "pageSize": 500, "isSum": True,
    "simpleVOs": [{"field": "vouchdate", "op": "between", "value1": "2026-04-20", "value2": "2026-04-20"}],
    "queryOrders": [{"field": "vouchdate", "order": "desc"}]
}
# ⚠️ 必须用 client.purchase._http_post_raw，不能用 client._http_post_raw
# client._http_post_raw 不带 access_token，会返回 "access_token不能为空"
url = f"{client.purchase.gateway_url}{client.purchase.base_path}/list?access_token={urllib.parse.quote(token)}"
result = client.purchase._http_post_raw(url, body)
records = result['data']['recordList']
```

**销售/采购通用注意：** `op` 不是 `opt`；`value1`/`value2` 不是 `value`。

**踩坑记录：**

| 错误写法 | 原因 |
|---------|------|
| `{"field": "vouchdate", "opt": "ge", "value": "..."}` | 字段名错误，`opt` → `op` |
| `{"field": "vouchdate", "op": "ge", "value1": "..."}` | API 返回 506 错误 |
| `client._http_post_raw(url, body)` | 无 access_token，返回"access_token不能为空" |
| 采购订单用 `query_purchase_orders(date_from=...)` | 参数不支持，直接报错 |
| `{"field": "vouchdate", "op": "le", "value2": "..."}` | API 返回 506 错误 |
| **正确** `op: "between", value1 + value2` | ✅ |

**适用场景：** 销售订单、采购订单、生产订单（所有 list 接口格式相同）。

**验证方法：** 生成每日趋势图，看是否有其他月份的数据。有则说明过滤失败。
---

## 📋 标准输出流程（强制）

### 步骤一：选脚本

```bash
cd ~/.hermes/skills/yonsuite-skill
python3 query_sale_orders_to_sheet.py 2026-04      # 查整月
python3 query_sale_orders_to_sheet.py 2026-04-03   # 查某日
```

### 步骤二：字段检查

输出前先展示检查报告：

```
【字段检查】销售订单 应有 XX 字段
✅ 已返回：XX 字段  ❌ 缺失：XX 字段（列出名称）
```

有缺失时告知用户，由用户决定是补全还是接受缺字段版本。

### 步骤三：输出正文

**主子表卡片样式（强制）：**
- 每个订单一个卡片（标题：单据编号 + 审批日期 + 订单状态）
- 主表字段用 key-value 表格（2列或3列布局）
- 明细行独立表格，字段完整不遗漏
- 尾部加订单小计
- 底部加全量汇总

**输出格式**：双轨输出——
1. **聊天框内**直接展示主子表卡片样式（Markdown 格式）
2. **同步生成 HTML 页面**（白底用友品牌风），通过 execute_code 拼装 HTML 字符串，写入 `~/Documents/YS_YYYY-MM-DD_类型.html`，生成后用 terminal 执行 `open` 打开。

**HTML 页面规范（重要 — 必须参照已有模板）：**
> ⚠️ 禁止凭感觉写 HTML，必须先找已有正确文件做参照。
- 样式参考：`~/Documents/YS_2026-04-20_采购日报.html`（含最新浅红渐变 Hero 规范）
- **Hero 区风格（v5.6+）：** 浅红渐变背景（`#fff5f5 → #ffe8e8 → #fff0f0`），标题和数字用深红色（`#8B0000`），给数字加粗大字展示，配浅红色装饰圆，与 KPI 卡片红色边线呼应
- KPI 卡片：白底卡片，左侧 4px 彩色边线区分（红色=金额、橙色=审核/到货、绿色=完成/入库、蓝色=默认）
- 图表区：白底卡片，flex 横向排列，每行 2 个图表，圆角 10px
- 决策简报：白底卡片，顶边 4px 蓝色线，分区用 `<h4>` 标题，表格表头浅蓝底色
- 品牌位：底部通栏，灰色小字 `YonSuite · 用友网络科技股份有限公司`

**图表布局规范（强制）：**
- **每行放 2 个图表**，用 CSS `flex` 横向排列：`display: flex; gap: 14px;`
- 每个图表宽度 `calc(50% - 7px)`，高度统一 **260px**：`img { width: calc(50% - 7px); height: 260px; object-fit: contain; }`
- 4 个图表分 2 行排列，超过 2 个图表必须换行

**订单明细表格规范（强制）：**
- **列出全部订单**，不截断，数据再多也要全量展示
- 用 `max-height: 420px` + `overflow-y: auto` 实现纵向滚动条
- 滚动条样式：`::-webkit-scrollbar { width: 5px; }`，滚动条拖动 thumb 用圆角颜色
- 表格列：单据编号 | 日期 | 客户 | 部门 | 状态 | 含税金额 | 物料明细
- 金额列右对齐加粗高亮：`text-align: right; color: #1a4db8; font-weight: 600;`
- 状态用彩色 tag 样式区分（如已完成=绿、待发货=橙、开立=蓝）

- 使用图表 MCP 工具先生成图表图片（theme=academy）
- HTML 内嵌图表 URL（使用 mdn.alipayobjects.com CDN 图床）
- 配色：academy 主题色系，金额高亮 `#1a4db8`
- 响应式布局，图表每行 2 个，表格支持纵向滚动

## 文件发送规则（强制检查，不可跳过）
> ⚠️ 交付方式由消息来源决定，不是任务内容决定。
> ⚠️ **每次生成文件后，必须先确认发送渠道，再执行发送。**
- **飞书频道来的需求**（用户在飞书发消息）→ 生成 HTML 后直接 send_file 发飞书，**不本机 open**
- **本机会话**（CLI/Terminal）→ 生成 HTML 后 open 本机预览
- **确认方法**：查看当前会话上下文（source 字段），或直接查 Project Context 的 Source

**第六步（可选）：飞书表格**
如需 Excel/电子表格格式，建飞书电子表格（`feishu_sheet`），不用飞书文档

---

## 📊 分析报表流水线（YonSuite → 图表 → HTML → 飞书）

### 触发条件

分析用友YonSuite销售、采购或生产数据，生成可视化HTML报告。

### 支持模块

| 模块 | 查询脚本 | 输出文件 |
|------|---------|---------|
| 销售 | `python3 query_sale_orders_to_sheet.py YYYY-MM` | `sale_order_result.json` |
| 采购 | `python3 query_purchase_orders_to_sheet.py YYYY-MM` | `purchase_order_result.json` |
| 生产 | `python3 query_production_orders_to_sheet.py YYYY-MM` | `production_order_result.json` |

数据目录：`~/.hermes/skills/yonsuite-skill/output/`

### 数据结构（统一 dict 格式）

所有三种订单查询脚本输出的 JSON 均为统一 dict 格式，结构完全一致：
```python
{
    "title": "销售订单_2026-04",
    "headers": [...],           # 表头列表（30字段）
    "data": [row1, row2, ...], # 明细行列表，每行按headers索引
    "summary": {
        "date": "2026-04",
        "order_count": 23,
        "row_count": 33,
        "grand_total": 42162568.0,
        "grand_tax": 4821340.66
    }
}
```

**关键规则：**
- `data` 是**明细行列表**，一个物料一行，订单头字段在每行重复
- 过滤：`单据编号 == "合计"`（汇总行）→ 跳过
- 销售金额：索引 `headers.index("含税金额")`
- 税额：索引 `headers.index("表体税额")`，直接使用（脚本已处理）

### 图表生成（mcp-server-chart）

始终直接调用具体 generate 工具，**不使用** `list_resources`（该方法不存在）。

#### 通用图表工具
- `generate_line_chart` — time+value，每日趋势
- `generate_pie_chart` — category+value，innerRadius=0.4 设置环形图
- `generate_column_chart` — category+value，堆叠时 stack=true
- `generate_bar_chart` — category+value，水平条形
- `generate_dual_axes_chart` — 金额与税额对比，税额÷1,000,000 同步副轴

#### 销售报表典型图表
1. 每日销售趋势（line chart）
2. 客户销售分布（pie chart，Top6+其他）
3. 部门销售分布（column chart）
4. 订单状态分布（pie chart）
5. 产品销售TOP10（bar chart）
6. 每日销售额与税额对比（dual axes chart）

#### 采购报表典型图表
1. 每日采购趋势（line chart）
2. 供应商采购分布（pie chart，Top4+其他）
3. 物料采购TOP10（bar chart）
4. 到货状态分布（pie chart）
5. 入库与发票状态统计（column chart，group=false, stack=false）
6. 每日采购金额与税额对比（dual axes chart）

#### 生产报表典型图表
1. 每日生产趋势（line chart）
2. 工厂生产分布（pie chart）
3. 主要物料生产计划TOP10（bar chart）
4. 完工进度（pie chart：已完成/未完成）
5. 入库/领料状态统计（column chart）
6. 订单状态分布（pie chart）

### HTML报告关键要素
- KPI卡片：总订单数、总额/总产量、完成率/入库率
- 图表懒加载：`loading="lazy"`
- 主题：`academy`（蓝色系 #1783FF）
- 响应式：移动端适配
- 输出文件名：`~/Documents/本月销售分析报表_YYYY_MM.html`
- 浏览器自动打开：`open html_file`

**读取数据生成图表的方式：**
```python
with open('sale_order_result.json') as f:
    data = json.load(f)
headers = data['headers']
rows = data['data']
# 按订单号聚合 or 按日期聚合，用于图表数据
```

---

## ⚡ 强制规则：必须调用 data-analysis 技能（每次都执行）

**每次报告生成（查询数据 → 生成图表 → 组装HTML）流程中，必须包含统计分析步骤，结果写入 HTML「决策简报」区块。**

⚠️ **禁止直接用 LLM 推理输出"洞察"，必须经过以下数据分析流程。**

### 分析流程（强制步骤）

> ⚠️ **禁止凭记忆执行**：必须先 skill_view 加载 data-analysis，确认文件路径后再执行。

| 步骤 | 操作 | 完成 |
|------|------|------|
| 1 | 读 SKILL.md 本节，确认是分析类任务 | [ ] |
| 2 | skill_view(name='data-analysis') 加载 techniques.md + decision-briefs.md + metric-contracts.md | [ ] |
| 3 | Python 执行统计分析（HHI/IQR/漏斗/分段） | [ ] |
| 4 | 按 decision-briefs.md 格式输出 Decision Brief | [ ] |
| 5 | 将 Decision Brief 写入 HTML「决策简报」区块 | [ ] |

1. 读取 `~/.hermes/skills/yonsuite-skill/output/{sale,purchase,production}_order_result.json`
2. 加载 `data-analysis` 技能（`skill_view(name='data-analysis')` 加载 techniques.md + decision-briefs.md）
3. 用 Python 执行统计分析（不依赖 LLM 主观判断）：
   - **HHI 集中度指数**（客户/供应商/产品维度）：`sum(share²)`，>0.25 为高集中，>0.4 为极高集中，>0.8 为极度异常
   - **IQR 异常值检测**：日金额分布，超 Q3+1.5×IQR 标记异常
   - **漏斗转化分析**：订单状态按行数+金额分组
   - **分段对比**：部门均单、产品TOP5占比
4. 按 `decision-briefs.md` 的 **Decision Brief** 标准格式输出
5. 将 Decision Brief 内容写入 HTML 报告的「决策简报」区块
6. **HTML Logo 位置**：统一放在 Hero 区**右上角**（不用左上角）

### ⚠️ 已踩过的坑（必须避免重复）

| 问题 | 现象 | 正确做法 |
|------|------|---------|
| 跳过 data-analysis | 公子直接纠正要求重做 | 必须先 skill_view 加载再执行 |
| 税额字段数值异常 | JSON 中 `表体税额` 返回大整数，疑似字段映射错位 | 分析结论回避该字段，以含税金额 `payMoney` 为主 |
| 月度数据不完整 | 4月报表仅到16日，月末10天无数据 | 必须在「关键不确定性」中注明数据截止日期 |
| CRM `parse_opportunities` 报错 | API 返回 `code: "0"`（字符串），代码判断 `!= 200`（整数）报错 | `crm.py` 中改为 `str(code) not in ('200','0','成功','')` |
| `Opportunity` 字段全错 | `models.py` 的 `from_api` 用旧 snake_case 映射，`amount`/`salesman_name` 等全不对 | 按实测重写：camelCase 字段 + `expectSignMoney`/`winOrderMoney`/`ower_name` |
| 商机金额字段不是 `amount` | 文档写 `amount`，实际 API 不返回此字段 | 进行中用 `expectSignMoney`，赢单用 `winOrderMoney` |

### 分析维度速查

| 分析维度 | 方法 | 阈值/标准 |
|---------|------|---------|
| 客户集中度 | HHI 指数 | >0.25 高集中，>0.4 极高，>0.8 极度异常 |
| 日销售异常 | IQR | >Q3+1.5×IQR |
| 订单执行率 | 漏斗占比 | 已完成/总额 |
| 产品集中度 | TOP5 占比 | >80% 需关注 |

### 决策简报 HTML 模板

```html
<div class="brief">
  <div class="brief-header">📋 决策简报 · Decision Brief</div>
  <div class="brief-body">
    <p><strong>核心结论：</strong>（一句话概括）</p>
    <h4>🔴 [维度名]</h4>
    <table>…证据表格…</table>
    <h4>⚡ 建议下一步</h4>
    <table>…行动+原因+优先级…</table>
    <h4>📌 关键不确定性</h4>
    <ul>…caveats…</ul>
  </div>
</div>
```

---

## 📦 飞书文件发送（直调 OpenAPI）

**注意：** 文件发送走直调 OpenAPI，不走 `lark-cli --file`（后者有不同验证逻辑）。

```python
import requests, json

def get_tat():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": os.environ["FEISHU_APP_ID"], "app_secret": os.environ["FEISHU_APP_SECRET"]}
    )
    return resp.json()["tenant_access_token"]

tat = get_tat()
OPEN_ID = "ou_4d1693fbc72962bdea90835b0ba293e5"

def send_file(file_path, file_name, receive_id=OPEN_ID):
    with open(file_path, "rb") as f:
        upload_resp = requests.post(
            f"https://open.feishu.cn/open-apis/im/v1/files?receive_id_type=open_id",
            headers={"Authorization": f"Bearer {tat}"},
            data={"file_name": file_name, "file_type": "stream", "receive_id": receive_id},
            files={"file": (file_name, f, "application/octet-stream")}
        )
    file_key = upload_resp.json()["data"]["file_key"]
    msg_resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        headers={"Authorization": f"Bearer {tat}", "Content-Type": "application/json"},
        json={"receive_id": receive_id, "msg_type": "file", "content": json.dumps({"file_key": file_key})}
    )
    return msg_resp.json()

send_file("/path/to/report.html", "report.html")
```

**关键坑：**
- `receive_id_type` 在 URL query string，**不在 body**
- `file_type: "stream"` **不是** `"file"`（`"file"` 会触发 MIME 白名单校验失败）
- HTML 文件用 `application/octet-stream` 可正常发送

**发送决策规则：**
- 飞书频道来的需求 → send_file 发飞书
- 本机会话 → open 本机预览

---

### 分析类任务流程（替代方案）

当任务是**整体分析**（如"本年销售情况"、"客户维度分析"、"商品销售排行"）时，无需逐单输出，流程如下：

1. **isSum=True + date_from/date_to 拉全量数据** → 直接调用 `client.query_sale_orders(isSum=True, date_from='YYYY-MM-DD', date_to='YYYY-MM-DD')`
   > ⚠️ `date_from`/`date_to` 在 `v4.2+` 已修复（详见「日期过滤」章节），无需绕路。
2. **Python 聚合** → `defaultdict` 按客户、商品、月份分组聚合金额/数量
3. **生成图表** → 调用 `mcp-server-chart` 的 `generate_pie_chart` / `generate_bar_chart` / `generate_column_chart`
4. **拼装 HTML 报告** → `execute_code` 拼 HTML 字符串，写入 `~/Documents/YS_YYYY-MM-DD_分析类型.html`，用 `open` 打开
5. **聊天框内展示关键数据** → 数字+百分比+简短结论，不输出每一条明细

> 分析类任务不输出逐单明细，以汇总数据+图表为主。

> ⚠️ **isSum=True 时含税金额字段：** 汇总分析时用 `payMoney`（主表层字段，每订单一条），**不是** `oriSum`（明细行层字段，一订单多条）。`oriSum` 仅在 `isSum=False` 逐单明细时使用。

---

## 📦 销售订单 — 字段清单（29字段）

| # | 字段名 | API字段 | 说明 |
|---|-------|--------|------|
| 1 | 单据编号 | `code` | |
| 2 | 单据日期 | `vouchdate` | |
| 3 | 审批日期 | `auditDate` | |
| 4 | 销售组织 | `salesOrgId_name` | |
| 5 | 交易类型 | `transactionTypeId_name` | |
| 6 | 客户 | `agentId_name` | |
| 7 | 销售部门 | `saleDepartmentId_name` | |
| 8 | 销售业务员 | `corpContactUserName` | |
| 9 | 订单状态 | `nextStatus` | 见状态映射 |
| 10 | 行号 | `lineno` | |
| 11 | 物料编码 | `skuCode` | |
| 12 | 物料名称 | `skuName` | |
| 13 | 销售数量 | `qty` | |
| 14 | 销售单位 | `productUnitName` | |
| 15 | 数量 | `qty` | 主计量单位数量，同13 |
| 16 | 主计量 | `qtyName` | |
| 17 | 币种 | `orderPrices.originalName` | 可能为null |
| 18 | 含税成交价 | `oriTaxUnitPrice` | 明细行顶层字段 |
| 19 | 含税金额 | `oriSum` | 明细行顶层字段，不是嵌套 |
| 20 | 税率 | `taxRate` | |
| 21 | 表体税额 | 公式计算 | `oriTax`返回null，用公式 |
| 22 | 计划发货日期 | `sendDate` | |
| 23 | 库存组织 | `stockOrgId_name` | |
| 24 | 发货仓库 | `stockName` | 可能为null |
| 25 | 累计已发货数量 | `sendQty` | |
| 26 | 累计出库金额 | `totalOutStockOriMoney` | |
| 27 | 累计开票数量 | `invoiceQty` | |
| 28 | 累计开票含税金额 | `invoiceOriSum` | |
| 29 | 累计出库确认数量 | `totalOutStockQuantity` | |

**销售订单状态映射（`nextStatus`）：**
`CONFIRMORDER`=开立，`DELIVERY_PART`=部分发货，`DELIVERGOODS`=待发货，`TAKEDELIVERY`=待收货，`ENDORDER`=已完成，`OPPOSE`=已取消，`DELIVERY_TAKE_PART`=部分收货

---

## 📦 采购订单 — 字段清单（32字段）

| # | 字段名 | API字段 | 说明 |
|---|-------|--------|------|
| 1 | 订单编号 | `code` | |
| 2 | 采购组织 | `demandOrg_name` | |
| 3 | 交易类型 | `bustype_name` | |
| 4 | 供货供应商 | `vendor_name` | |
| 5 | 开票供应商 | `invoiceVendor_name` | |
| 6 | 单据日期 | `vouchdate` | |
| 7 | 创建人 | `creator` | |
| 8 | 采购部门 | `department_name` | |
| 9 | 采购员 | `operator_name` | |
| 10 | 单据状态 | `status` | 0=开立,1=已审核,2=已关闭,3=审核中 |
| 11 | 行号 | `lineno` | |
| 12 | 物料编码 | `product_cCode` | |
| 13 | 物料名称 | `product_cName` | |
| 14 | 采购数量 | `subQty` | |
| 15 | 单位 | `unit_name` | |
| 16 | 含税单价 | `oriTaxUnitPrice` | |
| 17 | 含税金额 | **不是** purchaseOrders_natSum，`listOriSum` | **行级含税金额**，不是 oriSum |
| 18 | 税率 | `listTaxRate` | 订单级税率 |
| 19 | 税额 | `listOriTax` | **行级税额**，不是 oriTax |
| 20 | 计划到货日期 | `planArrivalDate` | 列表接口可能为空 |
| 21 | 收货组织 | `inOrg_name` | |
| 22 | 收票组织 | `inInvoiceOrg_name` | |
| 23 | 累计到货数量 | `purchaseOrders_totalConfirmInQty` | |
| 24 | 累计入库数量 | `purchaseOrders_totalInSubqty` | |
| 25 | 累计开票数量 | `purchaseOrders_totalInvoiceQty` | 可能为空 |
| 26 | 到货状态 | `purchaseOrders_arrivedStatus` | 1:到货完成,2:未到货,3:部分到货,4:到货完成 |
| 27 | 入库状态 | `purchaseOrders_inWHStatus` | 1:入库完成,2:未入库,3:部分入库,4:入库结束 |
| 28 | 发票状态 | `purchaseOrders_invoiceStatus` | 1:开票完成,2:未开票,3:部分开票,4:开票结束 |
| 29 | 汇率 | `exchRate` | |
| 30 | 流程名称 | `bizFlow_name` | |
| 31 | 币种 | `currency_name` | |
| 32 | 本币 | `natCurrency_name` | |

---

## 📦 生产订单 — 字段清单（24字段）

> ⚠️ API 有时会额外返回 `物料SKU编码`、`物料SKU名称`、`自由项特征组` 三个字段（脚本默认已过滤），输出时不展示。

| # | 字段名 | API字段 | 说明 |
|---|-------|--------|------|
| 1 | 单据编号 | `code` | |
| 2 | 工厂 | `orgName`（OrderProduct层） | |
| 3 | 交易类型 | `transTypeName` | |
| 4 | 单据日期 | `vouchdate` | |
| 5 | 创建时间 | `createTime` | |
| 6 | 创建人 | `creator` | |
| 7 | 审核时间 | `auditTime` | |
| 8 | 审批状态 | `verifystate` | 0=待审批,1=已审批 |
| 9 | 订单状态 | `status` | 0=开立,1=已审核,2=已关闭,3=审核中,4=已锁定,5=已开工,6=生产完工 |
| 10 | 生产部门 | `departmentName` | |
| 11 | 行号 | `OrderProduct_lineno` | |
| 12 | 物料编码 | `OrderProduct_materialCode` | 实测有值（如A010400003） |
| 13 | 物料名称 | `OrderProduct_materialName` | 实测有值（如沙拉酱500g） |
| 14 | 生产数量 | `OrderProduct_quantity` | |
| 15 | 主计量 | `OrderProduct_mainUnitName` | |
| 16 | 生产件数 | `OrderProduct_auxiliaryQuantity` | |
| 17 | 已完工数量 | `OrderProduct_completedQuantity` | |
| 18 | 累计入库数量 | `OrderProduct_incomingQuantity` / `cfmIncomingQty` | |
| 19 | 开工日期 | `OrderProduct_startDate` | |
| 20 | 完工日期 | `OrderProduct_finishDate` | |
| 21 | 入库状态 | `OrderProduct_stockStatus` | 0=未入库,1=部分入库,2=全部入库 |
| 22 | 完工申报状态 | `OrderProduct_finishedWorkApplyStatus` | 0=未申请,1=已申请,2=已审批 |
| 23 | 领料状态 | `OrderProduct_materialStatus` | 0=未领料,1=部分领料,2=已领料 |
| 24 | 挂起状态 | `OrderProduct_isHold` | 0=正常,1=挂起 |

---

## 📦 库存查询 — 字段清单（13字段）

**显示顺序（推荐）：** 库存组织 → 仓库 → 物料编码 → 物料名称 → 计量单位 → 批次号 → 现存量 → 可用量 → 库存状态（共9个字段）

|| # | 字段名 | API字段 | 说明 |
||---|-------|--------|------|
|| 1 | 物料编码 | `product_code` | |
|| 2 | 物料名称 | `product_name` | |
|| 3 | SKU编码 | `productsku_code` | |
|| 4 | SKU名称 | `productsku_name` | |
|| 5 | 仓库编码 | `warehouse_code` | |
|| 6 | 仓库名称 | `warehouse_name` | |
|| 7 | 库存组织 | `org_name` | |
|| 8 | 单位编码 | `product_unitCode` | |
|| 9 | 单位名称 | `product_unitName` | |
|| 10 | 现存量 | `currentqty` | |
|| 11 | 可用量 | `availableqty` | |
|| 12 | 批次号 | `batchno` | 可能为空，API 可能返回同一物料多条批次记录 |
|| 13 | 库存状态 | `stockStatusDoc_statusName` | 默认为"合格" |

**注意：** `stockUnitId_code/name` 在 API 返回中可能为 null，统一用 `product_unitCode/name`。`updatetime` 字段 API 未返回。

---

## ⚡ 常见错误（真实踩坑）

| _http_post_raw 调用 | `body=` 参数名 | `json_data=`（查看签名：`inspect.signature(client._http_post_raw)`） |
| _http_post_raw URL | `/yonbip/sd/voucherorder/list`（相对路径报错） | 完整 URL 如 `https://c2.yonyoucloud.com/iuap-api-gateway/yonbip/sd/voucherorder/list` |
| 销售订单含税金额 | `orderDetailPrices.natSum` | `oriSum`（明细行顶层） |
| 销售订单税额 | `orderDetailPrices.oriTax`（返回null） | 公式计算 |
| 销售订单发货仓库 | `stockOrgId_name`（是库存组织） | `stockName` |
| 销售订单商品编码 | `productCode` | `skuCode` |
| 销售订单商品名称 | `productName` | `skuName` |
| 采购订单含税金额 | `oriSum` | `listOriSum` |
| 采购订单税额 | `oriTax` | `listOriTax` |
| 采购订单物料编码 | `productCode` | `product_cCode` |
| 生产订单物料 | `materialCode/materialName`（返回null） | `skuCode/skuName` |
| 订单状态字段 | `statusCode` | 销售用 `nextStatus`，采购/生产用 `status` |
| 输出流程 | 跳过字段检查直接报数据 | **必须先展示字段检查报告，再输出正文和HTML** |
| HTML路径 | 随意路径 | 固定 `~/Documents/YS_YYYY-MM-DD_类型.html`，生成后 `open` |
| isSum=True 返回值 | `result['data']` 当列表用 | `result['data']` 是字典，记录在 `result['data']['recordList']` |
| isSum=True 含税金额 | `oriSum`（明细行字段） | 分析汇总用 `payMoney`（主表字段），`oriSum` 仅 isSum=False 时用 |

---

## 🔧 配置

**返回结构（踩坑）：** `client.query_sale_orders()` 返回的 `data` 是 dict（包含 `recordList`/`pageCount` 等），不是直接列表。正确访问：
```python
records = result['data']['recordList']   # 订单记录列表
total = result['data']['recordCount']     # 总记录数
```
- `isSum=True` 时每订单一行（主表层），含税金额字段是 `payMoney`（不是 `oriSum`），不含税金额是 `payMoneyOrigTaxfree`
- 订单状态用 `nextStatus`（值如 `TAKEDELIVERY`、`ENDORDER` 等）

**凭证**（`~/.hermes/skills/yonsuite-skill/.env`）：
```bash
YONSUITE_APP_KEY=your_app_key
YONSUITE_APP_SECRET=your_app_secret
YONSUITE_TENANT_ID=your_tenant_id
```

**API 地址：**
- Gateway: `https://c2.yonyoucloud.com/iuap-api-gateway`
- Token: `https://c2.yonyoucloud.com/iuap-api-auth`

---

## 📂 脚本（位于 `~/.hermes/skills/yonsuite-skill/`）

> ⚠️ **isSum 参数区别（重要）：**
> - `isSum=True`：按订单汇总（一单一行），用于**客户/商品统计**和**整体分析**
> - `isSum=False`（默认）：按商品明细分列（一行一商品），用于**逐单明细查看**

| 脚本 | 用途 |
|-----|------|
| `query_sale_orders_to_sheet.py [日期]` | 销售订单 → JSON，支持 `YYYY-MM-DD` 或 `YYYY-MM` 月份 |
| `query_purchase_orders_to_sheet.py [日期]` | 采购订单 → JSON |
| `query_production_orders_to_sheet.py [日期]` | 生产订单 → JSON |
| `query_stock_to_sheet.py` | 库存现存量 → JSON（支持 `--warehouse` / `--sku` 过滤）|

**直接调用 API（推荐用于分析任务）：**
```python
import sys
sys.path.insert(0, '~/.hermes/skills/yonsuite-skill')
from ys_client import YonSuiteClient
client = YonSuiteClient()
# 分析用：isSum=True
result = client.query_sale_orders(page_index=1, page_size=500, isSum=True)
# 逐单明细：isSum=False
result = client.query_sale_orders(page_index=1, page_size=500, isSum=False)
```

---

## 📌 命名规范

- 技能名：反映实际功能，不用具体工具名（避免 minimax-mcp-xxx）
- 输出文件：`{sale,purchase,production}_report_YYYY_MM.html`
- 销售合计行：过滤 `vouchdate == "合计"` 的汇总行
- 采购合计行：过滤 `订单编号 == "合计"` 的汇总行
- 生产合计行：过滤 `单据编号 == "合计"` 的汇总行
- 生产物料字段：需通过 `OrderProduct_*` 前缀访问（如 `OrderProduct_quantity`）
- 销售报表文件：`~/Documents/本月销售分析报表_YYYY_MM.html`
- 采购报表文件：`~/Documents/本月采购分析报表_YYYY_MM.html`
- 生产报表文件：`~/Documents/本月生产分析报表_YYYY_MM.html`

---

## 📌 API 参考
- 销售订单列表：`POST /yonbip/sd/voucherorder/list`
- 采购订单列表：`POST /yonbip/scm/purchaseorder/list`
- 生产订单列表：`POST /yonbip/mfg/productionorder/list`
- 库存现存量：`POST /yonbip/scm/stock/QueryCurrentStocksByCondition`
- **商机列表：`POST /yonbip/crm/oppt/bill/list`**
- 官方文档：https://open.yonyoucloud.com/#/doc-center/docDes/api

---

## 📌 CRM 商机查询

**调用方式：**
```python
import sys
sys.path.insert(0, '/Users/zuoxiaojun/.hermes/skills/yonsuite-skill')
from ys_client import YonSuiteClient
client = YonSuiteClient()

# 查询商机列表（原始 dict）
result = client.query_opportunities(
    page_index=1, page_size=500,
    oppt_state='0',       # 0-进行中；1-暂停；2-作废；3-关闭
    win_lose_state='2',    # 0-赢单；1-丢单；2-未定；3-部分赢单
    is_sum=True,
    date_from='2026-01-01',
    date_to='2026-04-21'
)
records = result['data']['recordList']  # List[Dict]
total = result['data']['recordCount']   # 总数

# 查询商机列表（解析为 Opportunity 对象）
opps = client.query_opportunities_parsed(
    page_index=1, page_size=500,
    oppt_state='0'
)
for opp in opps:
    print(opp.format())  # 格式化输出
```

**⚠️ 字段名 Gotcha（v5.9 重要更新）：**
> API 返回字段为 **camelCase**，不是 snake_case！文档中的 snake_case 名称是错的，实测如下：

| 实际字段名（camelCase） | 类型 | 说明 | 文档旧名（错误） |
|------------------------|------|------|----------------|
| `opptState` | int | 商机状态：0-进行中，1-暂停，2-作废，3-关闭 | `oppt_state` |
| `opptState_name` | str | 商机状态名称 | `oppt_state_name` |
| `winLoseOrderState` | int | 赢丢单状态：0-赢单，1-丢单，2-未定，3-部分赢单 | `win_lose_order_state` |
| `winLoseOrderState_name` | str | 赢丢单状态名称 | `win_lose_order_state_name` |
| `ower_name` | str | 业务员名称 | `salesman_name` |
| `expectSignMoney` | float | **进行中**商机预计签约金额（赢单前用这个） | `amount` |
| `winOrderMoney` | float | **赢单后**实际签约金额（赢单后才有值） | 无 |
| `winOrderDate` | str | 赢单日期（格式：2026-04-21） | 无 |
| `opptStage_name` | str | 商机阶段名称（如"签订合同"、"招投标"） | `stage_name` |
| `customer_name` | str | 客户名称 | `customer_name` ✅正确 |
| `dept_name` | str | 部门名称 | `dept_name` ✅正确 |
| `createDate` | str | 创建日期（格式：2026-04-20） | `create_time` |
| `createTime` | str | 创建时间（格式：2026-04-20 22:31:13） | 无 |
| `code` | str | 商机编码 | `code` ✅正确 |
| `name` | str | 商机名称 | `name` ✅正确 |

**金额字段判断逻辑：**
```python
# 进行中商机（opptState=0）：用 expectSignMoney
amt = float(r.get('expectSignMoney') or 0)

# 赢单商机（winLoseOrderState=0）：用 winOrderMoney
if r.get('winLoseOrderState') == 0:
    win_money = r.get('winOrderMoney')  # 赢单金额
    win_date = r.get('winOrderDate')    # 赢单日期
```

**状态映射常量：**
```python
oppt_state_map = {0:'进行中', 1:'暂停', 2:'作废', 3:'关闭'}
win_lose_map = {0:'赢单', 1:'丢单', 2:'未定', 3:'部分赢单'}
```

**Opportunity 核心字段（实测正确版）：**
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int/str | 商机ID |
| `code` | str | 商机编码 |
| `name` | str | 商机名称 |
| `opptState` | int | 商机状态：0-进行中；1-暂停；2-作废；3-关闭 |
| `winLoseOrderState` | int | 赢丢单状态：0-赢单；1-丢单；2-未定；3-部分赢单 |
| `expectSignMoney` | float | 进行中商机预计金额 |
| `winOrderMoney` | float | 赢单实际金额（仅赢单后有值） |
| `customer_name` | str | 客户名称 |
| `ower_name` | str | 业务员名称 |
| `dept_name` | str | 部门名称 |
| `opptStage_name` | str | 商机阶段名称 |
| `createDate` | str | 创建日期 |
| `createTime` | str | 创建时间 |

