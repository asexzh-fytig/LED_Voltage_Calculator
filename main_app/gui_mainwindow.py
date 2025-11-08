# -*- coding: utf-8 -*-
"""
电压范围计算器主界面
------------------------------------------------
功能：
- 集成8个步骤的导航（PowerPoint风格）
- 左侧导航栏 + 右侧内容区
- 启动时自动清理数据文件
- 带背景图片和黑色蒙版的现代化界面
- 预加载所有子界面
"""

import os
import sys
import shutil
import math
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget, QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor, QPainter, QBrush, QLinearGradient
from PyQt5.QtCore import QRect, QSize

# 导入所有步骤的界面
from gui_step1_rawdata import Step1RawDataWidget
from gui_step2_input_range import Step2InputRangeWidget
from gui_step3_bin_input import Step3BinInputWidget
from gui_step4_mixbin import Step4MixBinWidget
from gui_step5_interpolation import Step5InterpolationWidget
from gui_step6_parameters import Step6ParametersWidget
from gui_step7_final_calculation import Step7FinalCalculationWidget
from gui_step8_summary_output import Step8SummaryOutputWidget

# 导入统一的路径管理
from path_manager import get_data_files_dir, get_resources_dir


# ------------------ 工具函数 ------------------
def cleanup_data_files():
    """清理data_files内的8个步骤文件夹"""
    data_dir = get_data_files_dir()
    step_folders = [
        "step1_rawdata_analysis",
        "step2_input_process",
        "step3_bin_process",
        "step4_mixbin",
        "step5_interpolation",
        "step6_parameters",
        "step7_final_calculation",
        "step8_summary_output"
    ]

    cleaned_folders = []

    for folder in step_folders:
        folder_path = os.path.join(data_dir, folder)
        if os.path.exists(folder_path):
            try:
                # 删除文件夹内的所有内容，但保留文件夹本身
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"删除 {file_path} 时出错: {e}")

                cleaned_folders.append(folder)
            except Exception as e:
                print(f"清理 {folder} 时出错: {e}")

    return cleaned_folders


