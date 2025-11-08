# core_functions/step3_bin_process.py
# -*- coding: utf-8 -*-
"""
Step 3: 分 bin 区间处理
修复版本：确保在打包环境中路径正确
"""
import sys
import os
import csv
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np


# ========================= 路径管理 =========================
def get_base_directory():
    """获取基础目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)  # 返回项目根目录


def get_step1_dir():
    """返回step1数据目录"""
    base_dir = get_base_directory()
    step1_dir = os.path.join(base_dir, "data_files", "step1_rawdata_analysis")
    os.makedirs(step1_dir, exist_ok=True)
    return step1_dir


def get_step3_dir():
    """返回step3数据目录"""
    base_dir = get_base_directory()
    step3_dir = os.path.join(base_dir, "data_files", "step3_bin_process")
    os.makedirs(step3_dir, exist_ok=True)
    return step3_dir


# 使用统一的路径
RAW_DIR = get_step1_dir()
OUT_DIR = get_step3_dir()
NODES_CSV = os.path.join(OUT_DIR, 'step3_bin_nodes.csv')

LED_COUNT = 5
BIN_COUNT = 4  # (n1,n2], (n2,n3], (n3,n4], (n4,n5]

# 文件命名约定
RAW_FILE_TPL = 'LED{idx}_raw_data.csv'
BIN_FILE_TPL = 'LED{idx}_raw_data_bin_{bin_idx}.csv'


# ========================= 基础工具函数 =========================

def _validate_node_row(node_vals: List[float], row_idx: int) -> None:
    """
    验证单行节点数据的合法性：
    1. 必须是5个节点
    2. 非零部分必须严格递增
    3. 0只能出现在开头或结尾，中间不能有0
    """
    if len(node_vals) != 5:
        raise ValueError(f'第 {row_idx + 1} 行节点数量必须为 5 个，实际为 {len(node_vals)} 个')

    # 找到第一个非零节点和最后一个非零节点的索引
    non_zero_indices = [i for i, v in enumerate(node_vals) if v != 0]

    if not non_zero_indices:
        # 全部为0的情况
        return

    first_non_zero = non_zero_indices[0]
    last_non_zero = non_zero_indices[-1]

    # 检查中间是否有0：从第一个非零到最后一个非零之间不能有0
    for i in range(first_non_zero, last_non_zero + 1):
        if node_vals[i] == 0:
            raise ValueError(f'第 {row_idx + 1} 行节点中间不能有0，当前为：{node_vals}')

    # 检查非零部分是否严格递增
    non_zero_vals = [node_vals[i] for i in non_zero_indices]
    if len(non_zero_vals) > 1 and not all(
            non_zero_vals[j] < non_zero_vals[j + 1] for j in range(len(non_zero_vals) - 1)):
        raise ValueError(f'第 {row_idx + 1} 行非零节点必须严格递增，当前为：{node_vals}')


def _load_nodes(nodes_csv_path: str) -> List[List[float]]:
    """
    读取 step3_bin_nodes.csv，返回每行前五列的浮点数列表。
    """
    # 调试信息
    print(f"尝试读取节点文件: {nodes_csv_path}")
    print(f"文件是否存在: {os.path.exists(nodes_csv_path)}")

    if not os.path.isfile(nodes_csv_path):
        raise FileNotFoundError(f'未找到分段节点文件：{nodes_csv_path}')

    df_nodes = pd.read_csv(nodes_csv_path, header=None)

    # 严格检查：必须是5行5列
    if df_nodes.shape[0] != LED_COUNT or df_nodes.shape[1] < 5:
        raise ValueError(f'分段节点文件格式错误：必须为 {LED_COUNT} 行、且每行至少 5 列。实际形状：{df_nodes.shape}')

    # 确保只取前5列
    df_nodes = df_nodes.iloc[:, :5]

    nodes: List[List[float]] = []
    for i in range(LED_COUNT):
        row_vals = df_nodes.iloc[i, :5].tolist()
        try:
            floats = [float(v) for v in row_vals]
        except Exception:
            raise ValueError(f'第 {i + 1} 行的前五列存在非数值，无法解析：{row_vals}')

        # 验证节点格式
        _validate_node_row(floats, i)
        nodes.append(floats)

    return nodes


def _read_led_raw_df(led_idx: int) -> pd.DataFrame:
    """
    读取单颗 LED 的原始数据 CSV。
    修复：确保正确读取数据，不包含表头
    """
    csv_path = os.path.join(RAW_DIR, RAW_FILE_TPL.format(idx=led_idx))

    # 调试信息
    print(f"尝试读取LED{led_idx}原始数据: {csv_path}")
    print(f"文件是否存在: {os.path.exists(csv_path)}")
    print(f"RAW_DIR: {RAW_DIR}")

    if not os.path.isfile(csv_path):
        # 检查目录中的文件
        if os.path.exists(RAW_DIR):
            print(f"RAW_DIR中的文件: {os.listdir(RAW_DIR)}")
        raise FileNotFoundError(f'未找到原始数据文件：{csv_path}')

    try:
        # 确保没有表头，直接读取数据
        df = pd.read_csv(csv_path, header=None)
        print(f"成功读取LED{led_idx}数据，形状: {df.shape}")
        return df
    except Exception as e:
        print(f"读取原始数据失败：{csv_path}，错误：{e}")
        raise ValueError(f'读取原始数据失败：{csv_path}，错误：{e}')


def _detect_numeric_column(df: pd.DataFrame, target_column: Optional[str] = None) -> int:
    """
    确定用于分 bin 的目标列。
    修复：返回列索引而不是列名
    """
    if df is None or df.shape[1] == 0:
        raise ValueError('原始数据为空或无列，无法进行分 bin。')

    if target_column and target_column in df.columns:
        return df.columns.get_loc(target_column)

    # 自动检测：寻找第一个数值列
    for col_idx in df.columns:
        try:
            s = pd.to_numeric(df[col_idx], errors='coerce')
            if s.notna().any():
                return col_idx
        except:
            continue

    # 如果没有找到数值列，默认使用第一列
    return 0


def _create_empty_bin_files(led_idx: int) -> None:
    """
    预先创建某颗 LED 的 4 个空 bin 文件。
    修复：创建完全空白的文件，不写入任何内容
    """
    for b in range(1, BIN_COUNT + 1):
        out_path = os.path.join(OUT_DIR, BIN_FILE_TPL.format(idx=led_idx, bin_idx=b))
        print(f"创建bin文件: {out_path}")
        # 创建完全空白的文件
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                pass  # 创建空文件
            print(f"文件创建成功: {os.path.exists(out_path)}")
        except Exception as e:
            print(f"创建文件失败: {e}")


def _get_valid_intervals(node_vals: List[float]) -> List[Tuple[int, float, float]]:
    """
    根据节点值获取有效的区间列表。
    返回：[(bin_idx, lower, upper), ...]
    规则：只处理非零且严格递增的区间
    """
    intervals = []

    # 检查所有可能的区间
    for i in range(4):  # 有4个区间
        lower = node_vals[i]
        upper = node_vals[i + 1]

        # 跳过包含0的区间
        if lower == 0 or upper == 0:
            continue

        # 检查区间是否有效（严格递增）
        if lower >= upper:
            continue

        intervals.append((i + 1, lower, upper))

    return intervals


def _cut_into_bins(
        df: pd.DataFrame,
        value_col_idx: int,
        node_vals: List[float],
        led_idx: int
) -> List[pd.DataFrame]:
    """
    将 df 按 value_col 依据节点 [n1,n2,n3,n4,n5] 切分为四个区间。
    修复：使用列索引而不是列名
    """
    if len(node_vals) != 5:
        raise ValueError(f'节点数量应为 5 个，当前：{node_vals}')

    # 获取有效区间
    valid_intervals = _get_valid_intervals(node_vals)

    # 转换为数值类型
    s = pd.to_numeric(df[value_col_idx], errors='coerce')

    print(f"LED{led_idx} 数据范围: {s.min():.6f} ~ {s.max():.6f}")
    print(f"LED{led_idx} 节点值: {node_vals}")
    print(f"LED{led_idx} 有效区间: {valid_intervals}")

    # 初始化4个空的DataFrame
    bin_dfs = [pd.DataFrame() for _ in range(4)]

    # 设置浮点数比较容差
    tolerance = 1e-10

    # 定义容差比较函数
    def is_gt(a, b):
        """大于，考虑容差"""
        return a > b - tolerance

    def is_le(a, b):
        """小于等于，考虑容差"""
        return a <= b + tolerance

    # 对每个有效区间进行处理
    for bin_idx, lower, upper in valid_intervals:
        mask = is_gt(s, lower) & is_le(s, upper)
        bin_dfs[bin_idx - 1] = df[mask].copy()

        # 显示每个有效区间的统计
        if len(bin_dfs[bin_idx - 1]) > 0:
            bin_values = pd.to_numeric(bin_dfs[bin_idx - 1][value_col_idx], errors='coerce')
            print(f"  Bin {bin_idx}: {len(bin_dfs[bin_idx - 1])} 条数据, "
                  f"范围: {bin_values.min():.6f} ~ {bin_values.max():.6f}")
        else:
            print(f"  Bin {bin_idx}: {len(bin_dfs[bin_idx - 1])} 条数据 (空)")

    # 检查是否有数据未被分配
    assigned_mask = pd.Series([False] * len(df))
    for bin_idx, lower, upper in valid_intervals:
        assigned_mask = assigned_mask | (is_gt(s, lower) & is_le(s, upper))

    unassigned_count = len(df) - assigned_mask.sum()
    if unassigned_count > 0:
        print(f"警告：LED{led_idx} 有 {unassigned_count} 条数据未被分配到任何 bin")
        unassigned_data = s[~assigned_mask]
        if len(unassigned_data) > 0:
            print(f"未分配数据范围: {unassigned_data.min():.6f} ~ {unassigned_data.max():.6f}")

    return bin_dfs


# ========================= 对外主函数 =========================

def run_step3_bin_process(target_column: Optional[str] = None) -> Dict[str, Dict[str, int]]:
    """
    执行第 3 步分 bin 处理。
    :param target_column: 可选，指定用于分 bin 的列名；若不传将自动检测首个数值列
    :return: 每颗 LED 在 4 个 bin 的计数统计
    """

    # 调试信息
    print(f"=== Step3 分bin处理开始 ===")
    print(f"RAW_DIR: {RAW_DIR}")
    print(f"OUT_DIR: {OUT_DIR}")
    print(f"NODES_CSV: {NODES_CSV}")

    # 检查目录是否存在
    print(f"RAW_DIR 是否存在: {os.path.exists(RAW_DIR)}")
    print(f"OUT_DIR 是否存在: {os.path.exists(OUT_DIR)}")

    if os.path.exists(RAW_DIR):
        print(f"RAW_DIR 中的文件: {os.listdir(RAW_DIR)}")
    if os.path.exists(OUT_DIR):
        print(f"OUT_DIR 中的文件: {os.listdir(OUT_DIR)}")

    # 1) 读取分段节点
    nodes_rows = _load_nodes(NODES_CSV)
    print(f"读取到节点数据:")
    for i, nodes in enumerate(nodes_rows):
        print(f"  LED{i + 1}: {nodes}")

    summary: Dict[str, Dict[str, int]] = {}

    # 2) 遍历 5 颗 LED
    for led_idx in range(1, LED_COUNT + 1):
        led_key = f'LED{led_idx}'
        print(f"\n=== 处理 {led_key} ===")

        # 2.1 读取原始数据
        df_led = _read_led_raw_df(led_idx)

        if df_led.shape[0] == 0:
            print(f"警告：{led_key} 原始数据为空")
            # 创建空文件
            _create_empty_bin_files(led_idx)
            summary[led_key] = {f'bin_{i}': 0 for i in range(1, BIN_COUNT + 1)}
            continue

        # 2.2 确认用于分 bin 的列索引
        value_col_idx = _detect_numeric_column(df_led, target_column=target_column)
        print(f"使用第 {value_col_idx} 列进行分 bin")

        # 2.3 先创建 4 个空 bin 文件
        _create_empty_bin_files(led_idx)

        # 2.4 切分（第 i 行节点对应 LED i）
        node_vals = nodes_rows[led_idx - 1]
        bin_dfs = _cut_into_bins(df_led, value_col_idx=value_col_idx, node_vals=node_vals, led_idx=led_idx)

        # 2.5 写出 - 修复：只写入纯数据，不包含表头
        counts = {}
        for b_idx, sub_df in enumerate(bin_dfs, start=1):
            out_path = os.path.join(OUT_DIR, BIN_FILE_TPL.format(idx=led_idx, bin_idx=b_idx))
            print(f"写入bin文件: {out_path}, 数据行数: {sub_df.shape[0]}")
            # 只写入数据，不包含表头
            sub_df.to_csv(out_path, index=False, header=False, encoding='utf-8-sig')
            counts[f'bin_{b_idx}'] = int(sub_df.shape[0])

        summary[led_key] = counts

    # 检查最终生成的文件
    print(f"\n=== 最终文件检查 ===")
    if os.path.exists(OUT_DIR):
        bin_files = [f for f in os.listdir(OUT_DIR) if f.endswith('.csv') and 'bin_' in f]
        print(f"生成的bin文件数量: {len(bin_files)}")
        for f in sorted(bin_files):
            file_path = os.path.join(OUT_DIR, f)
            try:
                df = pd.read_csv(file_path, header=None)
                print(f"  {f}: {df.shape[0]} 行数据")
            except:
                print(f"  {f}: 读取失败")

    return summary


# 允许命令行直接运行用于本地快速测试
if __name__ == '__main__':
    try:
        result = run_step3_bin_process(target_column=None)
        # 打印简单摘要
        print('\n=== Step3 切分完成 ===')
        for k, v in result.items():
            print(f"{k}: {v}")
        print(f'输出目录：{OUT_DIR}')
    except Exception as e:
        print(f'[Step3 Error] {e}')
        import traceback

        traceback.print_exc()