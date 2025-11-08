# -*- coding: utf-8 -*-
"""
Step6 混bin组合串数处理模块（combos_process）
-------------------------------------------
功能：
- 读取 step6_series_count.csv 中的5个串数值
- 将 step4_mixbin_combos_uniformization.csv 的数据按4列一组乘以对应的串数值
- 生成串数处理后的组合文件

输入文件：
- step6_series_count.csv: 1行5列串数数据
- step4_mixbin_combos_uniformization.csv: 归一化混bin组合数据

输出文件：
- step6_parameters/Step6_mixbin_combos_uniformization_series.csv: 串数处理后的组合数据
"""
import sys
import os

# --- 统一加载 path_manager：开发环境从明确文件路径加载；打包环境退回普通 import ---
import importlib.util

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PM_PATH = os.path.normpath(os.path.join(CURRENT_DIR, '..', 'main_app', 'path_manager.py'))

if os.path.isfile(PM_PATH):
    # 开发环境：从项目里的 path_manager.py 明确加载
    spec = importlib.util.spec_from_file_location("path_manager", PM_PATH)
    path_manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(path_manager)
else:
    # 打包环境（如 PyInstaller）：模块会被打包，直接正常 import
    import path_manager  # noqa: F401,E402
    path_manager = sys.modules["path_manager"]

# 只通过 path_manager 获取目录（绑定函数句柄，后续代码不用改）
get_step4_dir = path_manager.get_step4_dir
get_step6_dir = path_manager.get_step6_dir

import os
import csv
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


def _step6_parameters_dir() -> str:
    """确保并返回 data_files/step6_parameters/ 目录"""
    return get_step6_dir()


def _step4_mixbin_dir() -> str:
    """返回 data_files/step4_mixbin/ 目录"""
    return get_step4_dir()

def process_combos_with_series_count():
    """
    处理混bin组合数据，乘以串数值
    :return: (成功标志, 消息)
    """
    try:
        step6_dir = _step6_parameters_dir()
        step4_dir = _step4_mixbin_dir()

        # 读取串数文件
        series_count_path = os.path.join(step6_dir, "step6_series_count.csv")
        if not os.path.exists(series_count_path):
            return False, f"串数文件不存在: {series_count_path}"

        with open(series_count_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            series_counts = [float(x) for x in next(reader)]

        print(f"读取到的串数值: {series_counts}")

        # 读取归一化组合文件
        uniformization_path = os.path.join(step4_dir, "step4_mixbin_combos_uniformization.csv")
        if not os.path.exists(uniformization_path):
            return False, f"归一化组合文件不存在: {uniformization_path}"

        # 读取并处理数据
        processed_rows = []
        with open(uniformization_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_idx, row in enumerate(reader):
                processed_row = []

                # 处理20列数据，每4列一组
                for group_idx in range(5):  # 5组，每组4列
                    start_col = group_idx * 4
                    end_col = start_col + 4
                    group_data = row[start_col:end_col] if len(row) >= end_col else []

                    # 确保每组有4个元素，不足的补空字符串
                    while len(group_data) < 4:
                        group_data.append("")

                    # 获取对应的串数值
                    series_count = series_counts[group_idx]

                    # 处理组内每个元素
                    for col_idx, cell_value in enumerate(group_data):
                        if cell_value and cell_value.strip():  # 非空单元格
                            try:
                                num_value = float(cell_value.strip())
                                processed_value = num_value * series_count
                                # 保留足够的精度，去除不必要的尾随零
                                processed_value_str = f"{processed_value:.10f}".rstrip('0').rstrip('.')
                                processed_row.append(processed_value_str)
                            except ValueError:
                                # 如果无法转换为数字，保持原值
                                processed_row.append(cell_value)
                        else:
                            # 空单元格保持为空
                            processed_row.append("")

                processed_rows.append(processed_row)

                # 每处理1000行打印进度
                if (row_idx + 1) % 1000 == 0:
                    print(f"已处理 {row_idx + 1} 行数据")

        # 写入输出文件
        output_path = os.path.join(step6_dir, "Step6_mixbin_combos_uniformization_series.csv")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(processed_rows)

        # 验证输出
        if processed_rows:
            print(f"\n处理完成统计:")
            print(f"  输入文件: {uniformization_path}")
            print(f"  输出文件: {output_path}")
            print(f"  数据尺寸: {len(processed_rows)} 行 × {len(processed_rows[0])} 列")

            # 显示前几个值的处理示例
            if len(processed_rows) > 0 and len(processed_rows[0]) >= 4:
                print(f"\n前几个值的处理示例:")
                for group_idx in range(min(2, 5)):  # 显示前2组
                    series_count = series_counts[group_idx]
                    start_col = group_idx * 4
                    print(f"  第{group_idx + 1}组 (串数={series_count}):")

                    # 显示第一行的处理示例
                    if len(processed_rows[0]) > start_col + 1:
                        original_values = []
                        processed_values = []

                        # 获取原始数据（需要重新读取）
                        with open(uniformization_path, 'r', encoding='utf-8') as orig_f:
                            orig_reader = csv.reader(orig_f)
                            first_row = next(orig_reader)
                            for i in range(4):
                                if len(first_row) > start_col + i:
                                    original_values.append(first_row[start_col + i])
                                else:
                                    original_values.append("")

                        for i in range(4):
                            processed_values.append(processed_rows[0][start_col + i])

                        for i in range(4):
                            if original_values[i] and processed_values[i]:
                                print(f"    {original_values[i]} × {series_count} = {processed_values[i]}")
        else:
            print("警告: 处理后的数据为空")

        return True, f"成功生成串数处理文件: {output_path}"

    except Exception as e:
        return False, f"串数处理时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step6 混bin组合串数处理模块 (combos_process)")
    print("=" * 50)

    success, message = process_combos_with_series_count()

    if success:
        print(f"\n✅ {message}")
        print("\n串数处理完成！")
    else:
        print(f"\n❌ {message}")
        print("\n串数处理失败！")


if __name__ == "__main__":
    main()