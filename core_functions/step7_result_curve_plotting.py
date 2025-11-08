# -*- coding: utf-8 -*-
"""
Step7 结果曲线绘制模块（result_curve_plotting）
------------------------------------------------
功能：
1. 读取每个 combos_i_Voltage.csv 的数据
2. 计算每个组合的4σ(99.9937%)最高密度区间的最小值、中位数和最大值
3. 将结果保存到 Step7_combos_Voltage_ranges.csv
4. 为每个组合绘制电压分布曲线图 combos_i_Voltage.jpg
"""
import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step7_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")
    # 备用方案
    def get_step7_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step7_dir = os.path.join(current_dir, '..', 'data_files', 'step7_final_calculation')
        os.makedirs(step7_dir, exist_ok=True)
        return step7_dir
import os
import csv
import numpy as np
import matplotlib

matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Callable
import sys


def calculate_highest_density_interval(data: np.ndarray, alpha: float = 0.000063) -> Tuple[float, float]:
    """
    计算最高密度区间(HDI)
    :param data: 输入数据
    :param alpha: 显著性水平 (1 - 置信水平)，4σ对应 1 - 0.999937 = 0.000063
    :return: (区间下限, 区间上限)
    """
    if len(data) == 0:
        return 0.0, 0.0

    # 对数据进行排序
    sorted_data = np.sort(data)

    # 计算需要包含的数据点数量
    n = len(sorted_data)
    hdi_size = int(np.floor((1 - alpha) * n))

    if hdi_size <= 0:
        return sorted_data[0], sorted_data[-1]

    # 寻找最短的区间
    min_range = float('inf')
    hdi_min = sorted_data[0]
    hdi_max = sorted_data[-1]

    for i in range(n - hdi_size + 1):
        current_range = sorted_data[i + hdi_size - 1] - sorted_data[i]
        if current_range < min_range:
            min_range = current_range
            hdi_min = sorted_data[i]
            hdi_max = sorted_data[i + hdi_size - 1]

    return hdi_min, hdi_max


def calculate_statistics(data: np.ndarray) -> Tuple[float, float, float]:
    """
    计算4σ最高密度区间的最小值、中位数和最大值
    :param data: 输入数据
    :return: (最小值, 中位数, 最大值)
    """
    if len(data) == 0:
        return 0.0, 0.0, 0.0

    # 计算4σ最高密度区间 (99.9937%)
    hdi_min, hdi_max = calculate_highest_density_interval(data, alpha=0.000063)

    # 计算中位数
    median = np.median(data)

    return hdi_min, median, hdi_max


