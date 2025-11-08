# -*- coding: utf-8 -*-
"""
第二步：输入LED信息和测试电流（PyQt版本）
------------------------------------------------
功能：
- 输入5个LED的品牌、封装、色温/波长、测试电流和备注
- 导出到Excel和CSV文件
- 保持原有UI布局和逻辑
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

# 路径导入
from path_manager import get_step2_dir

# Excel相关
from openpyxl import Workbook

# ---------------------------------------------
# 数据存储和路径工具
# ---------------------------------------------

# 存储LED电压范围和测试电流的字典（内存缓存）
led_data = {}


def save_input_data(led_values, test_currents, remarks):
    """
    保存输入的数据到字典
    :param led_values: dict[LED] -> (品牌, 封装, 色温/波长)
    :param test_currents: dict[LED] -> float|str
    :param remarks: dict[LED] -> str
    """
    for led in led_values:
        brand, package, color_temp = led_values[led]
        led_data[led] = {
            'MIN': brand,  # 注意：这里MIN实际存储品牌，MAX存储封装，TYP存储色温/波长
            'MAX': package,
            'TYP': color_temp,
            'TEST_CURRENT': test_currents.get(led, ""),  # 允许为空
            'REMARKS': remarks.get(led, "")
        }


def _find_project_root(start_dir: str) -> str:
    """定位项目根目录"""
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


# 修改 _data_files_dir 函数
def _data_files_dir() -> str:
    """返回 data_files/step2_input_process 目录"""
    return get_step2_dir()


# ---------------------------------------------
# 导出功能
# ---------------------------------------------

def _export_step2_to_excel():
    """
    将 led_data 导出到 data_files/step2_input_process/step2_LED信息及测试电流输入参数.xlsx
    表头：LED, 品牌, 封装, 色温/波长, 测试电流/mA, 备注
    返回 (success, message)
    """
    if not led_data:
        return False, "没有可导出的 LED 数据。"

    try:
        data_dir = _data_files_dir()
        out_path = os.path.join(data_dir, "step2_LED信息及测试电流输入参数.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Ranges"

        headers = ["   ", "品牌", "封装", "色温/波长", "测试电流/mA", "备注"]
        ws.append(headers)

        # 始终输出所有LED（LED1到LED5），即使没有数据
        for led in ["LED1", "LED2", "LED3", "LED4", "LED5"]:
            row = led_data.get(led, {})  # 获取该LED的字典
            # 如果没有数据，就用空字符串填充
            brand = row.get("MIN", "")
            package = row.get("MAX", "")
            color_temp = row.get("TYP", "")
            test_current = row.get("TEST_CURRENT", "")
            remark = row.get("REMARKS", "")

            # 写入数据，空值使用空字符串
            ws.append([led, brand, package, color_temp, test_current, remark])

        wb.save(out_path)
        return True, out_path
    except Exception as e:
        return False, f"导出 Excel 失败：{e}"


def _export_step2_currents_to_csv():
    """
    导出5个LED的测试电流值到CSV文件，未输入的填写0
    返回 (success, message)
    """
    try:
        data_dir = _data_files_dir()
        out_path = os.path.join(data_dir, "step2_currents.csv")

        # 准备5个LED的电流值，顺序为LED1到LED5
        currents = []
        for led in ["LED1", "LED2", "LED3", "LED4", "LED5"]:
            current_value = led_data.get(led, {}).get("TEST_CURRENT", 0)
            # 如果电流值为空字符串或None，设为0
            if current_value == "" or current_value is None:
                current_value = 0
            currents.append(current_value)

        # 写入CSV文件
        with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(currents)  # 写入一行，包含5个电流值

        return True, out_path
    except Exception as e:
        return False, f"导出 CSV 失败：{e}"


# ---------------------------------------------
# PyQt Widget 类
# ---------------------------------------------

class Step2InputRangeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # 输入框引用
        self.brand_edits = {}
        self.package_edits = {}
        self.color_temp_edits = {}
        self.current_edits = {}
        self.remark_edits = {}

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
        title_label = QLabel("第二步：输入并导出到 Excel")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        description_label = QLabel("这一步主要是填写测试电流(别写单位)，其他可以不填。点击'写入数据'导出。")
        description_label.setStyleSheet("color: #1f4a7c;")
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)

        # 表格框架
        table_frame = QFrame()
        table_frame.setFrameStyle(QFrame.Box)
        table_layout = QVBoxLayout(table_frame)

        # 创建表格
        self.table_widget = QTableWidget(5, 6)  # 6行6列（包括表头）
        headers = ["临时信息", "品牌", "封装", "色温/波长", "测试电流/mA", "备注"]
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
            # 品牌列
            brand_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 1, brand_edit)
            self.brand_edits[f"LED{row + 1}"] = brand_edit

            # 封装列
            package_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 2, package_edit)
            self.package_edits[f"LED{row + 1}"] = package_edit

            # 色温/波长列
            color_temp_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 3, color_temp_edit)
            self.color_temp_edits[f"LED{row + 1}"] = color_temp_edit

            # 测试电流列
            current_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 4, current_edit)
            self.current_edits[f"LED{row + 1}"] = current_edit

            # 备注列
            remark_edit = QLineEdit()
            self.table_widget.setCellWidget(row, 5, remark_edit)
            self.remark_edits[f"LED{row + 1}"] = remark_edit

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
        save_button.clicked.connect(self.on_save_button_click)
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

    def process_input_data(self):
        """
        处理输入的数据，保存到变量中 & 导出到 data_files/step2_input_process/
        """
        try:
            # 读取输入值
            led_values = {}
            test_currents = {}
            remarks = {}

            for i in range(5):
                led = f"LED{i + 1}"

                brand_value = self.brand_edits[led].text().strip()
                package_value = self.package_edits[led].text().strip()
                color_temp_value = self.color_temp_edits[led].text().strip()
                current_value = self.current_edits[led].text().strip()
                remark_value = self.remark_edits[led].text().strip()

                # 全空 => 跳过该LED（表示未使用）
                if not brand_value and not package_value and not color_temp_value and not remark_value and not current_value:
                    continue

                # 只对测试电流进行数字校验，其他字段可以是任意内容
                led_values[led] = (brand_value, package_value, color_temp_value)
                remarks[led] = remark_value

                if current_value:
                    try:
                        test_currents[led] = float(current_value)
                    except ValueError:
                        QMessageBox.critical(self, "错误", f"{led} 的测试电流必须是数字！")
                        return False

            # 保存到内存
            save_input_data(led_values, test_currents, remarks)

            # 导出到 Excel（控制成功/失败显示）
            success, message = _export_step2_to_excel()

            # 输出框：先清空
            self.output_box.clear()

            if not success:
                # 导出失败：写到输出框 & 弹窗，不跑进度条
                self.output_box.append(f"【导出失败】{message}")
                QMessageBox.critical(self, "错误", message)
                return False

            # 导出成功：输出框显示路径
            self.output_box.append(f"Excel导出成功：{message}")

            # 导出电流值到CSV
            success_csv, message_csv = _export_step2_currents_to_csv()
            if success_csv:
                self.output_box.append(f"CSV导出成功：{message_csv}")
            else:
                self.output_box.append(f"【CSV导出失败】{message_csv}")
                # CSV导出失败不中断流程，只提示

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
        QMessageBox.information(self, "成功", "数据写入成功！")

    def on_save_button_click(self):
        """写入数据按钮点击事件"""
        self.process_input_data()


# ---------------------------------------------
# 独立运行入口
# ---------------------------------------------

class Step2InputRangeWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第二步：输入并导出到 Excel")
        self.resize(900, 600)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step2InputRangeWidget(self)
        layout.addWidget(self.main_widget)


def main():
    import sys
    app = QApplication(sys.argv)
    window = Step2InputRangeWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()