# rez-manager

一个用于管理 [Rez](https://rez.readthedocs.io/en/stable/) 包环境的现代化图形界面工具。

rez-manager 提供桌面 UI，用于创建、编辑、预览和启动面向 DCC 工作流的 Rez context。

## 当前限制

- 当前应用仅在 Windows 平台测试过，其他平台暂不支持。
- rez-manager 不提供 Rez package 创建功能。用户需要根据 [Rez 文档](https://rez.readthedocs.io/en/stable/package_definition.html) 自行创建和维护 package。

## 功能特性

### 按项目分组管理 rez contexts

![group contexts by project](./images/group_contexts_by_project.gif)

### 一键启动 DCC 软件

![launch DCC software](./images/launch_dcc.gif)

### 为每个 context 选择要启动的 DCC 软件

![select DCC software](./images/select_dcc.gif)

### 配置 context 依赖的 packages

![config dependencies packages](./images/config_dependencies_packages.gif)

### 预览 context 解析后的环境

![preview resolved environment](./images/preview_resolved_environment.gif)

### 在配置 packages 时调试 context

![debug context](./images/debug_context.gif)

### 出错时便捷查看错误日志

![error logs](./images/error_logs.gif)

## 示例数据

[`./examples`](./examples) 目录中包含了一组示例项目和 Rez packages，可用于快速体验应用。
将应用设置指向这些示例目录后，你可以在不准备自有 package 仓库的情况下直接预览主要功能。

## 安装与构建

### 环境要求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- 项目环境中可用的 [Rez](https://rez.readthedocs.io/en/stable/)

### 从源码运行

```bash
uv sync
uv run rez-manager
```

### 运行预构建可执行文件

预构建的可执行文件可从 [Releases](https://github.com/FhyTan/rez-manager/releases) 页面下载。

### 构建桌面可执行文件

```bash
uv run pyinstaller --name rez-manager --windowed -y --clean ./src/rez_manager/__main__.py
```

## 开发

### 常用命令

```bash
uvx ruff check src      # 代码检查
uvx ruff format src     # 代码格式化
uv run pytest           # 测试
pyside6-qml-stubgen.exe src --out-dir ./qmltypes
pyside6-qmllint -I ./qmltypes <qml-files>
```

`qmltypes/` 是生成产物，刻意不纳入 git 跟踪。

如果想在 VS Code 等编辑器中获得正确的 QML 提示与补全，请先生成 QML 类型桩：
`pyside6-qml-stubgen.exe src --out-dir ./qmltypes`，然后将 `./qmltypes` 添加到
`qt-qml.qmlls.additionalImportPaths`。

如需基于这些生成类型对 QML 文件做 lint，可使用：
`pyside6-qmllint -I ./qmltypes <qml-files>`。

### 项目结构

```txt
src/rez_manager/
├── adapter/              # Rez API 封装层（唯一允许导入 rez.* 的层）
├── data/                 # 随应用打包的静态数据
├── hooks/                # PyInstaller 运行时 hook
├── models/               # 数据模型（纯 Python）
├── persistence/          # 文件系统存储与 project/context 持久化
├── qml/                  # QML UI 文件
├── resources/            # 图片和其他应用资源
├── ui/                   # 暴露给 QML 的 PySide6 控制器
└── app.py                # 应用启动入口与顶层初始化逻辑
docs/
├── design.md          # UI 与架构设计说明
└── rez-knowledge.md   # 面向 AI/开发的 Rez 知识与防幻觉指南
tests/
├── adapter/           # adapter 层测试
├── models/            # 数据模型测试
├── persistence/       # 存储与序列化测试
├── runtime/           # runtime 与异常钩子测试
└── ui/                # 控制器与 QML 交互行为测试
```

`adapter/` 是唯一允许导入 `rez.*` 的层。`models/` 保持为纯 Python，`ui/` 负责桥接
Python 与 QML，而 `qml/` 包含声明式界面。

详细架构与 UI 规范见 `docs/design.md`。

## License

MIT，详见 `LICENSE`。