def plot_voltage_distribution(data: np.ndarray, combo_index: int, output_dir: str):
    """
    绘制电压分布曲线图（参考step1样式）
    :param data: 电压数据
    :param combo_index: 组合索引
    :param output_dir: 输出目录
    """
    if len(data) == 0:
        print(f"警告: 组合 {combo_index} 无数据，跳过绘图")
        return

    plt.figure(figsize=(10, 7))  # 增加图形高度以容纳标题

    # 创建直方图数据（类似step1的分类统计）
    hist, bin_edges = np.histogram(data, bins=50, density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # 绘制折线图（参考step1样式）
    plt.plot(bin_centers, hist, linestyle='-', linewidth=2, color='blue', alpha=0.7)
    plt.fill_between(bin_centers, hist, alpha=0.3, color='blue')

    # 计算统计量
    hdi_min, median, hdi_max = calculate_statistics(data)

    # 标记统计点（参考step1样式）
    stats_points = [
        (hdi_min, "Min", 'red'),
        (median, "Median", 'green'),
        (hdi_max, "Max", 'purple')
    ]

    # 找到每个统计点在直方图中的对应位置
    for value, label, color in stats_points:
        # 找到最近的bin中心
        idx = np.argmin(np.abs(bin_centers - value))
        plt.scatter([bin_centers[idx]], [hist[idx]], s=100, color=color,
                    zorder=5, label=label, marker='D')
        plt.annotate(f'{label}\n{value:.4f}V',
                     xy=(bin_centers[idx], hist[idx]),
                     xytext=(10, 10), textcoords='offset points',
                     ha='left', va='bottom', fontsize=10,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # 设置图表属性
    plt.xlabel('Voltage (V)', fontsize=12)
    plt.ylabel('Probability Density', fontsize=12)

    # 调整标题位置，增加顶部边距
    plt.title(f'Combination {combo_index} Voltage Distribution\n'
              f'4σ HDI: [{hdi_min:.4f}V, {hdi_max:.4f}V], Median: {median:.4f}V',
              fontsize=14, fontweight='bold', pad=20)  # 增加pad参数

    plt.grid(True, alpha=0.3)
    plt.legend()

    # 调整布局，为标题留出更多空间
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # 顶部保留5%的空间给标题

    # 保存图片
    output_path = os.path.join(output_dir, f"combos_{combo_index}_Voltage.jpg")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  组合 {combo_index}: 分布图保存到 {output_path}")


def process_combos_voltage_results(progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Tuple[
    bool, str]:
    """
    处理所有组合的电压结果
    :param progress_callback: 进度回调函数
    :return: (成功标志, 消息)
    """
    try:
        step7_dir = get_step7_dir()

        # 查找所有combos电压文件
        voltage_files = []
        for filename in os.listdir(step7_dir):
            if filename.startswith("combos_") and filename.endswith("_Voltage.csv"):
                voltage_files.append(filename)

        voltage_files.sort(key=lambda x: int(x.split('_')[1]))

        if not voltage_files:
            return False, "未找到任何combos电压文件"

        total_combos = len(voltage_files)
        print(f"找到 {total_combos} 个combos电压文件")

        # 更新进度
        if progress_callback:
            progress_callback(0, total_combos, "开始处理电压结果...")

        # 准备输出CSV文件 - 保存到 step7_final_calculation/
        ranges_output_path = os.path.join(step7_dir, "Step7_combos_Voltage_ranges.csv")

        with open(ranges_output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # 写入表头
            writer.writerow(["Combo_Index", "HDI_Min", "Median", "HDI_Max"])

            # 处理每个组合
            for i, filename in enumerate(voltage_files, 1):
                combo_index = int(filename.split('_')[1])
                file_path = os.path.join(step7_dir, filename)

                # 更新进度
                detail = f"处理组合 {combo_index}/{total_combos}"
                print(detail)
                if progress_callback:
                    progress_callback(i, total_combos, detail)

                try:
                    # 读取电压数据
                    voltages = []
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row and row[0].strip():
                                try:
                                    voltages.append(float(row[0].strip()))
                                except ValueError:
                                    continue

                    if not voltages:
                        print(f"警告: 组合 {combo_index} 无有效数据")
                        # 写入默认值
                        writer.writerow([combo_index, 0.0, 0.0, 0.0])
                        continue

                    # 转换为numpy数组
                    voltage_array = np.array(voltages)

                    # 计算统计量
                    hdi_min, median, hdi_max = calculate_statistics(voltage_array)

                    # 写入CSV
                    writer.writerow([combo_index, hdi_min, median, hdi_max])

                    # 绘制分布图 - 保存到 step7_final_calculation/
                    plot_voltage_distribution(voltage_array, combo_index, step7_dir)

                    print(f"  组合 {combo_index}: HDI=[{hdi_min:.4f}, {hdi_max:.4f}], Median={median:.4f}")

                except Exception as e:
                    print(f"处理组合 {combo_index} 时出错: {e}")
                    # 写入错误标记
                    writer.writerow([combo_index, -1.0, -1.0, -1.0])

        success_message = f"成功处理 {total_combos} 个组合的电压结果\n" \
                          f"统计结果: {ranges_output_path}\n" \
                          f"分布图表: {step7_dir}"
        return True, success_message

    except Exception as e:
        return False, f"处理电压结果时出错: {e}"


def main():
    """独立运行的调试入口"""
    print("=" * 50)
    print("Step7 结果曲线绘制模块 (result_curve_plotting)")
    print("=" * 50)

    try:
        # 简单的控制台进度显示
        def console_progress_callback(current, total, detail):
            progress_percent = (current / total) * 100
            print(f"进度: {current}/{total} ({progress_percent:.1f}%) - {detail}")

        success, message = process_combos_voltage_results(console_progress_callback)

        if success:
            print(f"\n✅ {message}")
            print("\n结果曲线绘制完成！")
        else:
            print(f"\n❌ {message}")
            print("\n结果曲线绘制失败！")

    except KeyboardInterrupt:
        print("\n用户中断处理")
    except Exception as e:
        print(f"程序执行出错: {e}")


if __name__ == "__main__":
    main()