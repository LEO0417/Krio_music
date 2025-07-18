#!/usr/bin/env python3
"""
Local Music Generator 构建脚本
处理构建流程和依赖检查
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

class BuildError(Exception):
    """构建错误异常"""
    pass

class LocalMusicGeneratorBuilder:
    """本地音乐生成器构建器"""
    
    def __init__(self, args):
        self.args = args
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.build_dir = self.root_dir / "build"
        
        # 构建状态
        self.build_status = {
            'clean': False,
            'backend_lint': False,
            'backend_test': False,
            'backend_build': False,
            'frontend_lint': False,
            'frontend_test': False,
            'frontend_build': False,
            'documentation': False,
            'package': False
        }
        
        logger.info("初始化构建器")
    
    def clean_build_directory(self) -> bool:
        """清理构建目录"""
        print(f"{Colors.YELLOW}🧹 清理构建目录...{Colors.END}")
        
        try:
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                print(f"删除构建目录: {self.build_dir}")
            
            self.build_dir.mkdir(exist_ok=True)
            print(f"创建构建目录: {self.build_dir}")
            
            # 清理缓存
            cache_dirs = [
                self.backend_dir / "__pycache__",
                self.backend_dir / ".pytest_cache",
                self.frontend_dir / "node_modules" / ".cache",
                self.frontend_dir / "dist",
                self.frontend_dir / ".next",
            ]
            
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    print(f"清理缓存: {cache_dir}")
            
            print(f"{Colors.GREEN}✅ 构建目录清理完成{Colors.END}")
            self.build_status['clean'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 构建目录清理失败: {e}{Colors.END}")
            return False
    
    def lint_backend(self) -> bool:
        """后端代码检查"""
        print(f"{Colors.YELLOW}🔍 后端代码检查...{Colors.END}")
        
        try:
            os.chdir(self.backend_dir)
            
            # 检查是否有linting工具
            lint_tools = []
            
            # 检查flake8
            try:
                subprocess.run(['flake8', '--version'], 
                             capture_output=True, check=True)
                lint_tools.append('flake8')
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # 检查black
            try:
                subprocess.run(['black', '--version'], 
                             capture_output=True, check=True)
                lint_tools.append('black')
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # 检查mypy
            try:
                subprocess.run(['mypy', '--version'], 
                             capture_output=True, check=True)
                lint_tools.append('mypy')
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            if not lint_tools:
                print(f"{Colors.YELLOW}⚠️  没有找到linting工具，跳过代码检查{Colors.END}")
                self.build_status['backend_lint'] = True
                return True
            
            # 运行linting
            if 'flake8' in lint_tools:
                print("运行 flake8...")
                subprocess.run(['flake8', '.'], check=True)
            
            if 'black' in lint_tools:
                print("运行 black...")
                subprocess.run(['black', '--check', '.'], check=True)
            
            if 'mypy' in lint_tools:
                print("运行 mypy...")
                subprocess.run(['mypy', '.'], check=True)
            
            print(f"{Colors.GREEN}✅ 后端代码检查通过{Colors.END}")
            self.build_status['backend_lint'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 后端代码检查失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def test_backend(self) -> bool:
        """后端测试"""
        print(f"{Colors.YELLOW}🧪 后端测试...{Colors.END}")
        
        try:
            os.chdir(self.backend_dir)
            
            # 运行pytest
            cmd = [sys.executable, '-m', 'pytest']
            
            if self.args.coverage:
                cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
            
            if self.args.verbose:
                cmd.append('-v')
            
            subprocess.run(cmd, check=True)
            
            print(f"{Colors.GREEN}✅ 后端测试通过{Colors.END}")
            self.build_status['backend_test'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 后端测试失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def build_backend(self) -> bool:
        """构建后端"""
        print(f"{Colors.YELLOW}🔨 构建后端...{Colors.END}")
        
        try:
            os.chdir(self.backend_dir)
            
            # 创建后端构建目录
            backend_build_dir = self.build_dir / "backend"
            backend_build_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制源代码
            source_dirs = ['api', 'models', 'config', 'utils', 'audio']
            source_files = ['main.py', 'requirements.txt']
            
            for src_dir in source_dirs:
                src_path = self.backend_dir / src_dir
                if src_path.exists():
                    dst_path = backend_build_dir / src_dir
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    print(f"复制目录: {src_dir}")
            
            for src_file in source_files:
                src_path = self.backend_dir / src_file
                if src_path.exists():
                    dst_path = backend_build_dir / src_file
                    shutil.copy2(src_path, dst_path)
                    print(f"复制文件: {src_file}")
            
            # 编译Python文件
            print("编译Python文件...")
            subprocess.run([sys.executable, '-m', 'compileall', str(backend_build_dir)], 
                         check=True)
            
            # 创建版本信息文件
            version_info = {
                'version': '1.0.0',
                'build_date': datetime.now().isoformat(),
                'build_type': self.args.build_type,
                'git_commit': self.get_git_commit(),
                'python_version': sys.version
            }
            
            with open(backend_build_dir / 'version.json', 'w') as f:
                json.dump(version_info, f, indent=2)
            
            print(f"{Colors.GREEN}✅ 后端构建完成{Colors.END}")
            self.build_status['backend_build'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 后端构建失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def lint_frontend(self) -> bool:
        """前端代码检查"""
        print(f"{Colors.YELLOW}🔍 前端代码检查...{Colors.END}")
        
        try:
            os.chdir(self.frontend_dir)
            
            # 运行ESLint
            print("运行 ESLint...")
            subprocess.run(['npm', 'run', 'lint'], check=True)
            
            # 运行TypeScript检查
            print("运行 TypeScript 检查...")
            subprocess.run(['npx', 'tsc', '--noEmit'], check=True)
            
            print(f"{Colors.GREEN}✅ 前端代码检查通过{Colors.END}")
            self.build_status['frontend_lint'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 前端代码检查失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def test_frontend(self) -> bool:
        """前端测试"""
        print(f"{Colors.YELLOW}🧪 前端测试...{Colors.END}")
        
        try:
            os.chdir(self.frontend_dir)
            
            # 运行Jest测试
            cmd = ['npm', 'test', '--', '--watchAll=false']
            
            if self.args.coverage:
                cmd.append('--coverage')
            
            if self.args.verbose:
                cmd.append('--verbose')
            
            subprocess.run(cmd, check=True)
            
            print(f"{Colors.GREEN}✅ 前端测试通过{Colors.END}")
            self.build_status['frontend_test'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 前端测试失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def build_frontend(self) -> bool:
        """构建前端"""
        print(f"{Colors.YELLOW}🔨 构建前端...{Colors.END}")
        
        try:
            os.chdir(self.frontend_dir)
            
            # 设置构建环境变量
            env = os.environ.copy()
            env['NODE_ENV'] = 'production'
            env['REACT_APP_BUILD_TYPE'] = self.args.build_type
            env['REACT_APP_VERSION'] = '1.0.0'
            env['REACT_APP_BUILD_DATE'] = datetime.now().isoformat()
            
            # 运行构建
            print("运行前端构建...")
            subprocess.run(['npm', 'run', 'build'], env=env, check=True)
            
            # 复制构建结果
            frontend_build_dir = self.build_dir / "frontend"
            frontend_build_dir.mkdir(parents=True, exist_ok=True)
            
            dist_dir = self.frontend_dir / "dist"
            if dist_dir.exists():
                shutil.copytree(dist_dir, frontend_build_dir, dirs_exist_ok=True)
                print(f"复制构建结果到: {frontend_build_dir}")
            
            # 生成构建报告
            self.generate_build_report('frontend')
            
            print(f"{Colors.GREEN}✅ 前端构建完成{Colors.END}")
            self.build_status['frontend_build'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}❌ 前端构建失败: {e}{Colors.END}")
            return False
        finally:
            os.chdir(self.root_dir)
    
    def generate_documentation(self) -> bool:
        """生成文档"""
        print(f"{Colors.YELLOW}📚 生成文档...{Colors.END}")
        
        try:
            docs_build_dir = self.build_dir / "docs"
            docs_build_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制现有文档
            docs_dir = self.root_dir / "docs"
            if docs_dir.exists():
                shutil.copytree(docs_dir, docs_build_dir, dirs_exist_ok=True)
                print("复制文档文件")
            
            # 生成API文档
            self.generate_api_documentation(docs_build_dir)
            
            # 生成README
            self.generate_build_readme(docs_build_dir)
            
            print(f"{Colors.GREEN}✅ 文档生成完成{Colors.END}")
            self.build_status['documentation'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 文档生成失败: {e}{Colors.END}")
            return False
    
    def generate_api_documentation(self, docs_dir: Path):
        """生成API文档"""
        try:
            # 使用FastAPI自动生成API文档
            api_doc = docs_dir / "api.md"
            api_content = """# API Documentation

