# -*- coding: utf-8 -*-
"""
Step4 混bin“归一化”生成器（calc_3）
--------------------------------
输入：
- data_files/step4_mixbin/step4_mixbin_combos.csv   （多行，20列，数值）

处理：
- 对每一行，按 4 列为一组（共 5 组：1-4，5-8，9-12，13-16，17-20）
- 组内求和 sum_g
  - 若 sum_g > 0：每个值 / sum_g  （该组四个数之和=1）
  - 若 sum_g == 0：该组保持 (0,0,0,0)

输出：
- data_files/step4_mixbin/step4_mixbin_combos_uniformization.csv
  * 无表头，仅数字
  * 行数与 step4_mixbin_combos.csv 相同，20 列

可独立运行：python step4_mixbin_calc_3.py
"""
import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step4_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")
    # 备用方案
    def get_step4_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step4_dir = os.path.join(current_dir, '..', 'data_files', 'step4_mixbin')
        os.makedirs(step4_dir, exist_ok=True)
        return step4_dir
import os
import csv
from typing import List, Tuple

GROUP_SIZE = 4
NUM_GROUPS = 5
TOTAL_COLS = GROUP_SIZE * NUM_GROUPS  # 20


def _step4_dir() -> str:
    """确保并返回 data_files/step4_mixbin/ 目录"""
    return get_step4_dir()


# ---------- I/O ----------
def _read_csv_rows(path: str) -> List[List[str]]:
    rows: List[List[str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    return rows


def _write_csv_rows(path: str, rows: List[List[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# ---------- 工具 ----------
def _to_float(s: str) -> float:
    s = (s or "").strip()
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"发现非数字：{s!r}")


def _fmt(x: float) -> str:
    """
    输出紧凑数值：
    - 四舍五入到 6 位小数
    - 整数不带小数
    """
    if abs(x) < 1e-15:
        x = 0.0
    x = round(x, 6)
    if float(x).is_integer():
        return str(int(x))
    return f"{x:.6f}".rstrip("0").rstrip(".")


# ---------- 主逻辑 ----------
def build_mixbin_percentages() -> Tuple[str, int, int]:
    """
    读取 combos.csv，分组（每 4 列）归一化，写出 uniformization.csv
    返回：(输出路径, 行数, 列数)
    """
    step4_dir = _step4_dir()
    combos_path = os.path.join(step4_dir, "step4_mixbin_combos.csv")
    out_path = os.path.join(step4_dir, "step4_mixbin_combos_uniformization.csv")  # ← 改为统一化文件名

    if not os.path.exists(combos_path):
        raise FileNotFoundError(f"未找到输入：{combos_path}")

    combos_raw = _read_csv_rows(combos_path)
    if not combos_raw:
        _write_csv_rows(out_path, [])
        return out_path, 0, TOTAL_COLS

    out_rows: List[List[str]] = []
    for row in combos_raw:
        # 不足 20 列补 0，超出截断
        vals = [_to_float(c) for c in (row[:TOTAL_COLS] + ["0"] * max(0, TOTAL_COLS - len(row)))]
        # 逐组归一化
        for g in range(NUM_GROUPS):
            beg = g * GROUP_SIZE
            end = beg + GROUP_SIZE
            group = vals[beg:end]
            s = sum(group)
            if s > 0:
                vals[beg:end] = [v / s for v in group]
            else:
                vals[beg:end] = [0.0, 0.0, 0.0, 0.0]
        out_rows.append([_fmt(v) for v in vals])

    _write_csv_rows(out_path, out_rows)
    return out_path, len(out_rows), TOTAL_COLS


# ---------- 调试入口 ----------
def main():
    try:
        out_path, n_rows, n_cols = build_mixbin_percentages()
        print("=== Step4 混bin归一化 生成完成 ===")
        print(f"输出文件：{out_path}")
        print(f"表格尺寸：{n_rows} 行 × {n_cols} 列（无表头；每 4 列为一组归一化）")
    except Exception as e:
        print("生成失败：", e)


if __name__ == "__main__":
    main()
