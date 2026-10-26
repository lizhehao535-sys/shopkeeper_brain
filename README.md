# shopkeeper_brain

面向设备 / 仪器说明书的知识库问答系统。把 PDF 手册转换成可检索的向量知识，再通过**商品名对齐 → 多路召回 → 融合精排 → 大模型生成**回答用户的产品使用问题。

---

## 功能特性

- **文档入库**：PDF 经 MinerU 解析为 Markdown，自动切块、识别商品名、生成混合向量并写入 Milvus
- **商品名对齐**：LLM 从用户口语中抽取商品名，经向量匹配 + 分数对齐，定位到知识库中的标准名称
- **三路召回**：向量检索 / HyDE 检索 / 联网搜索（MCP）并行执行
- **融合精排**：RRF 融合多路结果 → BGE-Reranker 精排 → 断崖截断
- **流式问答**：FastAPI + SSE，前端逐字返回
- **双 Web 页面**：文件上传页与对话页

---

## 架构

### 入库流水线

```
PDF ──> pdf_to_md ──> md_img ──> document_split ──> item_name_rec ──> bge_embedding ──> import_milvus
        MinerU解析     图片处理      文档切块          商品名识别        BGE-M3向量        写入Milvus
```

### 查询流水线

```
                    ┌──> search_embedding      向量检索 ──┐
item_name_confirm ──┼──> search_embedding_hyde HyDE检索 ──┼──> join ──> rrf ──> rerank ──> answer_output
                    └──> web_search_mcp        联网检索 ──┘                          (SSE流式返回)

        │
        └──> 有候选/无结果时直接返回追问 (answer_output)
```

三路检索**并行**执行，`join` 汇合后进入 RRF 融合。

---

## 目录结构

```
shopkeeper_brain/
├── knowledge/
│   ├── api/                    # 两个 FastAPI 应用入口
│   │   ├── import_router.py    # 入库服务 (localhost:8000)
│   │   └── query_router.py     # 查询服务 (localhost:8001)
│   ├── core/                   # 依赖注入与路径工具
│   ├── front/                  # 原生 HTML 前端
│   │   ├── import.html
│   │   └── chat.html
│   ├── processor/
│   │   ├── import_process/     # 入库 LangGraph 流程
│   │   │   ├── main_graph.py
│   │   │   └── nodes/
│   │   └── query_process/      # 查询 LangGraph 流程
│   │       ├── main_graph.py
│   │       ├── base.py         # 节点基类（日志/任务追踪/异常包装）
│   │       └── nodes/
│   ├── prompt/                 # 提示词模板
│   ├── schema/                 # 请求/响应模型
│   ├── service/                # 业务服务层
│   ├── utils/                  # Milvus / Mongo / MinIO / 向量 工具
│   ├── requirements.txt
│   └── .env                    # 本地配置（**不入库**）
└── README.md
```

---

## 技术栈

| 层 | 选型 |
|---|---|
| 流程编排 | LangGraph |
| 向量数据库 | Milvus（`dense_vector` COSINE + `sparse_vector` IP，`WeightedRanker` 融合） |
| 嵌入模型 | BGE-M3（稠密 + 稀疏双向量） |
| 精排模型 | bge-reranker-large |
| 大模型 | Qwen（DashScope OpenAI 兼容接口） |
| 文档解析 | MinerU |
| 会话存储 | MongoDB |
| 文件存储 | MinIO |
| Web 框架 | FastAPI + Uvicorn + SSE |
| 网页搜索 | 阿里云百炼 MCP（`bailian_web_search`） |

---

## 快速开始

### 1. 环境要求

- Python 3.12+
- Milvus 2.4+
- MongoDB
- MinIO

### 2. 安装依赖

```bash
cd knowledge
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

> ⚠️ 运行入库流程前**必须先激活虚拟环境**——`pdf_to_md.py` 中调用的是裸命令 `mineru`，依赖 PATH 能找到它。

### 3. 配置 `.env`

在 `knowledge/` 下创建 `.env`，主要变量：

| 变量 | 说明 |
|---|---|
| `DASHSCOPE_API_KEY` | 阿里云百炼 API Key |
| `OPENAI_API_BASE` | DashScope 兼容模式地址 |
| `LLM_DEFAULT_MODEL` | 默认对话模型 |
| `BGE_M3_PATH` / `BGE_M3_DEVICE` | BGE-M3 模型路径与推理设备 |
| `BGE_RERANKER_LARGE` | 精排模型路径 |
| `MILVUS_URL` | Milvus 地址 |
| `CHUNKS_COLLECTION` / `ITEM_NAME_COLLECTION` | 集合名 |
| `MONGO_URL` / `MONGO_DB_NAME` | 会话历史库 |
| `MINIO_ENDPOINT` / `MINIO_BUCKET_NAME` | 对象存储 |
| `MINERU_BASE_URL` / `MINERU_API_TOKEN` | MinerU 解析服务 |
| `MCP_DASHSCOPE_BASE_URL` | 联网搜索 MCP 地址 |

> 该文件已在 `.gitignore` 中排除，请勿提交。

### 4. 启动服务

```bash
# 入库服务
python knowledge/api/import_router.py     # http://localhost:8000

# 查询服务
python knowledge/api/query_router.py      # http://localhost:8001
```

### 5. 访问页面

| 页面 | 地址 |
|---|---|
| 文档上传 | http://localhost:8000/import.html |
| 对话问答 | http://localhost:8001/chat.html |

---

## 主要接口

### 入库服务（8000）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/import.html` | 上传页面 |
| POST | `/upload` | 上传文件，异步触发入库任务 |
| GET | `/status/{task_id}` | 查询任务状态 |

### 查询服务（8001）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/chat.html` | 对话页面 |
| POST | `/query` | 提交问题 |
| GET | `/stream/{task_id}` | SSE 流式获取回答 |
| GET | `/history/{session_id}` | 查询会话历史 |

---

## 关键实现说明

### 商品名对齐

用户口语（"苹果15"）与库中标准名（"Apple iPhone 15 128GB"）字面对不上，因此分三步：

1. **向量匹配**：BGE-M3 双向量混合检索，取 top5 候选
2. **分数对齐**：`≥0.7` 且唯一 / 完全同名 → 直接确认；`≥0.7` 有多个 → 候选；`0.6~0.7` → 候选；`<0.6` → 丢弃
3. **差异过滤**：多个确认结果中，与最高分差超过 `0.15` 的剔除

输出 `confirmed`（确定）与 `options`（候选），拿不准时反问用户而不是硬猜。

### 检索融合

两处融合用了不同算法：

| 层级 | 位置 | 算法 |
|---|---|---|
| 向量内部 | Milvus `WeightedRanker` | `0.5 × dense + 0.5 × sparse`（归一化后加权） |
| 多路结果 | `rrf.py` | `Σ weight / (60 + rank)`，只看名次不看分数 |

---

## 注意事项

- **联网搜索需要先在百炼 MCP 广场开通 WebSearch 服务**，否则会返回 `未开通该MCP或非可用开通状态`
- 文档入库依赖 MinerU，需确认 `mineru` 命令可用（激活 venv 后验证 `mineru --version`）
- `.env` 含密钥，已在 `.gitignore` 中排除

---

## License

[MIT](LICENSE)