# ------------------ 美观的导航按钮类 ------------------
class NavigationButton(QPushButton):
    """美观的导航按钮"""

    def __init__(self, text, step_index, parent=None):
        super().__init__(text, parent)
        self.step_index = step_index
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 状态：0=未开始，1=进行中，2=已完成
        self.status = 0

        # 动画参数
        self.hover_progress = 0

        # 设置字体
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)

        self.update_style()

    def set_status(self, status):
        """设置按钮状态"""
        self.status = status
        self.update_style()

    def update_style(self):
        """更新按钮样式"""
        if self.status == 0:  # 未开始
            bg_color = "#e9ecef"
            text_color = "#495057"
            border_color = "#dee2e6"
        elif self.status == 1:  # 进行中
            bg_color = "#007bff"
            text_color = "white"
            border_color = "#0056b3"
        else:  # 已完成
            bg_color = "#28a745"
            text_color = "white"
            border_color = "#1e7e34"

        # 添加悬停效果
        if self.hover_progress > 0:
            # 根据状态调整悬停颜色
            if self.status == 0:
                hover_bg = "#dae0e5"
            elif self.status == 1:
                hover_bg = "#0069d9"
            else:
                hover_bg = "#218838"

            # 混合颜色
            r1, g1, b1 = self.hex_to_rgb(bg_color)
            r2, g2, b2 = self.hex_to_rgb(hover_bg)
            r = int(r1 + (r2 - r1) * self.hover_progress)
            g = int(g1 + (g2 - g1) * self.hover_progress)
            b = int(b1 + (b2 - b1) * self.hover_progress)
            bg_color = f"#{r:02x}{g:02x}{b:02x}"

        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-weight: {'bold' if self.status == 1 else 'normal'};
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(bg_color, 0.1)};
            }}
        """

        self.setStyleSheet(style)

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.animate_hover(1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.animate_hover(0)
        super().leaveEvent(event)

    def animate_hover(self, target):
        """动画悬停效果"""
        self.animation = QPropertyAnimation(self, b"hover_progress")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.hover_progress)
        self.animation.setEndValue(target)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    @pyqtProperty(float)
    def hover_progress(self):
        return self._hover_progress

    @hover_progress.setter
    def hover_progress(self, value):
        self._hover_progress = value
        self.update_style()

    def hex_to_rgb(self, hex_color):
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def darken_color(self, color, factor):
        """加深颜色"""
        r, g, b = self.hex_to_rgb(color)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"


# ------------------ 主窗口类 ------------------
class VoltageCalculatorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("电压范围计算器-V1")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)

        # 步骤完成状态
        self.step_completed = [False] * 8
        self.current_step = 0

        # 存储所有步骤界面
        self.step_widgets = []

        # 存储导航按钮
        self.nav_buttons = []

        self.setup_ui()

        # 启动时清理数据文件
        self.initial_cleanup()

    def setup_ui(self):
        """设置UI界面"""
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        self.setup_navigation_panel(main_layout)

        # 右侧内容区
        self.setup_content_panel(main_layout)

        # 预加载所有步骤界面
        self.preload_step_widgets()

    def setup_navigation_panel(self, main_layout):
        """设置左侧导航面板"""
        nav_frame = QFrame()
        nav_frame.setFixedWidth(300)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(248, 249, 250, 0.95);
                border-right: 1px solid #dee2e6;
            }
        """)

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(20, 20, 20, 20)
        nav_layout.setSpacing(15)

        # 标题区域 - 修改：去掉白底，直接透明
        title_label = QLabel("电压范围计算器-V1")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px; background: transparent;")
        nav_layout.addWidget(title_label)

        # 开发信息 - 修改：去掉白底，直接透明
        dev_label = QLabel("软件开发：产品光学部    时间：2025年10月")
        dev_label.setStyleSheet("color: #7f8c8d; font-size: 10px; margin-bottom: 20px; background: transparent;")
        nav_layout.addWidget(dev_label)

        # 步骤导航标题 - 修改：去掉白底，直接透明
        steps_label = QLabel("计算步骤")
        steps_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 14px; background: transparent;")
        nav_layout.addWidget(steps_label)

        # 步骤按钮
        step_names = [
            "第一步：原始数据分析",
            "第二步：输入LED信息",
            "第三步：分bin区间",
            "第四步：混bin方式",
            "第五步：插值计算",
            "第六步：串数和热损",
            "第七步：蒙特卡罗计算",
            "第八步：导出资料"
        ]

        for i, name in enumerate(step_names):
            btn = NavigationButton(name, i)
            btn.clicked.connect(lambda checked, idx=i: self.switch_step(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # 添加弹性空间
        nav_layout.addStretch()

        # 进度概览 - 修改：去掉白底，直接透明
        progress_label = QLabel("整体进度")
        progress_label.setStyleSheet("color: #495057; font-weight: bold; font-size: 14px; margin-top: 20px; background: transparent;")
        nav_layout.addWidget(progress_label)

        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e9ecef;
                border-radius: 4px;
            }
        """)
        nav_layout.addWidget(self.progress_bar)

        self.progress_fill = QFrame(self.progress_bar)
        self.progress_fill.setFixedHeight(8)
        self.progress_fill.setStyleSheet("""
            QFrame {
                background-color: #28a745;
                border-radius: 4px;
            }
        """)
        self.progress_fill.setFixedWidth(0)

        self.progress_text = QLabel("0/8 步骤完成")
        self.progress_text.setStyleSheet("color: #6c757d; font-size: 11px; background: transparent;")
        nav_layout.addWidget(self.progress_text)

        main_layout.addWidget(nav_frame)

    def setup_content_panel(self, main_layout):
        """设置右侧内容面板"""
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background: transparent;
            }
        """)

        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 使用堆叠窗口管理步骤界面
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(content_frame)

    def preload_step_widgets(self):
        """预加载所有步骤界面"""
        step_classes = [
            Step1RawDataWidget,
            Step2InputRangeWidget,
            Step3BinInputWidget,
            Step4MixBinWidget,
            Step5InterpolationWidget,
            Step6ParametersWidget,
            Step7FinalCalculationWidget,
            Step8SummaryOutputWidget
        ]

        for i, step_class in enumerate(step_classes):
            widget = step_class(self)
            self.stacked_widget.addWidget(widget)
            self.step_widgets.append(widget)

        # 显示第一步
        self.switch_step(0)

    def switch_step(self, step_index):
        """切换到指定步骤"""
        if step_index < 0 or step_index >= len(self.step_widgets):
            return

        self.current_step = step_index
        self.stacked_widget.setCurrentIndex(step_index)

        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_buttons):
            if i == step_index:
                btn.set_status(1)  # 进行中
            elif self.step_completed[i]:
                btn.set_status(2)  # 已完成
            else:
                btn.set_status(0)  # 未开始

        # 更新进度显示
        self.update_progress_display()

    def mark_step_completed(self, step_index):
        """标记步骤为完成"""
        if 0 <= step_index < len(self.step_completed):
            self.step_completed[step_index] = True
            self.switch_step(self.current_step)  # 刷新显示

    def update_progress_display(self):
        """更新进度显示"""
        completed_count = sum(self.step_completed)
        total_count = len(self.step_completed)

        # 更新进度条
        progress_width = int((completed_count / total_count) * self.progress_bar.width())
        self.progress_fill.setFixedWidth(progress_width)

        # 更新进度文本
        self.progress_text.setText(f"{completed_count}/{total_count} 步骤完成")

    def initial_cleanup(self):
        """初始清理数据文件"""
        try:
            cleaned = cleanup_data_files()
            if cleaned:
                print(f"已清理文件夹: {', '.join(cleaned)}")
            else:
                print("无需清理，文件夹可能不存在或为空")
        except Exception as e:
            print(f"清理数据文件时出错: {e}")

    def paintEvent(self, event):
        """绘制背景图片和蒙版"""
        painter = QPainter(self)

        # 加载背景图片
        bg_path = os.path.join(get_resources_dir(), "background.jpg")
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            if not pixmap.isNull():
                # 计算裁剪区域，保持比例
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                window_width = self.width()
                window_height = self.height()

                # 计算目标比例
                target_ratio = window_width / window_height
                pixmap_ratio = pixmap_width / pixmap_height

                if pixmap_ratio > target_ratio:
                    # 图片更宽，裁剪左右
                    crop_width = int(pixmap_height * target_ratio)
                    crop_x = (pixmap_width - crop_width) // 2
                    cropped_pixmap = pixmap.copy(crop_x, 0, crop_width, pixmap_height)
                else:
                    # 图片更高，裁剪上下
                    crop_height = int(pixmap_width / target_ratio)
                    crop_y = (pixmap_height - crop_height) // 2
                    cropped_pixmap = pixmap.copy(0, crop_y, pixmap_width, crop_height)

                # 缩放并绘制图片
                scaled_pixmap = cropped_pixmap.scaled(
                    window_width, window_height,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                painter.drawPixmap(0, 0, scaled_pixmap)

        # 绘制黑色蒙版（50%透明度）
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

        # 绘制内容区域的白色背景
        content_rect = QRect(300, 0, self.width() - 300, self.height())
        painter.fillRect(content_rect, QColor(255, 255, 255, 240))


def main():
    """主程序入口"""
    app = QApplication(sys.argv)

    # 设置应用程序样式 - 修改：使用系统默认样式，避免表格样式问题
    # app.setStyle('Fusion')

    window = VoltageCalculatorMainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()