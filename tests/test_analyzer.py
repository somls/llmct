"""测试结果分析器"""

import pytest
from llmct.core.analyzer import ResultAnalyzer


@pytest.fixture
def sample_results():
    """示例测试结果"""
    return [
        {
            'model': 'model-1',
            'success': True,
            'response_time': 1.5,
            'error_code': '',
            'content': 'Test response'
        },
        {
            'model': 'model-2',
            'success': True,
            'response_time': 2.0,
            'error_code': '',
            'content': 'Test response'
        },
        {
            'model': 'model-3',
            'success': False,
            'response_time': 0,
            'error_code': 'HTTP_403',
            'content': ''
        },
        {
            'model': 'model-4',
            'success': False,
            'response_time': 0,
            'error_code': 'HTTP_429',
            'content': ''
        },
        {
            'model': 'model-5',
            'success': False,
            'response_time': 0,
            'error_code': 'TIMEOUT',
            'content': ''
        }
    ]


def test_calculate_health_score(sample_results):
    """测试健康度评分计算"""
    analyzer = ResultAnalyzer()
    
    health_score = analyzer.calculate_health_score(sample_results)
    
    assert 'score' in health_score
    assert 'grade' in health_score
    assert 'details' in health_score
    assert 0 <= health_score['score'] <= 100
    assert health_score['grade'] in ['A', 'B', 'C', 'D', 'F']
    
    # 检查详细信息
    details = health_score['details']
    assert 'success_score' in details
    assert 'speed_score' in details
    assert 'stability_score' in details
    assert 'success_rate' in details
    assert 'avg_response_time' in details


def test_calculate_health_score_perfect():
    """测试完美健康度评分"""
    analyzer = ResultAnalyzer()
    
    perfect_results = [
        {
            'model': f'model-{i}',
            'success': True,
            'response_time': 1.0,
            'error_code': '',
            'content': 'OK'
        }
        for i in range(10)
    ]
    
    health_score = analyzer.calculate_health_score(perfect_results)
    
    # 100%成功率，快速响应，应该得高分
    assert health_score['score'] >= 90
    assert health_score['grade'] == 'A'
    assert health_score['details']['success_rate'] == 100.0


def test_calculate_health_score_poor():
    """测试糟糕的健康度评分"""
    analyzer = ResultAnalyzer()
    
    poor_results = [
        {
            'model': f'model-{i}',
            'success': False,
            'response_time': 0,
            'error_code': 'HTTP_500',
            'content': ''
        }
        for i in range(10)
    ]
    
    health_score = analyzer.calculate_health_score(poor_results)
    
    # 0%成功率，应该得低分
    assert health_score['score'] < 50
    assert health_score['grade'] in ['D', 'F']
    assert health_score['details']['success_rate'] == 0.0


def test_check_alerts_no_alerts(sample_results):
    """测试无告警情况"""
    analyzer = ResultAnalyzer()
    
    # 使用宽松的阈值，不应触发告警
    thresholds = {
        'min_success_rate': 0.2,  # 20%最低成功率
        'max_avg_response_time': 10.0,
        'max_429_errors': 10,
        'max_403_errors': 10,
        'max_timeout_errors': 10
    }
    
    alerts = analyzer.check_alerts(sample_results, thresholds)
    
    assert isinstance(alerts, list)
    # 应该没有告警或很少
    assert len(alerts) <= 1


def test_check_alerts_low_success_rate():
    """测试低成功率告警"""
    analyzer = ResultAnalyzer()
    
    results = [
        {'model': f'model-{i}', 'success': False, 'response_time': 0, 'error_code': 'HTTP_500', 'content': ''}
        for i in range(10)
    ]
    
    alerts = analyzer.check_alerts(results)
    
    # 应该触发低成功率告警
    assert any(alert['type'] == 'LOW_SUCCESS_RATE' for alert in alerts)


def test_check_alerts_rate_limit():
    """测试速率限制告警"""
    analyzer = ResultAnalyzer()
    
    results = [
        {'model': f'model-{i}', 'success': False, 'response_time': 0, 'error_code': 'HTTP_429', 'content': ''}
        for i in range(60)
    ]
    
    alerts = analyzer.check_alerts(results)
    
    # 应该触发速率限制告警
    assert any(alert['type'] == 'RATE_LIMIT' for alert in alerts)


def test_check_alerts_slow_response():
    """测试慢响应告警"""
    analyzer = ResultAnalyzer()
    
    results = [
        {'model': f'model-{i}', 'success': True, 'response_time': 10.0, 'error_code': '', 'content': 'OK'}
        for i in range(10)
    ]
    
    alerts = analyzer.check_alerts(results)
    
    # 应该触发慢响应告警
    assert any(alert['type'] == 'SLOW_RESPONSE' for alert in alerts)


def test_check_alerts_timeout():
    """测试超时告警"""
    analyzer = ResultAnalyzer()
    
    results = [
        {'model': f'model-{i}', 'success': False, 'response_time': 0, 'error_code': 'TIMEOUT', 'content': ''}
        for i in range(30)
    ]
    
    alerts = analyzer.check_alerts(results)
    
    # 应该触发超时告警
    assert any(alert['type'] == 'TIMEOUT' for alert in alerts)


def test_empty_results():
    """测试空结果"""
    analyzer = ResultAnalyzer()
    
    health_score = analyzer.calculate_health_score([])
    assert health_score['score'] == 0
    assert health_score['grade'] == 'F'
    
    alerts = analyzer.check_alerts([])
    assert alerts == []


def test_custom_weights():
    """测试自定义权重"""
    analyzer = ResultAnalyzer()
    
    results = [
        {'model': f'model-{i}', 'success': True, 'response_time': 1.0, 'error_code': '', 'content': 'OK'}
        for i in range(10)
    ]
    
    # 自定义权重：更注重成功率
    custom_weights = {
        'success_rate': 0.8,
        'response_speed': 0.1,
        'stability': 0.1
    }
    
    health_score = analyzer.calculate_health_score(results, weights=custom_weights)
    
    assert 'score' in health_score
    assert health_score['score'] > 0
