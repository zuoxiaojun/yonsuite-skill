# 更新日志

## v3.0 (2026-04-03) - 精简版 ⭐ 最新版

### 重大修正
- **主子表结构明确化**：三种订单均为主子表结构，`oriSum` 在明细行顶层，不是嵌套字段
- **字段路径修正**：含税金额 `oriSum`（销售）、`listOriSum`（采购）；发货仓库 `stockName`；商品编码 `skuCode`/`skuName`
- **删除错误内容**：常见错误对照表中已纠正的字段统一更新到字段清单，删除冗余章节

### 文档精简
- 删除版本历史累积冗余，合并为单一结构
- 删除过时的多版本注释

## v2.3 (2026-03-25) - 精简版（只保留官方 API）

### 🔧 精简优化

- **删除自行封装的业务方法**：
  - ❌ `get_customer_unshipped_orders()` - 客户未发货订单
  - ❌ `get_vendor_pending_orders()` - 供应商待交货订单
  - ❌ `get_product_stock_analysis()` - 物料库存分析
  - ❌ `get_production_order_progress()` - 生产订单进度
  - ❌ `get_my_pending_approvals()` - 我的待办审批
  - ❌ `search_orders_by_product()` - 按产品搜索订单
  - ❌ `query_vendors_batch()` - 供应商批量查询（非官方 API）
  - ❌ `query_production_orders_batch()` - 生产订单批量查询（非官方 API）

### ✅ 保留的官方 API 接口

**核心功能（全部来自官方文档）：**
- Token 管理
- 销售订单（列表 + 详情）
- 采购订单（列表 + 详情）
- 库存查询（现存量）
- 客户档案（列表 + 详情 + 批量详情）
- 供应商档案（列表 + 详情 + listV3 批量查询）
- 生产订单（列表 + 详情）
- 用户待办（待办 + 已办）

### 📝 原则

- **只保留官方 API 文档中的原始接口**
- **不自行封装业务逻辑方法**
- **如需封装，需用户明确指令**

---

## v2.2 (2026-03-25) - 批量查询 + 业务场景快捷方法 ⭐ 最新版

### ✨ 新增功能

#### 批量查询功能
- **供应商批量查询（listV3）** ⭐：
  - 新增 `query_vendors_listv3()` 方法：支持按 ID 列表批量查询供应商详情
  - 可选查询联系人、银行、地址、资质、业务范围等子表
  - API 端点：`POST /yonbip/digitalModel/vendor/listV3`
  - ⚠️ **权限要求**：此接口需要单独授权，如遇 403 错误需联系用友管理员开通
  - 📌 **官方文档**：https://open.yonyoucloud.com/#/doc-center/docDes/api?apiId=2151560680253685764
  
- **生产订单批量查询**：
  - 新增 `query_production_orders_batch()` 方法：一次查询最多 50 个生产订单的完整信息
  - 新增 `query_production_orders_batch_parsed()` 方法：解析为 ProductionOrderDetail 模型列表
  - 新增 `format_production_orders_batch()` 方法：格式化批量查询结果
  - API 端点：`POST /yonbip/mfg/productionorder/batchGet`



#### 数据模型增强
- **TodoItem 模型**：从 todo.py 迁移到 models.py，保持一致性
  - 支持 `from_api()` 转换
  - 支持 `format()` 格式化输出
  - 提供 `is_todo` 和 `is_done` 属性判断

### 📝 文档更新

- **SKILL.md 全面更新**：
  - 添加批量查询功能说明
  - 添加业务场景快捷方法详细说明
  - 添加日期参数详细说明（开工日期/创建时间/单据日期的区别）
  - 添加批量查询限制说明（供应商 100 个、生产订单 50 个）
  - 更新版本历史和使用示例

- **代码注释完善**：
  - 所有新增方法添加完整的 docstring
  - 添加使用示例和参数说明
  - 标注 v2.2 新增功能

### 🔧 代码优化

- **模块结构优化**：
  - 将 TodoItem 从 todo.py 迁移到 models.py，保持数据模型统一
  - todo.py 保留 TodoModule 和临时 TodoItem（兼容旧代码）
  
- **错误处理增强**：
  - 批量查询参数验证（空列表检查）
  - 批量数量超限警告日志
  - 统一的错误提示格式

### 📊 接口统计

- **总接口数**：14 → 20+
- **新增接口**：6+ 个（供应商批量、生产订单批量、6 个业务场景方法）
- **模块覆盖**：8 大模块 + 业务场景快捷方法

---

## v2.1 (2026-03-23) - 功能增强版

### ✨ 新增功能

