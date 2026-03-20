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
        self.assertIn('GoldMiner', html)
        
    def test_chat_endpoint(self):
        """测试聊天接口"""
        # 测试空消息
        response = self.client.post('/chat', 
                                    data=json.dumps({'message': ''}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
    def test_skills_endpoint(self):
        """测试技能列表接口"""
        response = self.client.get('/skills')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('skills', data)
        self.assertIsInstance(data['skills'], list)
        
    def test_memory_endpoint(self):
        """测试记忆接口"""
        response = self.client.get('/memory')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('memory', data)
        
    def test_sessions_endpoint(self):
        """测试会话列表接口"""
        response = self.client.get('/sessions')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('sessions', data)
        
    def test_interrupt_endpoint(self):
        """测试插话接口"""
        # 测试空消息
        response = self.client.post('/interrupt',
                                    data=json.dumps({'message': ''}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # 测试正常消息
        response = self.client.post('/interrupt',
                                    data=json.dumps({'message': '停止'}),
                                    content_type='application/json')
        self.assertIn(response.status_code, [200, 500])


class TestFrontendSessions(unittest.TestCase):
    """测试会话管理功能"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_create_new_session(self):
        """测试创建新会话"""
        response = self.client.post('/sessions/new',
                                    data=json.dumps({'title': '测试会话'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('session_id', data)
        
    def test_list_sessions(self):
        """测试获取会话列表"""
        response = self.client.get('/sessions')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('sessions', data)
        self.assertIsInstance(data['sessions'], list)


class TestFrontendMemory(unittest.TestCase):
    """测试长期记忆功能"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_get_memory(self):
        """测试获取记忆内容"""
        response = self.client.get('/memory')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('memory', data)
        
        # 检查记忆结构
        memory = data['memory']
        self.assertIn('summary', memory)
        self.assertIn('table_schemas', memory)
        self.assertIn('metric_definitions', memory)
        self.assertIn('business_background', memory)
        
    def test_clear_memory(self):
        """测试清空记忆"""
        response = self.client.post('/memory/clear')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        
    def test_save_to_memory(self):
        """测试保存到记忆"""
        # 保存表结构
        response = self.client.post('/memory/save',
                                    data=json.dumps({
                                        'type': 'table',
                                        'table_name': 'test_table',
                                        'columns': ['id', 'name']
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        
        # 保存指标定义
        response = self.client.post('/memory/save',
                                    data=json.dumps({
                                        'type': 'metric',
                                        'metric_name': 'test_metric',
                                        'definition': 'Test definition'
                                    }),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)


class TestFrontendConfig(unittest.TestCase):
    """测试配置接口"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
        
    def test_config_endpoint(self):
        """测试配置接口"""
        response = self.client.get('/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('config', data)


if __name__ == '__main__':
    unittest.main()
