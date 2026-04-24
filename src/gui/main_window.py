"""Main application window."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.worker import ConversionWorker


STATUS_PENDING = "等待中"
STATUS_RUNNING = "转换中"
STATUS_DONE = "完成"
STATUS_FAILED = "失败"
STATUS_CANCELLED = "已取消"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF 转 Word")
        self.resize(820, 560)
        self.setAcceptDrops(True)

        self._pdf_paths: List[Path] = []
        self._output_dir: Optional[Path] = None
        self._worker: Optional[ConversionWorker] = None

        self._build_ui()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        hint = QLabel("拖拽 PDF 文件到窗口，或点击下方按钮添加。转换后的 Word 文件默认保存到原文件目录。")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # File list
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["文件", "进度", "状态"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 220)
        self.table.setColumnWidth(2, 100)
        root.addWidget(self.table, 1)

        # File action row
        file_row = QHBoxLayout()
        self.add_btn = QPushButton("添加文件…")
        self.add_btn.clicked.connect(self._on_add_files)
        self.add_folder_btn = QPushButton("添加文件夹…")
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self._on_clear)
        file_row.addWidget(self.add_btn)
        file_row.addWidget(self.add_folder_btn)
        file_row.addWidget(self.remove_btn)
        file_row.addWidget(self.clear_btn)
        file_row.addStretch(1)
        root.addLayout(file_row)

        # Output dir row
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出目录:"))
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("留空则保存到每个 PDF 文件所在目录")
        self.out_edit.setReadOnly(True)
        out_row.addWidget(self.out_edit, 1)
        self.out_browse_btn = QPushButton("选择…")
        self.out_browse_btn.clicked.connect(self._on_choose_output)
        out_row.addWidget(self.out_browse_btn)
        self.out_clear_btn = QPushButton("清除")
        self.out_clear_btn.clicked.connect(self._on_clear_output)
        out_row.addWidget(self.out_clear_btn)
        root.addLayout(out_row)

        # Overall progress
        overall_row = QHBoxLayout()
        overall_row.addWidget(QLabel("总进度:"))
        self.overall_bar = QProgressBar()
        self.overall_bar.setValue(0)
        overall_row.addWidget(self.overall_bar, 1)
        self.status_label = QLabel("就绪")
        self.status_label.setMinimumWidth(120)
        overall_row.addWidget(self.status_label)
        root.addLayout(overall_row)

        # Action row
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setDefault(True)
        self.convert_btn.clicked.connect(self._on_convert)
        action_row.addWidget(self.convert_btn)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        action_row.addWidget(self.cancel_btn)
        root.addLayout(action_row)

    # ---------- Drag & drop ----------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and self._worker is None:
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths: List[Path] = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            p = Path(url.toLocalFile())
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.pdf")))
            elif p.suffix.lower() == ".pdf":
                paths.append(p)
        self._add_paths(paths)

    # ---------- File list management ----------

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        self._add_paths([Path(f) for f in files])

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self._add_paths(sorted(Path(folder).rglob("*.pdf")))

    def _on_remove_selected(self) -> None:
        if self._worker is not None:
            return
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
            del self._pdf_paths[r]

    def _on_clear(self) -> None:
        if self._worker is not None:
            return
        self.table.setRowCount(0)
        self._pdf_paths.clear()
        self.overall_bar.setValue(0)
        self.status_label.setText("就绪")

    def _add_paths(self, paths: List[Path]) -> None:
        if self._worker is not None:
            return
        existing = {p.resolve() for p in self._pdf_paths}
        for p in paths:
            if not p.exists() or p.suffix.lower() != ".pdf":
                continue
            resolved = p.resolve()
            if resolved in existing:
                continue
            existing.add(resolved)
            self._pdf_paths.append(p)
            self._append_row(p)

    def _append_row(self, path: Path) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QTableWidgetItem(str(path))
        name_item.setToolTip(str(path))
        self.table.setItem(row, 0, name_item)

        bar = QProgressBar()
        bar.setValue(0)
        self.table.setCellWidget(row, 1, bar)

        status_item = QTableWidgetItem(STATUS_PENDING)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, status_item)

    # ---------- Output dir ----------

    def _on_choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self._output_dir = Path(folder)
            self.out_edit.setText(folder)

    def _on_clear_output(self) -> None:
        self._output_dir = None
        self.out_edit.clear()

    # ---------- Conversion ----------

    def _on_convert(self) -> None:
        if not self._pdf_paths:
            QMessageBox.information(self, "提示", "请先添加要转换的 PDF 文件。")
            return
        if self._worker is not None:
            return

        # Reset row progress
        for row in range(self.table.rowCount()):
            bar = self.table.cellWidget(row, 1)
            if isinstance(bar, QProgressBar):
                bar.setValue(0)
            self.table.item(row, 2).setText(STATUS_PENDING)

        self.overall_bar.setValue(0)
        self.status_label.setText("转换中…")
        self._set_busy(True)

        worker = ConversionWorker(list(self._pdf_paths), self._output_dir, self)
        worker.file_started.connect(self._on_file_started)
        worker.file_progress.connect(self._on_file_progress)
        worker.file_finished.connect(self._on_file_finished)
        worker.file_failed.connect(self._on_file_failed)
        worker.all_finished.connect(self._on_all_finished)
        self._worker = worker
        worker.start()

    def _on_cancel(self) -> None:
        if self._worker is not None:
            self.status_label.setText("正在取消…")
            self._worker.cancel()

    def _set_busy(self, busy: bool) -> None:
        self.add_btn.setEnabled(not busy)
        self.add_folder_btn.setEnabled(not busy)
        self.remove_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        self.out_browse_btn.setEnabled(not busy)
        self.out_clear_btn.setEnabled(not busy)
        self.convert_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)

    # ---------- Worker signals ----------

    def _on_file_started(self, idx: int, total: int, name: str) -> None:
        self.table.item(idx, 2).setText(STATUS_RUNNING)
        self.status_label.setText(f"正在转换 {idx + 1}/{total}")

    def _on_file_progress(self, idx: int, done: int, total: int) -> None:
        bar = self.table.cellWidget(idx, 1)
        if isinstance(bar, QProgressBar) and total > 0:
            bar.setValue(int(done * 100 / total))
        # Overall progress: finished files + fractional current file
        total_files = self.table.rowCount()
        if total_files > 0 and total > 0:
            overall = (idx + done / total) / total_files * 100
            self.overall_bar.setValue(int(overall))

    def _on_file_finished(self, idx: int, output_path: str) -> None:
        bar = self.table.cellWidget(idx, 1)
        if isinstance(bar, QProgressBar):
            bar.setValue(100)
        item = self.table.item(idx, 2)
        item.setText(STATUS_DONE)
        item.setToolTip(output_path)

    def _on_file_failed(self, idx: int, message: str) -> None:
        item = self.table.item(idx, 2)
        item.setText(STATUS_FAILED)
        item.setToolTip(message)

    def _on_all_finished(self, ok: int, failed: int, cancelled: bool) -> None:
        # Mark any still-pending rows as cancelled
        if cancelled:
            for row in range(self.table.rowCount()):
                status_item = self.table.item(row, 2)
                if status_item.text() in (STATUS_PENDING, STATUS_RUNNING):
                    status_item.setText(STATUS_CANCELLED)

        if cancelled:
            self.status_label.setText(f"已取消（成功 {ok}，失败 {failed}）")
        elif failed == 0:
            self.status_label.setText(f"全部完成（{ok} 个文件）")
            self.overall_bar.setValue(100)
        else:
            self.status_label.setText(f"完成（成功 {ok}，失败 {failed}）")

        self._worker = None
        self._set_busy(False)
