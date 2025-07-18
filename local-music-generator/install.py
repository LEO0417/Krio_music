#!/usr/bin/env python3
"""
Local Music Generator 安装脚本
自动化安装和配置过程
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
        logging.FileHandler('install.log'),
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

class InstallationError(Exception):
    """安装错误异常"""
    pass

class LocalMusicGeneratorInstaller:
    """本地音乐生成器安装器"""
    
    def __init__(self, args):
        self.args = args
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.docs_dir = self.root_dir / "docs"
        
        # 系统信息
        self.system = platform.system()
        self.architecture = platform.machine()
        self.python_version = sys.version_info
        
        # 安装状态
        self.installation_status = {
            'system_check': False,
            'dependencies': False,
            'backend_setup': False,
            'frontend_setup': False,
            'configuration': False,
            'test_run': False
        }
        
        logger.info(f"初始化安装器 - 系统: {self.system}, 架构: {self.architecture}")
    
    def print_header(self):
        """打印欢迎信息"""
        print(f"{Colors.BLUE}{Colors.BOLD}")
        print("="*60)
        print("    Local Music Generator 安装器")
        print("    基于 Facebook MusicGen 的本地音乐生成应用")
        print("="*60)
        print(f"{Colors.END}")
        print()
    
    def check_system_requirements(self) -> bool:
        """检查系统要求"""
        print(f"{Colors.YELLOW}🔍 检查系统要求...{Colors.END}")
        
        requirements_met = True
        
        # 检查Python版本
        if self.python_version < (3, 8):
            print(f"{Colors.RED}❌ Python 版本过低 (需要 3.8+, 当前 {'.'.join(map(str, self.python_version[:2]))}):{Colors.END}")
            requirements_met = False
        else:
            print(f"{Colors.GREEN}✅ Python 版本: {'.'.join(map(str, self.python_version[:3]))}{Colors.END}")
        
        # 检查pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
            print(f"{Colors.GREEN}✅ pip 已安装{Colors.END}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ pip 未安装{Colors.END}")
            requirements_met = False
        
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
            print(f"{Colors.RED}❌ Node.js 未安装 (需要 16+){Colors.END}")
            requirements_met = False
        
        # 检查npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"{Colors.GREEN}✅ npm 版本: {version}{Colors.END}")
            else:
                raise subprocess.CalledProcessError(1, 'npm')
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}❌ npm 未安装{Colors.END}")
            requirements_met = False
        
        # 检查GPU支持
        gpu_available = False
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0)
                print(f"{Colors.GREEN}✅ GPU 支持: {gpu_name} (共 {gpu_count} 个){Colors.END}")
                gpu_available = True
            else:
                print(f"{Colors.YELLOW}⚠️  GPU 不可用，将使用 CPU 模式{Colors.END}")
        except ImportError:
            print(f"{Colors.YELLOW}⚠️  PyTorch 未安装，稍后将安装{Colors.END}")
        
        # 检查磁盘空间
        free_space = shutil.disk_usage(self.root_dir).free / (1024**3)  # GB
        if free_space < 10:
            print(f"{Colors.RED}❌ 磁盘空间不足 (需要 10GB+, 可用 {free_space:.1f}GB){Colors.END}")
            requirements_met = False
        else:
            print(f"{Colors.GREEN}✅ 磁盘空间: {free_space:.1f}GB 可用{Colors.END}")
        
        # 检查内存
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            if memory_gb < 8:
                print(f"{Colors.YELLOW}⚠️  内存较少 (建议 8GB+, 当前 {memory_gb:.1f}GB){Colors.END}")
            else:
                print(f"{Colors.GREEN}✅ 内存: {memory_gb:.1f}GB{Colors.END}")
        except ImportError:
            print(f"{Colors.YELLOW}⚠️  无法检查内存信息{Colors.END}")
        
        self.installation_status['system_check'] = requirements_met
        return requirements_met
    
    def install_backend_dependencies(self) -> bool:
        """安装后端依赖"""
        print(f"\n{Colors.YELLOW}📦 安装后端依赖...{Colors.END}")
        
        try:
            # 创建虚拟环境（可选）
            if self.args.create_venv:
                print("创建虚拟环境...")
                venv_path = self.root_dir / "venv"
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], 
                             check=True)
                
                # 激活虚拟环境
                if self.system == "Windows":
                    python_executable = venv_path / "Scripts" / "python.exe"
                    pip_executable = venv_path / "Scripts" / "pip.exe"
                else:
                    python_executable = venv_path / "bin" / "python"
                    pip_executable = venv_path / "bin" / "pip"
            else:
                python_executable = sys.executable
                pip_executable = sys.executable
            
            # 升级pip
            print("升级 pip...")
            subprocess.run([str(pip_executable), 'install', '--upgrade', 'pip'], 
                         check=True)
            
            # 安装依赖
            requirements_file = self.backend_dir / "requirements.txt"
            if requirements_file.exists():
                print("安装 Python 依赖...")
                subprocess.run([str(pip_executable), 'install', '-r', str(requirements_file)], 
                             check=True)
            else:
                print("手动安装核心依赖...")
                core_deps = [
                    'fastapi>=0.100.0',
                    'uvicorn>=0.22.0',
                    'torch>=2.0.0',
                    'transformers>=4.30.0',
                    'librosa>=0.10.0',
                    'psutil>=5.9.0',
                    'pytest>=7.3.1'
                ]
                
                for dep in core_deps:
                    print(f"安装 {dep}...")
                    subprocess.run([str(pip_executable), 'install', dep], 
                                 check=True)
            
            print(f"{Colors.GREEN}✅ 后端依赖安装完成{Colors.END}")
            self.installation_status['dependencies'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 后端依赖安装失败: {e}{Colors.END}")
            return False
    
    def install_frontend_dependencies(self) -> bool:
        """安装前端依赖"""
        print(f"\n{Colors.YELLOW}📦 安装前端依赖...{Colors.END}")
        
        try:
            # 切换到前端目录
            os.chdir(self.frontend_dir)
            
            # 安装npm依赖
            print("安装 npm 依赖...")
            subprocess.run(['npm', 'install'], check=True)
            
            print(f"{Colors.GREEN}✅ 前端依赖安装完成{Colors.END}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 前端依赖安装失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def setup_backend(self) -> bool:
        """设置后端"""
        print(f"\n{Colors.YELLOW}⚙️  设置后端...{Colors.END}")
        
        try:
            # 创建必要的目录
            data_dir = self.backend_dir / "data"
            logs_dir = self.backend_dir / "logs"
            models_dir = data_dir / "models"
            audio_dir = data_dir / "audio"
            
            for directory in [data_dir, logs_dir, models_dir, audio_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"创建目录: {directory}")
            
            # 创建环境变量文件
            env_file = self.backend_dir / ".env"
            if not env_file.exists():
                env_content = f"""# Local Music Generator 配置
