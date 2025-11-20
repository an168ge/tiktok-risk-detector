# GitHub 上传和管理指南

## 📤 首次上传到GitHub

### 步骤1: 在GitHub创建仓库

1. 登录 https://github.com
2. 点击右上角的 `+` -> `New repository`
3. 填写信息：
   - **Repository name**: `tiktok-risk-detector`
   - **Description**: `专业的TikTok访问环境风险检测工具`
   - **Visibility**: 选择 `Public` 或 `Private`
   - ⚠️ **不要**勾选 "Initialize with README" （我们已经有了）
4. 点击 `Create repository`

### 步骤2: 在本地初始化Git

在项目目录中打开Terminal（或Git Bash），执行：

```bash
# 进入项目目录
cd tiktok-risk-detector

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: TikTok风险检测工具完整版"

# 设置主分支名称
git branch -M main

# 关联远程仓库（替换YOUR-USERNAME为你的GitHub用户名）
git remote add origin https://github.com/YOUR-USERNAME/tiktok-risk-detector.git

# 推送到GitHub
git push -u origin main
```

### 步骤3: 验证上传

1. 刷新GitHub仓库页面
2. 确认所有文件已上传
3. 查看README.md是否正常显示

## 🔐 使用SSH方式（推荐）

### 配置SSH密钥

1. 生成SSH密钥：
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. 查看公钥：
```bash
cat ~/.ssh/id_ed25519.pub
```

3. 复制公钥内容

4. 在GitHub添加SSH密钥：
   - 点击头像 -> `Settings`
   - 左侧菜单 -> `SSH and GPG keys`
   - 点击 `New SSH key`
   - 粘贴公钥，点击 `Add SSH key`

5. 更改远程URL为SSH：
```bash
git remote set-url origin git@github.com:YOUR-USERNAME/tiktok-risk-detector.git
```

## 📝 日常开发流程

### 1. 开始新功能

```bash
# 创建新分支
git checkout -b feature/new-feature-name

# 进行开发...
# 修改代码

# 查看修改
git status

# 添加修改
git add .

# 提交
git commit -m "feat: 添加新功能描述"

# 推送到GitHub
git push origin feature/new-feature-name
```

### 2. 创建Pull Request

1. 访问GitHub仓库页面
2. 点击 `Compare & pull request`
3. 填写PR标题和描述
4. 点击 `Create pull request`
5. 等待代码审查或自行合并

### 3. 合并到主分支

```bash
# 切换到main分支
git checkout main

# 拉取最新代码
git pull origin main

# 合并功能分支
git merge feature/new-feature-name

# 推送到GitHub
git push origin main

# 删除功能分支（可选）
git branch -d feature/new-feature-name
git push origin --delete feature/new-feature-name
```

## 🏷️ 版本管理

### 创建Release

```bash
# 打标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到GitHub
git push origin v1.0.0

# 或推送所有标签
git push origin --tags
```

### 在GitHub创建Release

1. 访问仓库页面
2. 点击右侧的 `Releases`
3. 点击 `Create a new release`
4. 选择标签或创建新标签
5. 填写Release说明
6. 可上传编译文件（可选）
7. 点击 `Publish release`

## 🔄 更新和同步

### 拉取最新代码

```bash
# 拉取并合并
git pull origin main

# 或先拉取再合并
git fetch origin
git merge origin/main
```

### 解决冲突

如果出现冲突：

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突
# 文件中会标记 <<<<<<<, =======, >>>>>>>

# 标记冲突已解决
git add .

# 完成合并
git commit -m "fix: 解决合并冲突"

# 推送
git push origin main
```

## 🌳 分支策略

### 推荐的分支结构

```
main (生产环境)
  └── develop (开发环境)
       ├── feature/新功能
       ├── bugfix/修复bug
       └── hotfix/紧急修复
