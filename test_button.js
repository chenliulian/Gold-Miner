// 测试按钮点击的简单脚本
const http = require('http');

// 获取页面内容
http.get('http://127.0.0.1:5001/', (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
        // 检查关键元素
        const checks = [
            { name: 'startNewChat 函数', pattern: /async function startNewChat\(\)/ },
            { name: '新对话按钮', pattern: /class="new-chat-btn".*onclick="startNewChat\(\)"/ },
            { name: 'sendMessage 函数', pattern: /async function sendMessage\(\)/ },
            { name: 'fillInputBox 函数', pattern: /function fillInputBox\(message\)/ },
            { name: 'escapeHtml 函数', pattern: /function escapeHtml\(text\)/ },
            { name: 'switchPage 函数', pattern: /function switchPage\(page, element\)/ },
        ];
        
        console.log('页面元素检查:\n');
        checks.forEach(check => {
            if (check.pattern.test(data)) {
                console.log(`  ✓ ${check.name}`);
            } else {
                console.log(`  ✗ ${check.name} - 未找到`);
            }
        });
        
        // 检查 script 标签数量
        const scriptMatches = data.match(/<script>/g);
        console.log(`\nScript 标签数量: ${scriptMatches ? scriptMatches.length : 0}`);
        
        // 检查是否有语法错误提示
        if (data.includes('Uncaught SyntaxError')) {
            console.log('\n⚠ 页面包含 JavaScript 语法错误');
        } else {
            console.log('\n✓ 未检测到 JavaScript 语法错误标记');
        }
        
        // 检查按钮是否在正确的位置
        const buttonMatch = data.match(/<button class="new-chat-btn"[^>]*>[\s\S]*?<\/button>/);
        if (buttonMatch) {
            console.log('\n按钮 HTML:');
            console.log(buttonMatch[0].substring(0, 200));
        }
    });
}).on('error', (err) => {
    console.error('请求失败:', err.message);
});
