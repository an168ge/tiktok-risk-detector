#!/bin/bash

# TikTok风险检测工具 - 快速启动脚本

set -e

echo "======================================"
echo "  TikTok Risk Detector - Quick Start"
echo "======================================"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker环境检查通过"
echo ""

# 检查.env文件
if [ ! -f "backend/.env" ]; then
    echo "📝 创建环境配置文件..."
    cp backend/.env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件配置必要的参数"
    echo ""
fi

# 选择启动模式
echo "请选择启动模式："
echo "1) 开发模式 (包含前端热重载)"
echo "2) 生产模式 (使用Nginx)"
echo ""
read -p "请输入选项 (1-2): " mode

case $mode in
    1)
        echo ""
        echo "🚀 启动开发环境..."
        docker-compose up -d backend postgres redis frontend
        ;;
    2)
        echo ""
        echo "🚀 启动生产环境..."
        docker-compose --profile production up -d
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "======================================"
echo "  服务启动成功！"
echo "======================================"
echo ""

if [ "$mode" == "1" ]; then
    echo "📱 前端页面: http://localhost:3000"
    echo "🔧 后端API: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
else
    echo "🌐 应用地址: http://localhost"
    echo "🔧 后端API: http://localhost:8000"
fi

echo ""
echo "📊 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
echo ""
echo "======================================"
