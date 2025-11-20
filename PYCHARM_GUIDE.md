# PyCharm 使用指南

## 🎯 快速开始 (5分钟)

### 1. 导入项目

1. 打开 PyCharm
2. 选择 `File` -> `Open`
3. 选择项目文件夹 `tiktok-risk-detector`
4. 点击 `OK`

### 2. 配置Python环境

#### 方法一：使用虚拟环境（推荐）

1. PyCharm会自动检测到项目，询问是否创建虚拟环境
2. 点击 `OK` 创建虚拟环境
3. 等待虚拟环境创建完成

#### 方法二：手动配置

1. 点击右下角的 Python解释器
2. 选择 `Add New Interpreter` -> `Add Local Interpreter`
3. 选择 `Virtualenv Environment`
4. 基础解释器选择 Python 3.11+
5. 位置选择: `backend/venv`
6. 点击 `OK`

### 3. 安装依赖

PyCharm会自动检测 `requirements.txt` 并提示安装依赖：

1. 点击通知栏的 `Install requirements`
2. 或者在Terminal中手动执行：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### 4. 配置环境变量

1. 复制环境变量文件：
   ```bash
   cd backend
   cp .env.example .env
   ```

2. 在PyCharm中打开 `.env` 文件进行编辑

### 5. 启动服务

#### 方法一：使用配置好的运行配置

1. 点击右上角的运行配置下拉菜单
2. 选择 `Run Backend`
3. 点击绿色运行按钮

#### 方法二：使用Terminal

1. 打开PyCharm的Terminal（底部工具栏）
2. 执行命令：
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 6. 访问应用

后端启动后，在浏览器访问：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📝 详细配置

### 数据库配置（可选）

如果不使用Docker，需要本地安装PostgreSQL和Redis：

#### PostgreSQL

1. 安装 PostgreSQL 15
2. 创建数据库：
   ```sql
   CREATE DATABASE tiktok_detector;
   ```
3. 在 `.env` 中配置数据库URL：
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/tiktok_detector
   ```

#### Redis

1. 安装 Redis 7
2. 启动 Redis：
   ```bash
   redis-server
   ```
3. 在 `.env` 中配置Redis URL：
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

### 前端开发（可选）

如果需要同时开发前端：

1. 打开新的Terminal
2. 进入前端目录：
   ```bash
   cd frontend
   ```
3. 安装依赖：
   ```bash
   npm install
   ```
4. 启动开发服务器：
   ```bash
   npm run dev
   ```
5. 访问: http://localhost:3000

## 🐛 调试

### 后端调试

1. 在代码中设置断点（点击行号左侧）
2. 点击右上角的Debug按钮（虫子图标）
3. 发送API请求触发断点

### 使用PyCharm的HTTP Client测试API

1. 在项目根目录创建 `test.http` 文件
2. 添加测试请求：

```http
### 健康检查
GET http://localhost:8000/health

### 快速检查
GET http://localhost:8000/api/v1/detection/quick-check

### 完整检测
POST http://localhost:8000/api/v1/detection/start
Content-Type: application/json

{
  "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
  "timezone": "America/Los_Angeles",
  "language": "en-US",
  "screen_resolution": "375x812",
  "color_depth": 24,
  "platform": "iPhone",
  "hardware_concurrency": 6,
  "max_touch_points": 5
}
```

3. 点击请求旁边的绿色运行按钮发送请求

## 🐳 使用Docker（推荐）

如果不想手动配置数据库和Redis，推荐使用Docker：

### 方法一：PyCharm Docker集成

1. 安装 Docker Desktop
2. 在PyCharm中启用Docker插件
3. 右键点击 `docker-compose.yml`
4. 选择 `Run 'docker-compose.yml'`

### 方法二：Terminal命令

1. 在Terminal中执行：
   ```bash
   docker-compose up -d
   ```

2. 查看日志：
   ```bash
   docker-compose logs -f
   ```

3. 停止服务：
   ```bash
   docker-compose down
   ```

## 📂 项目结构说明

```
tiktok-risk-detector/
├── backend/                 # 后端代码（Python）
│   ├── app/                # 应用代码
│   │   ├── api/           # API路由
│   │   ├── services/      # 业务逻辑
│   │   ├── models/        # 数据模型
│   │   ├── schemas/       # 数据验证
│   │   └── main.py        # 入口文件
│   ├── requirements.txt   # Python依赖
│   └── .env               # 环境变量
│
├── frontend/               # 前端代码（Vue.js）
│   ├── src/               # 源代码
│   │   ├── views/        # 页面组件
│   │   ├── api/          # API调用
│   │   └── utils/        # 工具函数
│   └── package.json      # Node依赖
│
└── docker-compose.yml     # Docker配置
```

## 🔧 常见问题

### Q: 导入错误 "No module named 'app'"

**A**: 确保：
1. 工作目录设置为 `backend`
2. Python解释器正确
3. 依赖已安装

### Q: 数据库连接错误

**A**: 检查：
1. PostgreSQL是否运行
2. `.env` 中数据库URL是否正确
3. 或使用Docker: `docker-compose up -d postgres`

### Q: Redis连接错误

**A**: 检查：
1. Redis是否运行
2. `.env` 中Redis URL是否正确
3. 或使用Docker: `docker-compose up -d redis`

### Q: 端口被占用

**A**: 
1. 检查端口占用：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```
2. 终止占用进程或更改端口

### Q: 如何查看日志

**A**: 在Terminal中：
```bash
# Docker日志
docker-compose logs -f backend

# 或查看PyCharm的Run窗口
```

## 💡 开发技巧

### 1. 代码格式化

安装并配置Black代码格式化：

1. 安装：`pip install black`
2. PyCharm设置：
   - `File` -> `Settings` -> `Tools` -> `Black`
   - 启用 `On save`
   - 设置路径为虚拟环境中的black

### 2. 类型检查

启用类型检查：

1. 安装：`pip install mypy`
2. PyCharm会自动进行类型检查
3. 查看 `Problems` 工具窗口

### 3. 数据库工具

PyCharm Professional版本自带数据库工具：

1. 点击右侧的 `Database` 工具窗口
2. 添加 PostgreSQL数据源
3. 可视化查看和编辑数据

### 4. Git集成

PyCharm内置Git支持：

1. `VCS` -> `Enable Version Control Integration`
2. 使用 `Commit` 工具窗口提交代码
3. 使用 `Git` 工具窗口查看历史

## 🚀 部署

### 本地测试

```bash
# 使用Docker Compose
docker-compose up -d

# 访问
# 后端: http://localhost:8000
# 前端: http://localhost:3000
```

### 部署到服务器

```bash
# 使用部署脚本
chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

详细部署说明见 `README.md`

## 📚 学习资源

- **FastAPI文档**: https://fastapi.tiangolo.com
- **Vue.js文档**: https://vuejs.org
- **Python异步编程**: https://docs.python.org/3/library/asyncio.html
- **Docker文档**: https://docs.docker.com

## 🤝 获取帮助

如遇问题：

1. 查看 `DEVELOPMENT.md` 了解实现细节
2. 查看 `README.md` 了解功能说明
3. 查看项目的Issues或提交新Issue
4. 查看代码注释和docstring

---

**祝开发愉快！** 🎉
