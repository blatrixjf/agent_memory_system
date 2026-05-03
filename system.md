# 智能体记忆系统 (Agent Memory System)

## 项目概述

一个轻量级、原生Python实现的智能体记忆算法系统，支持对话事件存储、向量检索、概念召回和懒加载久远记忆。

---

## 目录结构

```
agent_memory_system/
├── main.py                        # 入口，对话循环
├── config.py                      # 配置（API Key、路径、阈值）
├── test_memory.py                 # 测试演示脚本
├── requirements.txt               # 依赖文件
├── models/
│   ├── __init__.py
│   ├── event.py                   # 事件数据模型
│   └── concept.py                 # 概念数据模型
├── database/
│   ├── __init__.py
│   ├── db.py                      # SQLite连接、表创建
│   ├── event_repo.py              # 事件CRUD
│   └── concept_repo.py            # 概念CRUD + 关联表操作
└── memory/
    ├── __init__.py
    ├── summarizer.py              # 摘要生成（OpenAI调用）
    ├── concept_extractor.py       # 抽象概念提取（OpenAI调用）
    ├── vector_store.py            # FAISS向量存储与检索
    └── memory_manager.py          # 记忆核心逻辑（检索、召回、懒加载）
```

---

## 核心算法逻辑

### 1. 事件存储
每轮对话 = 一个事件（event），存储：
- 用户消息
- AI回复
- 时间戳
- 摘要（1句话）
- 抽象概念列表（3-5个关键词）
- 向量（OpenAI Embeddings）

### 2. 处理流程
```
用户输入 → 生成简短摘要 → 提取抽象概念 → 生成向量 → 存入事件库 + 向量库
```

### 3. 概念-事件映射
- 概念表（concepts）：存储抽象概念及激活时间
- 事件表（events）：存储对话事件
- 关联表（event_concepts）：多对多映射关系

### 4. 记忆检索（省Token核心）
1. 新对话生成抽象概念和向量
2. 向量相似度检索，找出最相似的历史概念
3. 对匹配到的概念，**只召回该概念下最近的1条事件**
4. 把这条最近事件加入上下文，询问用户："我们之前是不是聊过【事件摘要】？"

### 5. 久远记忆懒加载触发条件（满足其一即加载）
- 用户回复"不是/不对/没聊过"等否定词
- 用户明确要求"更早的/上次之前的/之前那次"
- 用户直接指定某条事件ID或话题

### 6. 加载久远记忆
从该概念下的历史事件中，按时间倒序，追加1-3条到上下文，不超过Token限制。

### 7. 激活时间权重
每个概念记录最后激活时间，检索时优先最近激活的概念。

---

## 技术栈与约束

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 数据库 | SQLite（本地文件） |
| 向量存储 | FAISS（本地向量库） |
| 模型调用 | OpenAI 兼容接口（可配置） |
| 数据模型 | Pydantic |
| 时间处理 | datetime/time |

### 禁止使用
- LangChain
- LlamaIndex
- 其他大框架

### 代码规范
- 模块化设计
- 全中文注释
- 类型注解清晰
- 函数单一职责
- 可直接运行

---

## 文件说明

### config.py
- OpenAI API Key、API Base 配置
- 摘要/概念生成提示词
- 相似度阈值（默认0.75）
- 最大上下文Token限制（默认4000）
- 懒加载触发关键词列表

### database/db.py
- 自动创建三张表：events、concepts、event_concepts
- SQLite连接管理
- 索引优化

### database/event_repo.py
- 事件增删改查
- 按概念获取最新/历史事件
- 批量获取事件

### database/concept_repo.py
- 概念增删改查
- 概念-事件关联操作
- 激活时间更新

### memory/summarizer.py
- 调用OpenAI生成1句话摘要
- API失败时使用规则备用方案

### memory/concept_extractor.py
- 调用OpenAI提取3-5个抽象概念
- API失败时关键词匹配备用方案

### memory/vector_store.py
- OpenAI Embeddings向量化
- FAISS索引存储与检索
- ID映射持久化

### memory/memory_manager.py
- `process_new_event`: 处理新对话→摘要→概念→向量→入库
- `retrieve_recent_memory`: 根据新向量召回最近1条相似事件
- `lazy_load_older_memory`: 按概念加载久远事件（1-3条）
- `update_concept_activation`: 更新概念最后激活时间
- `should_trigger_lazy_load`: 判断是否触发懒加载
- `format_memory_context`: 格式化记忆上下文

### main.py
- 对话循环入口
- 用户输入处理
- 记忆检索与懒加载触发
- AI回复生成
- 命令支持：quit/exit/history/clear

### test_memory.py
包含4个测试用例：
1. 测试新对话存入事件与概念
2. 测试相似概念召回最近事件并询问用户
3. 测试用户否定后懒加载久远记忆
4. 测试概念激活时间更新

---

## 安装与运行

### 1. 安装依赖
```bash
cd agent_memory_system
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
# 方式1：修改config.py中的OPENAI_API_KEY
# 方式2：设置环境变量
export OPENAI_API_KEY=your-key-here
export OPENAI_API_BASE=https://api.openai.com/v1  # 可选
```

### 3. 运行测试
```bash
python test_memory.py
```

### 4. 运行对话系统
```bash
python main.py
```

---

## 依赖列表

```
openai>=1.0.0
faiss-cpu>=1.7.4
pydantic>=2.0.0
numpy>=1.24.0
```

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| SIMILARITY_THRESHOLD | 0.75 | 向量相似度阈值 |
| TOP_K_CONCEPTS | 5 | 检索返回的相似概念数量 |
| MAX_LAZY_LOAD_COUNT | 3 | 懒加载最多加载条数 |
| MAX_CONTEXT_TOKENS | 4000 | 最大上下文Token限制 |
| ESTIMATED_TOKENS_PER_EVENT | 100 | 单条事件估算Token数 |

---

## 数据库表结构

### events 表
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT NOT NULL,
    ai_reply TEXT NOT NULL,
    summary TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### concepts 表
```sql
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    last_activated DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### event_concepts 关联表
```sql
CREATE TABLE event_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    concept_id INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE(event_id, concept_id)
);
```

---

## 编译验证

所有12个Python文件均通过 `python -m py_compile` 语法检查，无错误。

---

**生成日期**: 2026-05-03  
**版本**: v1.0
