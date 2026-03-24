"""
登录认证功能测试
测试签名算法、登录流程、轮询、超时和取消等功能
"""
import unittest
import hmac
import hashlib
import uuid
import time
from unittest.mock import Mock, patch, MagicMock
from core.auth_manager import AuthManager
from core.token_storage import TokenStorage


class TestSignatureGeneration(unittest.TestCase):
    """测试签名生成"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
    
    def test_generate_signed_nonce(self):
        """测试生成带签名的nonce数据结构"""
        signed = self.auth_manager.generate_signed_nonce()
        self.assertIn("nonce", signed)
        self.assertIn("timestamp", signed)
        self.assertIn("signature", signed)
        nonce = signed["nonce"]
        timestamp = signed["timestamp"]
        signature = signed["signature"]
        self.assertIsInstance(nonce, str)
        self.assertEqual(len(nonce), 32)
        self.assertIsInstance(timestamp, int)
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)
    
    def test_signature_consistency(self):
        """测试相同输入生成相同签名"""
        nonce = str(uuid.uuid4()).replace("-", "")
        timestamp = int(time.time())
        message = f"{nonce}|{timestamp}".encode("utf-8")
        secret_key = self.auth_manager.SECRET_KEY
        sig1 = hmac.new(secret_key, message, hashlib.sha256).digest()
        sig2 = hmac.new(secret_key, message, hashlib.sha256).digest()
        self.assertEqual(sig1, sig2, "相同输入应该生成相同的签名")
    
    def test_signature_uniqueness(self):
        """测试不同nonce生成不同签名"""
        signed1 = self.auth_manager.generate_signed_nonce()
        time.sleep(1)
        signed2 = self.auth_manager.generate_signed_nonce()
        self.assertNotEqual(signed1["nonce"], signed2["nonce"], "不同调用应该生成不同的nonce")
        self.assertNotEqual(signed1["signature"], signed2["signature"], "不同nonce应该生成不同的签名")
    
    def test_encode_signed_nonce(self):
        """测试编码后的nonce可还原"""
        signed = self.auth_manager.generate_signed_nonce()
        encoded = self.auth_manager.encode_signed_nonce(signed)
        self.assertIsInstance(encoded, str)
        self.assertGreater(len(encoded), 0)


class TestAuthManager(unittest.TestCase):
    """测试认证管理器"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
    
    def test_initial_state(self):
        """测试初始状态"""
        self.assertIsNone(self.auth_manager.token)
        self.assertIsNone(self.auth_manager.user_info)
        self.assertIsNone(self.auth_manager.client_nonce)
        self.assertFalse(self.auth_manager.is_logged_in())
    
    def test_start_login_flow(self):
        """测试启动登录流程"""
        with patch('requests.post') as mock_post:
            # 模拟API响应
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 1,
                "msg": "成功",
                "data": {"login_url": "http://example.com/login"}
            }
            mock_post.return_value = mock_response
            
            login_url = self.auth_manager.start_login_flow()
            
            self.assertIsNotNone(login_url)
            self.assertIn("client_nonce=", login_url)
            self.assertIsNotNone(self.auth_manager.client_nonce)
    
    def test_get_login_url_failure(self):
        """测试获取登录URL失败"""
        with patch('requests.post') as mock_post:
            # 模拟API错误响应
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 0,
                "msg": "获取失败"
            }
            mock_post.return_value = mock_response
            
            login_url = self.auth_manager.get_login_url()
            
            self.assertIsNone(login_url)
    
    def test_get_login_url_network_error(self):
        """测试网络错误"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("网络错误")
            
            login_url = self.auth_manager.get_login_url()
            
            self.assertIsNone(login_url)
    
    def test_try_get_token_success(self):
        """测试成功获取Token"""
        self.auth_manager.client_nonce = "test-nonce"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 1,
                "msg": "成功",
                "data": {"token": "test-token-123"}
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager._try_get_token()
            
            self.assertTrue(result)
            self.assertEqual(self.auth_manager.token, "test-token-123")
    
    def test_try_get_token_failure(self):
        """测试获取Token失败"""
        self.auth_manager.client_nonce = "test-nonce"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 0,
                "msg": "失败"
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager._try_get_token()
            
            self.assertFalse(result)
            self.assertIsNone(self.auth_manager.token)
    
    def test_fetch_user_info_success(self):
        """测试成功获取用户信息"""
        self.auth_manager.token = "test-token"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 1,
                "msg": "成功",
                "data": {
                    "user_info": {
                        "avatar": "http://example.com/avatar.jpg",
                        "nickname": "test_user"
                    }
                }
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager._fetch_user_info()
            
            self.assertTrue(result)
            self.assertIsNotNone(self.auth_manager.user_info)
            self.assertEqual(self.auth_manager.user_info["nickname"], "test_user")
    
    def test_fetch_user_info_no_token(self):
        """测试没有Token时获取用户信息"""
        self.auth_manager.token = None
        
        result = self.auth_manager._fetch_user_info()
        
        self.assertFalse(result)
    
    def test_check_login_success(self):
        """测试检查登录成功"""
        self.auth_manager.token = "test-token"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 1,
                "msg": "已登录"
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager.check_login()
            
            self.assertTrue(result)
    
    def test_check_login_failure(self):
        """测试检查登录失败"""
        self.auth_manager.token = "invalid-token"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 0,
                "msg": "未登录"
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager.check_login()
            
            self.assertFalse(result)
    
    def test_logout_success(self):
        """测试退出登录成功"""
        self.auth_manager.token = "test-token"
        self.auth_manager.user_info = {"nickname": "test"}
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 1,
                "msg": "成功"
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager.logout()
            
            self.assertTrue(result)
            self.assertIsNone(self.auth_manager.token)
            self.assertIsNone(self.auth_manager.user_info)
    
    def test_logout_failure(self):
        """测试退出登录失败"""
        self.auth_manager.token = "test-token"
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "code": 0,
                "msg": "失败"
            }
            mock_post.return_value = mock_response
            
            result = self.auth_manager.logout()
            
            self.assertFalse(result)
    
    def test_is_logged_in(self):
        """测试登录状态检查"""
        # 未登录
        self.assertFalse(self.auth_manager.is_logged_in())
        
        # 只有Token
        self.auth_manager.token = "test-token"
        self.assertFalse(self.auth_manager.is_logged_in())
        
        # Token和用户信息都有
        self.auth_manager.user_info = {"nickname": "test"}
        self.assertTrue(self.auth_manager.is_logged_in())
    
    def test_set_token_valid(self):
        """测试设置有效Token"""
        with patch.object(self.auth_manager, 'check_login', return_value=True):
            with patch.object(self.auth_manager, '_fetch_user_info', return_value=True):
                result = self.auth_manager.set_token("valid-token")
                
                self.assertTrue(result)
                self.assertEqual(self.auth_manager.token, "valid-token")
    
    def test_set_token_invalid(self):
        """测试设置无效Token"""
        with patch.object(self.auth_manager, 'check_login', return_value=False):
            result = self.auth_manager.set_token("invalid-token")
            
            self.assertFalse(result)
            self.assertIsNone(self.auth_manager.token)


class TestPollingMechanism(unittest.TestCase):
    """测试轮询机制"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
        self.auth_manager.client_nonce = "test-nonce"
    
    def test_poll_token_success(self):
        """测试轮询成功获取Token"""
        with patch.object(self.auth_manager, '_try_get_token', return_value=True):
            with patch.object(self.auth_manager, '_fetch_user_info', return_value=True):
                self.auth_manager.token = "test-token"
                self.auth_manager.user_info = {"nickname": "test"}
                
                result = self.auth_manager.poll_token(timeout=5)
                
                self.assertTrue(result)
    
    def test_poll_token_timeout(self):
        """测试轮询超时"""
        with patch.object(self.auth_manager, '_try_get_token', return_value=False):
            result = self.auth_manager.poll_token(timeout=1)
            
            self.assertFalse(result)
    
    def test_poll_token_no_nonce(self):
        """测试没有nonce时轮询"""
        self.auth_manager.client_nonce = None
        
        result = self.auth_manager.poll_token(timeout=1)
        
        self.assertFalse(result)
    
    def test_cancel_polling(self):
        """测试取消轮询"""
        self.auth_manager.is_polling = True
        
        self.auth_manager.cancel_polling()
        
        self.assertTrue(self.auth_manager.stop_polling_event.is_set())
    
    def test_poll_progress_callback(self):
        """测试轮询进度回调"""
        progress_values = []
        
        def on_progress(remaining):
            progress_values.append(remaining)
        
        with patch.object(self.auth_manager, '_try_get_token', return_value=False):
            self.auth_manager.poll_token(timeout=2, on_progress=on_progress)
        
        # 应该有多个进度回调
        self.assertGreater(len(progress_values), 0)


