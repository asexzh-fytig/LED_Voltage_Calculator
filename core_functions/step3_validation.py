# core_functions/step3_validation.py
"""
第三步数据验证模块
- 验证生成的CSV文件内容是否符合要求
- 可独立运行测试
"""

import sys
import os

# 添加main_app目录到Python路径，以便导入path_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_dir = os.path.join(current_dir, '..', 'main_app')
sys.path.append(main_app_dir)

try:
    from path_manager import get_step3_dir
except ImportError as e:
    print(f"导入path_manager失败: {e}")
    # 备用方案（虽然你说不考虑，但保留结构）
    def get_step3_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step3_dir = os.path.join(current_dir, '..', 'data_files', 'step3_bin_process')
        os.makedirs(step3_dir, exist_ok=True)
        return step3_dir
import os
import csv


def validate_csv_file(csv_file_path):
    """
    验证CSV文件内容：
    1. 判断是否都为数字格式
    2. 判断非0数字是否都大于0而小于15

    Args:
        csv_file_path: CSV文件路径

    Returns:
        tuple: (is_valid, message)
            - is_valid: bool, 是否验证通过
            - message: str, 验证结果信息
    """
    try:
        if not os.path.exists(csv_file_path):
            return False, f"CSV文件不存在: {csv_file_path}"

        error_messages = []

        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            for row_idx, row in enumerate(reader, 1):
                for col_idx, value in enumerate(row, 1):
                    # 检查是否为数字
                    try:
                        num_value = float(value)
                    except ValueError:
                        error_messages.append(f"第{row_idx}行第{col_idx}列不是数字格式: '{value}'")
                        continue

                    # 检查非0数字的范围
                    if num_value != 0:
                        if num_value <= 0 or num_value >= 15:
                            error_messages.append(f"第{row_idx}行第{col_idx}列的值 {num_value} 不在0-15范围内")

        if error_messages:
            warning_msg = "检测到疑似输入错误，请再检查一下！确认没问题就进入下一步。\n" * 10
            warning_msg += "\n具体错误：\n" + "\n".join(error_messages)
            return False, warning_msg
        else:
            return True, "CSV文件验证通过：所有值都是数字格式，且非0数字都在0-15范围内"

    except Exception as e:
        return False, f"验证过程中发生错误：{e}"


# 独立运行测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("step3_validation.py 独立运行测试")
    print("=" * 50)

    # 测试文件路径 - 这里需要根据实际情况修改
    test_csv_path = os.path.join(get_step3_dir(), "step3_bin_nodes.csv")

    if os.path.exists(test_csv_path):
        print(f"测试文件: {test_csv_path}")
        is_valid, msg = validate_csv_file(test_csv_path)
        print(f"验证结果: {'通过' if is_valid else '不通过'}")
        print(f"消息: {msg}")
    else:
        print(f"测试文件不存在: {test_csv_path}")
        print("请先运行第三步生成CSV文件后再进行测试")

    print("\n测试完成！")