# Local Music Generator - 部署指南

## 概述

本文档提供了 Local Music Generator 应用程序的完整部署指南，涵盖了从开发环境到生产环境的各种部署方案。

## 部署选项

### 1. 本地开发部署
最简单的部署方式，适用于开发和测试。

### 2. Docker 部署
使用 Docker 容器化部署，适用于生产环境。

### 3. 自动化部署
使用部署脚本进行自动化部署。

### 4. 云平台部署
支持各种云平台的部署。

## 系统要求

### 最低要求
- **操作系统**: Ubuntu 18.04+, CentOS 7+, macOS 10.15+, Windows 10+
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **网络**: 稳定的互联网连接
- **Python**: 3.8+
- **Node.js**: 16+

### 推荐配置
- **内存**: 16GB+ RAM
- **GPU**: NVIDIA GPU with CUDA support
- **存储**: SSD 硬盘，50GB+ 可用空间
- **网络**: 高速宽带连接

## 部署方法

### 方法 1: 快速开始

```bash
# 克隆项目
git clone https://github.com/yourusername/local-music-generator.git
cd local-music-generator

# 运行安装脚本
python install.py

# 启动应用
./start_all.sh  # Linux/macOS
# 或
start_all.bat   # Windows
```

### 方法 2: 手动部署

#### 2.1 后端部署

```bash
# 切换到后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 运行后端
python main.py
```

#### 2.2 前端部署

```bash
# 切换到前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
npm run preview
```

### 方法 3: Docker 部署

#### 3.1 基础 Docker 部署

```bash
# 构建镜像
docker build -t local-music-generator .

# 运行容器
docker run -d \
  --name local-music-generator \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  local-music-generator
```

#### 3.2 Docker Compose 部署

```bash
# 基础部署
docker-compose up -d

# 包含监控
docker-compose --profile monitoring up -d

# 包含日志聚合
docker-compose --profile logging up -d

# 完整部署
docker-compose --profile monitoring --profile logging up -d
```

### 方法 4: 自动化部署

#### 4.1 使用构建脚本

```bash
# 构建应用
python build.py --build-type production

# 部署到生产环境
python deploy.py --environment production --docker
```

#### 4.2 使用 CI/CD

项目包含完整的 GitHub Actions 配置，支持：
- 自动化测试
- 代码质量检查
- 安全扫描
- 自动部署

## 配置选项

### 环境变量

创建 `.env` 文件配置应用：

```env
# 应用配置
APP_NAME=Local Music Generator
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 服务器配置
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000

# 模型配置
MODEL_NAME=facebook/musicgen-small
MODEL_CACHE_DIR=./data/models
AUTO_LOAD_MODEL=true
USE_GPU=true

# 音频配置
AUDIO_OUTPUT_DIR=./data/audio
AUDIO_FORMAT=mp3
AUDIO_SAMPLE_RATE=44100
AUDIO_QUALITY=high

# 性能配置
MAX_MEMORY_MB=8192
MAX_GENERATION_TIME=300
ENABLE_CACHING=true
CACHE_SIZE=1000

# 监控配置
ENABLE_MONITORING=true
MONITORING_INTERVAL=1.0
RESOURCE_HISTORY_SIZE=10000

# 安全配置
ALLOWED_ORIGINS=http://localhost:3000
ENABLE_CORS=true
```

### 数据库配置

应用支持多种数据存储选项：

```env
# SQLite (默认)
DATABASE_URL=sqlite:///./data/app.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/localmusic

# MySQL
DATABASE_URL=mysql://user:password@localhost/localmusic
```

### 缓存配置

```env
# Redis 缓存
REDIS_URL=redis://localhost:6379/0

# 内存缓存
CACHE_TYPE=memory
CACHE_SIZE=1000
```

## 监控和日志

### 监控配置

应用内置多种监控选项：

1. **应用指标**: 通过 `/metrics` 端点暴露 Prometheus 格式的指标
2. **健康检查**: 通过 `/health` 端点提供健康状态
3. **系统监控**: 监控 CPU、内存、磁盘使用情况

### 日志配置

```python
# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日志格式
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 日志文件
LOG_FILE=./logs/app.log
ERROR_LOG_FILE=./logs/error.log
```

### 使用 Grafana 监控

启用监控 profile：

```bash
docker-compose --profile monitoring up -d
```

访问 Grafana: http://localhost:3001
- 用户名: admin
- 密码: admin

## 性能优化

### 1. 硬件优化

- **GPU 加速**: 确保 NVIDIA GPU 驱动已安装
- **内存优化**: 增加系统内存，建议 16GB+
- **存储优化**: 使用 SSD 硬盘提高 I/O 性能

