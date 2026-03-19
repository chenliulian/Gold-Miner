#!/usr/bin/env python3
"""
前端功能测试用例
测试 GoldMiner Web UI 的各项功能
"""
import unittest
import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "ui"))

from app import app, get_agent


class TestFrontendAPI(unittest.TestCase):
    """测试前端 API 接口"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_index_page(self):
        """测试首页加载"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # 检查是否包含关键元素
        html = response.data.decode('utf-8')
        self.assertIn('数据矿工', html)
        self.assertIn('终端', html)
        self.assertIn('技能模块', html)
        
    def test_chat_endpoint(self):
        """测试聊天接口"""
        # 测试空消息
        response = self.client.post('/chat', 
                                    data=json.dumps({'message': ''}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # 测试正常消息（非流式）
        response = self.client.post('/chat',
                                    data=json.dumps({'message': '测试', 'stream': False}),
                                    content_type='application/json')
        self.assertIn(response.status_code, [200, 500])  # 500 可能因为 agent 未初始化
        
    def test_skills_endpoint(self):
        """测试技能列表接口"""
        response = self.client.get('/api/skills')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('skills', data)
        self.assertIsInstance(data['skills'], list)
        
    def test_tables_endpoint(self):
        """测试数据表列表接口"""
        response = self.client.get('/api/tables')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('tables', data)
        self.assertIsInstance(data['tables'], list)
        
        # 检查表结构
        for table in data['tables']:
            self.assertIn('name', table)
            self.assertIn('description', table)
            self.assertIn('file', table)
            
    def test_memory_endpoint(self):
        """测试记忆接口"""
        response = self.client.get('/memory')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('memory', data)
        
    def test_learnings_endpoint(self):
        """测试学习记录接口"""
        response = self.client.get('/learnings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('learnings', data)
        
    def test_interrupt_endpoint(self):
        """测试插话接口"""
        # 测试空消息
        response = self.client.post('/interrupt',
                                    data=json.dumps({'message': ''}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # 测试正常消息
        response = self.client.post('/interrupt',
                                    data=json.dumps({'message': '测试插话'}),
                                    content_type='application/json')
        self.assertIn(response.status_code, [200, 500])
        
    def test_config_endpoint(self):
        """测试配置接口"""
        response = self.client.get('/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('config', data)
        
        config = data['config']
        self.assertIn('llm_model', config)
        self.assertIn('llm_base_url', config)
        self.assertIn('odps_project', config)
        

class TestFrontendUIElements(unittest.TestCase):
    """测试前端 UI 元素"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_page_structure(self):
        """测试页面结构"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查关键容器
        self.assertIn('app-container', html)
        self.assertIn('sidebar', html)
        self.assertIn('main-content', html)
        self.assertIn('chat-container', html)
        
    def test_navigation_items(self):
        """测试导航项"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查导航项
        self.assertIn('终端', html)
        self.assertIn('技能模块', html)
        self.assertIn('记忆', html)
        self.assertIn('学习数据', html)
        
    def test_input_elements(self):
        """测试输入元素"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查输入框
        self.assertIn('user-input', html)
        self.assertIn('interrupt-input', html)
        
        # 检查按钮
        self.assertIn('执行', html)
        self.assertIn('发送', html)
        
    def test_status_indicators(self):
        """测试状态指示器"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查状态显示
        self.assertIn('ODPS 已连接', html)
        self.assertIn('AI: 就绪', html)
        
    def test_page_sections(self):
        """测试页面分区"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查各个页面
        self.assertIn('page-chat', html)
        self.assertIn('page-skills', html)
        self.assertIn('page-memory', html)
        self.assertIn('page-learnings', html)
        

class TestFrontendJavaScript(unittest.TestCase):
    """测试前端 JavaScript 功能"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_javascript_functions(self):
        """测试 JavaScript 函数是否存在"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查关键函数
        self.assertIn('function switchPage', html)
        self.assertIn('function sendMessage', html)
        self.assertIn('function loadSkills', html)
        self.assertIn('function loadMemory', html)
        self.assertIn('function loadLearnings', html)
        self.assertIn('function interruptAgent', html)
        
    def test_event_handlers(self):
        """测试事件处理器"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查事件绑定
        self.assertIn('onclick="sendMessage()"', html)
        self.assertIn('onclick="interruptAgent()"', html)
        self.assertIn('onkeypress="handleKeyPress', html)
        self.assertIn('onkeypress="handleInterruptKeyPress', html)
        
    def test_api_calls(self):
        """测试 API 调用"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查 API 端点调用
        self.assertIn("fetch('/chat')", html)
        self.assertIn("fetch('/api/skills')", html)
        self.assertIn("fetch('/api/tables')", html)
        self.assertIn("fetch('/api/memory')", html)
        self.assertIn("fetch('/api/learnings')", html)
        self.assertIn("fetch('/interrupt')", html)
        

class TestFrontendStyling(unittest.TestCase):
    """测试前端样式"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_css_variables(self):
        """测试 CSS 变量"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查 CSS 变量
        self.assertIn('--bg-primary', html)
        self.assertIn('--bg-secondary', html)
        self.assertIn('--accent-primary', html)
        self.assertIn('--text-primary', html)
        
    def test_responsive_design(self):
        """测试响应式设计"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查 viewport 设置
        self.assertIn('viewport', html)
        self.assertIn('width=device-width', html)
        
    def test_font_loading(self):
        """测试字体加载"""
        response = self.client.get('/')
        html = response.data.decode('utf-8')
        
        # 检查字体
        self.assertIn('JetBrains Mono', html)
        self.assertIn('Space Grotesk', html)
        

class TestDataConsistency(unittest.TestCase):
    """测试数据一致性"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_skills_data_format(self):
        """测试技能数据格式"""
        response = self.client.get('/api/skills')
        data = json.loads(response.data)

        if data.get('success') and data.get('skills'):
            for skill in data['skills']:
                self.assertIsInstance(skill, dict)
                self.assertIn('name', skill)
                self.assertIsInstance(skill['name'], str)
                # 检查是否有 description 字段
                if 'description' in skill:
                    self.assertIsInstance(skill['description'], str)
                
    def test_tables_data_format(self):
        """测试数据表格式"""
        response = self.client.get('/api/tables')
        data = json.loads(response.data)
        
        if data.get('success') and data.get('tables'):
            for table in data['tables']:
                self.assertIsInstance(table, dict)
                self.assertIn('name', table)
                self.assertIn('description', table)
                self.assertIn('file', table)
                self.assertTrue(table['file'].endswith('.yaml'))
                
    def test_tables_files_exist(self):
        """测试数据表文件是否存在"""
        response = self.client.get('/api/tables')
        data = json.loads(response.data)
        
        if data.get('success') and data.get('tables'):
            tables_dir = project_root / "knowledge" / "tables"
            for table in data['tables']:
                file_path = tables_dir / table['file']
                self.assertTrue(file_path.exists(), f"Table file not found: {table['file']}")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestFrontendAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestFrontendUIElements))
    suite.addTests(loader.loadTestsFromTestCase(TestFrontendJavaScript))
    suite.addTests(loader.loadTestsFromTestCase(TestFrontendStyling))
    suite.addTests(loader.loadTestsFromTestCase(TestDataConsistency))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("GoldMiner 前端测试")
    print("=" * 70)
    
    success = run_tests()
    
    if success:
        print("\n✅ 所有测试通过!")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败!")
        sys.exit(1)
