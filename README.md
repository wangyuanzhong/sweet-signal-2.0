# Sweet Signal 2.0

马卡龙色系的 **可调纯音发生器**：支持 **浏览器内试听**（Web Audio）与 **Windows 桌面版**（`pywebview` + `sounddevice` 枚举直连系统输出），频率范围约 **20 Hz–20 kHz**，音量以 **dBFS**（最大 0 dBFS）控制。

---

## 功能概览

| 模式 | 路径 | 说明 |
|------|------|------|
| Web | [`web/index.html`](web/index.html) | 单页 HTML/CSS/JS，`AudioContext` 生成纯正弦 |
| Desktop | [`desktop_app/`](desktop_app/) | 窗体嵌入 Web UI，后端 **NumPy + PortAudio** 输出，可选用 Windows **真实回放设备列表** |

---

## 快速开始

### 浏览器

直接打开 **`web/index.html`**。若在 `file://` 环境下设备枚举异常，改用本地静态服务或改用桌面应用。

### 桌面（源码）

```bash
python -m pip install -r requirements.txt
cd desktop_app && python main.py
```

详见 [`docs/BUILD.md`](docs/BUILD.md)。

### Actions 与工作流约定

CI 行为与产物验收条件见 **[`docs/GITHUB_ACTIONS.md`](docs/GITHUB_ACTIONS.md)**。

### 依赖一览

[`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) · 根目录 `requirements.txt` / `requirements-dev.txt`

---

## 本地打包 Windows exe

```bash
python -m pip install -r requirements-dev.txt
cd desktop_app && python -m PyInstaller --noconfirm SweetSignal.spec
```

也可以使用 **Apache Ant**（需本机安装 Ant）：`ant build-exe`。说明见 **[`docs/BUILD.md`](docs/BUILD.md)** 及根目录 **`build.xml`**。

---

## 从 GitHub Actions 下载 exe

本仓库配置了 **GitHub Actions**（[`.github/workflows/build-windows.yml`](.github/workflows/build-windows.yml)），每次向 `main` / `master` 的 **`push`** 或在对应 PR、`workflow_dispatch` 中会构建 Windows 安装包占位产物。

### 下载步骤

1. 在 GitHub 打开本仓库 → 标签栏选择 **Actions**。
2. 点开 **「Build Windows exe」** 工作流最近一次 **绿色**运行记录。
3. 在运行摘要页底部 **Artifacts** 区域下载 **SweetSignal-Windows**（ZIP，内含单个 **`SweetSignal.exe`**；解压后即可运行，可将 exe 拷贝到任意目录单独使用）。

> **首次打开偏慢 / SmartScreen**：未签名的下载应用可能被 Windows SmartScreen 提示；同意运行后系统仍会做信誉扫描。**单文件 exe** 首次冷启动会向 `%TEMP%` 解压内置文件，可能比目录分发略慢。若需尽量消除拦截，需自行配置 **代码签名证书** 对可执行文件签名。详见 **[`docs/BUILD.md`](docs/BUILD.md)**「Windows 首次打开与 SmartScreen」。

> Artifact 默认有 **过期时间**（由仓库/组织策略决定）。若需要长期、带版本号的公开下载链接，建议在后续迭代中增加 **tag 触发 Release**，将构建 ZIP 上传到 **GitHub Releases**（需在 workflow 中加 `GITHUB_TOKEN` 写权限的步骤）。

---

## Cursor Cloud Agent / 自动化开发

请先阅读 **`docs/DEPENDENCIES.md`**（锁版本与系统前提）再改代码；构建与打包流程统一见 **`docs/BUILD.md`**。修改桌面 UI 时注意同时维护 **`desktop_app/src/index.html`**（打包进 exe）与可选 **`web/index.html`**（纯浏览器版）。

---

## 许可证

未随仓库附带许可证文件时，默认保留作者全部权利；需要开源协议请自行追加 `LICENSE`。
