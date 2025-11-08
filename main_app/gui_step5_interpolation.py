# -*- coding: utf-8 -*-
"""
第五步：写入从小到大的数据（PyQt简化版）
------------------------------------------------
保留功能：
- 使用电流小表（LED1~5），导出到 data_files/step5_interpolation/step4_LED积分球测试数据.xlsx
- If/Vf 大表（25行×10列），导出到 data_files/step5_interpolation/step5_interpolation.csv
- 支持Excel式批量粘贴（Ctrl+V）到大表
- 清空单个LED两列（LED1~LED5）
- 进度条（点击前隐藏；写出成功后象征性运行0.6秒）
- 输出框显示操作信息

移除功能：
- 所有插值运算相关功能
"""

import os
import csv
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QShortcut)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence

# Excel相关
from openpyxl import Workbook

# 核心函数
try:
    from core_functions.step5_interpolation_1 import calculate_multipliers
    from core_functions.step5_interpolation_2 import scale_bin_data
except ImportError as e:
    print(f"警告：无法导入计算模块: {e}")


    # 定义备用函数
    def calculate_multipliers():
        return False, f"计算模块未加载: {e}"


    def scale_bin_data():
        return False, f"缩放模块未加载: {e}"

# 路径导入
from path_manager import get_step5_dir

# ------------------ 工具函数 ------------------
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


# 修改 _step5_interpolation_dir 函数
def _step5_interpolation_dir() -> str:
    """确保并返回 data_files/step5_interpolation/ 目录"""
    return get_step5_dir()


def _to_float(val):
    try:
        if val is None or str(val).strip() == "":
            return None
        return float(val)
    except Exception:
        return None


