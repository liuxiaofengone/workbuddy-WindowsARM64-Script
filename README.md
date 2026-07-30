# WorkBuddy Windows ARM64 原生构建工具链

本项目提供了一套完全自动化的工具链，帮助开发者在 **Windows ARM64**（如 Snapdragon X Elite/Plus 平台、Surface Pro、Lenovo Yoga 等设备）上，自动获取最新的腾讯 WorkBuddy (v5.x) 客户端解包、重新编译 Native C++ 插件、烧录 PE 图标头并重新打包为原生 ARM64 安装程序。

---

## 快速开始

### 方式一：双击运行批处理脚本（推荐）

双击运行根目录下的 **`build.bat`**：
1. 运行后将提示输入本地代理端口（例如 `7890`）。
2. 直接按回车将自动使用**网络直连模式**。

### 方式二：命令行运行 Python 脚本

```powershell
python build_workbuddy_arm64.py [--proxy http://127.0.0.1:7890]
```

---

## 详细使用文档与原理说明

请参阅 [README_BUILD.md](README_BUILD.md) 获取详细的环境依赖配置、全自动化构建流程原理及 FAQ。

---

## 开源协议与声明
本工具链仅用于技术交流与个人设备原生运行适配。WorkBuddy 归腾讯科技（深圳）有限公司所有。
