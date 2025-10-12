"""异步模型测试器"""

import asyncio
import aiohttp
from typing import List, Dict, Tuple, Optional
from llmct.utils.logger import get_logger

logger = get_logger()


class AsyncModelTester:
    """异步模型测试器 - 支持并发测试提升性能"""
    
    # 类级别连接池，跨实例复用
    _session_pool: Dict[str, aiohttp.ClientSession] = {}
    _pool_lock = asyncio.Lock()
    
    def __init__(self, api_key: str, base_url: str, timeout: int = 30, max_concurrent: int = 10):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_key = f"{base_url}_{timeout}"
    
    async def _get_or_create_session(self) -> aiohttp.ClientSession:
        """获取或创建连接池会话（优化：连接池复用）"""
        async with AsyncModelTester._pool_lock:
            if self._session_key not in AsyncModelTester._session_pool:
                # 创建带连接池的session
                connector = aiohttp.TCPConnector(
                    limit=100,              # 总连接数限制
                    limit_per_host=30,      # 单主机连接数限制
                    ttl_dns_cache=300,      # DNS缓存5分钟
                    use_dns_cache=True,
                    enable_cleanup_closed=True
                )
                
                AsyncModelTester._session_pool[self._session_key] = aiohttp.ClientSession(
                    connector=connector,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                )
                logger.debug(f"创建新的连接池: {self._session_key}")
            
            return AsyncModelTester._session_pool[self._session_key]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = await self._get_or_create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口（保持连接池，不关闭）"""
        # 不关闭session，保留连接池供下次使用
        pass
    
    @classmethod
    async def close_all_sessions(cls):
        """关闭所有连接池（程序退出时调用）"""
        async with cls._pool_lock:
            for session in cls._session_pool.values():
                await session.close()
            cls._session_pool.clear()
            logger.debug("所有连接池已关闭")
    
    async def _execute_request(
        self,
        method: str,
        url: str,
        payload: Dict,
        response_processor
    ) -> Tuple[bool, float, str, str]:
        """
        统一的请求执行方法（优化：减少代码重复）
        
        Args:
            method: HTTP方法
            url: 请求URL
            payload: 请求载荷
            response_processor: 响应处理函数
            
        Returns:
            (是否成功, 响应时间, 错误代码, 响应内容)
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.session.request(method, url, json=payload) as response:
                response_time = asyncio.get_event_loop().time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return response_processor(data, response_time)
                else:
                    error_code = f'HTTP_{response.status}'
                    return False, response_time, error_code, ''
        
        except asyncio.TimeoutError:
            return False, self.timeout, 'TIMEOUT', ''
        except aiohttp.ClientError as e:
            logger.debug(f"连接错误: {e}")
            return False, 0, 'REQUEST_FAILED', ''
        except Exception as e:
            logger.debug(f"未知错误: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)
    
    async def test_language_model_async(
        self, 
        model_id: str, 
        message: str = "hello"
    ) -> Tuple[bool, float, str, str]:
        """
        异步测试语言模型
        
        Args:
            model_id: 模型ID
            message: 测试消息
            
        Returns:
            (是否成功, 响应时间, 错误代码, 响应内容)
        """
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        def process_chat_response(data, response_time):
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return True, response_time, '', content.strip()
            else:
                return False, response_time, 'NO_CONTENT', ''
        
        return await self._execute_request('POST', url, payload, process_chat_response)
    
    async def test_vision_model_async(
        self, 
        model_id: str, 
        test_message: str = "What's in this image?",
        image_url: str = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    ) -> Tuple[bool, float, str, str]:
        """异步测试视觉模型"""
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": test_message},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            "max_tokens": 100
        }
        
        def process_vision_response(data, response_time):
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return True, response_time, '', content.strip()
            else:
                return False, response_time, 'NO_CONTENT', ''
        
        return await self._execute_request('POST', url, payload, process_vision_response)
    
    async def test_embedding_model_async(
        self, 
        model_id: str, 
        test_text: str = "hello world"
    ) -> Tuple[bool, float, str, str]:
        """异步测试嵌入模型"""
        url = f"{self.base_url}/v1/embeddings"
        payload = {
            "model": model_id,
            "input": test_text
        }
        
        def process_embedding_response(data, response_time):
            if 'data' in data and len(data['data']) > 0:
                embedding_dim = len(data['data'][0].get('embedding', []))
                return True, response_time, '', f'Embedding维度:{embedding_dim}'
            else:
                return False, response_time, 'NO_DATA', ''
        
        return await self._execute_request('POST', url, payload, process_embedding_response)
    
    async def test_model_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore,
        model: Dict,
        model_type: str,
        test_message: str = "hello"
    ) -> Dict:
        """
        使用信号量限制并发数地测试单个模型
        
        Args:
            semaphore: 信号量控制并发数
            model: 模型信息
            model_type: 模型类型
            test_message: 测试消息
        """
        async with semaphore:
            model_id = model.get('id', model.get('model', 'unknown'))
            
            # 根据模型类型选择测试方法
            if model_type == 'language':
                success, response_time, error_code, content = await self.test_language_model_async(
                    model_id, test_message
                )
            elif model_type == 'vision':
                success, response_time, error_code, content = await self.test_vision_model_async(
                    model_id
                )
            elif model_type == 'embedding':
                success, response_time, error_code, content = await self.test_embedding_model_async(
                    model_id
                )
            else:
                # 其他类型使用语言模型接口
                success, response_time, error_code, content = await self.test_language_model_async(
                    model_id, test_message
                )
            
            return {
                'model': model_id,
                'success': success,
                'response_time': response_time,
                'error_code': error_code,
                'content': content
            }
    
    async def test_models_concurrent(
        self, 
        models: List[Dict], 
        model_types: Dict[str, str],
        test_message: str = "hello",
        progress_callback=None
    ) -> List[Dict]:
        """
        并发测试多个模型
        
        Args:
            models: 模型列表
            model_types: 模型类型映射 {model_id: model_type}
            test_message: 测试消息
            progress_callback: 进度回调函数
            
        Returns:
            测试结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def test_with_progress(model):
            try:
                model_id = model.get('id', model.get('model', 'unknown'))
                model_type = model_types.get(model_id, 'language')
                
                result = await self.test_model_with_semaphore(
                    semaphore, model, model_type, test_message
                )
                
                if progress_callback:
                    progress_callback(result)
                
                return result
            except Exception as e:
                logger.error(f"测试异常: {e}")
                return {
                    'model': model.get('id', 'unknown'),
                    'success': False,
                    'response_time': 0,
                    'error_code': 'EXCEPTION',
                    'content': str(e)
                }
        
        tasks = [test_with_progress(m) for m in models]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return results


def test_models_async(
    api_key: str, 
    base_url: str, 
    models: List[Dict],
    model_types: Dict[str, str],
    max_concurrent: int = 10,
    timeout: int = 30,
    test_message: str = "hello",
    progress_callback=None
) -> List[Dict]:
    """
    同步接口：异步并发测试模型
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        models: 模型列表
        model_types: 模型类型映射
        max_concurrent: 最大并发数
        timeout: 超时时间
        test_message: 测试消息
        progress_callback: 进度回调
    
    Returns:
        测试结果列表
    """
    async def _run():
        async with AsyncModelTester(
            api_key, 
            base_url, 
            timeout, 
            max_concurrent
        ) as tester:
            return await tester.test_models_concurrent(
                models, 
                model_types,
                test_message,
                progress_callback
            )
    
    return asyncio.run(_run())
