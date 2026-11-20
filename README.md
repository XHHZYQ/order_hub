# 订单汇聚管理系统（order-hub）

面向电商商家的**多平台订单中台**：把淘宝/天猫、京东、拼多多、抖音/快手、自建商城多平台多店铺的订单汇聚为统一视图，并在系统内完成订单处理、库存同步、发货、售后与对账。

## 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 (TS) + Vite + Element Plus + ECharts + Pinia |
| 后端 | Python 3.13 + FastAPI + SQLModel |
| 数据库 | PostgreSQL（容器 `postgresql-container`，库/用户/密码均为 `order-hub`） |
| 包管理 | 后端 uv；前端 pnpm |

前后端分离，代码置于同一 Monorepo。

## 目录结构

```
order-hub/
├── docs/          # 设计文档（需求规格、概要设计、系统架构、项目结构、接口设计、数据库设计）
├── backend/       # 后端（FastAPI 单体服务）
├── frontend/      # 前端（Vue 3 + Vite）
└── deploy/        # 部署配置示例
```

## 环境准备

- Python 3.13 + [uv](https://docs.astral.sh/uv/)
- Node.js 22 + [pnpm](https://pnpm.io/)
- PostgreSQL（WSL2 Docker 容器 `postgresql-container`，库/用户/密码均为 `order-hub`）

## 后端启动

```bash
cd backend
cp .env.example .env          # 按需修改数据库连接
uv sync                       # 安装依赖
uv run python scripts/init_db.py       # 建表
uv run python scripts/seed_minimal.py  # 生成最小演示数据
uv run uvicorn app.main:app --reload --port 8000
```

接口文档：http://localhost:8000/docs

## 前端启动

```bash
cd frontend
pnpm install
pnpm dev                      # http://localhost:5173，/api 代理到 8000
```

## 默认账号

初始化数据（minimal）会创建演示账号，例如：

| 账号 | 密码 | 角色 |
| --- | --- | --- |
| admin | 123456 | 超级管理员 |

> 具体账号清单见 `backend/scripts/seed_minimal.py`。

## 设计文档

设计文档位于 `docs/`，是需求与实现的唯一依据：

- `需求规格说明书.md`：业务范围、功能需求、数据与非功能需求
- `概要设计.md`：总体架构、模块划分、关键技术方案、开发批次
- `系统架构.md`：部署架构、运行时视图、核心业务时序
- `项目结构.md`：目录结构、命名规范、页面菜单、UI 规范与主题
- `接口设计.md`：接口通用约定与完整接口清单
- `数据库设计.md`：表结构、索引、字典、字段映射、数据生成
