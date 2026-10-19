# 天眼通 2.0 交付文档 — 报告计划

- 报告类型：技术交付文档（项目验收用）
- 受众：开发团队 / 项目验收方
- 语言：中文
- 结构：Intro → 交付概览 → ①目录结构 → ②数据库设计（MySQL DDL + Neo4j）→ ③API 清单（含示例）→ ④前端页面清单 → ⑤核心代码 → ⑥数据来源合规说明 → 运行指南 → 来源
- Color preset: Product Teal — cue: 产品交付文档 + 天眼通青蓝产品调性
- Intro mode: contained — cue: 技术交付文档，无 Hero 媒体素材（no-image fallback）
- 图表：无 ECharts 图表；目录树用 pre 代码块；无图片
- 组件：metric 卡（交付概览）、分组表格（DDL 摘要 / API 清单）、callout（合规红线）、代码块（DDL / 核心代码）、feature list
- 宽表格策略：API 清单与 DDL 摘要表为附录级宽表，允许全宽 + 横向滚动并明确标注；核心表格保持可换行
- 引用：本地文件以文字标注（如 backend/tyt/core/security.py），外部数据源链接放 footer Sources
