# -*- coding: utf-8 -*-
"""
Step4 混bin字符串表格生成器（calc_2）
-----------------------------------
输入：
- data_files/step4_mixbin/step4_mixbin_combos.csv  （多行，20列，数值，来自 calc_1）
- data_files/step4_mixbin/step3_bin_ranges_pure.csv（1行，20列，字符串）

规则：
- 对 combos 的第 i 行第 j 列：
    若值 == 0       -> 输出 "0"
    若值 != 0       -> 输出 "<ranges[j]> <值>"   （中间用一个空格）
- 输出与 combos 同维度到：
    data_files/step4_mixbin/step4_mixbin_combos_text.csv
- 无表头

可独立运行：python step4_mixbin_calc_2.py
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
from path_manager import get_step3_dir


def _step4_dir() -> str:
    """返回 step4_mixbin 目录"""
    return get_step4_dir()


# ---------- I/O 工具 ----------
def _read_csv_rows(path: str, max_rows: int = None) -> List[List[str]]:
    rows: List[List[str]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if max_rows is not None and (i + 1) >= max_rows:
                break
    return rows


def _write_csv_rows(path: str, rows: List[List[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# ---------- 辅助 ----------
def _to_float_or_zero(s: str) -> float:
    # 空串也视为 0
    s = (s or "").strip()
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        # 如果 combos 中出现非数字，抛出错误更安全
        raise ValueError(f"组合表中存在非数字：{s!r}")


def _fmt_number_compact(x: float) -> str:
    # 让整数显示为不带小数的形式，其他按紧凑格式
    if float(x).is_integer():
        return str(int(x))
    # 使用通用格式，避免科学计数法太长
    return f"{x:g}"


# ---------- 主逻辑 ----------
def build_mixbin_combos_text() -> Tuple[str, int, int]:
    """
    组合文本表格并写出文件。
    返回：(输出路径, 行数, 列数)
    """
    step4_dir = _step4_dir()
    combos_path = os.path.join(step4_dir, "step4_mixbin_combos.csv")
    ranges_path = os.path.join(get_step3_dir(), "step3_bin_ranges_pure.csv")
    out_path = os.path.join(step4_dir, "step4_mixbin_combos_text.csv")

    if not os.path.exists(combos_path):
        raise FileNotFoundError(f"未找到输入：{combos_path}")
    if not os.path.exists(ranges_path):
        raise FileNotFoundError(f"未找到输入：{ranges_path}")

    # 读 ranges：只取第一行
    ranges_rows = _read_csv_rows(ranges_path, max_rows=1)
    if not ranges_rows or not ranges_rows[0]:
        raise ValueError("step3_bin_ranges_pure.csv 第一行为空。")
    ranges = [ (c or "").strip() for c in ranges_rows[0] ]

    # 读 combos：全部
    combos_raw = _read_csv_rows(combos_path)
    if not combos_raw:
        # 空输入 -> 输出空文件
        _write_csv_rows(out_path, [])
        return out_path, 0, len(ranges)

    num_cols_expected = len(ranges)
    out_rows: List[List[str]] = []

    for r_idx, row in enumerate(combos_raw):
        # 容错：若 combos 的列数与 ranges 不等，按 ranges 列数截断/补齐
        row_vals = list(row[:num_cols_expected]) + ["0"] * max(0, num_cols_expected - len(row))
        out_row: List[str] = []
        for j in range(num_cols_expected):
            v = _to_float_or_zero(row_vals[j])
            if v == 0.0:
                out_row.append("0")  # 明确写入字符 0
            else:
                out_row.append(f"{ranges[j]} { _fmt_number_compact(v) }")
        out_rows.append(out_row)

    _write_csv_rows(out_path, out_rows)
    return out_path, len(out_rows), num_cols_expected


# ---------- 调试入口 ----------
def main():
    try:
        out_path, n_rows, n_cols = build_mixbin_combos_text()
        print("=== Step4 混bin字符串表格 生成完成 ===")
        print(f"输出文件：{out_path}")
        print(f"表格尺寸：{n_rows} 行 × {n_cols} 列（无表头）")
        print("规则：0 -> 写入 '0'；非零 -> '<区间字符串> <数值>'。区间来自 step3_bin_ranges_pure.csv 第一行。")
    except Exception as e:
        print("生成失败：", e)


if __name__ == "__main__":
    main()