# ------------------ 主界面类 ------------------
class Step5InterpolationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.led_count = 5
        self.rows = 25
        self.cols = self.led_count * 2  # LED1 If, LED1 Vf, ..., LED5 If, LED5 Vf

        # 数据结构
        self.usage_edits = {}  # LED名称 -> QLineEdit
        self.big_table = None  # QTableWidget for If/Vf data

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
        title_label = QLabel("第五步：写入从小到大的数据")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_text = "将每个LED在LED模组上的实际使用电流和我们自己积分球测的LED从小到大的数据填入下表。"
        description_label = QLabel(description_text)
        description_label.setStyleSheet("color: #1f4a7c;")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(description_label)

        # ===================== 使用电流小表 =====================
        usage_frame = QFrame()
        usage_frame.setFrameStyle(QFrame.Box)
        usage_layout = QVBoxLayout(usage_frame)

        usage_title = QLabel("使用电流输入（单位：mA）")
        usage_title_font = QFont()
        usage_title_font.setPointSize(12)
        usage_title_font.setBold(True)
        usage_title.setFont(usage_title_font)
        usage_layout.addWidget(usage_title)

        # 创建使用电流表格
        usage_table = QTableWidget(6, 2)  # 6行2列（包括表头）
        usage_table.setHorizontalHeaderLabels(["临时信息", "使用电流/mA"])
        usage_table.setVerticalHeaderLabels(["", "LED1", "LED2", "LED3", "LED4", "LED5"])

        # 创建使用电流输入框
        self.usage_edits = {}
        for i in range(self.led_count):
            led_name = f"LED{i + 1}"
            edit = QLineEdit()
            edit.setAlignment(Qt.AlignCenter)
            usage_table.setCellWidget(i + 1, 1, edit)
            self.usage_edits[led_name] = edit

        # 设置表格属性
        usage_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        usage_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        usage_table.setAlternatingRowColors(True)

        usage_layout.addWidget(usage_table)
        main_layout.addWidget(usage_frame)

        # ===================== If/Vf 大表 =====================
        big_table_label = QLabel("If/Vf 数据表（25行×10列）")
        big_table_label.setFont(usage_title_font)
        main_layout.addWidget(big_table_label)

        # 创建大表
        self.big_table = QTableWidget(self.rows, self.cols + 1)  # +1 for row numbers

        # 设置表头
        headers = ["临时信息"]
        for i in range(1, self.led_count + 1):
            headers.extend([f"LED{i} If", f"LED{i} Vf"])
        self.big_table.setHorizontalHeaderLabels(headers)

        # 设置行号
        for i in range(self.rows):
            item = QTableWidgetItem(str(i + 1))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 只读
            self.big_table.setVerticalHeaderItem(i, item)

        # 设置表格属性
        self.big_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.big_table.setAlternatingRowColors(True)

        # 启用批量粘贴
        self.big_table.installEventFilter(self)

        main_layout.addWidget(self.big_table)

        # 清空 LED 数据按钮区
        clear_layout = QHBoxLayout()
        for i in range(self.led_count):
            clear_button = QPushButton(f"清空LED{i + 1}数据")
            clear_button.setStyleSheet("background-color: #ffefcc;")
            clear_button.clicked.connect(lambda checked, idx=i: self.clear_led_data(idx))
            clear_layout.addWidget(clear_button)
        main_layout.addLayout(clear_layout)

        # 操作按钮区
        button_layout = QHBoxLayout()
        write_button = QPushButton("写入数据")
        write_button.setStyleSheet("background-color: lightblue;")
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

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理批量粘贴"""
        if obj == self.big_table and event.type() == event.KeyPress:
            if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
                self.handle_paste()
                return True
        return super().eventFilter(obj, event)

    def handle_paste(self):
        """处理批量粘贴"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            return

        # 获取当前选中的单元格
        current_row = self.big_table.currentRow()
        current_col = self.big_table.currentColumn()

        if current_row == -1 or current_col == -1:
            return

        # 解析粘贴数据
        rows = [r.strip() for r in text.split('\n') if r.strip()]
        data = []
        for row in rows:
            # 支持制表符和逗号分隔
            if '\t' in row:
                data.append([cell.strip() for cell in row.split('\t')])
            else:
                data.append([cell.strip() for cell in row.split(',')])

        # 填充数据到表格
        for i, row_data in enumerate(data):
            if current_row + i >= self.rows:
                break
            for j, cell_data in enumerate(row_data):
                if current_col + j >= self.cols + 1:  # +1 for row number column
                    break
                # 跳过序号列（第0列）
                if current_col + j == 0:
                    continue

                # 验证并格式化数据
                try:
                    val = float(cell_data)
                    formatted_val = str(val)
                except ValueError:
                    formatted_val = ""

                # 设置单元格数据
                item = QTableWidgetItem(formatted_val)
                item.setTextAlignment(Qt.AlignCenter)
                self.big_table.setItem(current_row + i, current_col + j, item)

    def clear_led_data(self, led_index: int):
        """清空某个LED数据（If/Vf 两列）"""
        # 计算列索引：LED1 If=1, LED1 Vf=2, LED2 If=3, LED2 Vf=4, 等等
        col_if = led_index * 2 + 1  # +1 because column 0 is row numbers
        col_vf = led_index * 2 + 2

        for row in range(self.rows):
            self.big_table.setItem(row, col_if, QTableWidgetItem(""))
            self.big_table.setItem(row, col_vf, QTableWidgetItem(""))

        # 不显示提示信息，直接清空

    def _update_progress(self):
        """更新进度条动画"""
        self.progress_value += 1
        if self.progress_value >= 100:
            self.progress_value = 0

    def _export_ivf_to_csv(self) -> str:
        """导出25行10列数据到CSV，未输入填充0"""
        data_dir = _step5_interpolation_dir()
        out_path = os.path.join(data_dir, "step5_interpolation.csv")

        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            for row in range(self.rows):
                row_data = []
                for col in range(1, self.cols + 1):  # 跳过序号列
                    item = self.big_table.item(row, col)
                    if item is None or item.text().strip() == "":
                        row_data.append(0)
                    else:
                        f = _to_float(item.text())
                        row_data.append(f if f is not None else 0)
                writer.writerow(row_data)

        return out_path

    def _export_usage_to_excel(self) -> str:
        """导出使用电流数据到Excel"""
        data_dir = _step5_interpolation_dir()
        out_path = os.path.join(data_dir, "step5_LED积分球测试数据.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "UsageCurrent"
        ws.append(["LED", "使用电流/mA"])

        for i in range(self.led_count):
            led = f"LED{i + 1}"
            raw = self.usage_edits[led].text().strip()
            if raw == "":
                ws.append([led, ""])
            else:
                v = _to_float(raw)
                ws.append([led, (v if v is not None else "")])

        wb.save(out_path)
        return out_path

    def _export_current_to_csv(self) -> str:
        """导出5个使用电流数据到CSV，不含表头，1行5列"""
        data_dir = _step5_interpolation_dir()
        out_path = os.path.join(data_dir, "step5_current.csv")

        currents = []
        for i in range(self.led_count):
            led = f"LED{i + 1}"
            raw = self.usage_edits[led].text().strip()
            if raw == "":
                currents.append(0)
            else:
                v = _to_float(raw)
                currents.append(v if v is not None else 0)

        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(currents)

        return out_path

    def on_write_click(self):
        """写入数据（两个文件 + 象征性进度条）"""
        try:
            # 启用输出框
            self.output_box.clear()

            # 导出文件
            path_csv = self._export_ivf_to_csv()
            path_excel = self._export_usage_to_excel()
            path_csv_current = self._export_current_to_csv()

            # 输出成功信息
            self.output_box.append("=== 数据写入成功 ===\n")
            self.output_box.append(f"1. Excel文件: {path_excel}")
            self.output_box.append("   - 记录使用电流参数")
            self.output_box.append(f"2. CSV文件: {path_csv}")
            self.output_box.append("   - 包含25行×10列If/Vf数据，未输入填充0")
            self.output_box.append(f"3. 电流CSV文件: {path_csv_current}")
            self.output_box.append("   - 包含5个使用电流数据（一行五列）")

            # 显示导出的数据预览
            self.output_box.append("\n导出的数据预览：")

            # 串数预览
            series_preview = []
            for i in range(self.led_count):
                led = f"LED{i + 1}"
                raw_series = self.usage_edits[led].text().strip()
                series_val = _to_float(raw_series) if raw_series else 0
                series_preview.append(str(series_val))
            self.output_box.append(f"使用电流: {', '.join(series_preview)}")

            # 进度条动画
            self.progress_bar.setVisible(True)
            self.progress_timer.start(50)  # 20fps动画

            # 定时关闭进度条并调用核心函数
            QTimer.singleShot(600, self._finish_write)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"写入文件失败：{e}")

    def _finish_write(self):
        """完成写入操作"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)

        # 调用核心函数
        success, message = calculate_multipliers()
        if success:
            self.output_box.append("\n倍数计算成功")
            success, message = scale_bin_data()
            if success:
                self.output_box.append(f"\n✅ {message}")
                self.output_box.append("\n数据缩放完成！")
            else:
                self.output_box.append(f"\n❌ {message}")
                self.output_box.append("\n数据缩放失败！")
        else:
            self.output_box.append(f"\n倍数计算失败: {message}")

        QMessageBox.information(self, "成功", "数据写入完成！")


# ------------------ 独立运行 ------------------
class Step5InterpolationWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第五步：写入从小到大的数据")
        self.resize(1250, 980)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step5InterpolationWidget(self)
        layout.addWidget(self.main_widget)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = Step5InterpolationWindow()
    window.show()
    sys.exit(app.exec_())