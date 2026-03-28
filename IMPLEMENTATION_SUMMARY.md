# 豆沙包教师助手 - 功能实现总结

## 📋 需求清单与完成状态

### ✅ 1. 大模型根据与用户的多轮对话与知识库生成PPT
**完成状态：已完成**

#### 后端实现
- 位置：`backend/service/llm_service.py`
- 核心功能：
  - `_build_retrieval_query()` - 构造多轮对话的检索查询
  - `_extract_keywords_cn()` - 中文关键词抽取（无需第三方分词）
  - `_score_knowledge_doc()` - 基于关键词命中计分
  - `_retrieve_top_k_knowledge()` - 检索Top 5相关资料
  - `_format_knowledge_context()` - 格式化知识库上下文
  - `chat_with_llm_stream()` - **RAG增强的流式对话**
  - `generate_courseware_data()` - **知识库感知的PPT生成**

- 修复项：
  - 修复 `chat_with_llm_stream()` 中 `context_str` 未初始化的bug

#### 前端实现
- 自动传递用户ID到后端
- 位置：`src/components/chat/DashboardView.tsx` 第155行
- 调用：`chatWithGeminiStream(..., currentUser?.id || 'default_user')`

#### 工作流程
```
用户输入课题 & 打开知识库
         ↓
后端自动检索相关资料
         ↓
LLM基于资料 + 对话历史回复
         ↓
触发"生成PPT"
         ↓
再次检索资料，并注入到生成提示词
         ↓
生成结构化PPT（8-10页，>1500字）
```

---

### ✅ 2. 工作台界面自动记录大模型与用户的对话，至多30轮
**完成状态：已完成**

#### 后端实现
- 位置：`backend/repository/supabase_client.py`
- 核心功能：
  - `insert_message()` - 保存消息并自动裁剪
  - `trim_messages(user_id, limit=60)` - 仅保留最新60条（30轮）
  - `get_messages(user_id, limit=60)` - 按时间正序返回最新60条
  
- 数据库表：`messages`
  - 字段：`id`, `user_id`, `role`, `content`, `type`, `file_info`, `created_at`
  - 自动删除超过60条的旧消息

#### 前端实现
- 位置：`src/components/chat/DashboardView.tsx` 第62-80行
- `useEffect` 组件挂载时加载历史记录
- 自动格式化数据库消息

#### API端点
- GET `/api/chat/history?user_id=<value>`
- 自动返回该用户最新的60条对话

---

### ✅ 3. 删除草图识别界面
**完成状态：已完成**

#### 修改明细

**文件 1：`src/components/chat/DashboardView.tsx`**
- 第3行：移除 `PenTool` 导入
- 第280行：删除 `<button onClick={() => setActiveTab('sketch')}>` 按钮

**文件 2：`src/components/auth/OnboardingView.tsx`**
- 第3行：移除 `PenTool` 导入
- 第23-30行：从 `steps` 数组移除第3步"智能草图识别"

**文件 3：`src/App.tsx`**
- 第14行：移除 `PenTool` 导入
- 第698行：用 `BookOpen` 替换课后作业的图标

#### 后端
- 不需要删除后端接口（前端已不调用）

---

### ✅ 4. 根据账号独立记录用户上传的资料，在知识库界面显示和自行删改
**完成状态：已完成**

#### 后端实现
- 位置：`backend/api/knowledge.py` & `backend/repository/supabase_client.py`

1. **获取资料** - GET `/api/knowledge?user_id=<value>`
   - 仅返回该用户的资料
   - `get_knowledge_items(user_id)` 使用 `.eq("user_id", user_id)` 进行隔离

2. **上传资料** - POST `/api/knowledge/upload?user_id=<value>`
   - 自动转换为 .txt 格式
   - 文件内容存储在 `content` 字段用于RAG检索

3. **删除资料** - DELETE `/api/knowledge/{item_id}?user_id=<value>`
   - 权限检验：只能删除自己的资料
   - `delete_knowledge_item(item_id, user_id)` 使用 `.eq("user_id", user_id)`

4. **编辑资料** - PUT `/api/knowledge/{item_id}?user_id=<value>`
   - 支持编辑：名称、标签、内容
   - 权限检验：只能编辑自己的资料

#### 前端实现
- 位置：`src/App.tsx` 中的 `KnowledgeBaseView` 组件（~560行）

1. **显示资料列表**
   - 表格展示用户已有的资料
   - 包含：文件名、大小、上传日期、标签、状态

2. **编辑功能**
   - 点击"编辑"进入编辑模式
   - 可修改：名称、标签、内容
   - 保存或取消按钮

3. **删除功能**
   - 点击删除显示确认对话
   - 确认后永久删除

