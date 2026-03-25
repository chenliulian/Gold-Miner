#!/usr/bin/env python3
"""检查 HTML 文件中的 JavaScript 语法问题"""

import re

with open('ui/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查 script 标签内的内容
scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

print(f'找到 {len(scripts)} 个 script 块')

# 尝试检查常见的 JS 语法问题
issues = []

# 检查是否有未闭合的括号
for i, script in enumerate(scripts):
    open_parens = script.count('(') - script.count(')')
    open_braces = script.count('{') - script.count('}')
    open_brackets = script.count('[') - script.count(']')

    if open_parens != 0:
        issues.append(f'Script {i+1}: 括号不匹配 ({open_parens})')
    if open_braces != 0:
        issues.append(f'Script {i+1}: 花括号不匹配 ({open_braces})')
    if open_brackets != 0:
        issues.append(f'Script {i+1}: 方括号不匹配 ({open_brackets})')

if issues:
    print('发现的问题:')
    for issue in issues:
        print(f'  - {issue}')
else:
    print('括号检查通过')

# 检查关键函数是否存在
key_functions = ['startNewChat', 'sendMessage', 'switchPage', 'fillInputBox', 'escapeHtml']
print('\n关键函数检查:')
for func in key_functions:
    pattern = rf'function\s+{func}\s*\('
    if re.search(pattern, content):
        print(f'  ✓ {func}')
    else:
        print(f'  ✗ {func} (未找到)')

# 检查 onclick 事件
print('\n按钮 onclick 检查:')
buttons = re.findall(r'<button[^>]*onclick="([^"]*)"[^>]*>', content)
for btn in buttons[:10]:
    print(f'  - {btn}')
