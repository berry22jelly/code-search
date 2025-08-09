import os
import re
import fnmatch
import argparse
from pathlib import Path
from typing import List, Union, Optional

def scan_directory(
    root_dir: Union[str, Path],
    glob_pattern: Optional[str] = None,
    regex_pattern: Optional[str] = None
) -> List[str]:
    """
    扫描目录并返回符合条件的文件路径列表
    
    参数:
        root_dir: 要扫描的根目录
        glob_pattern: glob匹配模式 (例如: "*.txt")
        regex_pattern: 正则表达式匹配模式 (例如: ".*\\.txt$")
    
    返回:
        匹配的文件路径列表 (相对于根目录的绝对路径)
    """
    root_path = Path(root_dir).resolve()
    if not root_path.exists() or not root_path.is_dir():
        raise ValueError(f"无效的目录路径: {root_dir}")
    
    # 编译正则表达式（如果提供）
    regex = re.compile(regex_pattern) if regex_pattern else None
    
    matched_files = []
    
    # 递归遍历目录
    for current_path in root_path.rglob("*"):
        if not current_path.is_file():
            continue
        
        # 获取相对路径用于匹配
        rel_path = str(current_path.relative_to(root_path))
        
        # 应用glob过滤
        if glob_pattern:
            # 将glob模式转换为正则表达式，支持跨平台路径分隔符
            glob_re = fnmatch.translate(glob_pattern) #.replace("\\", "/")
            if not re.match(glob_re, rel_path):
                continue
        
        # 应用正则过滤
        if regex and not regex.search(str(current_path)):
            continue
        
        matched_files.append(str(current_path))
    
    return matched_files

def _main():
    
    parser = argparse.ArgumentParser(
        description="目录扫描工具 - 支持glob和正则表达式过滤"
    )
    parser.add_argument("directory", help="要扫描的根目录路径",default=".")
    parser.add_argument("-g", "--glob", help="glob匹配模式 (例如: '*.txt')")
    parser.add_argument("-r", "--regex", help="正则表达式匹配模式 (例如: '.*\\.txt$')")
    parser.add_argument("-o", "--output", help="输出结果到文件")
    
    args = parser.parse_args()
    
    try:
        results = scan_directory(
            args.directory,
            glob_pattern=args.glob,
            regex_pattern=args.regex
        )
        
        # 输出结果
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write("\n".join(results))
            print(f"找到 {len(results)} 个文件，结果已保存到: {args.output}")
        else:
            print(f"找到 {len(results)} 个匹配文件:")
            for file in results:
                print(file)
                
    except Exception as e:
        print(f"错误: {str(e)}")
        exit(1)

if __name__ == "__main__":
    _main()