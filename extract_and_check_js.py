#!/usr/bin/env python3
"""提取 JavaScript 并检查语法"""

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
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_code)
        temp_file = f.name
    
    try:
        # 使用 node 检查语法
        result = subprocess.run(
            ['node', '--check', temp_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print('✓ JavaScript 语法检查通过')
        else:
            print('✗ JavaScript 语法错误:')
            print(result.stderr)
    except FileNotFoundError:
        print('Node.js 未安装，使用基本检查')
        
        # 基本检查：统计括号
        open_parens = js_code.count('(')
        close_parens = js_code.count(')')
        open_braces = js_code.count('{')
        close_braces = js_code.count('}')
        open_brackets = js_code.count('[')
        close_brackets = js_code.count(']')
        
        print(f'括号: {open_parens} vs {close_parens}')
        print(f'花括号: {open_braces} vs {close_braces}')
        print(f'方括号: {open_brackets} vs {close_brackets}')
        
        if open_parens == close_parens and open_braces == close_braces and open_brackets == close_brackets:
            print('✓ 括号平衡')
        else:
            print('✗ 括号不平衡')
    finally:
        os.unlink(temp_file)
    
    # 检查关键函数是否完整
    print('\n检查关键函数:')
    
    # 检查 sendMessage 函数
    sendmessage_match = re.search(r'async function sendMessage\(\).*?(?=async function|function |</script>|$)', js_code, re.DOTALL)
    if sendmessage_match:
        func_code = sendmessage_match.group(0)
        open_count = func_code.count('{')
        close_count = func_code.count('}')
        if open_count == close_count:
            print('  ✓ sendMessage 函数完整')
        else:
            print(f'  ✗ sendMessage 函数括号不匹配: {open_count} vs {close_count}')
    
    # 检查 startNewChat 函数
    startnewchat_match = re.search(r'async function startNewChat\(\).*?(?=async function|function |</script>|$)', js_code, re.DOTALL)
    if startnewchat_match:
        func_code = startnewchat_match.group(0)
        open_count = func_code.count('{')
        close_count = func_code.count('}')
        if open_count == close_count:
            print('  ✓ startNewChat 函数完整')
        else:
            print(f'  ✗ startNewChat 函数括号不匹配: {open_count} vs {close_count}')