### 2. 应用优化

```env
# 启用模型缓存
ENABLE_CACHING=true
CACHE_SIZE=1000

# 优化内存使用
MAX_MEMORY_MB=8192
USE_GPU=true

# 启用压缩
ENABLE_GZIP=true
```

### 3. 系统优化

```bash
# 增加文件描述符限制
ulimit -n 65536

# 调整内核参数
echo 'net.core.somaxconn = 65536' >> /etc/sysctl.conf
sysctl -p
```

## 安全配置

### 1. 网络安全

```nginx
# 使用 HTTPS
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}

# 设置安全头
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
```

### 2. 应用安全

```env
# 启用 CORS
ENABLE_CORS=true
ALLOWED_ORIGINS=https://yourdomain.com

# 限制文件上传
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=mp3,wav,flac
```

### 3. 容器安全

```dockerfile
# 使用非 root 用户
USER appuser

# 最小化镜像
FROM python:3.9-slim

# 扫描漏洞
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
```

## 备份和恢复

### 1. 数据备份

```bash
# 使用 Docker Compose 备份
docker-compose run --rm backup

# 手动备份
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/
```

### 2. 数据恢复

```bash
# 解压备份
tar -xzf backup_20231201.tar.gz

# 恢复数据
docker-compose down
cp -r backup_data/* data/
docker-compose up -d
```

## 故障排除

### 1. 常见问题

#### 应用无法启动
```bash
# 检查日志
docker-compose logs app

# 检查端口占用
netstat -tulpn | grep :8000

# 检查依赖
pip check
```

#### 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 调整内存限制
export MAX_MEMORY_MB=4096
```

#### 模型加载失败
```bash
# 检查模型目录
ls -la data/models/

# 重新下载模型
rm -rf data/models/*
```

### 2. 性能问题

#### 生成速度慢
```bash
# 检查 GPU 使用
nvidia-smi

# 启用 GPU
export USE_GPU=true

# 优化批处理大小
export BATCH_SIZE=1
```

#### 内存泄漏
```bash
# 监控内存使用
docker stats --no-stream

# 重启应用
docker-compose restart app
```

### 3. 网络问题

#### 连接超时
```bash
# 检查防火墙
sudo ufw status

# 检查网络连接
curl -I http://localhost:8000/health

# 调整超时设置
export REQUEST_TIMEOUT=60
```

## 扩展部署

### 1. 负载均衡

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    deploy:
      replicas: 3
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
```

### 2. 数据库集群

```yaml
# 主从复制
postgres_master:
  image: postgres:13
  environment:
    - POSTGRES_REPLICATION_MODE=master

postgres_slave:
  image: postgres:13
  environment:
    - POSTGRES_REPLICATION_MODE=slave
    - POSTGRES_MASTER_HOST=postgres_master
```

### 3. 缓存集群

```yaml
# Redis Cluster
redis_cluster:
  image: redis:7-alpine
  command: redis-server --cluster-enabled yes
  deploy:
    replicas: 6
```

## 云平台部署

### 1. AWS 部署

#### 使用 ECS
```bash
# 创建任务定义
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 创建服务
aws ecs create-service --cluster my-cluster --service-name local-music-generator --task-definition local-music-generator:1
```

#### 使用 EKS
```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: local-music-generator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: local-music-generator
  template:
    metadata:
      labels:
        app: local-music-generator
    spec:
      containers:
      - name: app
        image: local-music-generator:latest
        ports:
        - containerPort: 8000
```

### 2. Azure 部署

#### 使用 Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name local-music-generator \
  --image local-music-generator:latest \
  --cpu 2 \
  --memory 4
```

### 3. Google Cloud 部署

#### 使用 Cloud Run
```bash
gcloud run deploy local-music-generator \
  --image gcr.io/PROJECT_ID/local-music-generator \
  --platform managed \
  --allow-unauthenticated
```

## 维护和更新

### 1. 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建
python build.py --build-type production

# 滚动更新
docker-compose up -d --no-deps app
```

### 2. 依赖更新

```bash
# 更新 Python 依赖
pip-review --local --auto

# 更新 Node.js 依赖
npm update

# 更新 Docker 镜像
docker-compose pull
```

### 3. 系统维护

```bash
# 清理 Docker 资源
docker system prune -a

# 清理日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理缓存
redis-cli FLUSHALL
```

## 联系支持

如果您在部署过程中遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看应用日志获取详细错误信息
3. 在 GitHub Issues 中提交问题
4. 联系技术支持团队

## 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。