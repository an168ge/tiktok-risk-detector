#!/bin/bash

#==============================================================================
# TikTok风险检测工具 - 服务器自动部署脚本
#==============================================================================
# 使用方法:
#   chmod +x deploy.sh
#   ./deploy.sh
#==============================================================================

set -e

echo "======================================"
echo "  TikTok Risk Detector - 服务器部署"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="tiktok-risk-detector"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
BACKUP_DIR="/opt/${PROJECT_NAME}-backup"
SYSTEMD_DIR="/etc/systemd/system"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ 请使用root用户运行此脚本${NC}"
        echo "   sudo ./deploy.sh"
        exit 1
    fi
}

# 检查系统
check_system() {
    echo -e "${GREEN}📋 检查系统环境...${NC}"
    
    # 检查操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        echo "   操作系统: $OS $VER"
    else
        echo -e "${RED}❌ 无法识别操作系统${NC}"
        exit 1
    fi
    
    # 检查必要命令
    for cmd in docker docker-compose git nginx; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${YELLOW}⚠️  未安装: $cmd${NC}"
            MISSING_COMMANDS="$MISSING_COMMANDS $cmd"
        else
            echo "   ✓ $cmd"
        fi
    done
    
    echo ""
}

# 安装依赖
install_dependencies() {
    if [ -n "$MISSING_COMMANDS" ]; then
        echo -e "${YELLOW}📦 安装缺失的依赖...${NC}"
        
        if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
            apt-get update
            
            if [[ $MISSING_COMMANDS == *"docker"* ]]; then
                echo "   安装 Docker..."
                curl -fsSL https://get.docker.com | bash
                systemctl enable docker
                systemctl start docker
            fi
            
            if [[ $MISSING_COMMANDS == *"docker-compose"* ]]; then
                echo "   安装 Docker Compose..."
                curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                chmod +x /usr/local/bin/docker-compose
            fi
            
            if [[ $MISSING_COMMANDS == *"git"* ]]; then
                apt-get install -y git
            fi
            
            if [[ $MISSING_COMMANDS == *"nginx"* ]]; then
                apt-get install -y nginx
            fi
            
        elif [[ "$OS" == "centos" || "$OS" == "rhel" ]]; then
            yum update -y
            
            if [[ $MISSING_COMMANDS == *"docker"* ]]; then
                yum install -y docker
                systemctl enable docker
                systemctl start docker
            fi
            
            if [[ $MISSING_COMMANDS == *"docker-compose"* ]]; then
                curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                chmod +x /usr/local/bin/docker-compose
            fi
            
            if [[ $MISSING_COMMANDS == *"git"* ]]; then
                yum install -y git
            fi
            
            if [[ $MISSING_COMMANDS == *"nginx"* ]]; then
                yum install -y nginx
            fi
        fi
        
        echo -e "${GREEN}✓ 依赖安装完成${NC}"
    fi
    echo ""
}

# 备份现有部署
backup_existing() {
    if [ -d "$DEPLOY_DIR" ]; then
        echo -e "${YELLOW}📦 备份现有部署...${NC}"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_PATH="${BACKUP_DIR}_${TIMESTAMP}"
        
        mkdir -p $(dirname "$BACKUP_PATH")
        cp -r "$DEPLOY_DIR" "$BACKUP_PATH"
        
        echo "   备份到: $BACKUP_PATH"
        echo ""
    fi
}

# 部署项目
deploy_project() {
    echo -e "${GREEN}🚀 部署项目...${NC}"
    
    # 如果目录不存在，从GitHub克隆
    if [ ! -d "$DEPLOY_DIR" ]; then
        echo "   从GitHub克隆项目..."
        read -p "   请输入GitHub仓库URL: " REPO_URL
        git clone "$REPO_URL" "$DEPLOY_DIR"
    else
        echo "   更新现有项目..."
        cd "$DEPLOY_DIR"
        git pull
    fi
    
    cd "$DEPLOY_DIR"
    echo ""
}

