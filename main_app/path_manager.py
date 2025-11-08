# -*- coding: utf-8 -*-
"""
统一的路径管理模块
确保打包后所有数据文件都保存在exe同一目录下
"""

import os
import sys
from pathlib import Path

def get_base_dir():
    """返回基础目录：如果是打包环境返回exe所在目录，否则返回项目根目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        this_dir = os.path.dirname(os.path.abspath(__file__))
        return _find_project_root(this_dir)

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

def get_data_files_dir():
    """返回data_files目录，确保目录存在"""
    base_dir = get_base_dir()
    data_dir = os.path.join(base_dir, "data_files")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_step_dir(step_name):
    """返回指定步骤的数据目录，确保目录存在"""
    data_dir = get_data_files_dir()
    step_dir = os.path.join(data_dir, step_name)
    os.makedirs(step_dir, exist_ok=True)
    return step_dir

# 各步骤目录的快捷方式
def get_step1_dir():
    """返回step1_rawdata_analysis目录，确保目录存在"""
    return get_step_dir("step1_rawdata_analysis")

def get_step2_dir():
    """返回step2_input_process目录，确保目录存在"""
    return get_step_dir("step2_input_process")

def get_step3_dir():
    """返回step3_bin_process目录，确保目录存在"""
    return get_step_dir("step3_bin_process")

def get_step4_dir():
    """返回step4_mixbin目录，确保目录存在"""
    return get_step_dir("step4_mixbin")

def get_step5_dir():
    """返回step5_interpolation目录，确保目录存在"""
    return get_step_dir("step5_interpolation")

def get_step6_dir():
    """返回step6_parameters目录，确保目录存在"""
    return get_step_dir("step6_parameters")

def get_step7_dir():
    """返回step7_final_calculation目录，确保目录存在"""
    return get_step_dir("step7_final_calculation")

def get_step8_dir():
    """返回step8_summary_output目录，确保目录存在"""
    return get_step_dir("step8_summary_output")

def get_resources_dir():
    """返回resources目录，确保目录存在"""
    base_dir = get_base_dir()
    resources_dir = os.path.join(base_dir, "resources")
    os.makedirs(resources_dir, exist_ok=True)
    return resources_dir

# 新增：获取核心函数目录
def get_core_functions_dir():
    """返回core_functions目录"""
    base_dir = get_base_dir()
    core_dir = os.path.join(base_dir, "core_functions")
    return core_dir

# 新增：获取main_app目录
def get_main_app_dir():
    """返回main_app目录"""
    base_dir = get_base_dir()
    main_app_dir = os.path.join(base_dir, "main_app")
    return main_app_dir