# 生产订单详情接口字段对照

**接口**: `GET /yonbip/mfg/productionorder/detail`

## 主表（订单头）

| 字段名 | API字段 | 说明 |
|-------|--------|------|
| 单据编号 | `code` | |
| 单据日期 | `vouchdate` | |
| 交易类型 | `transTypeName` | |
| 工厂 | `orgName` | |
| 生产部门 | `departmentName` | |
| 订单状态 | `status` | 0=开立, 1=已审核, 2=已关闭, 3=审核中, 4=已锁定, 5=已开工, 6=生产完工 |
| 审批状态 | `verifystate` | 0=待审批, 1=已提交, 2=已审批, -1=驳回 |
| 创建人 | `creator` | |
| 创建时间 | `createTime` | |
| 审核人 | `auditor` | |
| 审核时间 | `auditTime` | |
| 挂起状态 | `isHold` | |
| 齐套检查 | `completionInspection` | |

## 子表 orderProduct[]（产品行）

| 字段名 | API字段 | 说明 |
|-------|--------|------|
| 行号 | `lineNo` | |
| 物料编码 | `productCode` | |
| 物料名称 | `productName` | |
| 生产数量 | `quantity` | |
| 主计量 | `mainUnitName` | |
| 生产件数 | `auxiliaryQuantity` | |
| 已完工数量 | `completedQuantity` | |
| 累计入库数量 | `incomingQuantity` / `cfmIncomingQty` | |
| 入库状态 | `stockStatus` | 0=未入库, 1=部分入库, 2=全部入库 |
| 完工申报状态 | `finishedWorkApplyStatus` | 0=未申请, 1=已申请, 2=已审批 |
| 领料状态 | `materialStatus` | 0=未领料, 1=部分领料, 2=已领料 |
| 挂起状态 | `isHold` | |
| 开工日期 | `startDate` | |
| 完工日期 | `finishDate` | |
| 工艺路线 | `routingName` | |
| 生产模式 | `processMode` | 1=离散制造, 2=流程制造 |
| BOM用途 | `bomUseTypeName` | 自制/委外 |
| 批次号 | `batchNo` | |

## 孙子表 orderMaterial[]（材料明细）

**关键字段**：每条材料记录自带 `operationCode` + `operationName`，直接标明归属哪道工序。

| 字段名 | API字段 | 说明 |
|-------|--------|------|
| 行号 | `lineNo` | |
| 物料编码 | `materialCode` | |
| 物料名称 | `materialName` | |
| 单位用量 | `unitUseQuantity` | |
| 已领用量 | `receivedQuantity` | |
| 主单位 | `mainUnitName` | |
| 需求日期 | `requirementDate` | |
| 工序编号 | `operationCode` | **标记归属工序** |
| 工序名称 | `operationName` | **标记归属工序** |
| 供应类型 | `supplyType` | 0=自制, 1=外购 |
| 仓库 | `orgName` | |

## 孙子表 orderProcess[]（工序明细）

| 字段名 | API字段 | 说明 |
|-------|--------|------|
| 工序序号 | `sn` | |
| 工序编号 | `operationCode` | |
| 工序名称 | `operationName` | |
| 车间名称 | `workCenterName` | |
| 计划数量 | `qty` | |
| 工序时间 | `processTime` | 单位：秒 |
| 准备时间 | `prepareTime` | 单位：分钟 |
| 计划开始日期 | `planStartDate` | |
| 计划结束日期 | `planEndDate` | |
| 工序时间单位 | `timeUnit` | 2=分钟 |

## 订单状态映射

```
status（YonSuite API）→ 中文：
  0 → 开立
  1 → 已审核
  2 → 已关闭
  3 → 审核中
  4 → 已锁定
  5 → 已开工
  6 → 生产完工

verifystate → 中文：
  0 → 待审批
  1 → 已提交
  2 → 已审批
 -1 → 驳回
```

## 孙子表 orderByProduct[]（联副产品）

暂未获取到示例数据，字段待补充。
