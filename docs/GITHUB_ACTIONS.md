# GitHub Actions 产物需求说明（EXE 下载）

本文档概括 **Sweet Signal / Build Windows exe** 工作流的 **功能需求与设计约定**，便于审计 CI 是否与 README 表述一致。

## 目标（Goal）

运维与终端用户可从 **GitHub Actions 运行摘要页** 下载到 **单次构建生成的 Windows 可执行文件**，无需本地安装 Python/PyInstaller。

## 功能性需求（Functional）

1. **触发**  
   - `push` 至 **`main`**、**`master`** 或 **`cursor/**`**（例如 Cursor Cloud 工作分支）时触发构建。  
   - `pull_request` 至 **`main`** 或 **`master`** 时触发构建。  
   - 支持 **`workflow_dispatch`**（人工在 Actions 界面「Run workflow」）。

2. **运行环境**  
   - **`windows-latest`** 托管运行器。

3. **构建步骤**  
   - 检出仓库。  
   - 安装 **Python 3.11**（与 `docs/DEPENDENCIES.md` 对齐）。  
   - `pip install -r requirements-dev.txt`。  
   - 在 **`desktop_app`** 目录执行 `PyInstaller --noconfirm SweetSignal.spec`。

4. **产物（Artifact）**  
   - 名称：**`SweetSignal-Windows`**。  
   - 格式：**ZIP**。  
   - 内容：**`SweetSignal.exe`**（与其他文件二选一皆可，当前约定仅含 exe 便于解压即用）。  
   - 若无 `SweetSignal.exe`：**构建步骤必须失败**，不得上传空 Artifact。

## 非功能需求（Non-functional）

| 条目 | 说明 |
|------|------|
| 权限最小化 | 工作流 `permissions.contents: read`；上传 Artifact 不需写仓库内容权限。 |
| 可重现性 | 依赖 `requirements-dev.txt` 与锁定的 Python 补丁线（3.11）。 |
| 保留时间 | Artifact 保留由 **GitHub 仓库/组织策略**决定；不因本 workflow 设为永久。 |

## 与「正式发布」的差距（Deferred）

以下内容 **当前未在工作流实现**，可作为后续迭代需求：

- **GitHub Releases**：基于 `git tag v*` 自动生成 Release 并附上 `SweetSignal.exe`（永不随 Artifact 过期策略删除的逻辑由 Release 承接）。  
- **代码签名**：对 `SweetSmart.exe` 做 Authenticode / 证书签名。  
- **自动版本号**：从 tag 或 `pyproject`/资源文件写入版本。

## 用户侧操作流程（验收）

参见根目录 **`README.md`** 「从 GitHub Actions 下载 exe」小节：Actions → 成功运行 → Artifacts → 下载 **`SweetSignal-Windows`** ZIP。
