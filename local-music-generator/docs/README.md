# Local Music Generator

一个基于 Facebook MusicGen 模型的本地音乐生成应用程序，提供完整的前端界面和后端API，支持本地部署和使用，无需外部API依赖。

## 🎵 功能特性

- **🎼 音乐生成**: 基于文本描述生成高质量音乐
- **🎛️ 参数控制**: 完整的生成参数调整（时长、创造性、引导强度等）
- **🎵 音频管理**: 完整的音频文件管理系统
- **📱 响应式设计**: 支持桌面和移动设备
- **🎨 现代UI**: 采用苹果风格的现代界面设计
- **⚡ 性能优化**: 包含完整的性能监控和优化系统
- **🔧 系统监控**: 实时资源使用监控
- **🎯 无API依赖**: 完全本地运行，数据安全

## 🚀 快速开始

### 系统要求

#### 最低要求
- **操作系统**: Windows 10+, macOS 10.15+, 或 Linux (Ubuntu 18.04+)
- **内存**: 8GB RAM
- **存储**: 10GB 可用空间
- **Python**: 3.8+
- **Node.js**: 16+
- **处理器**: 4核以上

#### 推荐配置
- **内存**: 16GB+ RAM
- **GPU**: NVIDIA GPU (支持CUDA) 用于加速
- **存储**: SSD 硬盘
- **处理器**: 8核以上

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/yourusername/local-music-generator.git
cd local-music-generator
```

#### 2. 后端安装
```bash
cd backend
pip install -r requirements.txt
```

#### 3. 前端安装
```bash
cd frontend
npm install
```

#### 4. 启动应用

**启动后端服务**:
```bash
cd backend
python main.py
```

**启动前端开发服务器**:
```bash
cd frontend
npm run dev
```

#### 5. 访问应用
打开浏览器访问 `http://localhost:3000`

## 📖 使用指南

### 基本使用

1. **打开应用**: 在浏览器中打开应用程序
2. **输入描述**: 在文本框中输入音乐描述，例如 "upbeat jazz piano with drums"
3. **调整参数**: 根据需要调整生成参数
4. **开始生成**: 点击"Generate Music"按钮
5. **播放音乐**: 生成完成后可以直接播放和下载

### 参数说明

#### 基本参数
- **Duration (时长)**: 生成音乐的长度，范围 10-120 秒
- **Temperature (创造性)**: 控制生成的随机性，0.1-1.0
  - 低值 (0.1-0.5): 更保守，可预测性强
  - 高值 (0.6-1.0): 更有创造性，变化更大

#### 高级参数
- **Top K**: 限制每步选择的token数量，1-100
- **Top P**: 核心采样参数，0.1-1.0
- **Guidance Scale**: 文本引导强度，1.0-15.0
  - 低值: 更自由的生成
  - 高值: 更严格遵循文本描述

### 文本描述技巧

#### 有效的描述示例
- "slow acoustic guitar ballad with soft vocals"
- "energetic electronic dance music with heavy bass"
- "classical piano sonata in minor key"
- "jazz quartet with saxophone and drums"
- "ambient nature sounds with soft synthesizer"

#### 描述建议
- 包含**乐器类型** (piano, guitar, drums, synthesizer)
- 指定**音乐风格** (jazz, classical, electronic, folk)
- 描述**节奏感** (slow, fast, energetic, calm)
- 添加**情绪色彩** (happy, sad, mysterious, uplifting)

### 音频管理

#### 播放控制
- **播放/暂停**: 点击播放按钮或按空格键
- **进度控制**: 点击进度条跳转到指定位置
- **音量调节**: 使用音量滑块或方向键
- **快进/快退**: 使用键盘左右方向键

#### 文件管理
- **下载**: 点击下载按钮保存音频文件
- **重命名**: 在音频库中编辑文件名
- **删除**: 从音频库中删除不需要的文件
- **排序**: 按时间、名称或时长排序

### 键盘快捷键

#### 导航快捷键
- `Ctrl + 1`: 主页
- `Ctrl + 2`: 音频库
- `Ctrl + 3`: 历史记录
- `Ctrl + 4`: 设置页面

#### 应用快捷键
- `Ctrl + G`: 开始生成音乐
- `Ctrl + T`: 切换主题
- `/`: 显示帮助

#### 音频播放快捷键
- `Space` 或 `K`: 播放/暂停
- `S`: 停止播放
- `M`: 静音/取消静音
- `↑/↓`: 音量调节
- `←/→`: 快进/快退