## Overview
Local Music Generator 提供RESTful API用于音乐生成和管理。

## Base URL
```
http://localhost:8000
```

## Authentication
当前版本不需要身份验证。

## Endpoints

### Health Check
```
GET /health
```
检查服务健康状态。

### Generate Music
```
POST /api/generate
```
生成音乐。

**Parameters:**
- `prompt` (string): 音乐描述
- `duration` (integer): 时长（秒）
- `temperature` (float): 创造性参数
- `top_k` (integer): Top-K参数
- `top_p` (float): Top-P参数
- `guidance_scale` (float): 引导强度

### Get Models
```
GET /api/models
```
获取可用模型列表。

### System Status
```
GET /api/system/status
```
获取系统状态信息。

## Error Handling
API使用标准HTTP状态码：
- 200: 成功
- 400: 客户端错误
- 500: 服务器错误

## Rate Limiting
目前没有速率限制。

## WebSocket Support
支持WebSocket连接用于实时状态更新。
"""
            api_doc.write_text(api_content)
            print("生成API文档")
            
        except Exception as e:
            logger.error(f"生成API文档失败: {e}")
    
    def generate_build_readme(self, docs_dir: Path):
        """生成构建说明"""
        readme_content = f"""# Local Music Generator - Build {self.args.build_type.title()}