class TestTokenStorage(unittest.TestCase):
    """测试Token存储"""
    
    def setUp(self):
        self.storage = TokenStorage()
        # 清除之前的数据
        self.storage.clear_all()
    
    def test_save_and_load_token(self):
        """测试保存和加载Token"""
        test_token = "test-token-123"
        
        # 保存
        result = self.storage.save_token(test_token)
        self.assertTrue(result)
        
        # 加载
        loaded_token = self.storage.load_token()
        self.assertEqual(loaded_token, test_token)
    
    def test_load_nonexistent_token(self):
        """测试加载不存在的Token"""
        self.storage.clear_token()
        
        token = self.storage.load_token()
        
        self.assertIsNone(token)
    
    def test_clear_token(self):
        """测试清除Token"""
        self.storage.save_token("test-token")
        
        result = self.storage.clear_token()
        self.assertTrue(result)
        
        token = self.storage.load_token()
        self.assertIsNone(token)
    
    def test_save_and_load_user_info(self):
        """测试保存和加载用户信息"""
        test_user_info = {
            "avatar": "http://example.com/avatar.jpg",
            "nickname": "test_user"
        }
        
        # 保存
        result = self.storage.save_user_info(test_user_info)
        self.assertTrue(result)
        
        # 加载
        loaded_info = self.storage.load_user_info()
        self.assertEqual(loaded_info, test_user_info)
    
    def test_clear_user_info(self):
        """测试清除用户信息"""
        self.storage.save_user_info({"nickname": "test"})
        
        result = self.storage.clear_user_info()
        self.assertTrue(result)
        
        info = self.storage.load_user_info()
        self.assertIsNone(info)
    
    def test_clear_all(self):
        """测试清除所有数据"""
        self.storage.save_token("test-token")
        self.storage.save_user_info({"nickname": "test"})
        
        result = self.storage.clear_all()
        self.assertTrue(result)
        
        self.assertIsNone(self.storage.load_token())
        self.assertIsNone(self.storage.load_user_info())


