# -*- coding: utf-8 -*-
"""
Step6 原始数据热损处理模块（raw_data_process）
--------------------------------------------
功能：
- 读取 step6_thermal_loss.csv 中的5个热损值
- 将 step5_interpolation/ 中的插值bin数据乘以对应LED的热损值
- 生成热损处理后的bin数据文件
- 如果输入文件为空，则输出文件填充数字0

输入文件：
- step6_thermal_loss.csv: 1行5列热损数据
- step5_interpolation/LED{i}_raw_data_bin_{j}_interpolated.csv: 插值后的分bin数据

输出文件：
- step6_parameters/LED{i}_raw_data_bin_{j}_interpolated_loss.csv: 热损处理后的分bin数据
"""

import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step5_dir, get_step6_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")


    # 备用方案
    def get_step5_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step5_dir = os.path.join(current_dir, '..', 'data_files', 'step5_interpolation')
        os.makedirs(step5_dir, exist_ok=True)
        return step5_dir


    def get_step6_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step6_dir = os.path.join(current_dir, '..', 'data_files', 'step6_parameters')
        os.makedirs(step6_dir, exist_ok=True)
        return step6_dir
import os
import csv
import sys


def _step6_parameters_dir() -> str:
    """确保并返回 data_files/step6_parameters/ 目录"""
    return get_step6_dir()

def _step5_interpolation_dir() -> str:
    """返回 data_files/step5_interpolation/ 目录"""
    return get_step5_dir()


def process_raw_data_with_thermal_loss():
    """
    处理所有LED的bin数据，乘以热损值
    :return: (成功标志, 消息)
    """
    try:
        step6_dir = _step6_parameters_dir()
        step5_dir = _step5_interpolation_dir()

        # 读取热损文件
        thermal_loss_path = os.path.join(step6_dir, "step6_thermal_loss.csv")
        if not os.path.exists(thermal_loss_path):
            return False, f"热损文件不存在: {thermal_loss_path}"

        with open(thermal_loss_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            thermal_losses = [float(x) for x in next(reader)]

        print(f"读取到的热损值: {thermal_losses}")

        # 处理每个LED的4个bin文件
        processed_files = []

        for led_index in range(5):  # LED1~LED5
            thermal_loss = thermal_losses[led_index]
            led_name = f"LED{led_index + 1}"

            print(f"\n处理 {led_name}, 热损值: {thermal_loss}")

            for bin_index in range(1, 5):  # bin_1~bin_4
                # 输入文件路径
                input_filename = f"{led_name}_raw_data_bin_{bin_index}_interpolated.csv"
                input_path = os.path.join(step5_dir, input_filename)

                # 输出文件路径
                output_filename = f"{led_name}_raw_data_bin_{bin_index}_interpolated_loss.csv"
                output_path = os.path.join(step6_dir, output_filename)

                # 检查输入文件是否存在或为空
                if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
                    print(f"警告: 输入文件不存在或为空: {input_path}")
                    # 创建包含单个0的文件
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([0])
                    processed_files.append(output_filename)
                    print(f"  生成空文件占位: {output_filename} (填充0)")
                    continue

                # 读取和处理输入文件
                try:
                    # 保持原始顺序读取
                    with open(input_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()

                    data = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            # 保持原始行的字段顺序
                            row = []
                            for field in line.split(','):
                                field = field.strip()
                                if field:
                                    row.append(field)
                            if row:  # 只添加非空行
                                data.append(row)

                    # 处理数据 - 保持原始行顺序
                    processed_data = []
                    for row in data:
                        processed_row = []
                        for value in row:
                            if value:  # 非空值
                                try:
                                    num_value = float(value)
                                    processed_value = num_value * thermal_loss
                                    # 保留足够的精度
                                    processed_row.append(f"{processed_value:.10f}".rstrip('0').rstrip('.'))
                                except ValueError:
                                    # 如果无法转换为数字，保持原值
                                    processed_row.append(value)
                            else:
                                # 空值保持不变
                                processed_row.append('')
                        processed_data.append(processed_row)

                    # 写入输出文件
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(processed_data)

                    # 详细验证第一个值
                    if data and data[0] and data[0][0]:
                        try:
                            original_first_value = float(data[0][0].strip())
                            processed_first_value = float(processed_data[0][0])
                            expected_value = original_first_value * thermal_loss

                            print(f"  第一个值验证:")
                            print(f"    原始值: {original_first_value}")
                            print(f"    热损值: {thermal_loss}")
                            print(f"    期望值: {expected_value}")
                            print(f"    实际值: {processed_first_value}")

                            if abs(processed_first_value - expected_value) > 1e-10:
                                print(f"  ⚠️ 第一个值未正确乘以热损值!")
                            else:
                                print(f"  ✓ 第一个值正确乘以热损值")
                        except Exception as e:
                            print(f"  验证第一个值时出错: {e}")

                    processed_files.append(output_filename)
                    print(f"  生成: {output_filename} (数据行数: {len(processed_data)})")

                except Exception as e:
                    print(f"  处理 {input_filename} 时出错: {e}")
                    # 创建包含单个0的文件作为占位
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([0])
                    processed_files.append(output_filename)
                    print(f"  生成错误占位文件: {output_filename} (填充0)")

        return True, f"成功生成 {len(processed_files)} 个热损处理文件"

    except Exception as e:
        return False, f"热损处理时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step6 原始数据热损处理模块 (raw_data_process)")
    print("=" * 50)

    success, message = process_raw_data_with_thermal_loss()

    if success:
        print(f"\n✅ {message}")
        print("\n热损处理完成！")
    else:
        print(f"\n❌ {message}")
        print("\n热损处理失败！")


if __name__ == "__main__":
    main()