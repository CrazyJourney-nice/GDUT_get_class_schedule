# GDUT Class Schedule Fetcher (GDUT 课表获取工具)

## 简介
这是一个为广东工业大学 (GDUT) 学生设计的命令行工具。它能自动从教务系统爬取指定学期的课表，并生成标准日历文件 (`.ics`)。生成的日历文件可以直接导入到 iPhone (iOS) 或 Android 手机的日历应用中，让你随时随地查看课程安排。

本项目使用了现代化的 CLI 界面，支持 Windows, macOS 和 Linux。

## ✨ 功能特性
*   **自动爬取**: 只需输入学期代码和 Cookie，即可获取完整课表。
*   **美观界面**: 使用 `Rich` 库打造的现代化终端界面，包含进度条和彩色提示。
*   **并发加速**: 采用多线程技术，秒级获取 20 周课表。
*   **跨平台**: 提供 Windows, macOS 和 Linux 的独立可执行文件。
*   **稳定可靠**: 内置重试机制和智能错误处理。

## 📥 使用方法

1.  克隆仓库:
    ```bash
    git clone https://github.com/yourusername/GDUT_get_class_schedule.git
    cd GDUT_get_class_schedule
    ```
2.  安装依赖 (推荐使用 `uv`):
    ```bash
    uv sync
    ```
3.  运行:
    ```bash
    python get_your_scheduleOriginal.py
    ```

## 🚀 使用指南
1. **运行**get_your_scheduleOriginal.py
2. 按照提示输入**学号**和**密码**
3. 程序运行完成后，会在同目录下生成 `my_schedule.ics`。


## 📱 导入手机日历

*   **iOS (iPhone/iPad)**:
    *   将 `my_schedule.ics` 发送给自己的微信/QQ/邮箱。
    *   用系统自带的“文件”或“邮件”应用打开，点击“添加所有事件”即可。
*   **Android**:
    *   发送文件到手机，直接用系统日历应用打开并导入。

## 🛠️ 开发与构建

本项目使用 `uv` 进行包管理。

### 构建可执行文件
```bash
uv run pyinstaller get_your_schedule.spec
```
构建产物将位于 `dist/` 目录。

## 📝 贡献
欢迎提交 Issue 或 Pull Request 来改进这个项目！

## 📄 许可证
MIT License
