# 构建说明（Build）

面向本地开发者与 **Cursor Cloud Agent**：按顺序即可完成安装、运行与打包。

## 仓库布局

```
sweet-signal-2.0/
  web/index.html          # 浏览器内纯前端版（Web Audio）
  desktop_app/
    main.py               # Python 入口：pywebview + sounddevice 生成正弦
    src/index.html       # 桌面壳内嵌 UI（调用 pywebview API）
    SweetSignal.spec     # PyInstaller 配置
  build.xml              # 可选：Apache Ant 编排本地打包
  requirements.txt
  requirements-dev.txt
  .github/workflows/build-windows.yml
```

## A. 运行浏览器版（无 Python）

1. 用浏览器打开 `web/index.html`（或置于任意静态站点根目录）。
2. 若在 `file://` 下列不出设备 → 改用本地 HTTP Server 或直接用桌面版。

## B. 运行桌面版（源码）

在项目根目录：

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
cd desktop_app
python main.py
```

会从 `desktop_app` 加载 `src/index.html`（相对路径已由 `webview.create_window(..., 'src/index.html')` 指定）。

## C. Windows 一键打包 exe（PyInstaller）

项目根目录：

```bash
python -m pip install -r requirements-dev.txt
cd desktop_app
python -m PyInstaller --noconfirm SweetSignal.spec
```

产出：`desktop_app/dist/SweetSignal.exe`（单文件，无控制台）。

## D. 使用 `build.xml`（需已安装 Ant + Python）

在项目根目录：

```bash
ant pip-install      # 安装 requirements-dev.txt
ant build-exe        # depends on pip-install，再跑 PyInstaller
ant clean            # 清理 desktop_app/dist 与 desktop_app/build
ant rebuild          # clean + build-exe
```

若 Python 可执行文件名不是 `python`，可指定：

```bash
ant build-exe -Dpython.cmd=py
```

Ant 不负责安装 JDK；仅需本机可同时运行 `python`/`py` + `pip`。

## E. CI：从 GitHub Actions 下载 exe

1. 推送至远端后，打开仓库 **Actions**，选择 **「Build Windows exe」**。
2. 进入最近一次成功的运行摘要页。
3. 底部 **Artifacts** → 下载 **SweetSignal-Windows**（ZIP 内含 `SweetSignal.exe`）。
4. Artifact 有保留期限（仓库/组织策略决定）；长期分发请再配合 **GitHub Releases**（可在后续 workflow 中增加 tag 触发上传 Release assets）。

触发条件：`push` / `pull_request` 至 `main` 或 `master`，以及 **`workflow_dispatch`**（可手动在工作流页运行）。

## 常见问题

**Q：Cloud Agent / CI 应该用哪个 Python 版本？**  
建议 **3.11**，与 `.github/workflows/build-windows.yml` 保持一致。

**Q：改过 `SweetSignal.spec` 后 CI 挂了？**  
确认 `datas=[('src', 'src')]` 仍存在，且始终在 `desktop_app` 目录下执行 PyInstaller。

**Q：`pywebview` 白屏或无法启动 UI？**  
Windows 确认已安装 Edge WebView2 Runtime；若为远程无头 CI，本条不适用（CI 只做打包不写 UI 冒烟）。
