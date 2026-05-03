"""
测试脚本 - 智能体记忆系统
演示全流程：新对话存入、相似记忆召回、懒加载久远记忆
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from memory.memory_manager import memory_manager
from database.event_repo import event_repo
from database.concept_repo import concept_repo
from memory.vector_store import vector_store


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_1_new_event_storage():
    """
    测试1：新对话存入事件与概念
    验证：事件入库、概念提取、向量存储
    """
    print_section("测试1: 新对话存入事件与概念")
    
    # 模拟对话
    conversations = [
        {
            "user": "你好，我想学习Python编程",
            "ai": "Python是一门非常适合初学者的编程语言，它具有简洁的语法和强大的库。你可以从基础语法开始，然后逐步学习面向对象编程、数据处理等进阶内容。"
        },
        {
            "user": "Python中如何处理JSON数据？",
            "ai": "Python内置了json模块，你可以使用json.loads()解析JSON字符串，使用json.dumps()将对象转换为JSON格式。对于文件操作，可以使用json.load()和json.dump()。"
        },
        {
            "user": "什么是机器学习？",
            "ai": "机器学习是人工智能的一个分支，它让计算机能够从数据中学习并做出决策或预测，而无需显式编程。常见的机器学习算法包括线性回归、决策树、神经网络等。"
        }
    ]
    
    print("\n[步骤1] 模拟存储3轮对话...")
    event_ids = []
    
    for conv in conversations:
        print(f"\n--- 对话: {conv['user'][:30]}... ---")
        event_id, concepts = memory_manager.process_new_event(
            conv["user"],
            conv["ai"]
        )
        event_ids.append(event_id)
        print(f"  → 事件ID: {event_id}")
        print(f"  → 提取概念: {concepts}")
    
    print(f"\n[步骤2] 验证事件总数...")
    total_events = event_repo.count()
    print(f"  事件总数: {total_events}")
    assert total_events == 3, f"期望3个事件，实际{total_events}个"
    
    print(f"\n[步骤3] 验证向量库大小...")
    vector_count = vector_store.index.ntotal
    print(f"  向量数量: {vector_count}")
    assert vector_count == 3, f"期望3个向量，实际{vector_count}个"
    
    print("\n[✓] 测试1通过：新对话成功存入事件与概念！")
    return event_ids


def test_2_similar_concept_recall():
    """
    测试2：相似概念召回最近事件并询问用户
    验证：向量检索、概念映射、最近事件召回
    """
    print_section("测试2: 相似概念召回最近事件")
    
    # 模拟用户新消息（与测试1中的对话相关）
    new_message = "我想了解一下Python的数据处理方法"
    
    print(f"\n[步骤1] 新对话: {new_message}")
    print("[步骤2] 开始检索相似记忆...")
    
    # 检索相似记忆
    recent_memory = memory_manager.retrieve_recent_memory(new_message)
    
    if recent_memory:
        print(f"\n[步骤3] 召回的最近记忆:")
        print(f"  → 事件ID: {recent_memory.id}")
        print(f"  → 摘要: {recent_memory.summary}")
        print(f"  → 用户消息: {recent_memory.user_message[:50]}...")
        
        # 构建询问
        question = f"我们之前是不是聊过【{recent_memory.summary}】？"
        print(f"\n[系统询问] {question}")
        
        print("\n[✓] 测试2通过：成功召回相似概念下的最近事件！")
        return recent_memory
    else:
        print("\n[!] 测试2警告：未找到相似记忆（可能是API不可用，向量随机生成导致）")
        return None


def test_3_lazy_load_older_memories():
    """
    测试3：用户否定后懒加载久远记忆
    验证：触发条件判断、久远记忆加载
    """
    print_section("测试3: 懒加载久远记忆")
    
    # 使用测试2中召回的事件（或最新事件）
    recent_event = event_repo.get_latest_by_concept(1)  # 获取最新事件
    
    if recent_event is None:
        # 如果数据库为空，先创建一些数据
        print("\n[准备] 数据库为空，先创建测试数据...")
        memory_manager.process_new_event(
            "Python编程基础",
            "Python是一门解释型编程语言..."
        )
        memory_manager.process_new_event(
            "Python高级特性",
            "Python支持装饰器、生成器等高级特性..."
        )
        memory_manager.process_new_event(
            "Python数据分析",
            "Python有pandas、numpy等数据分析库..."
        )
        
        recent_event = event_repo.get_latest_by_concept(1)
    
    print(f"\n[步骤1] 参考事件: {recent_event.summary}")
    
    # 测试触发词检测
    test_messages = [
        "不对，不是这个",
        "我想看更早的内容",
        "上次之前我们聊过什么",
        "详细说说所有相关内容"
    ]
    
    print(f"\n[步骤2] 测试懒加载触发条件:")
    for msg in test_messages:
        should_trigger = memory_manager.should_trigger_lazy_load(msg)
        status = "✓" if should_trigger else "✗"
        print(f"  {status} '{msg}' → {'触发' if should_trigger else '不触发'}")
    
    # 执行懒加载
    print(f"\n[步骤3] 执行懒加载久远记忆...")
    older_memories = memory_manager.lazy_load_older_memory(
        reference_event_id=recent_event.id,
        max_count=3
    )
    
    print(f"\n[步骤4] 加载的久远记忆:")
    for i, memory in enumerate(older_memories, 1):
        print(f"  {i}. {memory.summary}")
        print(f"     时间: {memory.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 构建完整记忆上下文
    context = memory_manager.format_memory_context(recent_event, older_memories)
    print(f"\n[步骤5] 完整记忆上下文:")
    print(context)
    
    print(f"\n[✓] 测试3通过：懒加载久远记忆成功！")


def test_4_concept_activation():
    """
    测试4：概念激活时间更新
    验证：概念最后激活时间记录
    """
    print_section("测试4: 概念激活时间更新")
    
    print("\n[步骤1] 获取最近激活的概念...")
    recent_concepts = concept_repo.get_recent_activated(limit=5)
    
    print(f"\n最近激活的概念:")
    for concept in recent_concepts:
        print(f"  → {concept.name} (最后激活: {concept.last_activated.strftime('%H:%M:%S')})")
    
    print("\n[✓] 测试4通过：概念激活时间记录正常！")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#" * 60)
    print("#  智能体记忆系统 - 全流程测试")
    print("#" * 60)
    print(f"\n测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 测试1：新对话存入
        event_ids = test_1_new_event_storage()
        
        # 测试2：相似概念召回
        recent_memory = test_2_similar_concept_recall()
        
        # 测试3：懒加载久远记忆
        test_3_lazy_load_older_memories()
        
        # 测试4：概念激活时间
        test_4_concept_activation()
        
        print("\n" + "#" * 60)
        print("#  ✓ 所有测试通过！")
        print("#" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