## 🔧 高级配置

### 性能优化

#### GPU 加速
如果您有 NVIDIA GPU，应用会自动使用 GPU 加速：
```python
# 检查 GPU 可用性
import torch
print(torch.cuda.is_available())
```

#### 内存优化
在设置页面可以调整内存使用：
- **内存限制**: 设置最大内存使用量
- **批处理大小**: 调整批处理大小以平衡性能和内存
- **缓存管理**: 配置结果缓存大小

#### 性能监控
应用内置性能监控功能：
- **资源使用**: 实时监控 CPU、内存、磁盘使用
- **生成性能**: 跟踪生成时间和成功率
- **系统健康**: 自动检测性能问题

### 环境变量

创建 `.env` 文件配置环境变量：

```env
# 基本配置
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
CACHE_SIZE=100

# 监控配置
ENABLE_MONITORING=true
MONITORING_INTERVAL=1.0
RESOURCE_HISTORY_SIZE=1000
```

## 🛠️ 故障排除

### 常见问题

#### 1. 模型加载失败
**问题**: 启动时显示"Model loading failed"
**解决方案**:
- 检查网络连接（首次运行需要下载模型）
- 确认有足够的磁盘空间（约 5GB）
- 查看错误日志：`tail -f backend/logs/app.log`

#### 2. 内存不足
**问题**: 生成过程中出现内存错误
**解决方案**:
- 减少生成时长（< 60 秒）
- 降低批处理大小
- 关闭其他应用程序释放内存
- 在设置中启用内存优化

#### 3. 音频播放问题
**问题**: 生成的音频无法播放
**解决方案**:
- 检查浏览器音频支持
- 尝试下载文件本地播放
- 更新浏览器到最新版本
- 检查音频格式设置

#### 4. 生成速度缓慢
**问题**: 音乐生成时间过长
**解决方案**:
- 确认 GPU 驱动已正确安装
- 减少生成时长
- 在设置中启用性能优化
- 关闭其他占用 GPU 的应用

#### 5. 前端连接后端失败
**问题**: 前端无法连接到后端服务
**解决方案**:
- 确认后端服务正在运行
- 检查端口是否被占用
- 验证防火墙设置
- 查看浏览器控制台错误

### 日志和调试

#### 后端日志
```bash
# 查看实时日志
tail -f backend/logs/app.log

# 查看错误日志
tail -f backend/logs/error.log

# 查看性能日志
tail -f backend/logs/performance.log
```

#### 前端调试
1. 打开浏览器开发者工具 (F12)
2. 查看 Console 标签页的错误信息
3. 检查 Network 标签页的请求状态
4. 确认 Local Storage 中的设置

#### 性能分析
在设置页面启用性能分析：
- **生成性能**: 跟踪每次生成的时间
- **资源使用**: 监控系统资源
- **错误统计**: 记录错误和警告

### 兼容性检查

在设置页面运行兼容性检查：
- **浏览器支持**: 检查浏览器版本和功能
- **设备性能**: 分析设备硬件能力
- **音频支持**: 测试音频格式兼容性
- **网络性能**: 检查网络连接质量

## 📝 更新日志

### v1.0.0 (当前版本)
- ✅ 完整的音乐生成功能
- ✅ 现代化的用户界面
- ✅ 完整的音频管理系统
- ✅ 性能监控和优化
- ✅ 响应式设计支持
- ✅ 键盘快捷键支持
- ✅ 兼容性测试工具

### 即将发布的功能
- 🔄 批量生成功能
- 🔄 音频编辑工具
- 🔄 更多音乐风格预设
- 🔄 协作功能
- 🔄 API 接口文档

## 🤝 支持和贡献

### 获取帮助
- 📖 [GitHub Issues](https://github.com/yourusername/local-music-generator/issues)
- 💬 [讨论区](https://github.com/yourusername/local-music-generator/discussions)
- 📧 Email: support@example.com

### 贡献代码
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 报告问题
提交问题时请包含：
- 操作系统和版本
- 浏览器和版本
- 重现步骤
- 错误信息
- 相关日志

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Facebook MusicGen](https://github.com/facebookresearch/musicgen) - 核心音乐生成模型
- [Hugging Face Transformers](https://huggingface.co/transformers/) - 模型推理框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端API框架
- [React](https://reactjs.org/) - 前端框架
- [Styled Components](https://styled-components.com/) - 样式系统

---

**享受音乐创作的乐趣！** 🎵✨