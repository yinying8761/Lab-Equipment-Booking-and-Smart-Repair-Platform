# RAG 模块位置说明

课程提交清单中的 `src/rag/`（RAG 管道）在本项目中作为**独立 AI 服务的一个子模块**实现，
源码位于：

```
src/ai-service/app/rag/
├── pipeline.py      # 检索 + 生成 + 证据不足判定 + 降级
├── store.py         # Chroma 向量库封装（写入 / 查询 / 删除 / 分片读取）
├── embeddings.py    # 字符 n-gram 哈希向量（离线可重建）
└── text.py          # txt/md/pdf/docx 解析与递归切分
```

对外接口由 `src/ai-service/app/main.py` 提供：`POST /rag/index`、`POST /rag/chat`、`POST /rag/delete`。
语料位于 `data/知识库/`，切分与检索参数见 `src/ai-service/app/config.py` 与 `config/ai-service.env.example`。

单独运行该子模块的方式见项目根目录 `README.md` 的「启动步骤」一节。
