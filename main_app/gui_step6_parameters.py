# -*- coding: utf-8 -*-
"""
第六步：写入串数和热损（PyQt版本）
---------------------------------------------
功能：
- 输入5个LED的串数和热损参数
- 导出三个文件：
  1. step6_串数和热损.xlsx - 记录用户输入的完整参数
  2. step6_series_count.csv - 5个串数数据（一行五列）
  3. step6_thermal_loss.csv - 5个热损数据（一行五列）

注意：本步骤仅做数据记录，不进行任何计算。
"""

import os
import csv
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# 路径
from path_manager import get_step6_dir

# Excel相关
from openpyxl import Workbook

# 核心函数
try:
    from core_functions.step6_combos_process import process_combos_with_series_count
    from core_functions.step6_raw_data_process import process_raw_data_with_thermal_loss
except ImportError as e:
    print(f"警告：无法导入计算模块: {e}")


    # 定义备用函数
    def process_combos_with_series_count():
        return False, f"串数处理模块未加载: {e}"


    def process_raw_data_with_thermal_loss():
        return False, f"热损处理模块未加载: {e}"


# ------------------ 路径工具函数 ------------------
def _find_project_root(start_dir: str) -> str:
    cur = os.path.abspath(start_dir)
    for _ in range(6):
        has_data = os.path.isdir(os.path.join(cur, "data_files"))
        has_main = os.path.isdir(os.path.join(cur, "main_app"))
        has_core = os.path.isdir(os.path.join(cur, "core_functions"))
        if has_data or (has_main and has_core):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.abspath(start_dir))


# 修改 _step6_out_dir 函数
def _step6_out_dir() -> str:
    """确保并返回 data_files/step6_parameters/ 目录"""
    return get_step6_dir()


# ------------------ 数值转换工具 ------------------
def _to_int(val):
    """转换为整数，空值或无效值返回0"""
    try:
        if val is None or str(val).strip() == "":
            return 0
        return int(float(str(val).strip()))
    except Exception:
        return 0


def _to_float(val):
    """转换为浮点数，空值或无效值返回0.0"""
    try:
        if val is None or str(val).strip() == "":
            return 0.0
        return float(str(val).strip())
    except Exception:
        return 0.0


