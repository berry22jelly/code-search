# -*- coding: utf-8 -*-
# i18n 中文资源表

name = 'zh-cn'

ui = {
    "INDEXING_PANEL":{
    "TITLE_MAIN": "代码索引工具",
    "LABEL_DIR_SETTINGS": "目录设置",
    "LABEL_CODE_DIRECTORY": "代码目录:",
    "BUTTON_BROWSE": "浏览...",
    "LABEL_FILE_FILTER": "文件过滤",
    "LABEL_FILE_EXTENSIONS": "文件扩展名:",
    "DEFAULT_FILE_EXTENSION": "*.py",
    "LABEL_INDEX_OPTIONS": "索引选项",
    "CHECKBOX_INCLUDE_DOCSTRINGS": "包含文档字符串",
    "STATUS_READY": "准备就绪",
    "BUTTON_START_INDEXING": "开始索引",
    "BUTTON_CANCEL": "取消",
    "STATUS_SCANNING_DIRECTORY": "正在扫描目录...",
    "STATUS_PROCESSING_FILE": "正在处理: {filename} ({current}/{total})",
    "STATUS_INDEXING_COMPLETE": "索引完成",
    "STATUS_INDEXING_CANCELED": "索引已取消",
    "STATUS_INDEXING_ERROR": "索引出错",
    "TITLE_ERROR": "错误",
    "MESSAGE_NO_DIRECTORY_SELECTED": "请选择要索引的目录",
    "TITLE_INFO": "提示",
    "MESSAGE_NO_MATCHING_FILES": "没有找到匹配的文件",
    "TITLE_COMPLETE": "完成",
    "MESSAGE_INDEXING_SUCCESS": "成功索引 {count} 个文件",
    "ERROR_PROCESSING_FILE": "处理文件 {file} 时出错: {error}",
    "ERROR_INDEXING_FAILED": "索引过程中出错: {error}"
},
    "SYMBOL_ANALYZER": {
        "LABEL_TARGET_DIRECTORY": "目标目录:",
        "BUTTON_BROWSE": "浏览...",
        "LABEL_FILE_PATTERN": "文件模式:",
        "DEFAULT_FILE_PATTERN": "*.py",
        "BUTTON_ANALYZE_SYMBOLS": "分析符号",
        "TITLE_ERROR": "错误",
        "MESSAGE_NO_DIRECTORY_SELECTED": "请先选择目录",
        "TITLE_ANALYSIS_ERROR": "分析错误",
        "MESSAGE_ANALYSIS_ERROR": "分析过程中发生错误:\n{0}"
    },
    "SEARCH_PANEL": {
            'search': "搜索",
            'text_search': "文本搜索",
            'semantic_search': "语义搜索",
            'name': "名称",
            'type': "类型",
            'location': "位置",
            'documentation': "文档",
            'prompt': "提示",
            'empty_query': "请输入搜索内容",
            'error': "错误",
            'search_error': "搜索失败: {error}",
            'details': {
                'name': "名称",
                'type': "类型",
                'location': "位置",
                'line': "行号",
                'documentation': "\n文档:",
                'no_doc': "无文档字符串",
                'members': "\n成员列表:",
            },
            'messages': {
                'class_members': "{name} ({type})"
            }
        }
}

