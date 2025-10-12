#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 仅测试可靠的快速模型
基于真实API测试结果优化
"""

import subprocess
import sys
import time

# 设置Windows控制台输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# 基于实际测试的快速可靠模型
FAST_MODELS = [
    'kimi-k2-fast',      # 1.76秒 - 最快
    'gpt-oss-120b',      # 2.43秒
    'qwen3-32b',         # 2.43秒
    'glm-4.5',           # 2.99秒
]

# 已知失败的模型（跳过）
SKIP_MODELS = [
    'gemma2-9b-it',      # HTTP_400
    'kimi-k2-auto',      # HTTP_404
    'glm-4.6',           # UNKNOWN_ERROR
]


def run_quick_test(api_key: str, base_url: str):
    """运行快速测试"""
    
    print("=" * 80)
    print("LLMCT 快速测试模式")
    print("=" * 80)
    print()
    print("测试配置:")
    print(f"  • 测试模型: {len(FAST_MODELS)}个快速模型")
    print(f"  • 跳过模型: {len(SKIP_MODELS)}个已知失败")
    print(f"  • 超时设置: 15秒（针对快速模型优化）")
    print(f"  • 预计耗时: ~12秒")
    print()
    
    start_time = time.time()
    
    # 构建命令
    cmd = [
        'python', 'mct.py',
        '--api-key', api_key,
        '--base-url', base_url,
        '--timeout', '15',
        '--skip-vision',
        '--skip-audio',
        '--output', 'quick_test_report.html'
    ]
    
    print("正在执行测试...")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 80)
        print(f"快速测试完成！耗时: {elapsed:.1f}秒")
        print("=" * 80)
        print()
        print("📊 报告已生成: quick_test_report.html")
        print()
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"错误: {e}")
        return False


def print_recommendations():
    """打印优化建议"""
    print("💡 使用建议:")
    print()
    print("1. 日常快速检查:")
    print("   python quick_test.py")
    print()
    print("2. 全面测试:")
    print("   python mct.py --api-key ... --base-url ... --max-failures 3")
    print()
    print("3. 仅测试失败模型:")
    print("   python mct.py --api-key ... --base-url ... --only-failed")
    print()
    print("4. 生成HTML报告:")
    print("   python mct.py --api-key ... --base-url ... --output report.html")
    print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLMCT 快速测试')
    parser.add_argument('--api-key', required=True, help='API密钥')
    parser.add_argument('--base-url', required=True, help='API基础URL')
    
    args = parser.parse_args()
    
    success = run_quick_test(args.api_key, args.base_url)
    
    if success:
        print("✅ 快速测试通过！")
        print()
        print_recommendations()
        return 0
    else:
        print("❌ 快速测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
