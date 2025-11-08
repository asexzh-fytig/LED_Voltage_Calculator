# -*- coding: utf-8 -*-
"""
Step8 汇总输出模块（summary_output）
------------------------------------------------
功能：
1. 读取step4_mixbin_combos_text.csv，进行文字组合
2. 读取Step7_combos_Voltage_ranges.csv，获取统计值
3. 输出"电压分析计算结果.xlsx"到step8_summary_output/
"""
import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step4_dir, get_step7_dir, get_step8_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")


    # 备用方案
    def get_step4_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step4_dir = os.path.join(current_dir, '..', 'data_files', 'step4_mixbin')
        os.makedirs(step4_dir, exist_ok=True)
        return step4_dir


    def get_step7_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step7_dir = os.path.join(current_dir, '..', 'data_files', 'step7_final_calculation')
        os.makedirs(step7_dir, exist_ok=True)
        return step7_dir


    def get_step8_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step8_dir = os.path.join(current_dir, '..', 'data_files', 'step8_summary_output')
        os.makedirs(step8_dir, exist_ok=True)
        return step8_dir
import os
import csv
from typing import List, Tuple, Optional, Callable
from openpyxl import Workbook
from openpyxl.styles import Font
import sys


def _find_project_root(start_dir: str) -> str:
    """定位项目根目录"""
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


def combine_text_row(row_data: List[str]) -> str:
    """
    将一行20个单元格的数据按照规则组合成字符串
    规则：
    - 四个为一组，共5组
    - 组内非0的字符串用冒号连接（冒号左右加空格）
    - 如果组内全部为0，则跳过该组
    - 组之间用加号连接（加号左右加空格）
    """
    if len(row_data) < 20:
        # 如果不足20列，用空字符串补齐
        row_data = row_data + [""] * (20 - len(row_data))

    groups = []

    # 处理5组，每组4个单元格
    for group_idx in range(5):
        start_idx = group_idx * 4
        end_idx = start_idx + 4
        group_cells = row_data[start_idx:end_idx]

        # 过滤掉0和空字符串
        non_zero_cells = [cell for cell in group_cells if cell != "0" and cell.strip() != ""]

        # 如果组内有非0的单元格，则用冒号连接（左右加空格）
        if non_zero_cells:
            group_str = " : ".join(non_zero_cells)  # 冒号左右加空格
            groups.append(group_str)

    # 用加号连接所有非空组（左右加空格）
    return " + ".join(groups)  # 加号左右加空格


def read_combos_text_data(combos_text_path: str) -> List[List[str]]:
    """读取混bin组合文本数据"""
    combos_data = []

    if not os.path.exists(combos_text_path):
        raise FileNotFoundError(f"混bin组合文本文件不存在: {combos_text_path}")

    with open(combos_text_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # 跳过空行
                combos_data.append(row)

    return combos_data


def read_voltage_ranges_data(ranges_path: str) -> List[List[str]]:
    """读取电压范围数据"""
    ranges_data = []

    if not os.path.exists(ranges_path):
        raise FileNotFoundError(f"电压范围文件不存在: {ranges_path}")

    with open(ranges_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # 跳过表头
        next(reader, None)
        for row in reader:
            if row and len(row) >= 4:  # 确保有足够的列
                ranges_data.append(row)

    return ranges_data


def generate_summary_output(progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Tuple[bool, str]:
    """
    生成汇总输出
    :param progress_callback: 进度回调函数
    :return: (成功标志, 消息)
    """
    try:
        step4_dir = get_step4_dir()
        step7_dir = get_step7_dir()
        step8_dir = get_step8_dir()

        # 1. 读取混bin组合文本数据
        combos_text_path = os.path.join(step4_dir, "step4_mixbin_combos_text.csv")
        print("正在读取混bin组合文本数据...")
        if progress_callback:
            progress_callback(0, 100, "正在读取混bin组合文本数据...")

        combos_data = read_combos_text_data(combos_text_path)
        total_rows = len(combos_data)

        if total_rows == 0:
            return False, "混bin组合文本文件为空"

        print(f"读取到 {total_rows} 行混bin组合数据")

        # 2. 读取电压范围数据
        ranges_path = os.path.join(step7_dir, "Step7_combos_Voltage_ranges.csv")
        print("正在读取电压范围数据...")
        if progress_callback:
            progress_callback(20, 100, "正在读取电压范围数据...")

        ranges_data = read_voltage_ranges_data(ranges_path)

        if len(ranges_data) != total_rows:
            return False, f"数据行数不匹配: 混bin组合 {total_rows} 行, 电压范围 {len(ranges_data)} 行"

        # 3. 创建Excel工作簿
        output_path = os.path.join(step8_dir, "电压分析计算结果.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "电压分析结果"

        # 写入表头
        header_font = Font(bold=True)
        ws.append(["混bin组合", "最小值", "典型值", "最大值"])

        # 设置表头字体加粗
        for cell in ws[1]:
            cell.font = header_font

        # 4. 处理每一行数据
        print("正在生成汇总输出...")

        for i in range(total_rows):
            if progress_callback:
                progress = 20 + int((i / total_rows) * 80)
                progress_callback(progress, 100, f"处理第 {i + 1}/{total_rows} 行")

            # 获取混bin组合文本行
            combo_row = combos_data[i]

            # 组合文本
            combined_text = combine_text_row(combo_row)

            # 获取电压范围数据
            range_row = ranges_data[i]
            # 第2、3、4列对应最小值、典型值、最大值
            min_val = range_row[1] if len(range_row) > 1 else "0"
            median_val = range_row[2] if len(range_row) > 2 else "0"
            max_val = range_row[3] if len(range_row) > 3 else "0"

            # 写入Excel
            ws.append([combined_text, min_val, median_val, max_val])

            print(f"  第 {i + 1} 行: {combined_text}")

        # 5. 设置列宽
        # 第1列（A列）宽度为60
        ws.column_dimensions['A'].width = 60
        # 第2、3、4列（B、C、D列）宽度为20
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20

        # 6. 保存Excel文件
        wb.save(output_path)

        success_message = f"汇总输出完成！\n" \
                          f"输出文件: {output_path}\n" \
                          f"总行数: {total_rows}"

        return True, success_message

    except Exception as e:
        return False, f"生成汇总输出时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step8 汇总输出模块 (summary_output)")
    print("=" * 50)

    try:
        # 简单的控制台进度显示
        def console_progress_callback(current, total, detail):
            if total == 100:  # 百分比模式
                print(f"进度: {current}% - {detail}")
            else:  # 行数模式
                progress_percent = (current / total) * 100
                print(f"进度: {current}/{total} ({progress_percent:.1f}%) - {detail}")

        success, message = generate_summary_output(console_progress_callback)

        if success:
            print(f"\n✅ {message}")
            print("\n汇总输出完成！")
        else:
            print(f"\n❌ {message}")
            print("\n汇总输出失败！")

    except KeyboardInterrupt:
        print("\n用户中断处理")
    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()