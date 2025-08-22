
# SearchAgent

一个基于 LangChain + SiliconFlow 的轻量级 Agent-RAG 框架。  
核心流程：用户问题 → 澄清 → 规划 → 检索 → 筛选 → 清洗 → 写作 → 最终回答。

---

## 安装

```bash
git clone https://github.com/AwczR/SearchAgent.git
cd SearchAgent

# 建议虚拟环境
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

需要在项目根目录放置 `.env` 文件(参考.env.example)，至少包含：

```env
SILICONFLOW_API_KEY=你的API密钥
TAVILY_API_KEY=你的API密钥   # 可选，启用网页检索
```

---

## 使用

### 方式一：快速交互

在```scripts/quickstart.py```中填写```query```：```query = "你的问题"```
```bash
python scripts/quickstart.py
```
程序会：
1. 询问问题
2. 给出澄清问题
3. 等待你的补充回答
4. 输出最终答案 + 来源链接

---

## 项目结构

```
app/         # 主代码：agents / retrievers / llm / storage
scripts/     # 启动脚本
data/        # 工作区数据持久化
```

---

## 特性

- **多Agent**：澄清、规划、筛选、清洗、写作
- **可扩展检索**：支持 Tavily Web API，本地向量库预留接口
- **引用来源**：最终回答自动附带参考链接
