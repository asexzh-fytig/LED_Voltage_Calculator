# -*- coding: utf-8 -*-
"""
第七步：蒙特卡罗计算界面（PyQt版本 - 美观动画按钮）
------------------------------------------------
功能：
- 输入模拟次数
- 显示绚丽的圆形动画按钮
- 调用蒙特卡罗计算和结果绘制模块
- 显示进度信息
"""

import os
import math
import time
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QRect, QPoint
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QPen, QRadialGradient, QConicalGradient
from PyQt5.QtCore import QRectF, QPointF, pyqtProperty

# 导入路径管理
from path_manager import get_step7_dir

# 导入核心计算模块
try:
    from core_functions.step7_final_calculation import run_monte_carlo_simulation
    from core_functions.step7_result_curve_plotting import process_combos_voltage_results
except ImportError as e:
    print(f"警告：无法导入计算模块: {e}")


    # 定义备用函数
    def run_monte_carlo_simulation(simulation_count, progress_callback=None, stop_check=None):
        return False, f"计算模块未加载: {e}"


    def process_combos_voltage_results(progress_callback=None):
        return False, f"绘图模块未加载: {e}"


# ---------------------------------------------
# 美观动画按钮类
# ---------------------------------------------
class BeautifulAnimatedButton(QPushButton):
    """美观的动画圆形按钮"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(140, 140)

        # 动画参数
        self.hue = 0
        self.pulse_phase = 0
        self.glow_intensity = 0
        self.sparkle_angle = 0

        # 设置字体
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)

        # 定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)

        # 初始样式
        self.update_style()

    def start_animation(self):
        """开始按钮动画"""
        self.animation_timer.start(30)  # 30ms刷新，更流畅

    def stop_animation(self):
        """停止按钮动画"""
        self.animation_timer.stop()
        self.hue = 0
        self.pulse_phase = 0
        self.glow_intensity = 0
        self.sparkle_angle = 0
        self.update_style()

    def update_animation(self):
        """更新动画状态"""
        # 更新色调（彩虹色循环）
        self.hue = (self.hue + 2) % 360

        # 更新脉动相位
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)

        # 更新发光强度（呼吸效果）
        self.glow_intensity = 15 + 5 * math.sin(self.pulse_phase * 2)

        # 更新闪光角度
        self.sparkle_angle = (self.sparkle_angle + 5) % 360

        # 更新样式
        self.update_style()

    def update_style(self):
        """更新按钮样式"""
        # 计算主色调
        main_color = self.hsv_to_rgb(self.hue, 0.9, 0.9)
        light_color = self.hsv_to_rgb((self.hue + 30) % 360, 0.7, 1.0)
        dark_color = self.hsv_to_rgb((self.hue + 330) % 360, 0.9, 0.7)

        # 脉动缩放
        pulse_scale = 0.95 + 0.05 * math.sin(self.pulse_phase)

        # 创建样式表
        style = f"""
            QPushButton {{
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.8,
                    stop:0 {main_color},
                    stop:0.7 {dark_color},
                    stop:1 {light_color}
                );
                border-radius: 70px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 3px solid {light_color};
                min-width: 140px;
                min-height: 140px;
                max-width: 140px;
                max-height: 140px;
            }}
            QPushButton:hover {{
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.9,
                    stop:0 {light_color},
                    stop:0.7 {main_color},
                    stop:1 {dark_color}
                );
            }}
            QPushButton:pressed {{
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.7,
                    stop:0 {dark_color},
                    stop:0.7 {main_color},
                    stop:1 {light_color}
                );
            }}
        """

        self.setStyleSheet(style)

    def hsv_to_rgb(self, h, s, v):
        """HSV转RGB"""
        h = h / 360.0
        if s == 0.0:
            r = g = b = v
        else:
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            elif i == 5:
                r, g, b = v, p, q

        # 转换为十六进制颜色
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def paintEvent(self, event):
        """自定义绘制事件，添加发光效果和闪光"""
        # 先调用父类的绘制
        super().paintEvent(event)

        # 自定义绘制发光效果
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制发光效果
        if self.glow_intensity > 0:
            glow_color = QColor(*self.hex_to_rgb(self.hsv_to_rgb(self.hue, 0.8, 1.0)))
            glow_color.setAlpha(int(self.glow_intensity * 10))

            pen = QPen(glow_color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # 绘制多个同心圆实现发光效果
            for i in range(3):
                radius = 65 + i * 3
                painter.drawEllipse(QPoint(70, 70), radius, radius)

        # 绘制闪光效果
        sparkle_color = QColor(255, 255, 255, 200)
        painter.setPen(QPen(sparkle_color, 2))

        # 在按钮边缘绘制闪光点
        for i in range(8):
            angle = math.radians(self.sparkle_angle + i * 45)
            x = 70 + 60 * math.cos(angle)
            y = 70 + 60 * math.sin(angle)
            painter.drawPoint(int(x), int(y))

    def hex_to_rgb(self, hex_color):
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------
# 进度窗口类
# ---------------------------------------------
class ProgressDialog(QDialog):
    """进度显示对话框"""

    progress_updated = pyqtSignal(int, int, str)  # current, total, detail

    def __init__(self, parent=None, title="计算进度"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)

        layout = QVBoxLayout(self)

        # 进度标签
        self.progress_label = QLabel("准备开始...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 详细信息标签
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_label)

        # 连接信号
        self.progress_updated.connect(self.update_progress)

    def update_progress(self, current, total, detail):
        """更新进度显示"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_bar.setValue(int(progress_percent))
            self.progress_label.setText(f"进度: {current}/{total} ({progress_percent:.1f}%)")
        else:
            self.progress_bar.setValue(current)
            self.progress_label.setText(f"进度: {current}%")

        if detail:
            self.detail_label.setText(detail)


