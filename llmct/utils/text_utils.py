"""文本处理工具模块"""

import unicodedata
from typing import Literal


def display_width(text: str) -> int:
    """
    计算字符串的实际显示宽度
    
    中文、日文、韩文等全角字符算2个宽度，ASCII字符算1个宽度。
    
    Args:
        text: 要计算宽度的字符串
        
    Returns:
        显示宽度（整数）
        
    Example:
        >>> display_width("hello")
        5
        >>> display_width("你好")
        4
        >>> display_width("Hello世界")
        9
    """
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def pad_string(text: str, width: int, align: Literal['left', 'center', 'right'] = 'left') -> str:
    """
    根据显示宽度填充字符串
    
    考虑中文等全角字符的实际显示宽度，正确对齐文本。
    
    Args:
        text: 要填充的字符串
        width: 目标显示宽度
        align: 对齐方式，可选 'left'、'center'、'right'
        
    Returns:
        填充后的字符串
        
    Example:
        >>> pad_string("hello", 10, 'left')
        'hello     '
        >>> pad_string("你好", 10, 'center')
        '   你好   '
    """
    text_width = display_width(text)
    padding = width - text_width
    
    if padding <= 0:
        return text
    
    if align == 'center':
        left_pad = padding // 2
        right_pad = padding - left_pad
        return ' ' * left_pad + text + ' ' * right_pad
    elif align == 'right':
        return ' ' * padding + text
    else:  # left
        return text + ' ' * padding


def truncate_string(text: str, max_width: int, suffix: str = '...') -> str:
    """
    按显示宽度截断字符串
    
    Args:
        text: 要截断的字符串
        max_width: 最大显示宽度
        suffix: 截断后添加的后缀
        
    Returns:
        截断后的字符串
        
    Example:
        >>> truncate_string("很长的字符串内容", 10)
        '很长的...'
    """
    if display_width(text) <= max_width:
        return text
    
    suffix_width = display_width(suffix)
    target_width = max_width - suffix_width
    
    if target_width <= 0:
        return suffix[:max_width]
    
    result = ""
    current_width = 0
    
    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
        if current_width + char_width > target_width:
            break
        result += char
        current_width += char_width
    
    return result + suffix
