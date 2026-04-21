# 采购订单列表字段对照

**接口**: `POST /yonbip/scm/purchaseorder/list`

**说明**: API返回扁平结构（主表+子表字段混在一起），按单据编号聚合后每行一条明细。

## 字段清单（32字段）

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
| 10 | 单据状态 | `status` | 0:开立,1:已审核,2:已关闭,3:审核中 |
| 11 | 行号 | `lineno` | |
| 12 | 物料编码 | `product_cCode` | |
| 13 | 物料名称 | `product_cName` | |
| 14 | 采购数量 | `subQty` | |
| 15 | 单位 | `unit_name` | |
| 16 | 含税单价 | `oriTaxUnitPrice` | |
| 17 | 含税金额 | `oriSum` | 订单级（同一订单各行相同） |
| 18 | 税率 | `listTaxRate` | 订单级 |
| 19 | 税额 | `oriTax` | 订单级（同一订单各行相同） |
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

## 状态映射

**单据状态（status）**

| 值 | 中文 |
|---|------|
| 0 | 开立 |
| 1 | 已审核 |
| 2 | 已关闭 |
| 3 | 审核中 |

**到货状态（purchaseOrders_arrivedStatus）**

| 值 | 中文 |
|---|------|
| 1 | 到货完成 |
| 2 | 未到货 |
| 3 | 部分到货 |
| 4 | 到货完成 |

**入库状态（purchaseOrders_inWHStatus）**

| 值 | 中文 |
|---|------|
| 1 | 入库完成 |
| 2 | 未入库 |
| 3 | 部分入库 |
| 4 | 入库结束 |

**发票状态（purchaseOrders_invoiceStatus）**

| 值 | 中文 |
|---|------|
| 1 | 开票完成 |
| 2 | 未开票 |
| 3 | 部分开票 |
| 4 | 开票结束 |

## 完整 API 主表字段（供参考）

以下为 API 返回的所有字段（部分）：

| 字段 | 说明 |
|------|------|
| `code` | 订单编号 |
| `vouchdate` | 单据日期 |
| `createTime` | 创建时间 |
| `creator` | 创建人 |
| `modifier` | 修改人 |
| `modifyTime` | 修改时间 |
| `auditor` | 审核人 |
| `auditDate` | 审核日期 |
| `auditTime` | 审核时间 |
| `verifystate` | 审批状态 |
| `status` | 单据状态 |
| `bizstatus` | 业务状态 |
| `demandOrg` / `demandOrg_name` | 采购组织 |
| `org` / `org_name` | 工厂/库存组织 |
| `bustype` / `bustype_name` | 交易类型 |
| `vendor` / `vendor_name` | 供货供应商 |
| `invoiceVendor` / `invoiceVendor_name` | 开票供应商 |
| `inOrg` / `inOrg_name` | 收货组织 |
| `inInvoiceOrg` / `inInvoiceOrg_name` | 收票组织 |
| `department` / `department_name` | 采购部门 |
| `operator` / `operator_name` | 采购员 |
| `bizFlow` / `bizFlow_name` | 审批流/流程名称 |
| `currency` / `currency_name` | 币种 |
| `natCurrency` / `natCurrency_name` | 本币 |
| `exchRate` | 汇率 |
| `oriSum` | 含税金额（订单级） |
| `oriTax` | 税额（订单级） |
| `oriMoney` | 无税金额 |
| `listOriSum` | 订单明细含税金额（行级） |
| `listOriTax` | 订单明细税额（行级） |
| `listOriMoney` | 订单明细无税金额（行级） |
| `listTaxRate` | 税率（订单级） |
| `taxitems` / `taxitems_name` | 税率描述 |
| `receiveAgreementId_name` | 付款协议名称 |
| `submitter` / `submitter_username` | 提交人 |
| `submitTime` | 提交时间 |
| `source` / `srcBillNO` | 来源单据 |

## 完整 API 子表字段（物料行）

| 字段 | 说明 |
|------|------|
| `lineno` | 行号 |
| `product` | 物料ID |
| `product_cCode` | 物料编码 |
| `product_cName` | 物料名称 |
| `product_model` | 物料规格 |
| `subQty` | 采购数量 |
| `unit` / `unit_name` | 单位 |
| `oriTaxUnitPrice` | 含税单价 |
| `oriUnitPrice` | 无税单价 |
| `oriSum` | 含税金额 |
| `oriTax` | 税额 |
| `oriMoney` | 无税金额 |
| `purchaseOrders_subQty` | 采购数量（子表） |
| `purchaseOrders_purUOM` / `purchaseOrders_purUOM_Name` | 采购单位 |
| `purchaseOrders_totalConfirmInQty` | 累计到货数量 |
| `purchaseOrders_totalInSubqty` | 累计入库数量 |
| `purchaseOrders_totalInvoiceQty` | 累计开票数量 |
| `purchaseOrders_arrivedStatus` | 到货状态 |
| `purchaseOrders_inWHStatus` | 入库状态 |
| `purchaseOrders_invoiceStatus` | 发票状态 |
| `purchaseOrders_payStatus` | 付款状态 |
| `purchaseOrders_source` | 来源 |
| `purchaseOrders_project` / `purchaseOrders_project_name` / `purchaseOrders_project_code` | 项目 |
| `purchaseOrders_materialClassName` | 物料分类 |
| `wbsCode` / `wbsName` | WBS元素 |
| `activityCode` / `activityName` | 活动 |
