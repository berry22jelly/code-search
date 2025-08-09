
import os
import json
import openai
import csv
from tiktoken import get_encoding

# 初始化 OpenAI
openai.api_key = "YOUR_API_KEY"
MODEL = "gpt-4-turbo"

SYS="""你是一个资深 Java 代码分析专家，请严格按以下要求处理 Java 源代码：
1. **角色**：专业代码文档工程师，专注于 Javadoc 规范
2. **任务**：从 Java 文件中提取结构化文档信息
3. **输入**：完整的 Java 源代码文件
4. **输出**：仅返回 JSON 格式的提取结果，无其他内容
5. **处理原则**：
   - 只分析 /** ... */ 格式的文档注释
   - 忽略 // 和 /* ... */ 类型的注释
   - 精确识别代码元素的上下文关系
   - 保持原始文档格式的完整性

"""

TEMPLATE="""请分析以下 Java 文件并提取文档信息：
```java
{file_content}
```
"""

def scan_java_files(root_dir):
    """扫描目录获取 Java 文件列表"""
    java_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root, file))
    return java_files

def read_file(file_path):
    """读取文件内容并计算 token 数"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 计算 token 数 (使用 cl100k_base 编码)
    encoder = get_encoding("cl100k_base")
    token_count = len(encoder.encode(content))
    
    return content, token_count

def extract_doc(content, max_retries=3):
    """使用 OpenAI API 提取文档信息"""
    system_prompt = SYS # 上述系统提示词
    user_prompt = """请分析以下 Java 文件并提取文档信息：
```java
{content}
```
"""   # 上述用户提示词.format(file_content=content)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    for _ in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            print(f"提取失败: {str(e)}")
    return None

def save_to_csv(data, output_file):
    """将提取结果保存为 CSV"""
    fieldnames = [
        'element_type', 'qualified_name', 'signature', 'description',
        'parameters', 'return_desc', 'exceptions', 'authors', 'version',
        'since', 'see_also', 'deprecated', 'deprecation_desc',
        'is_generic', 'generic_params', 'containing_class', 'source_file'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            # 展平 JSON 结构
            row = {
                'source_file': item['metadata']['file_path'],
                'element_type': item['type'],
                'qualified_name': item['qualified_name'],
                'signature': item.get('signature', ''),
                'description': item.get('description', ''),
                'parameters': json.dumps(item.get('parameters', [])),
                'return_desc': item.get('return_desc', ''),
                'exceptions': json.dumps(item.get('exceptions', [])),
                'authors': json.dumps(item.get('authors', [])),
                'version': item.get('version', ''),
                'since': item.get('since', ''),
                'see_also': json.dumps(item.get('see_also', [])),
                'deprecated': str(item.get('deprecated', False)).lower(),
                'deprecation_desc': item.get('deprecation_desc', ''),
                'is_generic': str(item.get('is_generic', False)).lower(),
                'generic_params': json.dumps(item.get('generic_params', [])),
                'containing_class': item.get('containing_class', '')
            }
            writer.writerow(row)

def process_directory(root_dir, output_csv):
    """主处理流程"""
    java_files = scan_java_files(root_dir)
    all_results = []
    
    for file_path in java_files:
        print(f"处理: {file_path}")
        content, token_count = read_file(file_path)
        
        # Token 限制处理 (GPT-4 Turbo 128K 上下文)
        if token_count > 120000:
            print(f"文件过大 ({token_count} tokens)，跳过")
            continue
        
        result = extract_doc(content)
        if result:
            # 添加文件元数据
            result['metadata'] = {
                'file_path': file_path,
                'token_count': token_count
            }
            all_results.append(result)
    
    save_to_csv(all_results, output_csv)
    print(f"完成! 共处理 {len(all_results)} 个文件")

import json

def convert_item(item):
    # 类型标准化映射
    type_mapping = {
        "function": "function",
        "method": "function",
        "class": "class",
        "variable": "variable",
        "attribute": "variable"
    }
    
    # 基础字段映射
    result = {
        "name": item["qualified_name"],
        "type": type_mapping.get(item["element_type"], item["element_type"]),  # 未知类型保留原值
        "doc": item.get("description", "")
    }
    
    # 按类型处理特殊字段
    element_type = item["element_type"]
    if element_type in ("function", "method"):
        # 解析函数参数为元组
        try:
            params = json.loads(item.get("parameters", "[]"))
            result["signature"] = tuple(param["name"] for param in params)
        except (json.JSONDecodeError, KeyError):
            result["signature"] = ()
    
    elif element_type == "class":
        result["bases"] = []   # 无基类信息
        result["members"] = {}  # 无成员信息
    
    elif element_type in ("variable", "attribute"):
        result["annotation"] = ""  # 无类型注解信息
    
    return result

# 使用示例
if __name__ == "__main__":
    process_directory("./path", "javadocs.csv")