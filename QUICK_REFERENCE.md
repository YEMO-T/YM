# 豆沙包教师助手 - 快速参考指南

## 🎯 4 大功能实现一览表

| 需求 | 完成状态 | 涉及文件 | 关键改动 |
|------|---------|---------|---------|
| 1️⃣ PPT 生成 + 知识库集成 | ✅ 完成 | `llm_service.py` | 修复 RAG context_str 初始化 |
| 2️⃣ 对话记录（至多30轮） | ✅ 完成 | `supabase_client.py` | `trim_messages()` 自动裁剪 |
| 3️⃣ 删除草图识别 | ✅ 完成 | 3 个前端文件 | 移除 PenTool 按钮 |
| 4️⃣ 知识库按账号隔离 + 编辑 | ✅ 完成 | `knowledge.py`, `DashboardView` | 权限检验 + 管理UI |

---

## 🔑 核心代码片段

### 1. RAG 流程（llm_service.py）
```python
# 初始化 context_str（修复的关键行）
context_str = ""
knowledge_docs = get_knowledge_items(user_id)
if knowledge_docs:
    # 构造检索查询
    retrieval_query = _build_retrieval_query(prompt, history, max_user_turns=3)
    # 检索 Top 5
    retrieved_docs = _retrieve_top_k_knowledge(knowledge_docs, retrieval_query, k=5)
    # 格式化上下文
    knowledge_context = _format_knowledge_context(retrieved_docs)
    if knowledge_context:
        context_str = f"\n\n【补充资料参考】\n{knowledge_context}\n..."
```

### 2. 权限隔离（knowledge.py）
```python
# 删除业许检验：只能删除自己的资料
supabase.table("knowledge_items") \
    .delete() \
    .eq("id", item_id) \
    .eq("user_id", user_id)  # ← 权限检验
    .execute()
```

### 3. 前端传递 user_id（DashboardView.tsx）
```typescript
// 流式对话时传递 user_id
await chatWithGeminiStream(
    fullPrompt,
    updatedHistory,
    onChunk,
    onDone,
    onError,
    currentUser?.id || 'default_user'  // ← 关键
);
```

---

## 📍 文件改动位置速查

### 前端改动（只有删除，没有新增逻辑）
| 文件 | 行号 | 改动 |
|------|------|------|
| DashboardView.tsx | 3 | 移除 `PenTool` 导入 |
| DashboardView.tsx | 280 | 删除草图识别按钮 |
| OnboardingView.tsx | 3 | 移除 `PenTool` 导入 |
| OnboardingView.tsx | 23-30 | 从 steps 删除"智能草图识别" |
| App.tsx | 14 | 移除 `PenTool` 导入 |
| App.tsx | 698 | 用 `BookOpen` 替换 `PenTool` |

### 后端改动（只有 1 处修复）
| 文件 | 行号 | 改动 |
|------|------|------|
| llm_service.py | 160 | 添加 `context_str = ""` 初始化 |

---

## 🧪 快速验证方法

### 验证 1：删除草图识别
```bash
# 前端启动后，工作台底部应该看不到草图识别按钮
# 新手引导的步骤应该从 4 步变成 3 步
```

### 验证 2：对话历史裁剪
```bash
# 方法 1：进行 31 轮对话后，数据库应只保存 60 条
SELECT COUNT(*) FROM messages WHERE user_id = 'xxx';  -- 应该 = 60

# 方法 2：刷新工作台，应该看到最新的 30 轮对话
```

### 验证 3：知识库编辑
```bash
# 1. 上传资料
# 2. 编辑资料的名称、标签、内容
# 3. 刷新后应该显示编辑后的内容
```

### 验证 4：PPT 生成 + 知识库
```bash
# 1. 上传包含课题内容的知识库资料
# 2. 生成 PPT
# 3. 检查输出的 PPT 是否包含知识库的内容
```

---

## 🔌 API 调用示例

### 获取知识库
```bash
curl 'http://localhost:8000/api/knowledge?user_id=user123'
```

### 上传知识库
```bash
curl -X POST 'http://localhost:8000/api/knowledge/upload?user_id=user123' \
  -H 'Content-Type: application/json' \
  -d '{"name": "test.pdf", "type": "pdf", "size": "1.2MB", "tags": ["数学"], "content": "..."}'
```

### 生成课件
```bash
curl -X POST 'http://localhost:8000/api/coursewares/generate' \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "...", "history": [], "user_id": "user123"}'
```

---

## 💾 数据流图解

### 对话的知识库增强
```
用户输入课题
    ↓
[后端] 步骤 1：从知识库检索相关资料
       步骤 2：融入系统提示词
       步骤 3：调用 LLM 生成回复
    ↓
前端流式显示回复 + 知识库资料标记
```

### PPT 生成的知识库增强
```
用户触发"生成PPT"
    ↓
[后端] 步骤 1：再次从知识库检索
       步骤 2：构建带上下文的提示词
       步骤 3：调用 LLM 生成 JSON
       步骤 4：返回结构化课件
    ↓
前端接收 → 预览 → 导出
```

---

## 📋 配置要求

### 环境变量（后端）
```env
# .env 文件
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
LLM_API_KEY=your_api_key
LLM_API_BASE=https://api.deepseek.com/v1  # 或其他 OpenAI 兼容 API
LLM_MODEL=deepseek-chat
LLM_PROVIDER=openai  # 或 qianfan
```

### 前端配置
```typescript
// src/services/api.ts
const BASE_URL = 'http://localhost:8000/api';  // 修改为实际的后端地址
```

---

## 🎓 更新说明

### 新增功能
- ❌ 未添加新功能，只是优化现有功能和修复 bug

### 修改的功能
- ✅ PP T生成：现在支持知识库上下文
- ✅ 知识库管理：支持按账号隔离 + 编辑删除
- ✅ 对话历史：自动限制为 30 轮

### 移除的功能
- ❌ 草图识别界面（前端 UI 移除）

### Bug 修复
- 🔧 llm_service.py：修复 context_str 未初始化的问题

---

## 📞 常见问题

### Q: 为什么生成的 PPT 没有包含知识库内容？
**A:** 检查以下几点：
1. 知识库资料是否已上传（知识库界面应显示）
2. 后端日志中是否有"Trimmed X old messages"，说明数据库正常工作
3. 生成时知识库资料的关键词是否与生成的课题匹配

### Q: 对话历史为什么还是超过 30 轮？
**A:** 每条用户消息 + AI 回复 = 1 轮，所以 60 条消息 = 30 轮
- 30 轮对话记录 = 60 条消息记录

### Q: 如何自定义对话历史的轮数？
**A:** 修改 `supabase_client.py` 中的 `limit` 参数（默认 60）

### Q: 知识库为什么显示未读资料？
**A:** 刷新页面，或检查是否登录了不同账户

---

## 🚀 下一步建议

1. **集成向量数据库** - 升级 RAG 为向量相似度检索
2. **知识库分类** - 按学科、年级组织资料
3. **导出功能强化** - 支持更多格式（MD、HTML 等）
4. **多人协作** - 支持教师团队共享知识库
5. **生成历史** - 记录所有生成的 PPT，支持版本管理

---

**💡 技术栈：React + FastAPI + Supabase + DeepSeek LLM**  
**📅 实现时间：2026-03-26**  
**👤 维护者：GitHub Copilot**
