# 关帝灵境
## 关帝庙智慧保护与修复领航者

### 技术架构

`
┌─────────────────────┐    ┌──────────────────────────┐
│  Frontend @ Vercel   │    │    Backend @ Railway      │
│                     │    │                          │
│  index.html (静态页) │────▶  FastAPI (Python)        │
│  CSS / JS 内置      │    │  Session API             │
│  响应式设计          │    │  Chat API                │
│                     │    │  Monitor API             │
└─────────────────────┘    └──────────┬───────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │   Redis 数据库     │
                            │  (Session存储)    │
                            │  (聊天历史存储)   │
                            │  (7天过期)         │
                            └──────────────────┘
`

### 部署指南

#### 第一步：部署后端到 Railway

1. 将 ackend/ 目录上传到 GitHub 仓库
2. 在 [Railway](https://railway.app) 创建新项目并关联该仓库
3. 添加 Redis 数据库插件（Railway 原生支持）
4. 设置环境变量 REDIS_URL（自动注入）
5. Railway 会自动检测 equirements.txt 并安装依赖
6. 部署完成后获得后端 URL（如 https://guandi-backend.up.railway.app）

#### 第二步：部署前端到 Vercel

1. 将 rontend/ 目录上传到 GitHub 仓库
2. 在 [Vercel](https://vercel.com) 导入该项目
3. 框架预设选择 "Other"
4. 设置环境变量（可选）：
   - VITE_API_URL = 后端 Railway URL
5. 部署完成后获得前端 URL

### Session 管理机制

每个访客首次访问时自动分配独立的 Session ID（UUID v4）：
- Session 存储在 Redis 中，key 格式：session:<ID>
- 聊天历史存储在 Redis 中，key 格式：chat:<ID>
- 过期时间：7 天（自动清理）
- Redis 不可用时自动回退到内存存储

### 本地开发

`ash
# 后端
cd backend
pip install -r requirements.txt
python main.py  # 默认 http://localhost:8000

# 前端
# 直接用浏览器打开 frontend/index.html
# 或使用任何静态服务器：
python -m http.server 8080 --directory frontend
`

### 技术栈

- **后端框架**: FastAPI (Python 3.12)
- **前端**: 原生 HTML/CSS/JS (无框架依赖)
- **数据库**: Redis (Session + 聊天历史)
- **部署**: Railway (后端) + Vercel (前端)
- **架构**: 每个访客独立 Session，支持高并发
