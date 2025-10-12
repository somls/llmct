"""测试文本处理工具"""

import pytest
from llmct.utils.text_utils import display_width, pad_string, truncate_string


def test_display_width_ascii():
    """测试ASCII字符宽度"""
    assert display_width("hello") == 5
    assert display_width("test") == 4
    assert display_width("") == 0


def test_display_width_chinese():
    """测试中文字符宽度"""
    assert display_width("你好") == 4  # 2个中文字符 = 4个宽度
    assert display_width("测试") == 4


def test_display_width_mixed():
    """测试混合字符宽度"""
    assert display_width("Hello世界") == 9  # 5 + 4 = 9
    assert display_width("test测试") == 8  # 4 + 4 = 8


def test_pad_string_left():
    """测试左对齐填充"""
    result = pad_string("hello", 10, 'left')
    assert len(result) == 10
    assert result == "hello     "


def test_pad_string_right():
    """测试右对齐填充"""
    result = pad_string("hello", 10, 'right')
    assert len(result) == 10
    assert result == "     hello"


def test_pad_string_center():
    """测试居中对齐填充"""
    result = pad_string("hello", 10, 'center')
    assert len(result) == 10
    # 5个字符居中在10个宽度，左边2或3个空格，右边3或2个空格


def test_pad_string_chinese():
    """测试中文字符填充"""
    # "你好"宽度为4，填充到10
    result = pad_string("你好", 10, 'left')
    assert display_width(result) == 10


def test_pad_string_no_padding():
    """测试不需要填充的情况"""
    result = pad_string("hello", 5, 'left')
    assert result == "hello"
    
    result = pad_string("hello", 3, 'left')
    assert result == "hello"  # 不截断


def test_truncate_string_short():
    """测试短字符串（不需要截断）"""
    result = truncate_string("hello", 10)
    assert result == "hello"


def test_truncate_string_exact():
    """测试恰好等于最大宽度"""
    result = truncate_string("hello", 5)
    assert result == "hello"


def test_truncate_string_long():
    """测试需要截断的长字符串"""
    result = truncate_string("hello world", 8)
    assert result == "hello..."
    assert display_width(result) <= 8


def test_truncate_string_chinese():
    """测试截断中文字符串"""
    result = truncate_string("这是一个很长的中文字符串", 10)
    assert display_width(result) <= 10
    assert result.endswith("...")


def test_truncate_string_custom_suffix():
    """测试自定义后缀"""
    result = truncate_string("hello world", 8, suffix="…")
    assert result.endswith("…")


def test_truncate_string_mixed():
    """测试混合字符截断"""
    result = truncate_string("Hello这是测试内容", 10)
    assert display_width(result) <= 10
    assert result.endswith("...")