# ---------------------------------------------
# 计算线程类
# ---------------------------------------------
class CalculationThread(QThread):
    """计算线程"""

    progress_updated = pyqtSignal(int, int, str)  # current, total, detail
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, simulation_count, parent=None):
        super().__init__(parent)
        self.simulation_count = simulation_count
        self.stop_requested = False

    def stop_calculation(self):
        """停止计算"""
        self.stop_requested = True

    def run(self):
        """执行计算"""
        try:
            self.progress_updated.emit(0, 100, "开始蒙特卡罗模拟")

            # 第一步：运行蒙特卡罗模拟
            def progress_callback_step1(current, total, detail):
                if self.stop_requested:
                    return
                self.progress_updated.emit(current, total, f"蒙特卡罗模拟 - {detail}")

            def stop_check():
                return self.stop_requested

            success, message = run_monte_carlo_simulation(
                self.simulation_count,
                progress_callback=progress_callback_step1,
                stop_check=stop_check
            )

            if not success or self.stop_requested:
                self.finished.emit(success, message)
                return

            self.progress_updated.emit(50, 100, "蒙特卡罗模拟完成，开始绘制结果曲线...")

            # 第二步：绘制结果曲线
            def progress_callback_step2(current, total, detail):
                if self.stop_requested:
                    return
                self.progress_updated.emit(50 + current // 2, 100, f"结果曲线绘制 - {detail}")

            success2, message2 = process_combos_voltage_results(
                progress_callback=progress_callback_step2
            )

            # 合并结果消息
            final_message = f"{message}\n{message2}" if success2 else f"{message}\n绘图失败: {message2}"
            final_success = success and success2

            self.finished.emit(final_success, final_message)

        except Exception as e:
            self.finished.emit(False, f"计算过程中出错: {e}")


# ---------------------------------------------
# 主界面类
# ---------------------------------------------
class Step7FinalCalculationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # 计算控制变量
        self.calculation_thread = None
        self.progress_dialog = None
        self.stop_requested = False

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("第七步：蒙特卡罗计算")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(title_label)

        description_label = QLabel("输入模拟次数，点击开始计算")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("color: #7f8c8d;")
        main_layout.addWidget(description_label)

        # 输入框区域
        input_layout = QHBoxLayout()
        input_label = QLabel("请输入模拟次数：")
        input_layout.addWidget(input_label)

        self.simulation_count_edit = QLineEdit()
        self.simulation_count_edit.setText("100000")
        self.simulation_count_edit.setFixedWidth(100)
        self.simulation_count_edit.setAlignment(Qt.AlignCenter)
        input_layout.addWidget(self.simulation_count_edit)

        input_layout.addStretch()
        main_layout.addLayout(input_layout)

        # 动画按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.animated_button = BeautifulAnimatedButton("开始运算")
        self.animated_button.clicked.connect(self.start_calculation)
        button_layout.addWidget(self.animated_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 输出框
        output_label = QLabel("输出信息：")
        output_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(output_label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

    def log_message(self, message: str):
        """在输出框中添加日志消息"""
        self.output_box.append(message)
        # 自动滚动到底部
        self.output_box.verticalScrollBar().setValue(
            self.output_box.verticalScrollBar().maximum()
        )

    def start_calculation(self):
        """开始计算"""
        try:
            simulation_count = int(self.simulation_count_edit.text().strip())
            if simulation_count <= 0:
                QMessageBox.critical(self, "错误", "模拟次数必须为正整数")
                return
        except ValueError:
            QMessageBox.critical(self, "错误", "请输入有效的整数")
            return

        # 清空输出框
        self.output_box.clear()

        # 启动按钮动画
        self.animated_button.start_animation()

        # 禁用输入框
        self.simulation_count_edit.setEnabled(False)

        # 重置停止标志
        self.stop_requested = False

        # 创建进度对话框
        self.progress_dialog = ProgressDialog(self, "计算进度")
        self.progress_dialog.show()

        # 创建并启动计算线程
        self.calculation_thread = CalculationThread(simulation_count)
        self.calculation_thread.progress_updated.connect(self.progress_dialog.progress_updated)
        self.calculation_thread.finished.connect(self.calculation_finished)
        self.calculation_thread.start()

        self.log_message(f"开始蒙特卡罗模拟，模拟次数: {simulation_count}")

    def calculation_finished(self, success: bool, message: str):
        """计算完成后的处理"""
        # 停止按钮动画
        self.animated_button.stop_animation()

        # 启用输入框
        self.simulation_count_edit.setEnabled(True)

        # 关闭进度对话框
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        # 显示结果
        self.log_message(message)

        if success:
            self.log_message("✅ 所有计算完成！")
            QMessageBox.information(self, "完成", "蒙特卡罗计算和结果绘制完成！")
        else:
            self.log_message("❌ 计算失败！")
            if "用户请求停止" not in message:
                QMessageBox.critical(self, "错误", message)


# ---------------------------------------------
# 独立运行入口
# ---------------------------------------------
class Step7FinalCalculationWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("第七步：蒙特卡罗计算")
        self.resize(700, 500)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step7FinalCalculationWidget(self)
        layout.addWidget(self.main_widget)


def main():
    import sys
    app = QApplication(sys.argv)
    window = Step7FinalCalculationWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()