APP_NAME=Local Music Generator
DEBUG=false
LOG_LEVEL=INFO

# 服务器配置
HOST=localhost
PORT=8000
FRONTEND_URL=http://localhost:3000

# 模型配置
MODEL_NAME=facebook/musicgen-small
MODEL_CACHE_DIR=./data/models
AUTO_LOAD_MODEL=true
USE_GPU={"true" if self.args.gpu else "false"}

# 音频配置
AUDIO_OUTPUT_DIR=./data/audio
AUDIO_FORMAT=mp3
AUDIO_SAMPLE_RATE=44100
AUDIO_QUALITY=high

# 性能配置
MAX_MEMORY_MB=8192
MAX_GENERATION_TIME=300
ENABLE_CACHING=true
CACHE_SIZE=100

# 监控配置
ENABLE_MONITORING=true
MONITORING_INTERVAL=1.0
RESOURCE_HISTORY_SIZE=1000
"""
                env_file.write_text(env_content)
                print(f"创建环境配置文件: {env_file}")
            
            print(f"{Colors.GREEN}✅ 后端设置完成{Colors.END}")
            self.installation_status['backend_setup'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 后端设置失败: {e}{Colors.END}")
            return False
    
    def setup_frontend(self) -> bool:
        """设置前端"""
        print(f"\n{Colors.YELLOW}⚙️  设置前端...{Colors.END}")
        
        try:
            # 创建前端配置文件
            vite_config = self.frontend_dir / "vite.config.ts"
            if not vite_config.exists():
                vite_content = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
"""
                vite_config.write_text(vite_content)
                print(f"创建 Vite 配置文件: {vite_config}")
            
            print(f"{Colors.GREEN}✅ 前端设置完成{Colors.END}")
            self.installation_status['frontend_setup'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 前端设置失败: {e}{Colors.END}")
            return False
    
    def create_startup_scripts(self) -> bool:
        """创建启动脚本"""
        print(f"\n{Colors.YELLOW}📝 创建启动脚本...{Colors.END}")
        
        try:
            # 创建后端启动脚本
            if self.system == "Windows":
                backend_script = self.root_dir / "start_backend.bat"
                backend_content = f"""@echo off
cd /d "{self.backend_dir}"
{"venv\\Scripts\\python.exe" if self.args.create_venv else "python"} main.py
pause
"""
                backend_script.write_text(backend_content)
                
                frontend_script = self.root_dir / "start_frontend.bat"
                frontend_content = f"""@echo off
cd /d "{self.frontend_dir}"
npm run dev
pause
"""
                frontend_script.write_text(frontend_content)
                
                full_script = self.root_dir / "start_all.bat"
                full_content = f"""@echo off
echo Starting Local Music Generator...
echo.
echo Starting backend...
start "Backend" cmd /c "start_backend.bat"
timeout /t 3
echo Starting frontend...
start "Frontend" cmd /c "start_frontend.bat"
echo.
echo Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
"""
                full_script.write_text(full_content)
                
            else:
                backend_script = self.root_dir / "start_backend.sh"
                backend_content = f"""#!/bin/bash
cd "{self.backend_dir}"
{"./venv/bin/python" if self.args.create_venv else "python3"} main.py
"""
                backend_script.write_text(backend_content)
                backend_script.chmod(0o755)
                
                frontend_script = self.root_dir / "start_frontend.sh"
                frontend_content = f"""#!/bin/bash
cd "{self.frontend_dir}"
npm run dev
"""
                frontend_script.write_text(frontend_content)
                frontend_script.chmod(0o755)
                
                full_script = self.root_dir / "start_all.sh"
                full_content = f"""#!/bin/bash
echo "Starting Local Music Generator..."
echo ""
echo "Starting backend..."
./start_backend.sh &
BACKEND_PID=$!
sleep 3
echo "Starting frontend..."
./start_frontend.sh &
FRONTEND_PID=$!
echo ""
echo "Application is starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"
wait $BACKEND_PID $FRONTEND_PID
"""
                full_script.write_text(full_content)
                full_script.chmod(0o755)
            
            print(f"{Colors.GREEN}✅ 启动脚本创建完成{Colors.END}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 启动脚本创建失败: {e}{Colors.END}")
            return False
    
    def test_installation(self) -> bool:
        """测试安装"""
        print(f"\n{Colors.YELLOW}🧪 测试安装...{Colors.END}")
        
        try:
            # 测试后端导入
            print("测试后端模块...")
            os.chdir(self.backend_dir)
            
            # 测试基本导入
            test_imports = [
                'fastapi',
                'uvicorn',
                'torch',
                'transformers',
                'librosa',
                'psutil'
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    print(f"  ✅ {module}")
                except ImportError as e:
                    print(f"  ❌ {module}: {e}")
                    return False
            
            # 测试前端构建
            print("测试前端构建...")
            os.chdir(self.frontend_dir)
            
            # 运行类型检查
            result = subprocess.run(['npx', 'tsc', '--noEmit'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  ⚠️  TypeScript 检查警告: {result.stderr}")
            else:
                print("  ✅ TypeScript 检查通过")
            
            print(f"{Colors.GREEN}✅ 安装测试完成{Colors.END}")
            self.installation_status['test_run'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 安装测试失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def generate_report(self) -> None:
        """生成安装报告"""
        print(f"\n{Colors.BLUE}📋 安装报告{Colors.END}")
        print("="*50)
        
        total_steps = len(self.installation_status)
        completed_steps = sum(self.installation_status.values())
        
        print(f"安装进度: {completed_steps}/{total_steps} ({completed_steps/total_steps*100:.1f}%)")
        print()
        
        for step, status in self.installation_status.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {step.replace('_', ' ').title()}")
        
        print()
        
        if completed_steps == total_steps:
            print(f"{Colors.GREEN}🎉 安装完成!{Colors.END}")
            print()
            print("启动应用:")
            if self.system == "Windows":
                print("  双击 start_all.bat 或运行:")
                print("  start_backend.bat (后端)")
                print("  start_frontend.bat (前端)")
            else:
                print("  ./start_all.sh 或分别运行:")
                print("  ./start_backend.sh (后端)")
                print("  ./start_frontend.sh (前端)")
            print()
            print("访问地址:")
            print("  前端: http://localhost:3000")
            print("  后端API: http://localhost:8000")
            print("  API文档: http://localhost:8000/docs")
        else:
            print(f"{Colors.RED}❌ 安装未完成{Colors.END}")
            print("请检查错误信息并重新运行安装程序")
        
        # 保存报告到文件
        report_file = self.root_dir / "installation_report.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system': self.system,
            'architecture': self.architecture,
            'python_version': '.'.join(map(str, self.python_version[:3])),
            'installation_status': self.installation_status,
            'success': completed_steps == total_steps
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
    
    def run_installation(self) -> bool:
        """运行完整安装流程"""
        self.print_header()
        
        try:
            # 1. 系统检查
            if not self.check_system_requirements():
                if not self.args.force:
                    print(f"{Colors.RED}系统要求不满足，安装终止{Colors.END}")
                    return False
                else:
                    print(f"{Colors.YELLOW}强制模式：跳过系统要求检查{Colors.END}")
            
            # 2. 安装依赖
            if not self.install_backend_dependencies():
                raise InstallationError("后端依赖安装失败")
            
            if not self.install_frontend_dependencies():
                raise InstallationError("前端依赖安装失败")
            
            # 3. 设置环境
            if not self.setup_backend():
                raise InstallationError("后端设置失败")
            
            if not self.setup_frontend():
                raise InstallationError("前端设置失败")
            
            # 4. 创建启动脚本
            if not self.create_startup_scripts():
                raise InstallationError("启动脚本创建失败")
            
            # 5. 测试安装
            if not self.args.skip_test:
                if not self.test_installation():
                    raise InstallationError("安装测试失败")
            
            return True
            
        except InstallationError as e:
            logger.error(f"安装失败: {e}")
            return False
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}安装被用户中断{Colors.END}")
            return False
        except Exception as e:
            logger.error(f"意外错误: {e}")
            return False
        finally:
            self.generate_report()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Local Music Generator 安装脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--create-venv', 
        action='store_true',
        help='创建虚拟环境'
    )
    
    parser.add_argument(
        '--gpu', 
        action='store_true',
        help='启用GPU支持'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制安装，跳过系统要求检查'
    )
    
    parser.add_argument(
        '--skip-test', 
        action='store_true',
        help='跳过安装测试'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    installer = LocalMusicGeneratorInstaller(args)
    success = installer.run_installation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()