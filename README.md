# PDF2Word

把 PDF 转成 Word（`.docx`），尽量保留文字、图片、表格和排版。跨平台桌面应用，macOS / Windows 可直接双击运行。

---

## 功能

- 单文件转换
- 批量转换（支持选择文件夹，自动递归扫描 `.pdf`）
- 拖拽添加文件
- 每个文件独立进度条 + 总体进度
- 自定义输出目录（默认保存到原 PDF 同目录）
- 转换过程中可随时取消

## 技术栈

- **转换核心**：[pdf2docx](https://github.com/ArtifexSoftware/pdf2docx)（布局/表格/图片保留质量在开源方案里最优）
- **GUI**：PyQt6
- **打包**：PyInstaller

---

## 下载已构建的安装包

每次 push 到 `main` 或打 tag `v*`，GitHub Actions 会自动构建：

- **macOS**：`PDF2Word.dmg`（arm64，Apple Silicon）
- **Windows**：`PDF2Word-windows.zip`（解压后双击 `PDF2Word.exe`）

下载位置：
- 最新开发版：仓库 **Actions** 页 → 选一次 run → 底部 **Artifacts**
- 正式发布版：仓库 **Releases** 页（打 tag 时自动创建）

---

## 从源码运行

要求：Python 3.9+

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

---

## 自己打包

### macOS

```bash
./build_scripts/build-macos.sh
# 产物：dist/PDF2Word.app
# 压成 DMG（可选）：
hdiutil create -volname PDF2Word -srcfolder dist/PDF2Word.app \
  -ov -format UDZO dist/PDF2Word.dmg
```

### Windows

```cmd
build_scripts\build-windows.bat
REM 产物：dist\PDF2Word\PDF2Word.exe（整个文件夹一起分发）
```

> ⚠️ PyInstaller 不支持跨平台编译，必须在目标系统上打包。推荐直接用项目里的 GitHub Actions workflow。

### GitHub Actions 自动构建

`.github/workflows/build.yml` 已配置好。推到 GitHub 即可：

```bash
git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main

# 发布正式版本
git tag v0.1.0 && git push origin v0.1.0
```

---

## 项目结构

```
pdf/
├── src/
│   ├── main.py                      # 入口
│   ├── converter/
│   │   └── pdf_converter.py         # pdf2docx 封装（按页进度 + 取消）
│   └── gui/
│       ├── main_window.py           # PyQt6 主窗口
│       └── worker.py                # QThread 后台转换 worker
├── build_scripts/
│   ├── build-macos.sh
│   └── build-windows.bat
├── .github/workflows/build.yml      # CI 自动打包
├── pdf2word.spec                    # PyInstaller 配置
├── requirements.txt                 # 运行时依赖
└── requirements-build.txt           # 打包依赖（+ pyinstaller）
```

---

## 版本管理

版本号的单一来源是 **`src/__version__.py`**，改这一个文件即可。影响范围：

- 窗口标题栏（`PDF 转 Word  v0.1.0`）
- macOS `.app` 的 `CFBundleShortVersionString` / `CFBundleVersion`（Finder 显示、系统偏好设置）
- Windows `.exe` 的文件属性版本信息（右键属性 → 详细信息）

发版流程：

```bash
# 1. 改 src/__version__.py 里的版本号
# 2. 提交并打 tag
git add src/__version__.py
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push && git push origin v0.2.0
# GitHub Actions 自动构建并创建 Release
```

建议 tag 名 (`v0.2.0`) 和版本号 (`0.2.0`) 保持一致。

---

## 已知问题 & 注意

1. **PyMuPDF 版本锁定在 `<1.25`**
   pdf2docx 0.5.8 使用的 `Rect.get_area()` 在 PyMuPDF 1.25 被移除。等 pdf2docx 发布修复后可解锁。

2. **扫描版 PDF（图片型）不支持文字提取**
   需要加 OCR（Tesseract）才行，当前版本未集成。

3. **macOS 首次打开被 Gatekeeper 拦截**
   未签名应用分发给其他 Mac 时，用户需右键 → 打开（或在 "系统设置 → 隐私与安全性" 放行）。正式分发需 Apple Developer ID 签名 + 公证。

4. **Windows SmartScreen 警告**
   未签名 `.exe` 首次运行会出现蓝色警告，点 "更多信息 → 仍要运行" 即可。彻底解决需 EV 代码签名证书。

---

## License

MIT
