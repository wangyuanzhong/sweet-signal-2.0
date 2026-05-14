# 依赖说明（Dependencies）

本文档供人工与 **Cursor Cloud Agent** 在启动任务前核对环境（与 `requirements*.txt` 一致）。

## 语言与运行时

| 组件 | 版本建议 | 用途 |
|------|----------|------|
| Python | **3.11**（与 CI 对齐；3.10–3.12 一般可用） | 桌面应用、打包 |
| pip | 最新 | 安装依赖 |

浏览器内 **仅打开 `web/index.html`** 时不需 Python，但需要支持 **Web Audio API** 的现代浏览器。

## Python 包（桌面端）

安装方式：

```bash
python -m pip install -r requirements.txt
```

| 包 | 约束 | 作用 |
|----|------|------|
| `numpy` | `>=1.26,<3` | 采样缓冲、相位累加生成正弦波 |
| `sounddevice` | `>=0.4.6` | PortAudio 封装：枚举设备、PCM 输出 |
| `pywebview` | `>=5.0` | 内嵌 Edge WebView2（Windows），加载 `desktop_app/src/index.html`，JS ↔ Python |

## 仅打包时需额外安装的包

```bash
python -m pip install -r requirements-dev.txt
```

含 `requirements.txt` 以及 **PyInstaller**（`desktop_app/SweetSignal.spec`）。

## 操作系统与本机组件

### Windows（桌面 exe、CI 目标）

- **Microsoft Edge WebView2 Runtime**（Windows 10/11 通常已就绪；若报错再安装）。
- **扬声器/音频设备**：由 PortAudio / `sounddevice` 枚举；名称使用 UTF-8（中文设备名会正常传给前端）。

### 浏览器版（`web/index.html`）

- 推荐使用 **HTTPS 或 localhost**；`file://` 下麦克风/设备枚举可能受限（由浏览器策略决定）。

## 与仓库文件的对应关系

- 运行时：`requirements.txt`
- 开发 + CI 打包：`requirements-dev.txt`
- 入口：`desktop_app/main.py`、`desktop_app/src/index.html`
- PyInstaller：`desktop_app/SweetSignal.spec`
- CI：`.github/workflows/build-windows.yml`
