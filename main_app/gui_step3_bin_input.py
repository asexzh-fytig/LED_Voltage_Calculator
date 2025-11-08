# -*- coding: utf-8 -*-
"""
Step 3: 分bin节点输入与导出（PyQt精简版）
---------------------------------------------------------------
- 表格：6行×7列
  表头： 临时信息 | 节点1 | 节点2 | 节点3 | 节点4 | 节点5 | 备注
  行：   LED1 ~ LED5
- 任意节点可留空；若填写必须为数字
- 点击"写入数据"：
  1) 直接把用户填写的分bin区间（由相邻节点形成）输出到输出框
  2) 导出到 data_files/step3_bin_process/step3_bins.xlsx (Sheet: Nodes)
- 不再读取第二步的 EXCEL，也不做交集判断
- 进度条点击前隐藏；写出成功后象征性运行0.6秒再隐藏
"""

import os
import sys
import csv
import pandas as pd
import numpy as np


# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# 路径导入
from path_manager import get_step3_dir

# Excel相关
from openpyxl import Workbook

# 导入step3相关模块
try:
    from core_functions.step3_validation import validate_csv_file
except ImportError as e:
    print(f"警告：无法导入验证模块: {e}")


    # 定义一个备用函数，避免导入失败
    def validate_csv_file(csv_file_path):
        return True, "验证模块未加载"

try:
    from core_functions.step3_bin_process import run_step3_bin_process
except ImportError as e:
    print(f"警告：无法导入step3_bin_process模块: {e}")


    # 定义一个备用函数，避免导入失败
    def run_step3_bin_process(target_column=None):
        return {"LED1": {"bin_1": 0, "bin_2": 0, "bin_3": 0, "bin_4": 0},
                "LED2": {"bin_1": 0, "bin_2": 0, "bin_3": 0, "bin_4": 0},
                "LED3": {"bin_1": 0, "bin_2": 0, "bin_3": 0, "bin_4": 0},
                "LED4": {"bin_1": 0, "bin_2": 0, "bin_3": 0, "bin_4": 0},
                "LED5": {"bin_1": 0, "bin_2": 0, "bin_3": 0, "bin_4": 0}}

try:
    from core_functions.step3_bin_range import generate_bin_ranges
except ImportError as e:
    print(f"警告：无法导入step3_bin_range模块: {e}")


    # 定义一个备用函数，避免导入失败
    def generate_bin_ranges():
        return False, "step3_bin_range模块未加载"


# ---------------- 工具：项目根目录定位 ----------------
def _find_project_root(start_dir: str) -> str:
    cur = os.path.abspath(start_dir)
    for _ in range(5):
        has_data_files = os.path.isdir(os.path.join(cur, "data_files"))
        has_main = os.path.isdir(os.path.join(cur, "main_app"))
        has_core = os.path.isdir(os.path.join(cur, "core_functions"))
        if has_data_files or (has_main and has_core):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.abspath(start_dir))

# 修改 _step3_out_dir 函数
def _step3_out_dir() -> str:
    """确保并返回 data_files/step3_bin_process/ 目录"""
    return get_step3_dir()


# ---------------- 数据存储（内存） ----------------
led_bin_data = {}  # {"LED1": {"节点1":v1,...,"节点5":v5,"备注":txt}, ...}


def save_bin_data(bin_values):
    """保存分bin节点数据到内存字典"""
    for led, row in bin_values.items():
        led_bin_data[led] = row