# ------------------ 主界面类 ------------------
class Step6ParametersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.led_count = 5

        # 数据结构
        self.series_edits = {}  # LED名称 -> QLineEdit (串数)
        self.thermal_edits = {}  # LED名称 -> QLineEdit (热损)
        self.remark_edits = {}  # LED名称 -> QLineEdit (备注)

        # 进度条控制
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_value = 0

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 标题 & 描述
        title_label = QLabel("第六步：写入串数和热损")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_text = "将每种LED的串数和热损输入到下表中。比如稳态电压是瞬态的98%，热损写0.98。"
        description_label = QLabel(description_text)
        description_label.setStyleSheet("color: #1f4a7c;")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(description_label)

        # 表格框架
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.Box)
        table_layout = QVBoxLayout(table_frame)

        # 创建表格
        table = QTableWidget(5, 4)  # 6行4列（包括表头）
        headers = ["临时信息", "串数", "热损", "备注"]
        table.setHorizontalHeaderLabels(headers)

        # 设置表头样式
        header_font = QFont()
        header_font.setBold(True)
        table.horizontalHeader().setFont(header_font)

        # 设置行标签（LED1~LED5）
        row_labels = ["LED1", "LED2", "LED3", "LED4", "LED5"]
        for i, label in enumerate(row_labels):
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignCenter)
            table.setVerticalHeaderItem(i, item)

        # 创建输入框并存储引用
        for row in range(5):  # 5行数据
            led = f"LED{row + 1}"

            # 串数列
            series_edit = QLineEdit()
            series_edit.setAlignment(Qt.AlignCenter)
            table.setCellWidget(row, 1, series_edit)
            self.series_edits[led] = series_edit

            # 热损列
            thermal_edit = QLineEdit()
            thermal_edit.setAlignment(Qt.AlignCenter)
            table.setCellWidget(row, 2, thermal_edit)
            self.thermal_edits[led] = thermal_edit

            # 备注列
            remark_edit = QLineEdit()
            table.setCellWidget(row, 3, remark_edit)
            self.remark_edits[led] = remark_edit

        # 设置表格属性
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)

        table_layout.addWidget(table)
        main_layout.addWidget(table_frame)

        # 操作按钮
        button_layout = QHBoxLayout()
        write_button = QPushButton("写入数据")
        write_button.setStyleSheet("background-color: #d9ecff;")
        write_button.clicked.connect(self.on_write_click)
        button_layout.addWidget(write_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 进度条（初始隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        main_layout.addWidget(self.progress_bar)

        # 输出框
        output_label = QLabel("输出结果：")
        output_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(output_label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

    def _update_progress(self):
        """更新进度条动画"""
        self.progress_value += 1
        if self.progress_value >= 100:
            self.progress_value = 0

    def _export_to_excel(self) -> str:
        """导出完整参数到Excel文件"""
        data_dir = _step6_out_dir()
        out_path = os.path.join(data_dir, "step6_串数和热损.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Parameters"
        ws.append(["LED", "串数", "热损", "备注"])

        for i in range(self.led_count):
            led = f"LED{i + 1}"
            series_edit = self.series_edits[led]
            thermal_edit = self.thermal_edits[led]
            remark_edit = self.remark_edits[led]

            raw_series = series_edit.text().strip()
            raw_thermal = thermal_edit.text().strip()
            remark = remark_edit.text().strip()

            # 转换数值，空值保持为空字符串
            series_val = _to_int(raw_series) if raw_series else ""
            thermal_val = _to_float(raw_thermal) if raw_thermal else ""

            ws.append([led, series_val, thermal_val, remark])

        wb.save(out_path)
        return out_path

    def _export_series_to_csv(self) -> str:
        """导出5个串数到CSV文件（一行五列）"""
        data_dir = _step6_out_dir()
        out_path = os.path.join(data_dir, "step6_series_count.csv")

        series_data = []
        for i in range(self.led_count):
            led = f"LED{i + 1}"
            series_edit = self.series_edits[led]
            raw_series = series_edit.text().strip()
            series_val = _to_int(raw_series)  # 空值或无效值返回0
            series_data.append(series_val)

        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(series_data)

        return out_path

    def _export_thermal_to_csv(self) -> str:
        """导出5个热损到CSV文件（一行五列）"""
        data_dir = _step6_out_dir()
        out_path = os.path.join(data_dir, "step6_thermal_loss.csv")

        thermal_data = []
        for i in range(self.led_count):
            led = f"LED{i + 1}"
            thermal_edit = self.thermal_edits[led]
            raw_thermal = thermal_edit.text().strip()
            thermal_val = _to_float(raw_thermal)  # 空值或无效值返回0.0
            thermal_data.append(thermal_val)

        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(thermal_data)

        return out_path

    def on_write_click(self):
        """点击"写入数据" """
        try:
            # 启用输出框
            self.output_box.clear()

            # 导出三个文件
            path_excel = self._export_to_excel()
            path_series_csv = self._export_series_to_csv()
            path_thermal_csv = self._export_thermal_to_csv()

            # 输出成功信息
            self.output_box.append("=== 数据写入成功 ===\n")
            self.output_box.append(f"1. Excel文件: {path_excel}")
            self.output_box.append("   - 记录完整的串数、热损和备注参数")
            self.output_box.append(f"2. 串数CSV文件: {path_series_csv}")
            self.output_box.append("   - 包含5个串数数据（一行五列），未输入填充0")
            self.output_box.append(f"3. 热损CSV文件: {path_thermal_csv}")
            self.output_box.append("   - 包含5个热损数据（一行五列），未输入填充0.0")

            # 显示导出的数据预览
            self.output_box.append("\n导出的数据预览：")

            # 串数预览
            series_preview = []
            for i in range(self.led_count):
                led = f"LED{i + 1}"
                series_edit = self.series_edits[led]
                raw_series = series_edit.text().strip()
                series_val = _to_int(raw_series)
                series_preview.append(str(series_val))
            self.output_box.append(f"串数: {', '.join(series_preview)}")

            # 热损预览
            thermal_preview = []
            for i in range(self.led_count):
                led = f"LED{i + 1}"
                thermal_edit = self.thermal_edits[led]
                raw_thermal = thermal_edit.text().strip()
                thermal_val = _to_float(raw_thermal)
                thermal_preview.append(f"{thermal_val:.4f}")
            self.output_box.append(f"热损: {', '.join(thermal_preview)}")

            # 调用核心函数
            # 先调用热损处理
            success, message = process_raw_data_with_thermal_loss()
            if success:
                self.output_box.append("\n热损处理成功")
            else:
                self.output_box.append(f"\n热损处理失败: {message}")

            # 再调用串数处理
            success, message = process_combos_with_series_count()
            if success:
                self.output_box.append("串数处理成功")
            else:
                self.output_box.append(f"串数处理失败: {message}")

            # 进度条动画
            self.progress_bar.setVisible(True)
            self.progress_timer.start(50)  # 20fps动画

            # 定时关闭进度条
            QTimer.singleShot(600, self._finish_progress)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"写入文件失败：{e}")

    def _finish_progress(self):
        """完成进度条动画"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", "数据写入完成！")


# ------------------ 独立运行 ------------------
class Step6ParametersWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第六步：写入串数和热损")
        self.resize(900, 600)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step6ParametersWidget(self)
        layout.addWidget(self.main_widget)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = Step6ParametersWindow()
    window.show()
    sys.exit(app.exec_())