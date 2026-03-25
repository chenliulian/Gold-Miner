#!/usr/bin/env python3
"""检查 JavaScript 语法"""

import re
import subprocess
import tempfile
import os

with open('ui/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 script 内容
scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

if scripts:
    js_code = scripts[0]
    
    # 检查是否有未闭合的代码块
    lines = js_code.split('\n')
    
    # 跟踪括号平衡
    stack = []
    line_num = 0
    
    for line in lines:
        line_num += 1
        # 跳过注释和字符串
        cleaned = re.sub(r'"[^"]*"', '""', line)
        cleaned = re.sub(r"'[^']*'", "''", cleaned)
        cleaned = re.sub(r'`[^`]*`', '``', cleaned)
        cleaned = re.sub(r'//.*', '', cleaned)
        
        for char in cleaned:
            if char in '({[':
                stack.append((char, line_num))
            elif char in ')}]':
                if not stack:
                    print(f'错误: 第 {line_num} 行有未匹配的闭合括号')
                else:
                    last, _ = stack.pop()
                    pairs = {'(': ')', '{': '}', '[': ']'}
                    if pairs.get(last) != char:
                        print(f'错误: 第 {line_num} 行括号不匹配')
    
    if stack:
        print('未闭合的括号:')
        for char, line_num in stack:
            print(f'  - 第 {line_num} 行: {char}')
    else:
        print('✓ 括号平衡检查通过')
    
    # 检查 async/await 使用
    async_funcs = re.findall(r'async\s+function\s+(\w+)', js_code)
    print(f'\n异步函数: {len(async_funcs)} 个')
    for func in async_funcs[:5]:
        print(f'  - {func}')
    
    # 检查是否有 try 没有 catch
    try_blocks = re.findall(r'try\s*\{', js_code)
    catch_blocks = re.findall(r'catch\s*\(', js_code)
    print(f'\ntry 块: {len(try_blocks)} 个, catch 块: {len(catch_blocks)} 个')
    if len(try_blocks) != len(catch_blocks):
        print('  ⚠ try/catch 数量不匹配')
