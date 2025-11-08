# -*- coding: utf-8 -*-
"""
第八步：导出资料界面（PyQt版本）
------------------------------------------------
功能：
- 选择保存目录
- 执行step8_summary_output.py生成汇总文件
- 将所有.xlsx和.jpg文件复制到用户指定目录
"""

import os
import shutil
import math  # 添加math模块导入
from pathlib import Path

# PyQt相关导入
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit, QMessageBox,
                             QFrame, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# 导入路径管理
from path_manager import get_data_files_dir

# 导入核心模块
try:
    from core_functions.step8_summary_output import generate_summary_output
except ImportError as e:
    print(f"警告：无法导入导出模块: {e}")


    # 定义备用函数
    def generate_summary_output(progress_callback=None):
        return False, f"导出模块未加载: {e}"


# ---------------------------------------------
# 导出线程类
# ---------------------------------------------
class ExportThread(QThread):
    """导出线程"""

    progress_updated = pyqtSignal(int, int, str)  # current, total, detail
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, save_path, parent=None):
        super().__init__(parent)
        self.save_path = save_path
        self.is_running = True

    def stop_export(self):
        """停止导出"""
        self.is_running = False

    def run(self):
        """执行导出"""
        try:
            self.progress_updated.emit(0, 100, "开始导出流程...")

            # 第一步：生成汇总输出
            self.progress_updated.emit(10, 100, "第一步：生成电压分析计算结果...")

            def progress_callback(current, total, detail):
                if not self.is_running:
                    return
                if total == 100:  # 百分比模式
                    progress = 10 + int(current * 0.6)  # 占60%的进度
                    self.progress_updated.emit(progress, 100, f"生成汇总文件 - {detail}")
                else:  # 行数模式
                    progress_percent = (current / total) * 60  # 占60%的进度
                    progress = 10 + int(progress_percent)
                    self.progress_updated.emit(progress, 100, f"生成汇总文件 - {detail}")

            success, message = generate_summary_output(progress_callback)

            if not success:
                self.finished.emit(False, f"生成汇总文件失败: {message}")
                return

            if not self.is_running:
                self.finished.emit(False, "用户取消导出")
                return

            self.progress_updated.emit(70, 100, "✅ 电压分析计算结果生成完成")

            # 第二步：复制所有.xlsx和.jpg文件
            self.progress_updated.emit(70, 100, "第二步：复制所有Excel和图片文件...")

            data_files_dir = get_data_files_dir()
            copied_files = self._copy_data_files(data_files_dir, self.save_path)

            if not self.is_running:
                self.finished.emit(False, "用户取消导出")
                return

            if not copied_files:
                self.finished.emit(False, "没有找到任何Excel或图片文件")
                return

            self.progress_updated.emit(100, 100, "✅ 文件复制完成")

            success_message = f"导出完成！\n" \
                              f"保存目录: {self.save_path}\n" \
                              f"共复制 {len(copied_files)} 个文件\n\n" \
                              f"复制的文件:\n" + "\n".join(f"  - {f}" for f in copied_files)

            self.finished.emit(True, success_message)

        except Exception as e:
            self.finished.emit(False, f"导出过程中出错: {e}")

    def _copy_data_files(self, source_dir: str, target_dir: str) -> list:
        """复制所有.xlsx和.jpg文件到目标目录"""
        copied_files = []

        try:
            # 遍历data_files目录及其所有子目录
            for root, dirs, files in os.walk(source_dir):
                if not self.is_running:
                    break

                for file in files:
                    if not self.is_running:
                        break

                    if file.lower().endswith(('.xlsx', '.jpg', '.jpeg', '.png')):
                        source_path = os.path.join(root, file)
                        target_path = os.path.join(target_dir, file)

                        # 处理同名文件
                        counter = 1
                        base_name, ext = os.path.splitext(file)
                        while os.path.exists(target_path):
                            new_name = f"{base_name}_{counter}{ext}"
                            target_path = os.path.join(target_dir, new_name)
                            counter += 1

                        try:
                            shutil.copy2(source_path, target_path)
                            copied_files.append(os.path.basename(target_path))
                            self.progress_updated.emit(
                                70 + int(30 * len(copied_files) / max(len(files), 1)),
                                100,
                                f"已复制: {os.path.basename(target_path)}"
                            )
                        except Exception as e:
                            self.progress_updated.emit(
                                70, 100, f"复制失败 {file}: {e}"
                            )

            return copied_files

        except Exception as e:
            self.progress_updated.emit(70, 100, f"遍历文件时出错: {e}")
            return copied_files


