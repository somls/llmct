"""测试模型分类器"""

import pytest
from llmct.core.classifier import ModelClassifier


def test_classify_language_model():
    """测试语言模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("gpt-4") == "language"
    assert classifier.classify("gpt-3.5-turbo") == "language"
    assert classifier.classify("claude-3") == "language"
    assert classifier.classify("llama-2-70b") == "language"


def test_classify_vision_model():
    """测试视觉模型分类"""
    classifier = ModelClassifier()
    
    # 使用实际匹配分类规则的模型名
    assert classifier.classify("gpt-4o-vl") == "vision"
    assert classifier.classify("qwen-vl-max") == "vision"
    assert classifier.classify("glm-4v") == "vision"
    assert classifier.classify("internvl-chat") == "vision"
    assert classifier.classify("qvq-72b") == "vision"


def test_classify_audio_model():
    """测试音频模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("whisper-1") == "audio"
    assert classifier.classify("tts-1") == "audio"
    assert classifier.classify("cosyvoice") == "audio"
    assert classifier.classify("fish-speech") == "audio"


def test_classify_embedding_model():
    """测试嵌入模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("text-embedding-ada-002") == "embedding"
    assert classifier.classify("text-embedding-3-small") == "embedding"
    assert classifier.classify("bge-m3") == "embedding"
    assert classifier.classify("bge-large-zh") == "embedding"


def test_classify_image_generation_model():
    """测试图像生成模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("dall-e-3") == "image_generation"
    assert classifier.classify("stable-diffusion-xl") == "image_generation"
    assert classifier.classify("flux-pro") == "image_generation"
    assert classifier.classify("kolors") == "image_generation"


def test_classify_reranker_model():
    """测试重排模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("reranker-v1") == "reranker"
    assert classifier.classify("bge-reranker-base") == "reranker"


def test_classify_moderation_model():
    """测试审核模型分类"""
    classifier = ModelClassifier()
    
    assert classifier.classify("text-moderation-latest") == "moderation"
    assert classifier.classify("text-moderation-stable") == "moderation"


def test_classify_batch():
    """测试批量分类"""
    classifier = ModelClassifier()
    
    models = ["gpt-4", "whisper-1", "dall-e-3", "text-embedding-ada-002"]
    results = classifier.classify_batch(models)
    
    assert results["gpt-4"] == "language"
    assert results["whisper-1"] == "audio"
    assert results["dall-e-3"] == "image_generation"
    assert results["text-embedding-ada-002"] == "embedding"


def test_get_statistics():
    """测试统计功能"""
    classifier = ModelClassifier()
    
    models = [
        "gpt-4", "gpt-3.5-turbo",  # 2 language
        "whisper-1", "tts-1",  # 2 audio
        "dall-e-3",  # 1 image_generation
        "text-embedding-ada-002",  # 1 embedding
    ]
    
    stats = classifier.get_statistics(models)
    
    assert stats["language"] == 2
    assert stats["audio"] == 2
    assert stats["image_generation"] == 1
    assert stats["embedding"] == 1


def test_custom_patterns():
    """测试自定义分类规则（仅更新现有类型）"""
    # 修改现有类型的规则
    from llmct.core.classifier import ModelClassifier
    
    custom_patterns = ModelClassifier.DEFAULT_PATTERNS.copy()
    # 修改vision类型的匹配规则，添加custom-vision
    custom_patterns['vision']['patterns'].append('custom-vision')
    
    classifier = ModelClassifier(patterns=custom_patterns)
    result = classifier.classify("custom-vision-model")
    
    # 应该匹配vision类型
    assert result == "vision"
    
    # 验证原有规则仍然有效
    assert classifier.classify("gpt-4o-vl") == "vision"


def test_exclude_patterns():
    """测试排除规则"""
    classifier = ModelClassifier()
    
    # vision模型中排除了embedding
    # 所以包含embedding的模型即使匹配vision也不会被分类为vision
    model_id = "some-embedding-vl-model"
    result = classifier.classify(model_id)
    
    # 应该被分类为embedding而不是vision
    assert result == "embedding"