#### 待办查询功能（2026-03-23 下午）
- **用户待办查询模块**：新增 TodoModule 模块
  - 新增 `query_user_todos()` 方法：查询用户待办/已办事项列表
  - 新增 `query_user_todos_parsed()` 方法：解析为 TodoItem 模型对象
  - 新增 `format_todo_info()` 方法：格式化输出待办列表
  - 新增 `TodoItem` 数据模型：类型安全的待办事项表示
  - API 端点：`GET /yonbip/uspace/rest/open/yhttoken/todo/query/list`
  - 支持状态筛选：todo=待办，done=已办
  - 支持分页查询：pageNo（页码）、pageSize（每页数量，最大 1000）
  - 返回信息：标题、内容、状态、来源、表单 ID、处理链接等

#### 客户档案详情批量查询
- **客户档案详情批量查询**：支持一次查询多个客户的完整档案信息
  - 新增 `query_customer_detail()` 方法（单个客户详情）
  - 新增 `query_customer_details_batch()` 方法（批量查询）
  - 新增 `format_customer_detail()` 格式化输出方法
  - API 端点：`POST /yonbip/digitalModel/merchant/newBatchDetail`
  
#### 采购订单详情查询
- **采购订单详情查询**：支持查询采购订单的完整信息
  - 新增 `get_purchase_order_detail()` 方法
  - 新增 `format_order_detail()` 格式化输出方法
  - 返回订单明细、付款计划、付款执行明细
  - API 端点：`GET /yonbip/scm/purchaseorder/detail`

### 📝 文档更新

- 更新 SKILL.md 添加新接口使用说明
- 更新命令行帮助和示例
- 完善使用场景说明

### 🔧 代码优化

- 完善客户模块和采购模块的类型注解
- 优化错误处理和日志输出
- 统一命令行参数命名规范

### 📊 接口统计

- 总接口数：13 → 14
- 新增接口：3 个（待办查询、客户详情批量、采购订单详情）
- 模块覆盖：8 大模块全部就绪（销售、采购、库存、客户、供应商、生产、待办）

---

## v2.0 (2026-03-20) - 重构优化版

### 🎯 重大变更

- **模块化重构**：将单一文件拆分为多个功能模块
- **配置管理**：支持环境变量和 .env 文件
- **错误处理**：完善的异常体系和重试机制
- **Token 缓存**：支持内存 + 文件持久化缓存
- **数据模型**：使用 dataclass 提供类型安全
- **日志系统**：完整的日志记录

### 📦 新增文件

```
skills/yonsuite/
├── config.py              # 配置管理
├── exceptions.py          # 异常定义
├── cache.py               # Token 缓存
├── models.py              # 数据模型
├── requirements.txt       # 依赖管理
├── API_REFERENCE.md       # API 参考文档
├── CHANGELOG.md           # 更新日志
├── modules/               # 功能模块
│   ├── __init__.py
│   ├── base.py            # 基础 HTTP 客户端
│   ├── sales.py           # 销售订单
│   ├── purchase.py        # 采购订单
│   ├── stock.py           # 库存查询
│   ├── customer.py        # 客户档案
│   ├── vendor.py          # 供应商档案
│   └── production.py      # 生产订单
├── tests/                 # 单元测试
│   └── test_ys_client.py
└── examples/              # 使用示例
    ├── basic_usage.py
    └── advanced_usage.py
```

### ✨ 新功能

- **环境变量配置**：敏感信息不再硬编码
- **Token 持久化**：进程重启后仍可使用缓存
- **自动重试**：网络错误自动重试
- **类型提示**：完整的类型注解
- **单元测试**：基础测试覆盖

### 🔧 优化

- 代码结构更清晰，易于维护
- 错误信息更友好
- 日志输出更详细
- 支持模块化调用

### ⚠️ 兼容性

- 保持与 v1.x 的 API 兼容
- 现有代码无需修改即可升级

---

## v1.6 (2026-03-19)

### 新增
- 生产订单列表查询接口
- 生产订单详情查询接口
- 格式化生产订单信息方法

---

## v1.5 (2026-03-17)

### 新增
- 供应商档案列表查询接口

---

## v1.4 (2026-03-17)

### 新增
- 供应商档案详情查询接口

---

## v1.3 (2026-03-17)

### 新增
- 客户档案列表查询接口

---

## v1.2 (2026-03-17)

### 新增
- 采购订单列表查询接口

---

## v1.1 (2026-03-17)

### 变更
- 移除销售订单创建功能（保留查询/详情）

### 保留功能
- Token 获取
- 销售订单查询/详情
- 库存现存量查询

---

## v1.0 (2026-03-17)

### 初始版本
- Token 管理
- 销售订单管理
- 库存查询