# ---------------------------------------------
# 美观的导出按钮类
# ---------------------------------------------
class ExportButton(QPushButton):
    """美观的导出按钮"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(120, 120)

        # 动画参数
        self.hue = 0
        self.pulse_phase = 0

        # 设置字体
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)

        # 定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)

        # 初始样式
        self.update_style()

    def start_animation(self):
        """开始按钮动画"""
        self.animation_timer.start(40)

    def stop_animation(self):
        """停止按钮动画"""
        self.animation_timer.stop()
        self.hue = 0
        self.pulse_phase = 0
        self.update_style()

    def update_animation(self):
        """更新动画状态"""
        # 更新色调
        self.hue = (self.hue + 3) % 360

        # 更新脉动相位
        self.pulse_phase = (self.pulse_phase + 0.08) % (2 * math.pi)

        # 更新样式
        self.update_style()

    def update_style(self):
        """更新按钮样式"""
        # 计算主色调 - 使用金色系
        main_color = self.hsv_to_rgb(45 + self.hue % 60, 0.9, 0.9)  # 金色系
        light_color = self.hsv_to_rgb(45 + (self.hue + 20) % 60, 0.7, 1.0)
        dark_color = self.hsv_to_rgb(45 + (self.hue + 40) % 60, 0.9, 0.7)

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
                border-radius: 60px;
                color: #2c3e50;
                font-weight: bold;
                font-size: 12px;
                border: 3px solid {light_color};
                min-width: 120px;
                min-height: 120px;
                max-width: 120px;
                max-height: 120px;
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


# ---------------------------------------------
# 主界面类
# ---------------------------------------------
class Step8SummaryOutputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # 导出控制变量
        self.export_thread = None
        self.is_exporting = False

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("最后一步：导出资料")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")
        main_layout.addWidget(title_label)

        description_label = QLabel("选择保存目录以保存文件")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("color: #7f8c8d;")
        main_layout.addWidget(description_label)

        # 路径选择区域
        path_frame = QFrame()
        path_layout = QHBoxLayout(path_frame)

        path_label = QLabel("保存路径：")
        path_layout.addWidget(path_label)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)

        self.browse_button = QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_button)

        main_layout.addWidget(path_frame)

        # 动画按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.export_button = ExportButton("确定导出")
        self.export_button.clicked.connect(self.start_export)
        button_layout.addWidget(self.export_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 输出框
        output_label = QLabel("输出信息：")
        output_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(output_label)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

    def browse_directory(self):
        """浏览选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.path_edit.setText(directory)

    def log_message(self, message: str):
        """在输出框中添加日志消息"""
        self.output_box.append(message)
        # 自动滚动到底部
        self.output_box.verticalScrollBar().setValue(
            self.output_box.verticalScrollBar().maximum()
        )

    def start_export(self):
        """开始导出"""
        save_path = self.path_edit.text().strip()

        if not save_path:
            QMessageBox.critical(self, "错误", "请先选择保存目录")
            return

        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建目录: {e}")
                return

        # 清空输出框
        self.output_box.clear()

        # 禁用按钮
        self.export_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.is_exporting = True

        # 启动按钮动画
        self.export_button.start_animation()

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 在新线程中运行导出
        self.export_thread = ExportThread(save_path)
        self.export_thread.progress_updated.connect(self.update_progress)
        self.export_thread.finished.connect(self.export_finished)
        self.export_thread.start()

        self.log_message("开始导出流程...")

    def update_progress(self, current, total, detail):
        """更新进度显示"""
        self.progress_bar.setValue(current)
        if detail:
            self.log_message(detail)

    def export_finished(self, success: bool, message: str):
        """导出完成后的处理"""
        # 启用按钮
        self.export_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.is_exporting = False

        # 停止按钮动画
        self.export_button.stop_animation()

        # 隐藏进度条
        self.progress_bar.setVisible(False)

        # 显示结果
        self.log_message("\n" + "=" * 50)
        self.log_message(message)

        if success:
            self.log_message("✅ 导出流程完成！")
            QMessageBox.information(self, "完成", "所有文件已成功导出！")
        else:
            self.log_message("❌ 导出流程失败！")
            QMessageBox.critical(self, "错误", message)


# ---------------------------------------------
# 独立运行入口
# ---------------------------------------------
class Step8SummaryOutputWindow(QWidget):
    """独立运行时的窗口类，保持向后兼容"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("最后一步：导出资料")
        self.resize(700, 500)

        # 创建主Widget
        layout = QVBoxLayout(self)
        self.main_widget = Step8SummaryOutputWidget(self)
        layout.addWidget(self.main_widget)


def main():
    import sys
    app = QApplication(sys.argv)
    window = Step8SummaryOutputWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()