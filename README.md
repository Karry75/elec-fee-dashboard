# 电费管理系统 (Electricity Fee Management System)

## 在线访问

- 本站看板（在线）：https://karry75.github.io/elec-fee-dashboard/
- 全部看板作品集（导航页）：https://karry75.github.io/dashboard-portal/

## 技术速览

- **形态**：单文件静态看板（HTML + JavaScript + ECharts），数据以离线快照形式随页面加载，纯前端渲染、无后端依赖。
- **原理**：业务库（阿里云 AnalyticDB）→ Python 抽取/构建管线 → 脱敏聚合快照 → 静态页面；页面打开即渲染，支持按维度筛选与下钻。
- **用途**：电费管理系统看板：站点电费与用电流水分析。
- **脱敏**：公开发布版本已移除数据库连接信息、账号口令与个人敏感字段，仅保留聚合指标。


打通「电费结算登记表 (Excel A)」与「电费情况总库 (Excel B / mysql-dudu)」的数据割裂，建立统一网点/商户电费结算管理中心：**结算状态可视、下次结算提前预警、扫码采集一体化**。

技术栈：**React 18 + Vite（前端 SPA）** + **Flask 2.3（后端 API + 生产托管）** + **SQLite（本地快照）**。
端口 **8173**（避开 8081）。

---

## 目录结构

```
elec_fee_dashboard/
├── config.py / config.example.py   # 运行配置（读 .env，禁止明文密码）
├── .env.example                    # 环境变量样例
├── requirements.txt                # 后端依赖
├── run_sync.py / run_sync.bat      # 同步入口（pull→merge→warn→log）
├── serve.py                        # Flask 启动入口（生产托管前端 dist + API）
├── backend/                       # Flask 应用、数据层、同步层、API、服务
│   ├── models.py                  # SQLAlchemy 2.0 ORM
│   ├── sync/                      # import_excel / pull_mysql / merge_view / compute_warn / run_sync
│   ├── api/                       # dashboard / board / expense / scan / writeback / import
│   ├── services/                  # stats_service / warn_service
│   └── util/                      # auth(admin+scan HMAC) / qr / notify(企微) / helpers
├── frontend/                      # Vite + React 18 SPA（4 页 + 移动端扫码页 + 导航）
└── data/                         # elec_fee.db（gitignore）、uploads/、seed/
```

## 四大模块 + P2 增强

1. **数据整合主看板** `/`：Excel/DB 导入 → station_master 合并视图；核心列展示；A/B 同字段不一致行内高亮+来源徽标；筛选（城市/物业/要结算/付款/来源）；行内编辑结算方式/度数/金额 → 进入 `pending_writeback` 写回队列（需 DBA 授权）。
2. **电费看板** `/board`：结算状态展示；预警规则 `need_settle=是 且 (next_settle_date−today)≤N(默认7) 且 is_settled≠是 → warn_flag=是`；顶部预警条 + 行高亮；网点点击下钻抽屉（合同/发票/抄表/商户提交/预警记录）。
3. **商户信息录入（扫码）** `/merchant` + `/scan`：后台为网点生成二维码（含限时 HMAC token，默认 24h）；移动端 H5 表单提交 → 写 `merchant_profile`（含图片上传 P2）。
4. **费用支出看板** `/expense`：按 结算类型/物业/城市 维度汇总；ECharts 柱状/饼/折线 + 指标卡；多维筛选 + Excel 导出。

P2：① 扫码图片上传 `data/uploads/` ② 待提单管理 `/pending`（读 A 表「8月待提单」）③ 注销网点管理 `/cancel`（读 A 表「南方电网需注销」）④ 预警企微推送（配置 `WECOM_WEBHOOK` 门控）⑤ 合同/押金到期提醒（由 `contract_term` 解析）。

## 快速开始

### 0. 准备依赖
```bash
# 后端（Python 3.10+）
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 1. 配置
复制 `config.example.py` → `config.py`（或直接用 `.env`）。默认 `SYNC_SOURCE=excel`，
`EXCEL_A_PATH` / `EXCEL_B_PATH` 指向本机两份 Excel（见 `.env.example`）。

### 2. 同步数据（Excel 回退，默认路径，必须可用）
```bash
python run_sync.py excel
# 或双击 run_sync.bat
```
成功填充 `data/elec_fee.db`，退出码 `[OK]/[WARN]` → 0，`[ERR]` → 1。

### 3. 启动服务
```bash
# 生产：Flask 托管 frontend/dist + API
python serve.py
# 开发：前端热更新（Vite 代理 /api → :8173）
cd frontend && npm run dev   # 另一个终端运行 python serve.py
```
访问 `http://localhost:8173/`（内网）或 `http://localhost:8173/`。

### 4. 构建前端
```bash
cd frontend && npm run build   # 产物 frontend/dist 由 Flask 生产托管
```

## 部署 / 安全

- **端口 8173**（内网 `localhost:8173`），`BASE_URL` 用于生成扫码 URL。
- **公网穿透（natapp）**：仅将 `/scan` 与只读看板（`/`、`/board`、`/expense`、`/pending`、`/cancel`）映射到公网；
  **管理接口**（`/api/import`、`/api/admin/*`、二维码生成）**不**经穿透暴露，且需 `ADMIN_TOKEN` 校验。
- **双轨 token**：扫码 token = `HMAC(SCAN_SECRET, site_id:exp)`，限时默认 24h；管理 token = `ADMIN_TOKEN`。
- 未配置 `ADMIN_TOKEN` 时管理接口进入 **dev-open** 模式（仅本地，日志告警，切勿生产使用）。
- 写回 mysql 为 P1 能力：**先入 `pending_writeback` 队列，默认标记「待DBA授权」**，实际落库需 DBA 授权 + MySQL 凭证。
- mysql 写回、企微推送均以 config 门控；缺失时优雅跳过并留清晰日志，不影响核心路径。

## 自测清单

1. `cd frontend && npm install && npm run build` 通过。
2. `python serve.py` 以 Excel 回退模式启动（默认 `SYNC_SOURCE=excel`）。
3. `python run_sync.py` → `data/elec_fee.db` 填充成功，退出码 `[OK]`；`station_master` 有数据且 `warn_flag` 按规则计算。
4. `curl http://localhost:8173/` 返回页面；`/api/dashboard`、`/api/board`、`/api/expense` 返回 JSON。
5. 模拟扫码提交：`curl -X POST 'http://localhost:8173/api/scan/submit?site_id=xxx&token=yyy&exp=zzz' -H 'Content-Type: application/json' -d '{...}'` → `merchant_profile` 入库。
6. 校验导出 `/api/expense/export`、预警规则、下钻 `/api/board/<site_id>`。

## 数据模型（SQLite）

`station_master`(PK=site_id) · `merchant_profile` · `warn_record` · `sync_log` · `pending_writeback` · `pending_submit` · `cancel_site`
详见 `backend/models.py`。
