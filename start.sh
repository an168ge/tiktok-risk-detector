#!/bin/bash

echo "======================================"
echo "  TikTok风险检测工具 - 一键启动"
echo "======================================"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到Docker"
    echo ""
    echo "请先安装Docker:"
    echo "  Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

echo "✓ Docker 已安装"
echo ""

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "📝 首次运行，创建配置文件..."
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  已创建 backend/.env 文件"
    echo "   可以编辑该文件配置API密钥"
    echo ""
fi

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "======================================"
echo "  ✨ 启动完成！"
echo "======================================"
echo ""
echo "访问地址:"
echo "  前端页面: http://localhost:3000"
echo "  API文档:  http://localhost:8000/docs"
echo "  健康检查: http://localhost:8000/health"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
echo "======================================"
