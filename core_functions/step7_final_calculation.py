# -*- coding: utf-8 -*-
"""
Step7 蒙特卡罗计算核心模块（final_calculation）- 无进度条版
----------------------------------------------------------------
优化策略：
1. 一次只处理一个组合，避免同时存储所有组合结果
2. 模拟结果立即写入文件，不存储在内存中
3. 空文件处理：默认为[0]
4. 有放回抽样
5. 使用回调函数更新进度
"""
import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step6_dir, get_step7_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")

import os
import csv
import random
import math
from typing import List, Tuple, Optional, Callable
import sys


def _load_bin_data_memory_efficient(step6_dir: str) -> List[List[float]]:
    """
    内存优化的bin数据加载
    如果文件为空或不存在，返回[0]
    """
    bin_data = []
    led_count = 5
    bin_per_led = 4

    # 定义文件顺序
    file_order = []
    for led_idx in range(1, led_count + 1):
        for bin_idx in range(1, bin_per_led + 1):
            filename = f"LED{led_idx}_raw_data_bin_{bin_idx}_interpolated_loss.csv"
            file_order.append(filename)

    for filename in file_order:
        filepath = os.path.join(step6_dir, filename)

        data_list = []
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        for value in row:
                            if value.strip():  # 非空值
                                try:
                                    data_list.append(float(value.strip()))
                                except ValueError:
                                    # 忽略非数字值
                                    continue
            except Exception as e:
                print(f"警告: 读取文件 {filename} 时出错: {e}")
                data_list = [0.0]  # 出错时默认返回[0]
        else:
            # 文件为空或不存在，默认返回[0]
            data_list = [0.0]

        bin_data.append(data_list)
        print(f"加载 {filename}: {len(data_list)} 个数据点")

    return bin_data


def _sample_from_bin(bin_data: List[float], sample_count: float) -> float:
    """
    从bin数据中有放回抽样并求和
    :param bin_data: bin数据列表（至少包含一个元素，为空时默认为[0]）
    :param sample_count: 抽样次数（可能是小数）
    :return: 抽样结果之和
    """
    if not bin_data:
        return 0.0

    total = 0.0

    # 整数部分抽样
    integer_part = int(sample_count)
    for _ in range(integer_part):
        total += random.choice(bin_data)

    # 小数部分处理
    fractional_part = sample_count - integer_part
    if fractional_part > 1e-10:  # 避免浮点数精度问题
        last_sample = random.choice(bin_data)
        total += last_sample * fractional_part

    return total


def run_monte_carlo_simulation(simulation_count: int,
                               progress_callback: Optional[Callable[[int, int, str], None]] = None,
                               stop_check: Optional[Callable[[], bool]] = None) -> Tuple[bool, str]:
    """
    执行蒙特卡罗模拟 - 无进度条版本，使用回调函数更新进度
    :param simulation_count: 模拟次数
    :param progress_callback: 进度回调函数，参数为(current, total, detail)
    :param stop_check: 停止检查函数，返回True表示需要停止计算
    :return: (成功标志, 消息)
    """
    try:
        step6_dir = get_step6_dir()
        step7_dir = get_step7_dir()

        # 1. 加载混bin组合数据
        combos_file = os.path.join(step6_dir, "Step6_mixbin_combos_uniformization_series.csv")
        if not os.path.exists(combos_file):
            return False, f"混bin组合文件不存在: {combos_file}"

        combos_data = []
        with open(combos_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # 跳过空行
                    try:
                        # 转换为浮点数，处理可能的空值
                        float_row = [float(x) if x.strip() else 0.0 for x in row]
                        combos_data.append(float_row)
                    except ValueError as e:
                        print(f"警告: 跳过无法解析的行: {row}, 错误: {e}")
                        continue

        if not combos_data:
            return False, "混bin组合文件为空或无法解析"

        total_combos = len(combos_data)
        print(f"加载了 {total_combos} 个混bin组合")

        # 更新进度
        if progress_callback:
            progress_callback(0, total_combos, "正在加载bin数据文件...")

        # 2. 加载20个bin数据文件（约160MB内存）
        print("正在加载bin数据文件...")
        bin_data_list = _load_bin_data_memory_efficient(step6_dir)

        if len(bin_data_list) != 20:
            return False, f"bin数据文件数量不正确，期望20个，实际{len(bin_data_list)}个"

        # 3. 逐个组合处理，避免内存累积
        processed_count = 0

        for combo_idx, combo in enumerate(combos_data, 1):
            # 检查是否请求停止
            if stop_check and stop_check():
                return False, "用户请求停止计算"

            combo_detail = f"处理组合 {combo_idx}/{total_combos}, 模拟次数: {simulation_count}"
            print(combo_detail)

            if progress_callback:
                progress_callback(combo_idx, total_combos, combo_detail)

            # 创建输出文件并立即写入结果
            output_file = os.path.join(step7_dir, f"combos_{combo_idx}_Voltage.csv")

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 进行指定次数的模拟，结果立即写入文件
                for sim_idx in range(simulation_count):
                    # 定期检查停止请求（每1000次模拟检查一次）
                    if sim_idx % 1000 == 0 and stop_check and stop_check():
                        return False, "用户请求停止计算"

                    total_voltage = 0.0

                    # 对20个bin依次抽样
                    for bin_idx, sample_count in enumerate(combo[:20]):  # 只处理前20列
                        if bin_idx < len(bin_data_list):
                            bin_contribution = _sample_from_bin(bin_data_list[bin_idx], sample_count)
                            total_voltage += bin_contribution

                    # 立即写入这一轮模拟的结果
                    writer.writerow([total_voltage])

            processed_count += 1
            print(f"  组合 {combo_idx}: 完成 {simulation_count} 次模拟，结果保存到 {output_file}")

        success_message = f"蒙特卡罗模拟完成！共处理 {total_combos} 个组合，每个组合 {simulation_count} 次模拟"
        return True, success_message

    except Exception as e:
        return False, f"蒙特卡罗模拟过程中出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step7 蒙特卡罗计算核心模块 (final_calculation) - 无进度条版")
    print("=" * 50)

    try:
        # 获取用户输入的模拟次数
        if len(sys.argv) > 1:
            simulation_count = int(sys.argv[1])
        else:
            simulation_count = int(input("请输入蒙特卡罗模拟次数: "))

        if simulation_count <= 0:
            print("错误: 模拟次数必须为正整数")
            return

        print(f"开始蒙特卡罗模拟，模拟次数: {simulation_count}")

        # 简单的控制台进度显示
        def console_progress_callback(current, total, detail):
            progress_percent = (current / total) * 100
            print(f"进度: {current}/{total} ({progress_percent:.1f}%) - {detail}")

        success, message = run_monte_carlo_simulation(simulation_count, console_progress_callback)

        if success:
            print(f"\n✅ {message}")
            print("\n蒙特卡罗模拟完成！")
        else:
            print(f"\n❌ {message}")
            print("\n蒙特卡罗模拟失败！")

    except ValueError:
        print("错误: 请输入有效的整数")
    except KeyboardInterrupt:
        print("\n用户中断模拟")
    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()