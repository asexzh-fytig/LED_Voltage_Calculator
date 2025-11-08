# -*- coding: utf-8 -*-
"""
Step5 数据缩放模块（interpolation_2）
-----------------------------------
功能：
- 读取 step5_multiplier.csv 中的倍数
- 将 step3_bin_process/ 中的原始 bin 数据乘以对应倍数
- 生成插值后的 bin 数据文件
- 如果输入文件为空，则输出文件填充数字0

输入文件：
- step5_multiplier.csv: 1行5列倍数数据
- step3_bin_process/LED{i}_raw_data_bin_{j}.csv: 原始分bin数据

输出文件：
- step5_interpolation/LED{i}_raw_data_bin_{j}_interpolated.csv: 缩放后的分bin数据
"""
import sys
import os
import csv

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)



try:
    from path_manager import get_step5_dir, get_step3_dir  # 添加 get_step3_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")


    # 备用方案
    def get_step5_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step5_dir = os.path.join(current_dir, '..', 'data_files', 'step5_interpolation')
        os.makedirs(step5_dir, exist_ok=True)
        return step5_dir


    # 添加备用方案
    def get_step3_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step3_dir = os.path.join(current_dir, '..', 'data_files', 'step3_bin_process')
        os.makedirs(step3_dir, exist_ok=True)
        return step3_dir




def scale_bin_data():
    """
    缩放所有LED的bin数据
    :return: (成功标志, 消息)
    """
    try:
        step5_dir = get_step5_dir()  # 直接使用导入的函数
        step3_dir = get_step3_dir()

        # 读取倍数文件
        multiplier_path = os.path.join(step5_dir, "step5_multiplier.csv")
        if not os.path.exists(multiplier_path):
            return False, f"倍数文件不存在: {multiplier_path}"

        with open(multiplier_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            multipliers = [float(x) for x in next(reader)]

        print(f"读取到的倍数: {multipliers}")

        # 处理每个LED的4个bin文件
        processed_files = []

        for led_index in range(5):  # LED1~LED5
            multiplier = multipliers[led_index]
            led_name = f"LED{led_index + 1}"

            print(f"\n处理 {led_name}, 倍数: {multiplier}")

            for bin_index in range(1, 5):  # bin_1~bin_4
                # 输入文件路径
                input_filename = f"{led_name}_raw_data_bin_{bin_index}.csv"
                input_path = os.path.join(step3_dir, input_filename)

                # 输出文件路径
                output_filename = f"{led_name}_raw_data_bin_{bin_index}_interpolated.csv"
                output_path = os.path.join(step5_dir, output_filename)

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
                    scaled_data = []
                    for row in data:
                        scaled_row = []
                        for value in row:
                            if value:  # 非空值
                                try:
                                    num_value = float(value)
                                    scaled_value = num_value * multiplier
                                    # 保留足够的精度
                                    scaled_row.append(f"{scaled_value:.10f}".rstrip('0').rstrip('.'))
                                except ValueError:
                                    # 如果无法转换为数字，保持原值
                                    scaled_row.append(value)
                            else:
                                # 空值保持不变
                                scaled_row.append('')
                        scaled_data.append(scaled_row)

                    # 写入输出文件
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(scaled_data)

                    # 详细验证第一个值
                    if data and data[0] and data[0][0]:
                        try:
                            original_first_value = float(data[0][0].strip())
                            scaled_first_value = float(scaled_data[0][0])
                            expected_value = original_first_value * multiplier

                            print(f"  第一个值验证:")
                            print(f"    原始值: {original_first_value}")
                            print(f"    倍数: {multiplier}")
                            print(f"    期望值: {expected_value}")
                            print(f"    实际值: {scaled_first_value}")

                            if abs(scaled_first_value - expected_value) > 1e-10:
                                print(f"  ⚠️ 第一个值未正确缩放!")
                            else:
                                print(f"  ✓ 第一个值正确缩放")
                        except Exception as e:
                            print(f"  验证第一个值时出错: {e}")

                    processed_files.append(output_filename)
                    print(f"  生成: {output_filename} (数据行数: {len(scaled_data)})")

                except Exception as e:
                    print(f"  处理 {input_filename} 时出错: {e}")
                    # 创建包含单个0的文件作为占位
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([0])
                    processed_files.append(output_filename)
                    print(f"  生成错误占位文件: {output_filename} (填充0)")

        return True, f"成功生成 {len(processed_files)} 个插值文件"

    except Exception as e:
        return False, f"缩放bin数据时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step5 数据缩放模块 (interpolation_2)")
    print("=" * 50)

    success, message = scale_bin_data()

    if success:
        print(f"\n✅ {message}")
        print("\n数据缩放完成！")
    else:
        print(f"\n❌ {message}")
        print("\n数据缩放失败！")


if __name__ == "__main__":
    main()