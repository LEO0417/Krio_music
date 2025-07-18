#!/usr/bin/env python3
"""
Local Music Generator 部署脚本
自动化部署和配置管理
"""

import os
import sys
import platform
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """终端颜色代码"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DeploymentError(Exception):
    """部署错误异常"""
    pass

class LocalMusicGeneratorDeployer:
    """本地音乐生成器部署器"""
    
    def __init__(self, args):
        self.args = args
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.build_dir = self.root_dir / "build"
        self.deploy_dir = self.root_dir / "deploy"
        
        # 系统信息
        self.system = platform.system()
        self.architecture = platform.machine()
        self.python_version = sys.version_info
        
        # 部署状态
        self.deployment_status = {
            'environment_check': False,
            'dependencies_install': False,
            'build_backend': False,
            'build_frontend': False,
            'package_application': False,
            'create_distribution': False,
            'deploy_services': False,
            'configure_runtime': False,
            'health_check': False
        }
        
        logger.info(f"初始化部署器 - 系统: {self.system}, 架构: {self.architecture}")
    
    def print_header(self):
        """打印欢迎信息"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("="*60)
        print("    Local Music Generator 部署器")
        print("    自动化部署和配置管理")
        print("="*60)
        print(f"{Colors.END}")
        print()
    
    def check_deployment_environment(self) -> bool:
        """检查部署环境"""
        print(f"{Colors.YELLOW}🔍 检查部署环境...{Colors.END}")
        
        requirements_met = True
        
        # 检查Python版本
        if self.python_version < (3, 8):
            print(f"{Colors.RED}❌ Python 版本过低 (需要 3.8+){Colors.END}")
            requirements_met = False
        else:
            print(f"{Colors.GREEN}✅ Python 版本: {'.'.join(map(str, self.python_version[:3]))}{Colors.END}")
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"{Colors.GREEN}✅ Node.js 版本: {version}{Colors.END}")
            else:
                raise subprocess.CalledProcessError(1, 'node')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}❌ Node.js 未安装{Colors.END}")
            requirements_met = False
        
        # 检查Docker（可选）
        if self.args.docker:
            try:
                result = subprocess.run(['docker', '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"{Colors.GREEN}✅ Docker 版本: {version}{Colors.END}")
                else:
                    raise subprocess.CalledProcessError(1, 'docker')
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"{Colors.RED}❌ Docker 未安装{Colors.END}")
                if self.args.docker:
                    requirements_met = False
        
        # 检查磁盘空间
        free_space = shutil.disk_usage(self.root_dir).free / (1024**3)  # GB
        if free_space < 5:
            print(f"{Colors.RED}❌ 磁盘空间不足 (需要 5GB+, 可用 {free_space:.1f}GB){Colors.END}")
            requirements_met = False
        else:
            print(f"{Colors.GREEN}✅ 磁盘空间: {free_space:.1f}GB 可用{Colors.END}")
        
        self.deployment_status['environment_check'] = requirements_met
        return requirements_met
    
    def install_dependencies(self) -> bool:
        """安装依赖"""
        print(f"\n{Colors.YELLOW}📦 安装依赖...{Colors.END}")
        
        try:
            # 安装后端依赖
            print("安装后端依赖...")
            os.chdir(self.backend_dir)
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True)
            
            # 安装前端依赖
            print("安装前端依赖...")
            os.chdir(self.frontend_dir)
            subprocess.run(['npm', 'install'], check=True)
            
            print(f"{Colors.GREEN}✅ 依赖安装完成{Colors.END}")
            self.deployment_status['dependencies_install'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 依赖安装失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def build_backend(self) -> bool:
        """构建后端"""
        print(f"\n{Colors.YELLOW}🔨 构建后端...{Colors.END}")
        
        try:
            os.chdir(self.backend_dir)
            
            # 运行测试
            if not self.args.skip_tests:
                print("运行后端测试...")
                subprocess.run([sys.executable, '-m', 'pytest', '-v'], check=True)
            
            # 编译Python文件
            print("编译Python文件...")
            subprocess.run([sys.executable, '-m', 'compileall', '.'], check=True)
            
            # 创建构建目录
            backend_build_dir = self.build_dir / "backend"
            backend_build_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制必要文件
            essential_files = [
                'main.py',
                'requirements.txt',
                'api/',
                'models/',
                'config/',
                'utils/',
                'audio/',
            ]
            
            for file_path in essential_files:
                src = self.backend_dir / file_path
                dst = backend_build_dir / file_path
                
                if src.is_file():
                    shutil.copy2(src, dst)
                elif src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            
            print(f"{Colors.GREEN}✅ 后端构建完成{Colors.END}")
            self.deployment_status['build_backend'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 后端构建失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def build_frontend(self) -> bool:
        """构建前端"""
        print(f"\n{Colors.YELLOW}🔨 构建前端...{Colors.END}")
        
        try:
            os.chdir(self.frontend_dir)
            
            # 运行测试
            if not self.args.skip_tests:
                print("运行前端测试...")
                subprocess.run(['npm', 'test', '--', '--watchAll=false'], check=True)
            
            # 构建生产版本
            print("构建生产版本...")
            subprocess.run(['npm', 'run', 'build'], check=True)
            
            # 复制构建结果
            frontend_build_dir = self.build_dir / "frontend"
            frontend_build_dir.mkdir(parents=True, exist_ok=True)
            
            dist_dir = self.frontend_dir / "dist"
            if dist_dir.exists():
                shutil.copytree(dist_dir, frontend_build_dir, dirs_exist_ok=True)
            
            print(f"{Colors.GREEN}✅ 前端构建完成{Colors.END}")
            self.deployment_status['build_frontend'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 前端构建失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def package_application(self) -> bool:
        """打包应用"""
        print(f"\n{Colors.YELLOW}📦 打包应用...{Colors.END}")
        
        try:
            # 创建部署目录
            self.deploy_dir.mkdir(exist_ok=True)
            
            # 复制构建文件
            if (self.build_dir / "backend").exists():
                shutil.copytree(self.build_dir / "backend", self.deploy_dir / "backend", dirs_exist_ok=True)
            
            if (self.build_dir / "frontend").exists():
                shutil.copytree(self.build_dir / "frontend", self.deploy_dir / "frontend", dirs_exist_ok=True)
            
            # 创建配置文件
            config = {
                "version": "1.0.0",
                "build_date": datetime.now().isoformat(),
                "environment": self.args.environment,
                "system": self.system,
                "architecture": self.architecture,
                "features": {
                    "docker": self.args.docker,
                    "ssl": self.args.ssl,
                    "monitoring": self.args.monitoring
                }
            }
            
            with open(self.deploy_dir / "config.json", 'w') as f:
                json.dump(config, f, indent=2)
            
            # 创建部署脚本
            self.create_deployment_scripts()
            
            print(f"{Colors.GREEN}✅ 应用打包完成{Colors.END}")
            self.deployment_status['package_application'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 应用打包失败: {e}{Colors.END}")
            return False
    
    def create_deployment_scripts(self):
        """创建部署脚本"""
        print("创建部署脚本...")
        
        # 创建启动脚本
        if self.system == "Windows":
            # Windows批处理脚本
            start_script = self.deploy_dir / "start.bat"
            start_content = f"""@echo off
echo Starting Local Music Generator...
echo.

REM 启动后端
echo Starting backend...
start "Backend" cmd /c "cd /d backend && python main.py"

REM 等待后端启动
timeout /t 5

REM 启动前端服务器 (如果需要)
if exist "frontend" (
    echo Starting frontend server...
    start "Frontend" cmd /c "cd /d frontend && python -m http.server 3000"
)

echo.
echo Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all services...
pause > nul

REM 停止服务
taskkill /f /im python.exe
"""
            start_script.write_text(start_content)
            
            # 停止脚本
            stop_script = self.deploy_dir / "stop.bat"
            stop_content = """@echo off
echo Stopping Local Music Generator...
taskkill /f /im python.exe
echo Services stopped.
pause
"""
            stop_script.write_text(stop_content)
            
        else:
            # Linux/macOS Shell脚本
            start_script = self.deploy_dir / "start.sh"
            start_content = f"""#!/bin/bash
echo "Starting Local Music Generator..."
echo ""

# 启动后端
echo "Starting backend..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 5

# 启动前端服务器 (如果需要)
if [ -d "frontend" ]; then
    echo "Starting frontend server..."
    cd frontend
    python -m http.server 3000 &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "Application is running..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# 等待信号
wait $BACKEND_PID $FRONTEND_PID
"""
            start_script.write_text(start_content)
            start_script.chmod(0o755)
            
            # 停止脚本
            stop_script = self.deploy_dir / "stop.sh"
            stop_content = """#!/bin/bash
echo "Stopping Local Music Generator..."
pkill -f "python main.py"
pkill -f "python -m http.server 3000"
echo "Services stopped."
"""
            stop_script.write_text(stop_content)
            stop_script.chmod(0o755)
        
        # 创建健康检查脚本
        health_script = self.deploy_dir / "health_check.py"
        health_content = '''#!/usr/bin/env python3
"""
健康检查脚本
"""
import requests
import sys
import time

def check_backend_health():
    """检查后端健康状态"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def check_frontend_health():
    """检查前端健康状态"""
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def main():
    """主函数"""
    print("Running health check...")
    
    # 检查后端
    if check_backend_health():
        print("✅ Backend: Healthy")
    else:
        print("❌ Backend: Unhealthy")
        sys.exit(1)
    
    # 检查前端
    if check_frontend_health():
        print("✅ Frontend: Healthy")
    else:
        print("⚠️  Frontend: Not available (may be expected)")
    
    print("Health check completed.")

if __name__ == "__main__":
    main()
'''
        health_script.write_text(health_content)
        if self.system != "Windows":
            health_script.chmod(0o755)
    
    def create_docker_configuration(self) -> bool:
        """创建Docker配置"""
        if not self.args.docker:
            return True
            
        print(f"\n{Colors.YELLOW}🐳 创建Docker配置...{Colors.END}")
        
        try:
            # 创建后端Dockerfile
            backend_dockerfile = self.deploy_dir / "backend" / "Dockerfile"
            backend_dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libsndfile1 \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/models data/audio logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
'''
            backend_dockerfile.write_text(backend_dockerfile_content)
            
            # 创建前端Dockerfile
            frontend_dockerfile = self.deploy_dir / "frontend" / "Dockerfile"
            frontend_dockerfile_content = '''FROM nginx:alpine

# 复制构建文件
COPY . /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
'''
            frontend_dockerfile.write_text(frontend_dockerfile_content)
            
            # 创建nginx配置
            nginx_config = self.deploy_dir / "frontend" / "nginx.conf"
            nginx_config_content = '''events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    upstream backend {
        server backend:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files $uri $uri/ /index.html;
        }
        
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
'''
            nginx_config.write_text(nginx_config_content)
            
            # 创建docker-compose.yml
            docker_compose = self.deploy_dir / "docker-compose.yml"
            docker_compose_content = '''version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped
    
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
    
volumes:
  data:
  logs:
'''
            docker_compose.write_text(docker_compose_content)
            
            print(f"{Colors.GREEN}✅ Docker配置创建完成{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Docker配置创建失败: {e}{Colors.END}")
            return False
    
    def create_distribution_package(self) -> bool:
        """创建分发包"""
        print(f"\n{Colors.YELLOW}📦 创建分发包...{Colors.END}")
        
        try:
            # 创建压缩包
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"local-music-generator_{timestamp}"
            
            if self.system == "Windows":
                # 创建ZIP文件
                import zipfile
                zip_path = self.root_dir / f"{package_name}.zip"
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(self.deploy_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(self.deploy_dir)
                            zipf.write(file_path, arcname)
                
                print(f"分发包创建完成: {zip_path}")
                
            else:
                # 创建tar.gz文件
                import tarfile
                tar_path = self.root_dir / f"{package_name}.tar.gz"
                
                with tarfile.open(tar_path, 'w:gz') as tar:
                    tar.add(self.deploy_dir, arcname=package_name)
                
                print(f"分发包创建完成: {tar_path}")
            
            # 创建安装说明
            install_readme = self.deploy_dir / "INSTALL.md"
            install_content = f"""# Local Music Generator 部署说明

## 版本信息
- 版本: 1.0.0
- 构建时间: {datetime.now().isoformat()}
- 环境: {self.args.environment}

## 部署步骤

### 1. 解压文件
将分发包解压到目标目录

### 2. 检查依赖
确保系统已安装：
- Python 3.8+
- Node.js 16+
- 足够的磁盘空间 (5GB+)

### 3. 启动应用
{"- Windows: 双击 start.bat" if self.system == "Windows" else "- Linux/macOS: ./start.sh"}

### 4. 验证部署
- 运行健康检查: python health_check.py
- 访问应用: http://localhost:3000
- 检查API: http://localhost:8000/docs

## Docker部署（可选）
如果包含Docker配置：
```bash
docker-compose up -d
```

## 故障排除
1. 检查端口占用: netstat -an | grep :8000
2. 查看日志: tail -f logs/app.log
3. 重启服务: 停止后重新启动

## 支持
如有问题请联系技术支持团队
"""
            install_readme.write_text(install_content)
            
            print(f"{Colors.GREEN}✅ 分发包创建完成{Colors.END}")
            self.deployment_status['create_distribution'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 分发包创建失败: {e}{Colors.END}")
            return False
    
    def deploy_services(self) -> bool:
        """部署服务"""
        print(f"\n{Colors.YELLOW}🚀 部署服务...{Colors.END}")
        
        try:
            if self.args.docker:
                # Docker部署
                os.chdir(self.deploy_dir)
                print("使用Docker部署...")
                subprocess.run(['docker-compose', 'up', '-d'], check=True)
                
            else:
                # 直接部署
                print("使用直接部署...")
                # 这里可以添加systemd服务创建等逻辑
                
            print(f"{Colors.GREEN}✅ 服务部署完成{Colors.END}")
            self.deployment_status['deploy_services'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 服务部署失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def configure_runtime(self) -> bool:
        """配置运行时环境"""
        print(f"\n{Colors.YELLOW}⚙️  配置运行时环境...{Colors.END}")
        
        try:
            # 创建运行时目录
            runtime_dirs = [
                self.deploy_dir / "data" / "models",
                self.deploy_dir / "data" / "audio",
                self.deploy_dir / "logs",
                self.deploy_dir / "cache"
            ]
            
            for dir_path in runtime_dirs:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"创建目录: {dir_path}")
            
            # 设置权限
            if self.system != "Windows":
                for dir_path in runtime_dirs:
                    os.chmod(dir_path, 0o755)
            
            # 创建环境变量文件
            env_file = self.deploy_dir / ".env"
            env_content = f"""# Local Music Generator 生产环境配置
ENVIRONMENT={self.args.environment}
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
"""
            env_file.write_text(env_content)
            
            print(f"{Colors.GREEN}✅ 运行时环境配置完成{Colors.END}")
            self.deployment_status['configure_runtime'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 运行时环境配置失败: {e}{Colors.END}")
            return False
    
    def run_health_check(self) -> bool:
        """运行健康检查"""
        print(f"\n{Colors.YELLOW}🏥 运行健康检查...{Colors.END}")
        
        try:
            # 等待服务启动
            import time
            time.sleep(10)
            
            # 运行健康检查脚本
            health_script = self.deploy_dir / "health_check.py"
            if health_script.exists():
                result = subprocess.run([sys.executable, str(health_script)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ 健康检查通过{Colors.END}")
                    print(result.stdout)
                else:
                    print(f"{Colors.RED}❌ 健康检查失败{Colors.END}")
                    print(result.stderr)
                    return False
            
            self.deployment_status['health_check'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 健康检查失败: {e}{Colors.END}")
            return False
    
    def generate_deployment_report(self) -> None:
        """生成部署报告"""
        print(f"\n{Colors.BLUE}📋 部署报告{Colors.END}")
        print("="*50)
        
        total_steps = len(self.deployment_status)
        completed_steps = sum(self.deployment_status.values())
        
        print(f"部署进度: {completed_steps}/{total_steps} ({completed_steps/total_steps*100:.1f}%)")
        print()
        
        for step, status in self.deployment_status.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {step.replace('_', ' ').title()}")
        
        print()
        
        if completed_steps == total_steps:
            print(f"{Colors.GREEN}🎉 部署完成!{Colors.END}")
            print()
            print("应用访问地址:")
            print("  前端: http://localhost:3000")
            print("  后端API: http://localhost:8000")
            print("  API文档: http://localhost:8000/docs")
            print()
            print("管理命令:")
            if self.system == "Windows":
                print("  启动服务: start.bat")
                print("  停止服务: stop.bat")
            else:
                print("  启动服务: ./start.sh")
                print("  停止服务: ./stop.sh")
            print("  健康检查: python health_check.py")
            
        else:
            print(f"{Colors.RED}❌ 部署未完成{Colors.END}")
            print("请检查错误信息并重新运行部署")
        
        # 保存报告到文件
        report_file = self.deploy_dir / "deployment_report.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.args.environment,
            'system': self.system,
            'architecture': self.architecture,
            'deployment_status': self.deployment_status,
            'success': completed_steps == total_steps
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
    
    def run_deployment(self) -> bool:
        """运行完整部署流程"""
        self.print_header()
        
        try:
            # 1. 环境检查
            if not self.check_deployment_environment():
                if not self.args.force:
                    print(f"{Colors.RED}环境检查失败，部署终止{Colors.END}")
                    return False
                else:
                    print(f"{Colors.YELLOW}强制模式：跳过环境检查{Colors.END}")
            
            # 2. 安装依赖
            if not self.install_dependencies():
                raise DeploymentError("依赖安装失败")
            
            # 3. 构建后端
            if not self.build_backend():
                raise DeploymentError("后端构建失败")
            
            # 4. 构建前端
            if not self.build_frontend():
                raise DeploymentError("前端构建失败")
            
            # 5. 打包应用
            if not self.package_application():
                raise DeploymentError("应用打包失败")
            
            # 6. 创建Docker配置
            if not self.create_docker_configuration():
                raise DeploymentError("Docker配置创建失败")
            
            # 7. 创建分发包
            if not self.create_distribution_package():
                raise DeploymentError("分发包创建失败")
            
            # 8. 部署服务
            if not self.args.package_only:
                if not self.deploy_services():
                    raise DeploymentError("服务部署失败")
                
                # 9. 配置运行时
                if not self.configure_runtime():
                    raise DeploymentError("运行时配置失败")
                
                # 10. 健康检查
                if not self.args.skip_health_check:
                    if not self.run_health_check():
                        raise DeploymentError("健康检查失败")
            
            return True
            
        except DeploymentError as e:
            logger.error(f"部署失败: {e}")
            return False
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}部署被用户中断{Colors.END}")
            return False
        except Exception as e:
            logger.error(f"意外错误: {e}")
            return False
        finally:
            self.generate_deployment_report()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Local Music Generator 部署脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--environment', 
        choices=['development', 'staging', 'production'],
        default='production',
        help='部署环境'
    )
    
    parser.add_argument(
        '--docker', 
        action='store_true',
        help='使用Docker部署'
    )
    
    parser.add_argument(
        '--ssl', 
        action='store_true',
        help='启用SSL/TLS'
    )
    
    parser.add_argument(
        '--monitoring', 
        action='store_true',
        help='启用监控'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制部署，跳过环境检查'
    )
    
    parser.add_argument(
        '--skip-tests', 
        action='store_true',
        help='跳过测试'
    )
    
    parser.add_argument(
        '--package-only', 
        action='store_true',
        help='仅创建分发包，不部署'
    )
    
    parser.add_argument(
        '--skip-health-check', 
        action='store_true',
        help='跳过健康检查'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    deployer = LocalMusicGeneratorDeployer(args)
    success = deployer.run_deployment()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()