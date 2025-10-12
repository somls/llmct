#!/usr/bin/env python3
"""
测试模型分类功能
"""

from mct import ModelTester

def test_model_classification():
    """测试各种模型的分类是否正确"""
    
    tester = ModelTester(api_key="test", base_url="https://test.com", timeout=30)
    
    test_cases = [
        # 语言模型
        ("gpt-4o", "language"),
        ("gpt-3.5-turbo", "language"),
        ("claude-3-opus", "language"),
        ("qwen-max", "language"),
        ("glm-4-9b-chat", "language"),
        ("moonshot-v1-128k", "language"),
        
        # 视觉模型
        ("gpt-4o", "language"),  # gpt-4o 应该被识别为语言模型，虽然支持vision
        ("qwen-vl-plus", "vision"),
        ("glm-4v", "vision"),
        ("claude-3-5-sonnet", "language"),  # claude默认是语言，除非明确带vision
        ("internvl2-8b", "vision"),
        ("qvq-72b", "vision"),
        
        # 音频模型
        ("whisper-1", "audio"),
        ("tts-1", "audio"),
        ("@cf/openai/whisper", "audio"),
        ("cosyvoice2-0.5b", "audio"),
        ("fish-speech-1.4", "audio"),
        ("sensevoice", "audio"),
        
        # 嵌入模型
        ("text-embedding-ada-002", "embedding"),
        ("text-embedding-3-large", "embedding"),
        ("bge-m3", "embedding"),
        ("bge-large-zh-v1.5", "embedding"),
        ("doubao-embedding-large", "embedding"),
        
        # 图像生成
        ("dall-e-2", "image_generation"),
        ("dall-e-3", "image_generation"),
        ("flux.1-schnell", "image_generation"),
        ("stable-diffusion", "image_generation"),
        ("kolors", "image_generation"),
        ("cogview-3", "image_generation"),
        ("dreamshaper-8", "image_generation"),
        
        # Reranker
        ("bge-reranker-v2-m3", "reranker"),
        
        # Moderation
        ("text-moderation-stable", "moderation"),
        ("text-moderation-latest", "moderation"),
    ]
    
    print("="*80)
    print("模型分类测试")
    print("="*80)
    print(f"{'模型ID':<40} | {'预期类型':<20} | {'实际类型':<20} | 结果")
    print("-"*80)
    
    passed = 0
    failed = 0
    
    for model_id, expected_type in test_cases:
        actual_type = tester.classify_model(model_id)
        is_correct = actual_type == expected_type
        result = "PASS" if is_correct else "FAIL"
        
        if is_correct:
            passed += 1
        else:
            failed += 1
        
        print(f"{model_id:<40} | {expected_type:<20} | {actual_type:<20} | {result}")
    
    print("="*80)
    print(f"测试完成: 总计 {len(test_cases)} | 通过 {passed} | 失败 {failed} | 准确率 {passed/len(test_cases)*100:.1f}%")
    print("="*80)
    
    return passed == len(test_cases)

if __name__ == '__main__':
    success = test_model_classification()
    exit(0 if success else 1)