## Build Information
- **Version**: 1.0.0
- **Build Date**: {datetime.now().isoformat()}
- **Build Type**: {self.args.build_type}
- **Git Commit**: {self.get_git_commit()}

## Build Status
"""
        
        for step, status in self.build_status.items():
            icon = "✅" if status else "❌"
            readme_content += f"- {icon} {step.replace('_', ' ').title()}\n"
        
        readme_content += f"""
## Directory Structure
```
build/
├── backend/          # 后端构建文件
├── frontend/         # 前端构建文件
├── docs/             # 文档文件
└── package/          # 打包文件
```

## Deployment
参见部署文档或运行 `python deploy.py` 进行部署。

## Testing
- 后端测试: `pytest` in backend directory
- 前端测试: `npm test` in frontend directory

## Performance
- 构建时间: {self.get_build_time()}
- 包大小: {self.get_package_size()}

## Support
如有问题请联系开发团队。
"""
        
        readme_path = docs_dir / "BUILD_README.md"
        readme_path.write_text(readme_content)
        print("生成构建说明")
    
    def create_package(self) -> bool:
        """创建分发包"""
        print(f"{Colors.YELLOW}📦 创建分发包...{Colors.END}")
        
        try:
            package_dir = self.build_dir / "package"
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制构建文件
            build_components = ['backend', 'frontend', 'docs']
            for component in build_components:
                src_path = self.build_dir / component
                if src_path.exists():
                    dst_path = package_dir / component
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    print(f"打包组件: {component}")
            
            # 创建包信息文件
            package_info = {
                'name': 'local-music-generator',
                'version': '1.0.0',
                'build_date': datetime.now().isoformat(),
                'build_type': self.args.build_type,
                'components': build_components,
                'checksum': self.calculate_checksum(package_dir)
            }
            
            with open(package_dir / 'package.json', 'w') as f:
                json.dump(package_info, f, indent=2)
            
            print(f"{Colors.GREEN}✅ 分发包创建完成{Colors.END}")
            self.build_status['package'] = True
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ 分发包创建失败: {e}{Colors.END}")
            return False
    
    def generate_build_report(self, component: str):
        """生成构建报告"""
        report_dir = self.build_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"{component}_build_report.json"
        
        if component == 'frontend':
            # 分析前端构建结果
            dist_dir = self.frontend_dir / "dist"
            if dist_dir.exists():
                files = list(dist_dir.rglob("*"))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                report = {
                    'component': component,
                    'build_date': datetime.now().isoformat(),
                    'total_files': len(files),
                    'total_size': total_size,
                    'files': [str(f.relative_to(dist_dir)) for f in files if f.is_file()]
                }
                
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
    
    def get_git_commit(self) -> str:
        """获取Git提交哈希"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except Exception:
            pass
        return 'unknown'
    
    def get_build_time(self) -> str:
        """获取构建时间"""
        return "估计构建时间"
    
    def get_package_size(self) -> str:
        """获取包大小"""
        try:
            package_dir = self.build_dir / "package"
            if package_dir.exists():
                total_size = sum(f.stat().st_size for f in package_dir.rglob("*") if f.is_file())
                return f"{total_size / (1024*1024):.1f} MB"
        except Exception:
            pass
        return "unknown"
    
    def calculate_checksum(self, path: Path) -> str:
        """计算目录校验和"""
        import hashlib
        
        hasher = hashlib.sha256()
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
        return hasher.hexdigest()[:16]
    
    def generate_final_report(self):
        """生成最终构建报告"""
        print(f"\n{Colors.BLUE}📋 构建报告{Colors.END}")
        print("="*50)
        
        total_steps = len(self.build_status)
        completed_steps = sum(self.build_status.values())
        
        print(f"构建进度: {completed_steps}/{total_steps} ({completed_steps/total_steps*100:.1f}%)")
        print()
        
        for step, status in self.build_status.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {step.replace('_', ' ').title()}")
        
        print()
        
        if completed_steps == total_steps:
            print(f"{Colors.GREEN}🎉 构建完成!{Colors.END}")
            print(f"构建文件位于: {self.build_dir}")
            print(f"分发包位于: {self.build_dir / 'package'}")
        else:
            print(f"{Colors.RED}❌ 构建未完成{Colors.END}")
            print("请检查错误信息并重新运行构建")
    
    def run_build(self) -> bool:
        """运行完整构建流程"""
        print(f"{Colors.BLUE}{Colors.BOLD}开始构建 Local Music Generator...{Colors.END}")
        
        try:
            # 1. 清理构建目录
            if not self.clean_build_directory():
                raise BuildError("清理构建目录失败")
            
            # 2. 后端代码检查
            if not self.args.skip_lint:
                if not self.lint_backend():
                    if not self.args.force:
                        raise BuildError("后端代码检查失败")
            
            # 3. 后端测试
            if not self.args.skip_tests:
                if not self.test_backend():
                    if not self.args.force:
                        raise BuildError("后端测试失败")
            
            # 4. 后端构建
            if not self.build_backend():
                raise BuildError("后端构建失败")
            
            # 5. 前端代码检查
            if not self.args.skip_lint:
                if not self.lint_frontend():
                    if not self.args.force:
                        raise BuildError("前端代码检查失败")
            
            # 6. 前端测试
            if not self.args.skip_tests:
                if not self.test_frontend():
                    if not self.args.force:
                        raise BuildError("前端测试失败")
            
            # 7. 前端构建
            if not self.build_frontend():
                raise BuildError("前端构建失败")
            
            # 8. 生成文档
            if not self.generate_documentation():
                raise BuildError("文档生成失败")
            
            # 9. 创建分发包
            if not self.create_package():
                raise BuildError("分发包创建失败")
            
            return True
            
        except BuildError as e:
            logger.error(f"构建失败: {e}")
            return False
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}构建被用户中断{Colors.END}")
            return False
        except Exception as e:
            logger.error(f"意外错误: {e}")
            return False
        finally:
            self.generate_final_report()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Local Music Generator 构建脚本')
    
    parser.add_argument(
        '--build-type',
        choices=['development', 'staging', 'production'],
        default='production',
        help='构建类型'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='跳过测试'
    )
    
    parser.add_argument(
        '--skip-lint',
        action='store_true',
        help='跳过代码检查'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='生成测试覆盖率报告'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制构建，忽略错误'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    builder = LocalMusicGeneratorBuilder(args)
    success = builder.run_build()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()