```

### 工作流程

1. **主分支 (main)**: 
   - 只包含稳定代码
   - 通过PR合并
   - 自动触发部署（CI/CD）

2. **开发分支 (develop)**:
   - 日常开发
   - 功能开发完成后合并到main

3. **功能分支 (feature/)**:
   - 从develop创建
   - 开发完成后合并回develop

```bash
# 创建develop分支
git checkout -b develop
git push origin develop

# 创建功能分支
git checkout develop
git checkout -b feature/add-pdf-export

# 开发完成后
git checkout develop
git merge feature/add-pdf-export
git push origin develop
```

## 🤖 自动化（GitHub Actions）

项目已配置GitHub Actions，每次push会自动：

1. 运行测试
2. 检查代码质量
3. 构建Docker镜像
4. 部署到服务器（需配置Secrets）

### 配置Secrets

在GitHub仓库中配置：

1. 点击 `Settings` -> `Secrets and variables` -> `Actions`
2. 点击 `New repository secret`
3. 添加以下Secrets：
   - `DOCKER_USERNAME`: Docker Hub用户名
   - `DOCKER_PASSWORD`: Docker Hub密码
   - `SERVER_HOST`: 服务器IP
   - `SERVER_USER`: SSH用户名
   - `SERVER_SSH_KEY`: SSH私钥

## 📋 提交规范

### Commit Message格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 重构
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建或辅助工具变动

### 示例

```bash
git commit -m "feat(detection): 添加设备模拟器检测功能"

git commit -m "fix(api): 修复IP检测超时问题"

git commit -m "docs: 更新部署文档"
```

## 📊 项目管理

### 使用Issues

1. 在GitHub仓库点击 `Issues`
2. 点击 `New issue`
3. 填写Issue模板：
   - Bug报告
   - 功能请求
   - 文档改进

### 使用Project Board

1. 点击 `Projects` -> `New project`
2. 选择模板（如Kanban）
3. 创建列：
   - Todo
   - In Progress
   - Review
   - Done
4. 将Issues拖拽到对应列

## 🔒 安全注意事项

### 不要提交敏感信息

⚠️ **永远不要提交：**

- `.env` 文件（已在.gitignore中）
- API密钥
- 数据库密码
- SSL证书私钥
- 任何个人信息

### 检查历史记录

如果不小心提交了敏感信息：

```bash
# 从历史记录中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作！）
git push origin --force --all
```

⚠️ 更好的方法是立即更换泄露的密钥！

## 👥 团队协作

### 添加协作者

1. 仓库设置 -> `Collaborators`
2. 点击 `Add people`
3. 输入GitHub用户名或邮箱
4. 选择权限级别

### Code Review

1. 创建PR后，请求审查者
2. 审查者查看代码
3. 留下评论或批准
4. 解决所有评论后合并

### 保护分支

1. 设置 -> `Branches`
2. 添加分支保护规则
3. 要求PR审查
4. 要求CI通过

## 🎯 常用命令速查

```bash
# 克隆仓库
git clone https://github.com/YOUR-USERNAME/tiktok-risk-detector.git

# 查看状态
git status

# 查看差异
git diff

# 查看提交历史
git log --oneline --graph

# 撤销修改
git checkout -- <file>

# 回退提交
git reset HEAD~1

# 查看远程仓库
git remote -v

# 更新远程分支列表
git fetch origin

# 清理已删除的远程分支
git remote prune origin
```

## 🌟 最佳实践

1. **频繁提交**: 小步提交，便于回滚
2. **清晰消息**: 提交信息描述具体改动
3. **分支开发**: 不直接在main分支开发
4. **及时同步**: 经常拉取最新代码
5. **代码审查**: 重要代码通过PR审查
6. **测试通过**: 提交前确保测试通过
7. **文档更新**: 代码改动同步更新文档

## 📚 学习资源

- Git官方文档: https://git-scm.com/doc
- GitHub文档: https://docs.github.com
- Pro Git（免费电子书）: https://git-scm.com/book/zh/v2

---

**祝协作愉快！** 🚀
