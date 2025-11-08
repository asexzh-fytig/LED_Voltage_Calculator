# -*- coding: utf-8 -*-
"""
Step4 混bin组合生成器（calc_1）
--------------------------------
规则：
1) 分别读取 data_files/step4_mixbin/step4_mixbin_input_LED1~5.csv
2) 每个 CSV 仅检查【前 5 行、前 4 列】：
   - 将空串视为 0，非数字报错
   - “前 4 列全为 0”的行视为无效行
   - 其它行视为候选行
3) 若某个 CSV 在前 5 行里【没有任何候选行】，则用占位行 (0,0,0,0) 代替
4) 对 LED1..LED5 的候选行做【笛卡尔积】，每个组合拼成 20 列（5*4）
5) 输出至 data_files/step4_mixbin/step4_mixbin_combos.csv
   - 无表头，仅数字

可独立运行：python step4_mixbin_calc_1.py
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
import itertools
from typing import List, Tuple


def _step4_dir() -> str:
    """返回 step4_mixbin 目录"""
    return get_step4_dir()

# ---------- 读/筛 ----------
def _read_first5_rows_4cols(csv_path: str) -> List[List[float]]:
    rows: List[List[float]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            first4 = row[:4] + ["0"] * max(0, 4 - len(row))
            parsed: List[float] = []
            for val in first4:
                s = (val or "").strip()
                if s == "":
                    s = "0"
                try:
                    parsed.append(float(s))
                except ValueError:
                    raise ValueError(f"{os.path.basename(csv_path)} 第{i+1}行存在非数字内容: {val!r}")
            rows.append(parsed)
    return rows


def _is_all_zero(first4: List[float]) -> bool:
    return all(x == 0.0 for x in first4)


def _collect_candidates(csv_path: str) -> List[List[float]]:
    raw = _read_first5_rows_4cols(csv_path)
    return [r for r in raw if not _is_all_zero(r)]


def _write_csv(out_path: str, rows: List[List[float]]) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


# ---------- 主逻辑 ----------
def build_mixbin_combos() -> Tuple[str, int]:
    step4_dir = _step4_dir()
    input_files = [
        os.path.join(step4_dir, "step4_mixbin_input_LED1.csv"),
        os.path.join(step4_dir, "step4_mixbin_input_LED2.csv"),
        os.path.join(step4_dir, "step4_mixbin_input_LED3.csv"),
        os.path.join(step4_dir, "step4_mixbin_input_LED4.csv"),
        os.path.join(step4_dir, "step4_mixbin_input_LED5.csv"),
    ]
    for p in input_files:
        if not os.path.exists(p):
            raise FileNotFoundError(f"未找到输入文件：{p}")

    all_candidates: List[List[List[float]]] = []
    for p in input_files:
        cands = _collect_candidates(p)
        # 关键变化：若无候选，用 (0,0,0,0) 作为占位行
        if not cands:
            cands = [[0.0, 0.0, 0.0, 0.0]]
        all_candidates.append(cands)

    out_path = os.path.join(step4_dir, "step4_mixbin_combos.csv")

    # 笛卡尔积生成所有组合（product 的右侧迭代最快）
    combos: List[List[float]] = []
    for tpl in itertools.product(*all_candidates):
        merged: List[float] = []
        for block in tpl:
            merged.extend(block)
        combos.append(merged)

    _write_csv(out_path, combos)
    return out_path, len(combos)


# ---------- 调试入口 ----------
def main():
    try:
        out_path, n_rows = build_mixbin_combos()
        print("=== Step4 混bin组合生成 完成 ===")
        print(f"输出文件：{out_path}")
        print(f"组合数量：{n_rows} 行（无表头、每行20列）")
        print("说明：若某 CSV 无有效行，已按规则用 (0,0,0,0) 占位后参与笛卡尔积。")
    except Exception as e:
        print("生成失败：", e)


if __name__ == "__main__":
    main()
