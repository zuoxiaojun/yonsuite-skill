# 销售订单列表字段对照

**接口**: `POST /yonbip/sd/voucherorder/list`

**说明**: API返回扁平结构（主表+子表字段混在一起），按单据编号聚合后每行一条明细。

## 字段清单（29字段）

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
| 9 | 订单状态 | `statusCode` | CONFIRMORDER/DELIVERGOODS/ENDORDER 等 |
| 10 | 行号 | `lineno` | |
| 11 | 物料编码 | `skuCode` | |
| 12 | 物料名称 | `skuName` | |
| 13 | 销售数量 | `qty` | |
| 14 | 销售单位 | `productUnitName` | |
| 15 | 数量 | `qty` | |
| 16 | 主计量 | `qtyName` | |
| 17 | 币种 | `currency_name` | 默认为 CNY |
| 18 | 含税成交价 | `oriUnitPrice` | |
| 19 | 含税金额 | `oriSum` | |
| 20 | 税率 | `taxRate` | |
| 21 | 表体税额 | `oriTax` | |
| 22 | 计划发货日期 | `sendDate` | |
| 23 | 库存组织 | `stockOrgId_name` | |
| 24 | 发货仓库 | `logisticsOrgName` | |
| 25 | 累计已发货数量 | `sendQty` | |
| 26 | 累计出库金额 | `totalOutStockOriMoney` | |
| 27 | 累计开票数量 | `invoiceQty` | |
| 28 | 累计开票含税金额 | `invoiceOriSum` | |
| 29 | 累计出库确认数量 | `totalOutStockQuantity` | |

## 订单状态（nextStatus）

| statusCode | 中文 |
|-----------|-----|
| CONFIRMORDER | 已确认 |
| DELIVERGOODS | 已发货 |
| ENDORDER | 已完成 |
| CLOSEDORDER | 已关闭 |

## 完整 API 主表字段（供参考）

以下为 API 返回的所有字段（部分）：

| 字段 | 说明 |
|------|------|
| `code` | 单据编号 |
| `vouchdate` | 单据日期 |
| `auditDate` | 审批日期 |
| `auditTime` | 审批时间 |
| `creator` | 创建人 |
| `createTime` | 创建时间 |
| `modifier` | 修改人 |
| `modifyTime` | 修改时间 |
| `auditor` | 审核人 |
| `verifystate` | 审批状态：0=待审批, 1=已提交, 2=已审批 |
| `salesOrgId` / `salesOrgId_name` | 销售组织 |
| `transactionTypeId` / `transactionTypeId_name` | 交易类型 |
| `agentId` / `agentId_name` | 客户 |
| `receiverCustId` / `receiverCustId_name` | 收货方 |
| `saleDepartmentId` / `saleDepartmentId_name` | 销售部门 |
| `corpContactUserName` | 销售业务员 |
| `stockOrgId` / `stockOrgId_name` | 库存组织 |
| `logisticsOrgName` | 发货仓库 |
| `sendDate` | 计划发货日期 |
| `confirmDate` | 确认日期 |
| `orderPayType` / `receiveAgreementId_name` | 付款方式 |
| `bizFlow` / `bizFlow_name` | 审批流 |
| `nextStatus` | 订单下一状态 |
| `status` | 状态码 |
| `statusCode` | 状态编码 |
| `changeStatus` | 变更状态 |
| `taxRate` | 税率 |
| `taxCode` | 税码 |
| `taxItems` | 税率描述 |
| `currency_name` | 币种 |
| `exchRateDate` | 汇率日期 |
| `invExchRate` | 票据汇率 |
| `priceMark` | 定价标志 |
| `isreserve` | 是否预留 |
| `projectId` / `projectId_name` / `projectId_code` | 项目 |
| `mainprojectId` / `mainprojectId_name` / `mainprojectId_code` | 主营项目 |

## 完整 API 子表字段（物料行）

| 字段 | 说明 |
|------|------|
| `lineno` | 行号 |
| `productId` | 物料ID |
| `productCode` | 物料编码 |
| `productName` | 物料名称 |
| `skuId` | SKU ID |
| `skuCode` | SKU编码 |
| `skuName` | SKU名称 |
| `qty` | 数量 |
| `productUnitName` | 销售单位 |
| `qtyName` | 主计量 |
| `masterUnitId` | 主计量ID |
| `priceUOM_Code` | 报价单位编码 |
| `priceQty` | 报价数量 |
| `oriUnitPrice` | 含税成交价 |
| `oriSum` | 含税金额 |
| `noTaxSalePrice` | 无税成交价 |
| `noTaxSaleCost` | 无税金额 |
| `taxRate` | 税率 |
| `oriTax` | 税额 |
| `sendQty` | 累计已发货数量 |
| `returnQty` | 累计退货数量 |
| `invoiceQty` | 累计开票数量 |
| `invoiceOriSum` | 累计开票含税金额 |
| `totalOutStockQuantity` | 累计出库确认数量 |
| `totalOutStockOriMoney` | 累计出库金额 |
| `totalOutStockOriTaxMoney` | 累计出库无税金额 |
| `totalVarianceQty` | 累计出库差异数量 |
| `receiveCustId` | 收货方ID |
| `receiveCustId_name` | 收货方名称 |
