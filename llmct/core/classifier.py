"""模型分类器"""

import json
from pathlib import Path
from typing import Dict


class ModelClassifier:
    """
    模型分类器 - 根据模型ID识别模型类型
    
    支持的类型：
    - language: 语言模型
    - vision: 视觉模型
    - audio: 音频模型
    - embedding: 嵌入模型
    - image_generation: 图像生成模型
    - reranker: 重排模型
    - moderation: 审核模型
    """
    
    # 默认分类规则
    DEFAULT_PATTERNS = {
        'image_generation': {
            'patterns': ['dall-e', 'flux', 'stable-diffusion', 'dreamshaper', 
                        'kolors', 'cogview', 'seedream', 'seedance', 
                        'seededit', 't2i', 'i2i', 't2v', 'i2v'],
            'exclude': []
        },
        'audio': {
            'patterns': ['whisper', 'tts', 'speech', 'audio', 'cosyvoice', 
                        'fish-speech', 'teletts', 'teleaudio', 'teleasr',
                        'sensevoice', 'gpt-sovits', 'rvc'],
            'exclude': []
        },
        'embedding': {
            'patterns': ['embedding', 'bge-m3', 'bge-large'],
            'exclude': []
        },
        'reranker': {
            'patterns': ['reranker'],
            'exclude': []
        },
        'moderation': {
            'patterns': ['moderation'],
            'exclude': []
        },
        'vision': {
            'patterns': ['-vl', 'qwen-image', 'internvl', 'qvq', 'glm-4v', 
                        'llama-vision', 'molmo', 'aria', 'qwen-vl'],
            'exclude': ['embedding']
        }
    }
    
    def __init__(self, patterns: Dict = None):
        """
        Args:
            patterns: 自定义分类规则（可选）
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS
    
    @classmethod
    def from_file(cls, patterns_file: str):
        """
        从JSON文件加载分类规则
        
        Args:
            patterns_file: 规则文件路径
        
        Returns:
            ModelClassifier实例
        """
        with open(patterns_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        return cls(patterns)
    
    def classify(self, model_id: str) -> str:
        """
        分类模型类型
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型类型字符串
        """
        model_lower = model_id.lower()
        
        # 按优先级顺序检查
        for category in ['image_generation', 'audio', 'embedding', 'reranker', 'moderation', 'vision']:
            rules = self.patterns.get(category, {})
            patterns = rules.get('patterns', [])
            exclude = rules.get('exclude', [])
            
            # 检查匹配模式
            if any(p in model_lower for p in patterns):
                # 检查排除模式
                if not any(e in model_lower for e in exclude):
                    return category
        
        # 默认为语言模型
        return 'language'
    
    def classify_batch(self, model_ids: list) -> Dict[str, str]:
        """
        批量分类模型
        
        Args:
            model_ids: 模型ID列表
            
        Returns:
            {model_id: model_type} 映射字典
        """
        return {model_id: self.classify(model_id) for model_id in model_ids}
    
    def get_statistics(self, model_ids: list) -> Dict[str, int]:
        """
        获取模型类型统计
        
        Args:
            model_ids: 模型ID列表
            
        Returns:
            {model_type: count} 统计字典
        """
        classifications = self.classify_batch(model_ids)
        
        stats = {}
        for model_type in classifications.values():
            stats[model_type] = stats.get(model_type, 0) + 1
        
        return stats
    
    def save_patterns(self, output_file: str):
        """保存分类规则到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