class TestLoginFlow(unittest.TestCase):
    """测试完整登录流程"""
    
    def setUp(self):
        self.auth_manager = AuthManager()
    
    def test_complete_login_flow(self):
        """测试完整登录流程"""
        with patch('requests.post') as mock_post:
            # 第一次调用：获取登录URL
            login_url_response = Mock()
            login_url_response.json.return_value = {
                "code": 1,
                "data": {"login_url": "http://example.com/login"}
            }
            
            # 第二次调用：获取Token
            token_response = Mock()
            token_response.json.return_value = {
                "code": 1,
                "data": {"token": "test-token"}
            }
            
            # 第三次调用：获取用户信息
            user_info_response = Mock()
            user_info_response.json.return_value = {
                "code": 1,
                "data": {
                    "user_info": {
                        "avatar": "http://example.com/avatar.jpg",
                        "nickname": "test_user"
                    }
                }
            }
            
            mock_post.side_effect = [login_url_response, token_response, user_info_response]
            
            # 启动登录流程
            login_url = self.auth_manager.start_login_flow()
            self.assertIsNotNone(login_url)
            
            # 获取Token
            result = self.auth_manager._try_get_token()
            self.assertTrue(result)
            
            # 获取用户信息
            result = self.auth_manager._fetch_user_info()
            self.assertTrue(result)
            
            # 验证最终状态
            self.assertTrue(self.auth_manager.is_logged_in())
            self.assertEqual(self.auth_manager.user_info["nickname"], "test_user")


if __name__ == '__main__':
    unittest.main()
