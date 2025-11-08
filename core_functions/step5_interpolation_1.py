# -*- coding: utf-8 -*-
"""
Step5 插值运算模块（interpolation_1）
-----------------------------------
功能：
- 读取 step5_interpolation.csv、step5_current.csv 和 step2_currents.csv
- 对每个LED进行插值运算，计算倍数
- 将结果写入 step5_multiplier.csv

输入文件：
- step5_interpolation.csv: 25行10列If/Vf数据
- step5_current.csv: 1行5列使用电流数据
- step2_currents.csv: 1行5列测试电流数据

输出文件：
- step5_multiplier.csv: 1行5列倍数数据

运算规则：
对每个LED i (0-4):
1. 读取step5_interpolation.csv的第2*i列(If)和第2*i+1列(Vf)
2. 如果If列全为0，则倍数=0
3. 否则：
   - 从step5_current.csv读取第i列值作为x1(使用电流)
   - 从step2_currents.csv读取第i列值作为x2(测试电流)
   - 对x1和x2分别进行线性插值得到y1和y2
   - 计算倍数 = y1 / y2
"""

import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step5_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")
    # 备用方案
    def get_step5_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step5_dir = os.path.join(current_dir, '..', 'data_files', 'step5_interpolation')
        os.makedirs(step5_dir, exist_ok=True)
        return step5_dir
import os
import csv
from path_manager import get_step2_dir
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


def _step5_interpolation_dir() -> str:
    """确保并返回 data_files/step5_interpolation/ 目录"""
    return get_step5_dir()


def linear_interpolation(x_data, y_data, x_target):
    """
    线性插值函数
    :param x_data: x值列表
    :param y_data: y值列表
    :param x_target: 目标x值
    :return: 插值得到的y值
    """
    # 确保数据按x排序
    combined = sorted(zip(x_data, y_data), key=lambda pair: pair[0])
    x_sorted, y_sorted = zip(*combined) if combined else ([], [])

    # 如果目标值小于最小值，使用前两个点
    if x_target <= x_sorted[0]:
        return y_sorted[0]

    # 如果目标值大于最大值，使用最后两个点
    if x_target >= x_sorted[-1]:
        return y_sorted[-1]

    # 找到刚好比目标值大和小的点
    for i in range(len(x_sorted) - 1):
        if x_sorted[i] <= x_target <= x_sorted[i + 1]:
            x1, x2 = x_sorted[i], x_sorted[i + 1]
            y1, y2 = y_sorted[i], y_sorted[i + 1]

            # 线性插值公式
            return y1 + (y2 - y1) * (x_target - x1) / (x2 - x1)

    # 如果找不到合适的区间（理论上不会执行到这里）
    return 0


def calculate_multipliers():
    """
    计算5个LED的倍数并写入step5_multiplier.csv
    :return: (成功标志, 消息)
    """
    try:
        data_dir = _step5_interpolation_dir()

        # 文件路径
        interpolation_path = os.path.join(data_dir, "step5_interpolation.csv")
        current_path = os.path.join(data_dir, "step5_current.csv")
        step2_currents_path = os.path.join(get_step2_dir(), "step2_currents.csv")
        output_path = os.path.join(data_dir, "step5_multiplier.csv")

        # 检查输入文件是否存在
        if not os.path.exists(interpolation_path):
            return False, f"文件不存在: {interpolation_path}"
        if not os.path.exists(current_path):
            return False, f"文件不存在: {current_path}"
        if not os.path.exists(step2_currents_path):
            return False, f"文件不存在: {step2_currents_path}"

        # 读取step5_current.csv（使用电流）
        with open(current_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            current_data = list(reader)[0]  # 只取第一行
        usage_currents = [float(x) for x in current_data[:5]]  # 取前5列

        # 读取step2_currents.csv（测试电流）
        with open(step2_currents_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            step2_current_data = list(reader)[0]  # 只取第一行
        test_currents = [float(x) for x in step2_current_data[:5]]  # 取前5列

        # 读取step5_interpolation.csv
        with open(interpolation_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            interpolation_data = list(reader)

        # 初始化倍数列表
        multipliers = [0] * 5

        # 对每个LED进行处理
        for led_index in range(5):
            # 提取该LED的If和Vf数据
            if_col = led_index * 2  # If列索引
            vf_col = led_index * 2 + 1  # Vf列索引

            # 提取非零数据
            x_data = []
            y_data = []

            for row in interpolation_data:
                if len(row) > max(if_col, vf_col):
                    if_val = float(row[if_col])
                    vf_val = float(row[vf_col])
                    if if_val != 0 and vf_val != 0:  # 只取非零数据
                        x_data.append(if_val)
                        y_data.append(vf_val)

            # 检查是否全为0
            if not x_data:
                multipliers[led_index] = 0
                print(f"LED{led_index + 1}: 数据全为0，倍数设为0")
                continue

            # 获取对应的电流值
            x1 = usage_currents[led_index]  # 使用电流
            x2 = test_currents[led_index]  # 测试电流

            # 进行插值运算
            try:
                y1 = linear_interpolation(x_data, y_data, x1)  # 使用电流对应的Vf
                y2 = linear_interpolation(x_data, y_data, x2)  # 测试电流对应的Vf

                # 计算倍数
                if y2 != 0:
                    multiplier = y1 / y2
                    multipliers[led_index] = multiplier
                    print(
                        f"LED{led_index + 1}: 使用电流={x1}, Vf={y1:.6f}; 测试电流={x2}, Vf={y2:.6f}; 倍数={multiplier:.6f}")
                else:
                    multipliers[led_index] = 0
                    print(f"LED{led_index + 1}: 测试电流对应的Vf为0，倍数设为0")

            except Exception as e:
                multipliers[led_index] = 0
                print(f"LED{led_index + 1}: 插值计算失败: {e}")

        # 写入step5_multiplier.csv
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(multipliers)

        return True, f"倍数计算完成，结果已写入: {output_path}"

    except Exception as e:
        return False, f"计算倍数时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step5 插值运算模块 (interpolation_1)")
    print("=" * 50)

    success, message = calculate_multipliers()

    if success:
        print("\n✅ " + message)
        print("\n计算完成！")
    else:
        print("\n❌ " + message)
        print("\n计算失败！")


if __name__ == "__main__":
    main()