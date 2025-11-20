# TikTok风险检测工具

一个专业的Web应用，用于检测TikTok访问环境的风险，包括IP质量、DNS泄露、WebRTC泄露、浏览器指纹一致性等。

## 功能特性

### 核心检测模块

1. **IP检测** (30%权重)
   - IP类型识别（住宅/数据中心/VPN/代理）
   - IP信誉评分
   - 地理位置信息
   - 黑名单检测

2. **隐私泄露检测** (25%权重)
   - DNS泄露检测
   - WebRTC泄露检测
   - 真实IP暴露检测

3. **浏览器指纹分析** (20%权重)
   - Canvas指纹
   - WebGL指纹
   - 字体指纹
   - 一致性分析（UA/时区/语言/分辨率）

4. **设备检测** (15%权重)
   - 设备类型识别
   - 模拟器检测
   - 自动化工具检测

5. **网络质量检测** (10%权重)
   - TikTok连接性测试
   - 延迟测试
   - CDN可达性

### 特色功能

- ✅ 综合风险评分（0-100分）
- ✅ 风险等级分类（低/中/高/严重）
- ✅ 详细的问题诊断
- ✅ 优先级排序的修复建议
- ✅ 移动端和桌面端完美适配
- ✅ 实时检测结果展示
- ✅ 历史记录查看（可选）

## 技术栈

### 后端
- **框架**: FastAPI 0.109+
- **语言**: Python 3.11+
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **异步**: asyncio + asyncpg
- **API**: RESTful + WebSocket

### 前端
- **框架**: Vue.js 3
- **构建**: Vite
- **UI**: Element Plus / Vant
- **样式**: TailwindCSS
- **图表**: ECharts
- **兼容**: Chrome 90+, Safari 14+

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Uvicorn + Gunicorn

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (可选)
- PostgreSQL 15+ (或使用Docker)
- Redis 7+ (或使用Docker)

### 方式一：Docker Compose (推荐)

```bash
# 克隆项目
git clone <repository-url>
cd tiktok-risk-detector

# 复制环境变量文件
cp backend/.env.example backend/.env

# 编辑.env文件，配置必要的参数

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问应用
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
# 前端页面: http://localhost:3000
```

### 方式二：手动安装

#### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 初始化数据库
# (确保PostgreSQL已运行)
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑.env文件

# 启动开发服务器
npm run dev

# 或构建生产版本
npm run build
```

## 配置说明

### 环境变量

主要配置项（backend/.env）：

```env
# 应用配置
DEBUG=True
PORT=8000

# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000

# 第三方API (可选)
IPHUB_API_KEY=your_key_here
IPQUALITYSCORE_API_KEY=your_key_here

# 限流
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_PERIOD=60
```

### 第三方API配置

项目支持多个IP检测API，按优先级使用：

1. **IPHub** (推荐)
   - 注册地址: https://iphub.info
   - 免费额度: 1000次/天
   
2. **IPQualityScore**
   - 注册地址: https://www.ipqualityscore.com
   - 免费额度: 5000次/月

3. **免费API** (默认)
   - 使用proxycheck.io免费API
   - 无需注册，但功能有限

## API文档

启动后端服务后，访问以下地址查看完整API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点

```
GET  /health                       # 健康检查
GET  /api/v1/detection/quick-check # 快速检查
POST /api/v1/detection/start       # 开始完整检测
GET  /api/v1/detection/{id}        # 获取检测结果
POST /api/v1/detection/ip          # 单独IP检测
POST /api/v1/detection/fingerprint # 单独指纹检测
```

## 开发指南

### 代码结构

```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心功能（缓存、限流等）
│   ├── models/       # 数据库模型
│   ├── schemas/      # Pydantic数据验证
│   ├── services/     # 业务逻辑服务
│   ├── utils/        # 工具函数
│   └── main.py       # 应用入口

frontend/
├── src/
│   ├── api/          # API请求封装
│   ├── components/   # Vue组件
│   ├── views/        # 页面视图
│   ├── utils/        # 工具函数
│   └── main.js       # 应用入口
```

### 添加新的检测模块

1. 在`backend/app/services/`创建新的服务文件
2. 在`backend/app/schemas/`定义数据结构
3. 在`backend/app/api/v1/endpoints/`添加API端点
4. 在风险评分引擎中集成新模块
5. 前端添加相应的UI组件

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 部署指南

### 生产环境部署

1. **使用Docker Compose**

```bash
# 构建镜像
docker-compose build

# 启动生产环境
docker-compose --profile production up -d

# 包括Nginx反向代理
```

2. **手动部署**

```bash
# 后端
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# 前端
cd frontend
npm run build
# 将dist目录部署到Nginx
```

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 性能优化

### 后端优化
- ✅ Redis缓存（IP检测结果缓存1小时）
- ✅ 异步并发检测
- ✅ 数据库连接池
- ✅ API限流（防止滥用）

### 前端优化
- ✅ 组件懒加载
- ✅ 图片懒加载
- ✅ 代码分割
- ✅ Gzip压缩

## 常见问题

### 1. IP检测不准确？
- 配置第三方API密钥（IPHub或IPQualityScore）
- 免费API准确度有限

### 2. 检测速度慢？
- 检查网络连接
- 确保Redis正常运行（缓存）
- 考虑使用CDN加速

### 3. Docker容器启动失败？
- 检查端口是否被占用
- 确保有足够的磁盘空间
- 查看日志：`docker-compose logs`

## 安全建议

1. **生产环境必须修改的配置**:
   - SECRET_KEY
   - 数据库密码
   - Redis密码

2. **HTTPS**:
   - 生产环境必须使用HTTPS
   - 配置SSL证书（Let's Encrypt推荐）

3. **限流**:
   - 根据实际情况调整限流参数
   - 防止API滥用

4. **数据隐私**:
   - IP地址存储时部分隐藏
   - 检测记录定期清理（默认30天）

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]

## 更新日志

### v1.0.0 (2024-01-15)
- ✅ 初始版本发布
- ✅ 核心检测功能完成
- ✅ 前后端完整实现
- ✅ Docker支持
- ✅ 完整文档
