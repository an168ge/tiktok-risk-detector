@echo off
chcp 65001 >nul
echo ====================================
echo   TikTok风险检测工具 - 一键启动
echo ====================================
echo.

REM 检查Docker Desktop
docker version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Docker Desktop
    echo.
    echo 请先安装Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo ✓ Docker Desktop 已安装
echo.

REM 检查.env文件
if not exist "backend\.env" (
    echo 📝 首次运行，创建配置文件...
    copy backend\.env.example backend\.env
    echo.
    echo ⚠️  已创建 backend\.env 文件
    echo    可以编辑该文件配置API密钥
    echo.
)

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

echo.
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

echo.
echo ====================================
echo   ✨ 启动完成！
echo ====================================
echo.
echo 访问地址:
echo   前端页面: http://localhost:3000
echo   API文档:  http://localhost:8000/docs
echo   健康检查: http://localhost:8000/health
echo.
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo.
echo ====================================
pause
