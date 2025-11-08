# step3_bin_range.py
import os
import csv
import sys
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
    # 备用方案
    def get_step3_dir():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        step3_dir = os.path.join(current_dir, '..', 'data_files', 'step3_bin_process')
        os.makedirs(step3_dir, exist_ok=True)
        return step3_dir


def get_base_directory():
    """
    获取应用程序的基础目录
    在开发环境中是项目根目录，在打包后是exe所在目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境 - 假设脚本在core_functions目录中
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_bin_ranges():
    """
    根据step3_bin_nodes.csv生成step3_bin_ranges_pure.csv
    将相邻的bin节点组合成区间字符串格式(xxx-yyy)，如果有一个节点是0则填充"-"
    """
    try:
        # 使用path_manager获取目录
        data_dir = get_step3_dir()

        input_file = os.path.join(data_dir, "step3_bin_nodes.csv")
        output_file = os.path.join(data_dir, "step3_bin_ranges_pure.csv")

        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"找不到输入文件: {input_file}")

        # 读取step3_bin_nodes.csv
        with open(input_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            nodes_data = list(reader)

        # 处理数据，生成区间字符串
        bin_ranges = []

        # 处理5行数据
        for row_idx, row in enumerate(nodes_data):
            # 确保每行至少有5个数据，不足则用0填充
            while len(row) < 5:
                row.append("0")

            # 将字符串转换为浮点数
            nodes = []
            for node in row[:5]:
                try:
                    nodes.append(float(node))
                except:
                    nodes.append(0.0)

            # 生成4个区间，进行逻辑判断
            for i in range(4):
                # 如果两个数字中有一个是0，则填充"-"
                if nodes[i] == 0 or nodes[i + 1] == 0:
                    range_str = "-"
                else:
                    range_str = f"({nodes[i]}-{nodes[i+1]})"
                bin_ranges.append(range_str)

        # 保存为CSV文件（单行20列）
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(bin_ranges)

        print(f"成功生成bin区间文件: {output_file}")
        print(f"生成的区间: {bin_ranges}")

        return True, bin_ranges

    except Exception as e:
        error_msg = f"生成bin区间时出错: {str(e)}"
        print(error_msg)
        return False, error_msg


if __name__ == "__main__":
    # 测试代码
    success, result = generate_bin_ranges()
    if success:
        print("测试成功！")
    else:
        print(f"测试失败: {result}")