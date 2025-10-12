"""测试异步模型测试器"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from llmct.core.async_tester import AsyncModelTester, test_models_async


@pytest.fixture
def mock_api_key():
    return "test-api-key"


@pytest.fixture
def mock_base_url():
    return "https://api.test.com"


@pytest.mark.asyncio
async def test_tester_initialization(mock_api_key, mock_base_url):
    """测试测试器初始化"""
    async with AsyncModelTester(mock_api_key, mock_base_url, timeout=30, max_concurrent=10) as tester:
        assert tester.api_key == mock_api_key
        assert tester.base_url == mock_base_url
        assert tester.timeout == 30
        assert tester.max_concurrent == 10


@pytest.mark.asyncio
async def test_connection_pool_reuse(mock_api_key, mock_base_url):
    """测试连接池复用"""
    # 清空连接池
    AsyncModelTester._session_pool.clear()
    
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester1:
        session_key = tester1._session_key
        assert session_key in AsyncModelTester._session_pool
        
        async with AsyncModelTester(mock_api_key, mock_base_url) as tester2:
            # 应该复用同一个session
            assert tester2._session_key == session_key
            assert tester1.session is tester2.session


@pytest.mark.asyncio
async def test_language_model_success(mock_api_key, mock_base_url):
    """测试语言模型成功响应"""
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        # Mock session request
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [
                {'message': {'content': 'Hello! How can I help you?'}}
            ]
        })
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            success, response_time, error_code, content = await tester.test_language_model_async('gpt-4')
            
            assert success is True
            assert response_time > 0
            assert error_code == ''
            assert content == 'Hello! How can I help you?'


@pytest.mark.asyncio
async def test_language_model_http_error(mock_api_key, mock_base_url):
    """测试HTTP错误响应"""
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        mock_response = AsyncMock()
        mock_response.status = 403
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            success, response_time, error_code, content = await tester.test_language_model_async('gpt-4')
            
            assert success is False
            assert error_code == 'HTTP_403'


@pytest.mark.asyncio
async def test_language_model_timeout(mock_api_key, mock_base_url):
    """测试超时"""
    async with AsyncModelTester(mock_api_key, mock_base_url, timeout=1) as tester:
        async def slow_request(*args, **kwargs):
            await asyncio.sleep(2)
            raise asyncio.TimeoutError()
        
        with patch.object(tester.session, 'request', side_effect=slow_request):
            success, response_time, error_code, content = await tester.test_language_model_async('gpt-4')
            
            assert success is False
            assert error_code == 'TIMEOUT'


@pytest.mark.asyncio
async def test_vision_model(mock_api_key, mock_base_url):
    """测试视觉模型"""
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [
                {'message': {'content': 'This is a beautiful landscape'}}
            ]
        })
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            success, response_time, error_code, content = await tester.test_vision_model_async('gpt-4-vision')
            
            assert success is True
            assert 'landscape' in content.lower()


@pytest.mark.asyncio
async def test_embedding_model(mock_api_key, mock_base_url):
    """测试嵌入模型"""
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'embedding': [0.1] * 1536}
            ]
        })
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            success, response_time, error_code, content = await tester.test_embedding_model_async('text-embedding-ada-002')
            
            assert success is True
            assert '1536' in content


@pytest.mark.asyncio
async def test_concurrent_models(mock_api_key, mock_base_url):
    """测试并发测试多个模型"""
    models = [
        {'id': 'gpt-4', 'model': 'gpt-4'},
        {'id': 'gpt-3.5-turbo', 'model': 'gpt-3.5-turbo'},
        {'id': 'claude-3', 'model': 'claude-3'}
    ]
    
    model_types = {
        'gpt-4': 'language',
        'gpt-3.5-turbo': 'language',
        'claude-3': 'language'
    }
    
    async with AsyncModelTester(mock_api_key, mock_base_url, max_concurrent=2) as tester:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{'message': {'content': 'Test response'}}]
        })
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            results = await tester.test_models_concurrent(models, model_types)
            
            assert len(results) == 3
            assert all(r['success'] for r in results)
            assert all('model' in r for r in results)


@pytest.mark.asyncio
async def test_semaphore_limit(mock_api_key, mock_base_url):
    """测试信号量限制并发"""
    concurrent_count = []
    max_concurrent = 0
    
    async def mock_request(*args, **kwargs):
        concurrent_count.append(1)
        nonlocal max_concurrent
        max_concurrent = max(max_concurrent, len(concurrent_count))
        await asyncio.sleep(0.1)
        concurrent_count.pop()
        
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            'choices': [{'message': {'content': 'Test'}}]
        })
        return response
    
    models = [{'id': f'model-{i}', 'model': f'model-{i}'} for i in range(20)]
    model_types = {f'model-{i}': 'language' for i in range(20)}
    
    async with AsyncModelTester(mock_api_key, mock_base_url, max_concurrent=5) as tester:
        with patch.object(tester.session, 'request', side_effect=mock_request):
            results = await tester.test_models_concurrent(models, model_types)
            
            assert len(results) == 20
            # 最大并发数不应超过限制
            assert max_concurrent <= 5


def test_sync_interface(mock_api_key, mock_base_url):
    """测试同步接口"""
    models = [
        {'id': 'gpt-4', 'model': 'gpt-4'}
    ]
    
    model_types = {'gpt-4': 'language'}
    
    # Mock async 函数
    with patch('llmct.core.async_tester.AsyncModelTester') as MockTester:
        mock_instance = AsyncMock()
        mock_instance.test_models_concurrent = AsyncMock(return_value=[
            {'model': 'gpt-4', 'success': True, 'response_time': 1.0, 'error_code': '', 'content': 'Test'}
        ])
        MockTester.return_value.__aenter__.return_value = mock_instance
        
        results = test_models_async(
            mock_api_key,
            mock_base_url,
            models,
            model_types
        )
        
        # 验证调用
        assert MockTester.called


@pytest.mark.asyncio
async def test_progress_callback(mock_api_key, mock_base_url):
    """测试进度回调"""
    progress_results = []
    
    def progress_callback(result):
        progress_results.append(result)
    
    models = [{'id': f'model-{i}', 'model': f'model-{i}'} for i in range(5)]
    model_types = {f'model-{i}': 'language' for i in range(5)}
    
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'choices': [{'message': {'content': 'Test'}}]
        })
        
        with patch.object(tester.session, 'request', return_value=mock_response):
            results = await tester.test_models_concurrent(
                models, 
                model_types, 
                progress_callback=progress_callback
            )
            
            # 验证进度回调被调用
            assert len(progress_results) == 5


@pytest.mark.asyncio
async def test_exception_handling(mock_api_key, mock_base_url):
    """测试异常处理"""
    models = [{'id': 'failing-model', 'model': 'failing-model'}]
    model_types = {'failing-model': 'language'}
    
    async with AsyncModelTester(mock_api_key, mock_base_url) as tester:
        # Mock一个会抛出异常的请求
        with patch.object(tester.session, 'request', side_effect=Exception("Network error")):
            results = await tester.test_models_concurrent(models, model_types)
            
            assert len(results) == 1
            assert results[0]['success'] is False
            assert results[0]['error_code'] == 'UNKNOWN_ERROR'