4. **上传功能**
   - "上传资料"按钮打开文件选择器
   - 支持 PDF、DOCX 等格式（后端自动转txt）

#### 权限隔离说明
所有操作都通过数据库层的 `.eq("user_id", user_id)` 确保用户只能操作自己的资料：
```python
# 示例：删除权限检验
supabase.table("knowledge_items") \
    .delete() \
    .eq("id", item_id) \
    .eq("user_id", user_id)  # ← 权限检验
    .execute()
```

---

## 🔄 集成工作流程

### 对话 & PPT 生成完整流程

```
┌─ 用户登录 ─┐
│            │
└─→ 打开工作台
    ├─ 自动加载历史对话（最多30轮）
    ├─ 显示已上传的知识库资料
    │
    └─→ 用户输入课题
        │
        ├─ 后端自动检索相关知识库
        ├─ LLM 基于资料 + 历史对话生成回复
        └─ 前端流式显示回复
            │
            ├─ 如果包含 [READY_TO_GENERATE]
            │ └─→ 显示"开始生成PPT"按钮
            │
            └─→ 用户触发"生成PPT"
                ├─ 后端再次检索知识库
                ├─ LLM 生成结构化PPT（slides + lesson_plan + interaction）
                └─ 前端预览 & 导出 (PPTX/DOCX)
```

---

## 📊 数据库表结构

### `messages` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户ID（用于隔离） |
| role | TEXT | 'user' \| 'assistant' |
| content | TEXT | 对话内容 |
| type | TEXT | 'text' \| 'file' \| 'plan' |
| file_info | JSONB | 文件信息（可选） |
| created_at | TIMESTAMP | 创建时间 |

### `knowledge_items` 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户ID（用于隔离） |
| name | TEXT | 文件名 |
| type | TEXT | 文件类型（统一转为'txt'） |
| size | TEXT | 文件大小 |
| tags | JSONB | 标签数组 |
| content | TEXT | 文本内容（用于RAG检索） |
| status | TEXT | 'completed' \| 'syncing' |
| created_at | TIMESTAMP | 创建时间 |

---

## 🚀 API 端点参考

### 对话相关
- POST `/api/chat` - 流式对话（SSE）
- GET `/api/chat/history?user_id=<value>` - 获取历史对话

### 知识库相关
- GET `/api/knowledge?user_id=<value>` - 列表
- POST `/api/knowledge/upload?user_id=<value>` - 上传
- DELETE `/api/knowledge/{item_id}?user_id=<value>` - 删除
- PUT `/api/knowledge/{item_id}?user_id=<value>` - 编辑

### 课件生成
- POST `/api/coursewares/generate` - 生成PPT（已集成知识库）

---

## 💡 技术要点

### 1. RAG 检索策略
```python
retrieval_query = _build_retrieval_query(prompt, history, max_user_turns=3)
retrieved_docs = _retrieve_top_k_knowledge(knowledge_docs, retrieval_query, k=5)
```
- 基于关键词匹配，极轻量级（无需向量化）
- 检索最相关的 top 5 资料
- 自动注入LLM系统提示词

### 2. 对话历史管理
```python
trim_messages(user_id, limit=60)  # 仅保留最新60条（30轮）
```
- 每次保存消息时自动触发
- 防止数据库膨胀

### 3. 用户隔离
所有查询都包含 `.eq("user_id", user_id)` 确保数据安全

---

## ⚠️ 已知限制与后续优化

### 当前限制
1. RAG 使用关键词匹配，未来可升级为向量相似度
2. 知识库大小限制：建议单个资料 <10MB
3. 对话历史最多30轮（可配置）

### 后续优化建议
1. **向量化检索** - 使用 OpenAI Embeddings 或开源模型
2. **知识库分类** - 支持多分类标签
3. **多人协作** - 支持知识库共享
4. **高级PPT定制** - 自定义样式、模板
5. **RAG优化** - 支持多种数据源（网页、数据库等）

---

## 📝 测试检查清单

- [ ] 用户登录后，工作台自动加载历史对话
- [ ] 对话超过30轮后，自动删除最早的消息
- [ ] 知识库显示当前用户的全部资料
- [ ] 编辑资料名称、标签、内容后保存成功
- [ ] 删除资料后确认对话出现
- [ ] 上传新资料后自动出现在列表
- [ ] 生成PPT时，后端成功检索到相关知识库内容
- [ ] 生成的PPT包含知识库资料的内容

---

## 📞 支持与反馈

如有问题，请检查：
1. 后端是否正常启动：`http://localhost:8000/api/health`
2. Supabase 连接是否正确
3. LLM API Key 是否有效
4. 前端 BASE_URL 是否指向正确的后端地址

---

**最后更新：2026-03-26**
**实现者：GitHub Copilot**
