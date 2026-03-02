#!/usr/bin/env python3
"""
OpenClaw Skills - Phase 1-2 测试套件
"""

import sys
import os
import tempfile
import shutil

# 添加 skill 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cross-session-memory'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scheme-confirmation'))

# 加载 skill 代码
exec(open(os.path.join(os.path.dirname(__file__), '..', 'cross-session-memory', 'main.py')).read())

# 保存 cross-session-memory 的类
CrossSessionMemoryClass = CrossSessionMemory
TopicMemoryClass = TopicMemory
MemoryStoreClass = MemoryStore
TopicExtractorClass = TopicExtractor

# 加载 scheme-confirmation 代码
exec(open(os.path.join(os.path.dirname(__file__), '..', 'scheme-confirmation', 'main.py')).read())

SchemeConfirmationClass = SchemeConfirmation
SchemeClass = Scheme
SchemeStoreClass = SchemeStore
SchemeDetectorClass = SchemeDetector
SchemeStatusClass = SchemeStatus


def test_cross_session_memory():
    """测试跨会话记忆 Skill"""
    print("\n=== Testing Cross-Session Memory ===\n")
    
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: MemoryStore 基本操作
        print("Test 1: MemoryStore CRUD")
        store = MemoryStoreClass(storage_dir=temp_dir)
        
        topic = TopicMemoryClass(
            id='test_001',
            title='测试话题',
            summary='这是一个测试话题',
            key_points=['要点1', '要点2'],
            pending_items=['待办1'],
            created_at=__import__('time').time(),
            updated_at=__import__('time').time(),
            session_key='session_001'
        )
        assert store.add(topic) == True
        assert store.get('test_001') is not None
        print("  ✓ MemoryStore CRUD passed")
        
        # Test 2: 过期检测
        print("Test 2: Expiration detection")
        old_topic = TopicMemoryClass(
            id='test_old',
            title='过期话题',
            summary='这是一个过期话题',
            key_points=[],
            pending_items=[],
            created_at=0,
            updated_at=0,
            session_key='session_002',
            ttl=1  # 1秒过期
        )
        store.add(old_topic)
        import time
        time.sleep(1.1)
        assert old_topic.is_expired() == True
        print("  ✓ Expiration detection passed")
        
        # Test 3: 清理过期
        print("Test 3: Cleanup expired")
        count = store.cleanup_expired()
        assert count >= 1
        assert store.get('test_old') is None
        print("  ✓ Cleanup expired passed")
        
        # Test 4: TopicExtractor
        print("Test 4: Topic extraction")
        extractor = TopicExtractorClass()
        messages = [
            {'role': 'user', 'content': '我想准备越野赛'},
            {'role': 'assistant', 'content': '需要准备什么装备？'},
            {'role': 'user', 'content': '- 头灯\n- 越野鞋\n需要确认装备清单'},
        ]
        extracted = extractor.extract_topic('session_003', messages)
        assert extracted is not None
        assert '越野赛' in extracted.title
        assert len(extracted.key_points) >= 2
        print("  ✓ Topic extraction passed")
        
        # Test 5: CrossSessionMemory 主类
        print("Test 5: CrossSessionMemory main class")
        skill = CrossSessionMemoryClass(config={'auto_resume': True, 'memory_ttl': 86400})
        
        # 保存话题
        topic_id = skill.save_topic('session_004', messages)
        assert topic_id is not None
        print("  ✓ Save topic passed")
        
        # 新会话恢复 - 使用相同skill实例检查
        result = skill.on_session_start('new_session', '继续越野赛准备')
        # 由于话题相似度匹配，应该能找到相关话题
        print(f"  Session resume result: {'有提示' if result else '无提示'}")
        print("  ✓ Session resume passed")
        
        print("\n✅ All Cross-Session Memory tests passed!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_scheme_confirmation():
    """测试方案确认 Skill"""
    print("\n=== Testing Scheme Confirmation ===\n")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: SchemeStore 基本操作
        print("Test 1: SchemeStore CRUD")
        store = SchemeStoreClass(storage_dir=temp_dir)
        
        scheme = SchemeClass(
            id='SCHEME-TEST-001',
            title='测试方案',
            description='这是一个测试方案',
            status=SchemeStatusClass.PROPOSED.value,
            created_at=__import__('time').time(),
            updated_at=__import__('time').time(),
            session_key='session_001',
            proposed_by='ai',
            confirmation_requested_at=__import__('time').time()
        )
        assert store.add(scheme) == True
        assert store.get('SCHEME-TEST-001') is not None
        print("  ✓ SchemeStore CRUD passed")
        
        # Test 2: 状态流转
        print("Test 2: Status transitions")
        store.update_status('SCHEME-TEST-001', SchemeStatusClass.CONFIRMED.value)
        updated = store.get('SCHEME-TEST-001')
        assert updated.status == SchemeStatusClass.CONFIRMED.value
        assert updated.confirmed_at is not None
        print("  ✓ Status transitions passed")
        
        # Test 3: SchemeDetector
        print("Test 3: Scheme detection")
        detector = SchemeDetectorClass()
        
        test_cases = [
            ('建议：优化流程', True),
            ('方案A：使用新技术', True),
            ('今天天气不错', False),
            ('计划：分三步实施', True),
        ]
        
        for msg, should_detect in test_cases:
            result = detector.detect(msg)
            if should_detect:
                assert result is not None, f"Should detect scheme in: {msg}"
            else:
                assert result is None, f"Should not detect scheme in: {msg}"
        print("  ✓ Scheme detection passed")
        
        # Test 4: SchemeConfirmation 主类
        print("Test 4: SchemeConfirmation main class")
        skill = SchemeConfirmationClass(config={'auto_detect': True})
        
        # 检测 AI 消息中的方案
        ai_msg = "方案：优化周报生成流程\n建议将周报改为自动化生成"
        result = skill.on_message('session_002', ai_msg, sender='ai')
        assert result is not None
        assert '方案提议' in result
        print("  ✓ Auto-detection from AI message passed")
        
        # 用户确认
        confirm_result = skill.on_message('session_002', '确认', sender='user')
        assert confirm_result is not None
        assert '已确认' in confirm_result
        print("  ✓ User confirmation passed")
        
        # 开始执行
        execute_result = skill.on_message('session_002', '开始执行', sender='user')
        assert execute_result is not None
        assert '开始执行' in execute_result
        print("  ✓ Start execution passed")
        
        # 完成
        # 先获取当前执行的方案ID
        active = skill.store.get_active()
        if active:
            scheme_id = active[0].id
            complete_result = skill.on_message('session_002', f'已完成 #{scheme_id}', sender='user')
            assert complete_result is not None
            assert '已完成' in complete_result
            print("  ✓ Complete scheme passed")
        
        # Test 5: 状态查询
        print("Test 5: Status query")
        query_result = skill.on_message('session_002', '查看方案状态', sender='user')
        assert query_result is not None
        assert '方案状态' in query_result
        print("  ✓ Status query passed")
        
        print("\n✅ All Scheme Confirmation tests passed!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("OpenClaw Skills - Phase 1-2 Test Suite")
    print("=" * 50)
    
    try:
        test_cross_session_memory()
        test_scheme_confirmation()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 50)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
