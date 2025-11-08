# -*- coding: utf-8 -*-
"""
GUI 第四步：混bin方式录入（PyQt版本）
------------------------------------------------
- 保留原有UI界面
- 只实现数据记录和导出功能：
  1. step4_LED混bin信息.xlsx - 记录用户输入的参数
  2. step4_mixbin_input_LED1.csv ~ LED5.csv - 每个表格6行4列，记录用户输入的混bin方式数字
"""

import os
import csv
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# 路径导入
from path_manager import get_step4_dir

# Excel相关
from openpyxl import Workbook

# 导入核心函数
try:
    from core_functions.step4_mixbin_calc_1 import build_mixbin_combos
    from core_functions.step4_mixbin_calc_2 import build_mixbin_combos_text
    from core_functions.step4_mixbin_calc_3 import build_mixbin_percentages
except ImportError as e:
    print(f"警告：无法导入计算模块: {e}")


    # 定义备用函数
    def build_mixbin_combos():
        return "path/to/combos.csv", 0


    def build_mixbin_combos_text():
        return "path/to/combos_text.csv", 0, 0


    def build_mixbin_percentages():
        return "path/to/uniformization.csv", 0, 0


# ========== 路径工具 ==========
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


# 修改 _step4_out_dir 函数
def _step4_out_dir() -> str:
    """确保并返回 data_files/step4_mixbin/ 目录"""
    return get_step4_dir()


# ========== 数值辅助 ==========
def _to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def _fmt_bin(bstr):
    """将 'a-b' 这样的字符串标准化；若不是有效区间，返回空串"""
    if not bstr or bstr == "0":
        return ""
    s = str(bstr).strip()
    if "-" not in s:
        return ""
    parts = s.split("-")
    if len(parts) != 2:
        return ""
    try:
        a = float(parts[0].strip())
        b = float(parts[1].strip())
    except Exception:
        return ""
    if b <= a:
        return ""
    return f"{a}-{b}"