# 配置环境变量
configure_env() {
    echo -e "${GREEN}⚙️  配置环境变量...${NC}"
    
    if [ ! -f "$DEPLOY_DIR/backend/.env" ]; then
        cp "$DEPLOY_DIR/backend/.env.example" "$DEPLOY_DIR/backend/.env"
        
        echo "   请配置以下环境变量:"
        echo ""
        
        # 生成随机SECRET_KEY
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/your-secret-key-please-change-in-production/$SECRET_KEY/" "$DEPLOY_DIR/backend/.env"
        echo "   ✓ SECRET_KEY (已自动生成)"
        
        # 生成随机数据库密码
        DB_PASSWORD=$(openssl rand -hex 16)
        sed -i "s/password123/$DB_PASSWORD/" "$DEPLOY_DIR/backend/.env"
        sed -i "s/password123/$DB_PASSWORD/" "$DEPLOY_DIR/docker-compose.yml"
        echo "   ✓ DATABASE_PASSWORD (已自动生成)"
        
        # 询问域名
        read -p "   请输入域名 (留空使用IP): " DOMAIN_NAME
        if [ -n "$DOMAIN_NAME" ]; then
            sed -i "s|http://localhost:3000|https://$DOMAIN_NAME|" "$DEPLOY_DIR/backend/.env"
            echo "   ✓ DOMAIN_NAME: $DOMAIN_NAME"
        fi
        
        # 询问API密钥
        echo ""
        echo "   可选: 配置第三方API密钥 (提高检测准确度)"
        read -p "   IPHub API Key (回车跳过): " IPHUB_KEY
        if [ -n "$IPHUB_KEY" ]; then
            sed -i "s/IPHUB_API_KEY=/IPHUB_API_KEY=$IPHUB_KEY/" "$DEPLOY_DIR/backend/.env"
            echo "   ✓ IPHUB_API_KEY"
        fi
        
        read -p "   IPQualityScore API Key (回车跳过): " IPQS_KEY
        if [ -n "$IPQS_KEY" ]; then
            sed -i "s/IPQUALITYSCORE_API_KEY=/IPQUALITYSCORE_API_KEY=$IPQS_KEY/" "$DEPLOY_DIR/backend/.env"
            echo "   ✓ IPQUALITYSCORE_API_KEY"
        fi
    else
        echo "   .env 文件已存在，跳过配置"
    fi
    
    echo ""
}

# 配置Nginx
configure_nginx() {
    echo -e "${GREEN}🌐 配置Nginx...${NC}"
    
    read -p "   是否配置Nginx? (y/n): " CONFIGURE_NGINX
    if [ "$CONFIGURE_NGINX" != "y" ]; then
        echo "   跳过Nginx配置"
        echo ""
        return
    fi
    
    read -p "   请输入域名 (或IP地址): " SERVER_NAME
    
    cat > "$NGINX_CONF_DIR/$PROJECT_NAME" <<EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    # 前端
    location / {
        root $DEPLOY_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

    # 启用站点
    ln -sf "$NGINX_CONF_DIR/$PROJECT_NAME" "$NGINX_ENABLED_DIR/$PROJECT_NAME"
    
    # 测试配置
    nginx -t
    
    # 重载Nginx
    systemctl reload nginx
    
    echo "   ✓ Nginx配置完成"
    echo ""
    
    # 询问是否配置SSL
    read -p "   是否配置SSL证书 (Let's Encrypt)? (y/n): " CONFIGURE_SSL
    if [ "$CONFIGURE_SSL" == "y" ]; then
        configure_ssl "$SERVER_NAME"
    fi
}

# 配置SSL
configure_ssl() {
    local domain=$1
    echo -e "${GREEN}🔒 配置SSL证书...${NC}"
    
    # 安装certbot
    if ! command -v certbot &> /dev/null; then
        if [[ "$OS" == "ubuntu" || "$OS" == "debian" ]]; then
            apt-get install -y certbot python3-certbot-nginx
        elif [[ "$OS" == "centos" || "$OS" == "rhel" ]]; then
            yum install -y certbot python3-certbot-nginx
        fi
    fi
    
    # 获取证书
    certbot --nginx -d "$domain" --non-interactive --agree-tos --email admin@$domain
    
    echo "   ✓ SSL证书配置完成"
    echo ""
}

# 启动服务
start_services() {
    echo -e "${GREEN}🚀 启动服务...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # 使用Docker Compose启动
    docker-compose down 2>/dev/null || true
    docker-compose up -d --build
    
    echo "   等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}   ✓ 服务启动成功${NC}"
    else
        echo -e "${RED}   ❌ 服务启动失败${NC}"
        echo "   查看日志: docker-compose logs"
        exit 1
    fi
    
    echo ""
}

# 显示部署信息
show_info() {
    echo "======================================"
    echo -e "${GREEN}✨ 部署完成！${NC}"
    echo "======================================"
    echo ""
    echo "访问地址:"
    if [ -n "$DOMAIN_NAME" ]; then
        echo "   https://$DOMAIN_NAME"
    else
        SERVER_IP=$(hostname -I | awk '{print $1}')
        echo "   http://$SERVER_IP"
    fi
    echo ""
    echo "API文档:"
    echo "   http://$SERVER_IP:8000/docs"
    echo ""
    echo "常用命令:"
    echo "   查看日志: cd $DEPLOY_DIR && docker-compose logs -f"
    echo "   重启服务: cd $DEPLOY_DIR && docker-compose restart"
    echo "   停止服务: cd $DEPLOY_DIR && docker-compose down"
    echo "   更新项目: cd $DEPLOY_DIR && git pull && docker-compose up -d --build"
    echo ""
    echo "======================================"
}

# 主流程
main() {
    check_root
    check_system
    install_dependencies
    backup_existing
    deploy_project
    configure_env
    configure_nginx
    start_services
    show_info
}

# 执行主流程
main