# === 导出返回 (success, msg) ===
def _export_step3_nodes_to_excel():
    """
    将 led_bin_data 导出到 data_files/step3_bin_process/step3_LED分bin信息.xlsx (Sheet: Nodes)
    列：LED, 节点1, 节点2, 节点3, 节点4, 节点5, 备注
    返回 (success, msg)
      - success=True: msg 为导出路径
      - success=False: msg 为错误信息
    """
    if not led_bin_data:
        return False, "没有可导出的分bin节点数据。"

    try:
        data_dir = _step3_out_dir()
        out_path = os.path.join(data_dir, "step3_LED分bin信息.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Nodes"

        headers = ["LED", "节点1", "节点2", "节点3", "节点4", "节点5", "备注"]
        ws.append(headers)

        for led in ["LED1", "LED2", "LED3", "LED4", "LED5"]:
            row = led_bin_data.get(led, {})
            ws.append([
                led,
                row.get("节点1", ""),
                row.get("节点2", ""),
                row.get("节点3", ""),
                row.get("节点4", ""),
                row.get("节点5", ""),
                row.get("备注", ""),
            ])

        wb.save(out_path)
        return True, out_path
    except Exception as e:
        return False, f"导出 Excel 失败：{e}"


def _export_step3_nodes_to_csv():
    """
    将 led_bin_data 导出为5*5的CSV文件
    用户未输入的部分填充0
    返回 (success, msg)
      - success=True: msg 为导出路径
      - success=False: msg 为错误信息
    """
    if not led_bin_data:
        return False, "没有可导出的分bin节点数据。"

    try:
        data_dir = _step3_out_dir()
        out_path = os.path.join(data_dir, "step3_bin_nodes.csv")

        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # 不写入表头，直接写入数据，按LED1~LED5顺序
            for led in ["LED1", "LED2", "LED3", "LED4", "LED5"]:
                row_data = []  # 不再包含LED名称
                row = led_bin_data.get(led, {})

                # 对于每个节点，如果有值则使用，否则填充0
                for i in range(1, 6):
                    node_value = row.get(f"节点{i}", "")
                    if node_value == "":
                        row_data.append(0)
                    else:
                        row_data.append(float(node_value))

                writer.writerow(row_data)

        return True, out_path
    except Exception as e:
        return False, f"导出 CSV 失败：{e}"


# ---------------- 小工具 ----------------
def _to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        s = str(v).strip()
        if s == "":
            return None
        return float(s)
    except Exception:
        return None


def build_intervals_from_nodes(nodes_list):
    """由节点序列构建相邻区间，去空、去重、升序。"""
    if not nodes_list:
        return []
    nums = sorted({_to_float(x) for x in nodes_list if _to_float(x) is not None})
    if len(nums) < 2:
        return []
    return [(nums[i], nums[i + 1]) for i in range(len(nums) - 1)]


def fmt_intervals(intervals):
    """格式化 [(a,b),...] -> 'a-b,a-b,...'；为空则返回空字符串"""
    if not intervals:
        return ""
    return ",".join(f"{a}-{b}" for (a, b) in intervals)


# ---------------------------------------------
# PyQt Widget 类
# ---------------------------------------------

class Step3BinInputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # 输入框引用
        self.node_edits = {}  # {"LED1": [edit1, edit2, edit3, edit4, edit5], ...}
        self.remark_edits = {}  # {"LED1": edit, ...}

        # 进度条控制
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_value = 0

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 标题与描述
        title_label = QLabel("第三步：写入供应商分bin区间节点")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_text = (
            "将供应商给的分bin区间的节点输入到下表中。LED模组有几种LED就填几行。\n"
            "例如供应商提供的是 2.6-2.7, 2.7-2.8, 2.8-2.9，则填入节点：2.6, 2.7, 2.8, 2.9。"
        )
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
        self.table_widget = QTableWidget(5, 7)  # 6行7列（包括表头）
        headers = ["临时信息", "节点1", "节点2", "节点3", "节点4", "节点5", "备注"]
        self.table_widget.setHorizontalHeaderLabels(headers)

        # 设置表头样式
        header_font = QFont()
        header_font.setBold(True)
        self.table_widget.horizontalHeader().setFont(header_font)

        # 设置行标签（LED1~LED5）
        row_labels = ["LED1", "LED2", "LED3", "LED4", "LED5"]
        for i, label in enumerate(row_labels):
            item = QTableWidgetItem(label)
            item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setVerticalHeaderItem(i, item)

        # 创建输入框并存储引用
        for row in range(5):  # 5行数据
            led = f"LED{row + 1}"
            self.node_edits[led] = []

            # 节点1-5列
            for col in range(1, 6):  # 列1-5对应节点1-5
                node_edit = QLineEdit()
                node_edit.setAlignment(Qt.AlignCenter)
                self.table_widget.setCellWidget(row, col, node_edit)
                self.node_edits[led].append(node_edit)

            # 备注列
            remark_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 6, remark_edit)
            self.remark_edits[led] = remark_edit

        # 设置表格属性
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.setAlternatingRowColors(True)

        table_layout.addWidget(self.table_widget)
        main_layout.addWidget(table_frame)

        # 操作按钮
        button_layout = QHBoxLayout()
        save_button = QPushButton("写入数据")
        save_button.setStyleSheet("background-color: lightblue;")
        save_button.clicked.connect(self.on_save_click)
        button_layout.addWidget(save_button)
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

    def process_bin_data(self):
        """
        处理分bin节点数据并写出，且在输出框展示分bin区间（不做交集）
        """
        try:
            # 读取表单
            bin_values = {}
            for led, node_edits in self.node_edits.items():
                row = {}
                node_values = []

                # 首先检查所有输入是否为数字
                for idx, edit in enumerate(node_edits, start=1):
                    raw = edit.text().strip()
                    if raw == "":
                        row[f"节点{idx}"] = ""
                        node_values.append(None)
                    else:
                        try:
                            value = float(raw)
                            row[f"节点{idx}"] = value
                            node_values.append(value)
                        except ValueError:
                            QMessageBox.critical(self, "错误", f"{led} 的 节点{idx} 必须是数字！")
                            return False

                # 检查节点值是否递增（忽略空值）
                non_empty_values = [v for v in node_values if v is not None]
                for i in range(1, len(non_empty_values)):
                    if non_empty_values[i] <= non_empty_values[i - 1]:
                        QMessageBox.critical(
                            self,
                            "错误",
                            f"{led} 的节点值必须递增！\n当前值: {non_empty_values[i - 1]} → {non_empty_values[i]}"
                        )
                        return False

                row["备注"] = self.remark_edits[led].text().strip()
                bin_values[led] = row

            # 保存到内存并导出
            save_bin_data(bin_values)

            # 导出到Excel
            success, msg = _export_step3_nodes_to_excel()
            if not success:
                self.output_box.append(f"【导出失败】{msg}")
                QMessageBox.critical(self, "错误", msg)
                return False

            # 导出到CSV
            success_csv, msg_csv = _export_step3_nodes_to_csv()
            if not success_csv:
                self.output_box.append(f"【CSV导出失败】{msg_csv}")
                QMessageBox.critical(self, "错误", msg_csv)
                return False

            # ========== 新增的CSV验证部分 ==========
            # 获取CSV文件路径并进行验证
            data_dir = _step3_out_dir()
            csv_file_path = os.path.join(data_dir, "step3_bin_nodes.csv")

            if os.path.exists(csv_file_path):
                is_valid, validation_msg = validate_csv_file(csv_file_path)
                csv_validation_passed = is_valid
            else:
                csv_validation_passed = False
                validation_msg = "CSV文件未找到"

            # 如果验证失败，直接返回
            if not csv_validation_passed:
                self.output_box.append(f"\n【CSV验证失败】{validation_msg}")
                return False

            # ========== 按正确顺序调用核心函数 ==========

            # 1. 先调用step3_bin_process进行分bin处理
            try:
                self.output_box.append(f"\n【开始分bin处理...】")
                bin_summary = run_step3_bin_process(target_column=None)
                self.output_box.append(f"\n【分bin处理完成】")
                for led, bins in bin_summary.items():
                    self.output_box.append(f"{led}: {bins}")
            except Exception as e:
                self.output_box.append(f"\n【调用step3_bin_process时出错】")
                self.output_box.append(f"{e}")
                return False

            # 2. 再调用step3_bin_range生成区间文件
            try:
                success, result = generate_bin_ranges()
                if success:
                    self.output_box.append(f"\n【Bin区间生成成功】")
                    self.output_box.append(f"已生成step3_bin_ranges.csv文件")
                    self.output_box.append(f"区间列表: {result}")
                else:
                    self.output_box.append(f"\n【Bin区间生成失败】")
                    self.output_box.append(f"{result}")
                    return False
            except Exception as e:
                self.output_box.append(f"\n【调用step3_bin_range时出错】")
                self.output_box.append(f"{e}")
                return False

            # 输出框：只显示用户形成的分bin区间
            self.output_box.append("说明：以下为根据节点相邻形成的分bin区间。\n")

            any_line = False
            for i in range(1, 6):
                led = f"LED{i}"
                row = led_bin_data.get(led, {})
                nodes = [row.get(f"节点{k}", "") for k in range(1, 6)]
                if all((x == "" for x in nodes)):
                    self.output_box.append(f"{led}：无数据，跳过。")
                    continue

                intervals = build_intervals_from_nodes(nodes)
                txt = fmt_intervals(intervals)
                if txt:
                    self.output_box.append(f"{led} 的分bin区间：{txt}\n")
                else:
                    self.output_box.append(f"{led} 的分bin区间：（节点不足形成区间）\n")
                any_line = True

            if not any_line:
                self.output_box.append("未检测到任何 LED 的节点输入。")

            # 进度条象征性运行
            self.progress_bar.setVisible(True)
            self.progress_timer.start(50)  # 20fps动画

            # 定时关闭进度条
            QTimer.singleShot(600, self._finish_progress)

            return True

        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生错误：{e}")
            return False

    def _finish_progress(self):
        """完成进度条动画"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        QMessageBox.information(
            self,
            "成功",
            "分bin节点数据写入成功！\n已在输出框显示分bin区间。\n同时导出了Excel和CSV文件。"
        )

    def on_save_click(self):
        """写入数据按钮点击事件"""
        # 清空输出框
        self.output_box.clear()
        self.process_bin_data()


# ---------------------------------------------
# 独立运行入口
# ---------------------------------------------

class Step3BinInputWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第三步：写入供应商分bin区间节点")
        self.resize(900, 630)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step3BinInputWidget(self)
        layout.addWidget(self.main_widget)


def main():
    import sys
    app = QApplication(sys.argv)
    window = Step3BinInputWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()