# ========== GUI 类 ==========
class Step4MixBinWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # 数据结构
        self.led_tabs = {}  # led -> QWidget
        self.headers = {}  # led -> list[QLabel] (4 header labels)
        self.entries = {}  # led -> list[list[QLineEdit]] 6 rows x 4 cols

        # 进度条控制
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_value = 0

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 标题与说明
        title_label = QLabel("第四步：写入混bin方式")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_label = QLabel("工程师根据产出比设计混bin方式，将混bin方式填入下表。每种LED可支持6种混bin方式。")
        description_label.setStyleSheet("color: #1f4a7c;")
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)

        # Notebook per LED
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建5个LED的标签页
        for i in range(1, 6):
            led = f"LED{i}"
            tab = QWidget()
            self.tab_widget.addTab(tab, led)
            self.led_tabs[led] = tab
            self._build_led_table(tab, led)

        # 按钮区
        button_layout = QHBoxLayout()
        get_ranges_button = QPushButton("获取区间")
        get_ranges_button.setStyleSheet("background-color: #e8ffd9;")
        get_ranges_button.clicked.connect(self.on_get_ranges)
        button_layout.addWidget(get_ranges_button)

        write_button = QPushButton("写入数据")
        write_button.setStyleSheet("background-color: lightblue;")
        write_button.clicked.connect(self.on_write)
        button_layout.addWidget(write_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 进度条（初始隐藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定模式
        main_layout.addWidget(self.progress_bar)

        # 输出标题与输出框
        output_label = QLabel("输出结果：")
        output_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(output_label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

    def _build_led_table(self, container, led: str):
        """
        搭建每个LED的表：
        行0：临时信息 | (待填充) | (待填充) | (待填充) | (待填充)
        行1..6：混bin方式1..6 | qty1 | qty2 | qty3 | qty4
        """
        layout = QVBoxLayout(container)

        # 创建表格
        table = QTableWidget(7, 5)  # 7行5列（包括表头）
        layout.addWidget(table)

        # 设置表头
        headers = ["临时信息", "(待填充)", "(待填充)", "(待填充)", "(待填充)"]
        table.setHorizontalHeaderLabels(headers)

        # 设置行标签
        row_labels = ["", "混bin方式1", "混bin方式2", "混bin方式3", "混bin方式4", "混bin方式5", "混bin方式6"]
        table.setVerticalHeaderLabels(row_labels)

        # 存储表头标签和输入框
        header_labels = []
        for col in range(1, 5):  # 第1-4列
            header_item = table.horizontalHeaderItem(col)
            header_labels.append(header_item)
        self.headers[led] = header_labels

        # 创建输入框
        grid_entries = []
        for row in range(1, 7):  # 6行混bin方式
            row_entries = []
            for col in range(1, 5):  # 4列数量
                edit = QLineEdit()
                edit.setAlignment(Qt.AlignCenter)
                table.setCellWidget(row, col, edit)
                row_entries.append(edit)
            grid_entries.append(row_entries)
        self.entries[led] = grid_entries

        # 设置表格属性
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)

    def _update_progress(self):
        """更新进度条动画"""
        self.progress_value += 1
        if self.progress_value >= 100:
            self.progress_value = 0

    def _update_led_headers(self, led, ranges):
        """更新指定LED的表头标签"""
        if led in self.headers and len(ranges) == 4:
            for i, label in enumerate(self.headers[led]):
                label.setText(ranges[i])

    def on_get_ranges(self):
        """获取区间：读取 step3 的区间文件"""
        try:
            # 获取 step3_bin_ranges_pure.csv 路径
            data_dir = _step4_out_dir()
            ranges_csv_path = os.path.join(data_dir, "..", "step3_bin_process", "step3_bin_ranges_pure.csv")

            # 检查文件是否存在
            if not os.path.exists(ranges_csv_path):
                QMessageBox.warning(self, "提示", f"未找到区间文件: {ranges_csv_path}")
                return

            # 读取CSV文件
            with open(ranges_csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                row = next(reader)  # 读取第一行

                # 确保有20个区间
                if len(row) < 20:
                    QMessageBox.critical(self, "错误", f"区间文件格式错误，需要20个区间，但只找到{len(row)}个")
                    return

                # 提取20个区间字符串
                ranges = row[:20]

                # 更新LED表头
                # LED1: 索引0-3 (第1-4列)
                self._update_led_headers("LED1", ranges[0:4])
                # LED2: 索引4-7 (第5-8列)
                self._update_led_headers("LED2", ranges[4:8])
                # LED3: 索引8-11 (第9-12列)
                self._update_led_headers("LED3", ranges[8:12])
                # LED4: 索引12-15 (第13-16列)
                self._update_led_headers("LED4", ranges[12:16])
                # LED5: 索引16-19 (第17-20列)
                self._update_led_headers("LED5", ranges[16:20])

            QMessageBox.information(self, "完成", "区间获取完成，已从step3_bin_ranges.csv读取区间数据。")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取区间失败：{e}")

    def _export_user_mix_excel(self, data_dir, led_bins, led_mix_data):
        """
        导出用户在 6 行中填的每 LED 的数量到Excel
        每个LED一个工作表，格式为：
        第一行：LEDx(1-5)和四个区间
        第二行开始：6行混bin方式，每行4列用户输入
        """
        try:
            path = os.path.join(data_dir, "step4_LED混bin信息.xlsx")
            wb = Workbook()

            # 删除默认创建的工作表
            wb.remove(wb.active)

            for i in range(1, 6):  # LED1 to LED5
                led = f"LED{i}"
                bins = led_bins[led]  # 4个区间
                mix_matrix = led_mix_data[led]  # 6x4 matrix

                # 为每个LED创建单独的工作表
                ws = wb.create_sheet(title=led)

                # 写入表头：第一列是LEDx(1-5)，后面四列是区间
                header_row = [f"LED{i}"]  # 第一列是LED名称
                header_row.extend(bins)  # 后面四列是区间
                ws.append(header_row)

                # 写入混bin方式数据
                for r in range(6):  # 6行混bin方式
                    row_data = [f"混bin方式{r + 1}"]  # 第一列是混bin方式标签
                    row_data.extend(mix_matrix[r])  # 后面四列是用户输入的数字
                    ws.append(row_data)

            wb.save(path)
            return True, path
        except Exception as e:
            return False, f"导出Excel失败：{e}"

    def _export_mix_csv(self, data_dir, led_mix_data):
        """
        导出5个CSV文件，每个文件6行4列，只包含数字
        """
        try:
            for i in range(1, 6):
                led = f"LED{i}"
                mix_matrix = led_mix_data[led]
                csv_path = os.path.join(data_dir, f"step4_mixbin_input_{led}.csv")

                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    for row in mix_matrix:
                        writer.writerow(row)

            return True, "5个CSV文件已生成"
        except Exception as e:
            return False, f"导出CSV失败：{e}"

    def on_generate_combos(self):
        """
        调用 Step4 的三个核心计算：
          1) build_mixbin_combos() 生成 data_files/step4_mixbin/step4_mixbin_combos.csv
          2) build_mixbin_combos_text() 生成 data_files/step4_mixbin/step4_mixbin_combos_text.csv
          3) build_mixbin_percentages() 生成 data_files/step4_mixbin/step4_mixbin_uniformization.csv
        """
        try:
            # 先生成数值组合
            out1, n_rows1 = build_mixbin_combos()  # -> (path, rows)

            # 再由 combos + step3 的 ranges 生成文本组合
            out2, n_rows2, n_cols2 = build_mixbin_combos_text()  # -> (path, rows, cols)

            # 继续生成"归一化"组合
            out3, n_rows3, n_cols3 = build_mixbin_percentages()

            # 输出到窗口
            self.output_box.append("=== 混bin组合计算完成 ===")
            self.output_box.append(f"数值组合：{out1}")
            self.output_box.append(f"   行数：{n_rows1}")
            self.output_box.append(f"文本组合：{out2}")
            self.output_box.append(f"   尺寸：{n_rows2} 行 × {n_cols2} 列（与数值组合一一对应）")
            self.output_box.append(f"归一化组合：{out3}")
            self.output_box.append(f"   尺寸：{n_rows3} 行 × {n_cols3} 列（每4列一组归一化）")

            QMessageBox.information(self, "完成", "混bin组合与文本组合已生成。")

        except FileNotFoundError as e:
            # 常见：还没"写入数据"，导致输入CSV不存在；或 step3 的 ranges 未就绪
            QMessageBox.critical(self, "错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成混bin组合失败：{e}")

    def on_write(self):
        """写入数据：导出两个文件"""
        try:
            data_dir = _step4_out_dir()

            # 读取表头（4个 bin 区间）
            led_bins = {}  # led -> [bin1..bin4]（字符串 a-b 或 ""/0）
            for i in range(1, 6):  # LED1..LED5
                led = f"LED{i}"
                bins = []
                for lab in self.headers[led]:
                    text = lab.text()
                    # 检查是否获取了区间
                    if text == "(待填充)":
                        QMessageBox.critical(self, "错误", "未获取区间，请先点击'获取区间'按钮")
                        return
                    bins.append(text)
                led_bins[led] = bins

            # 读取 6 行数量
            led_mix_data = {}  # led -> 6x4 矩阵，未输入填充0
            has_input = False  # 检查是否有任何输入

            for i in range(1, 6):  # LED1..LED5
                led = f"LED{i}"
                mix_matrix = []
                for r in range(6):  # 6 rows
                    row = self.entries[led][r]
                    row_data = []
                    for c in range(4):  # 4 columns
                        txt = row[c].text().strip()
                        if txt == "":
                            row_data.append(0)
                        else:
                            try:
                                val = float(txt)
                                row_data.append(val)
                                has_input = True  # 标记有输入
                            except ValueError:
                                QMessageBox.critical(self, "错误", f"{led} 第{r + 1}行 第{c + 1}列数量非数字。")
                                return
                    mix_matrix.append(row_data)
                led_mix_data[led] = mix_matrix

            # 检查是否有任何输入
            if not has_input:
                QMessageBox.critical(self, "错误", "未输入任何混bin方式")
                return

            # 导出 1：用户输入混bin方式 (step4_LED混bin信息.xlsx)
            success1, msg1 = self._export_user_mix_excel(data_dir, led_bins, led_mix_data)
            if not success1:
                self.output_box.append(f"【导出失败】{msg1}")
                QMessageBox.critical(self, "错误", msg1)
                return

            # 导出 2：5个CSV文件
            success2, msg2 = self._export_mix_csv(data_dir, led_mix_data)
            if not success2:
                self.output_box.append(f"【导出失败】{msg2}")
                QMessageBox.critical(self, "错误", msg2)
                return

            # 在输出框中显示成功信息
            self.output_box.clear()
            self.output_box.append("=== 导出成功 ===\n")
            self.output_box.append(f"1. step4_LED混bin信息.xlsx: {msg1}")
            self.output_box.append(f"2. CSV文件: {msg2}")
            self.output_box.append("\n导出的CSV文件内容预览：")

            # 显示每个LED的混bin数据预览
            for i in range(1, 6):
                led = f"LED{i}"
                self.output_box.append(f"\n{led}:")
                matrix = led_mix_data[led]
                for row in matrix:
                    row_str = " ".join(f"{val:8.2f}" if val != 0 else "0.00     " for val in row)
                    self.output_box.append(f"  {row_str}")

            # 生成混bin组合（calc_1 + calc_2 + calc_3）
            self.on_generate_combos()

            # 成功：象征性跑进度条
            self.progress_bar.setVisible(True)
            self.progress_timer.start(50)  # 20fps动画

            # 定时关闭进度条
            QTimer.singleShot(600, self._finish_progress)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误：{e}")

    def _finish_progress(self):
        """完成进度条动画"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", "混bin数据已写入。")


# ===== 独立运行 =====
class Step4MixBinWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第四步：写入混bin方式")
        self.resize(1100, 780)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step4MixBinWidget(self)
        layout.addWidget(self.main_widget)


def main():
    import sys
    app = QApplication(sys.argv)
    window = Step4MixBinWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()