# learn-claude-code-with-langchain

这是一个基于 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) 的最小化 LangChain 重构实验。

上游项目强调一个核心观点：真正的 Agent 产品不是单纯的模型，也不是一堆提示词拼接，而是 `Model + Harness`。模型负责推理与决策，Harness 负责工具、观察、执行环境与权限控制。这个仓库保留这个思路，但把核心循环改写成 LangChain 风格，作为继续重构的起点。

当前版本还不是对上游仓库的完整移植，而是一个小而清晰、可直接运行的单文件原型，方便后续继续扩展。

## 项目目标

- 用 LangChain 重写一个最小可运行的 coding agent。
- 保留上游仓库“模型 + Harness”的设计思路。
- 使用 LangChain 的消息对象与工具调用机制，减少手写协议代码。
- 为后续拆分模块、补充工具、接入 LangGraph 做准备。

## 当前状态

当前实现只有一个核心脚本：[sub01_langchain.py](/home/shl/agents/learning/sub01_langchain.py)。

它已经具备以下能力：

- 通过 `python-dotenv` 加载环境变量
- 使用 `init_chat_model(...)` 初始化兼容 OpenAI 接口的聊天模型
- 通过 LangChain `@tool` 定义 `run_bash` 工具
- 支持模型反复调用工具，直到不再发出 tool call
- 使用 `HumanMessage`、`AIMessage`、`SystemMessage`、`ToolMessage` 维护对话历史

## 目录结构

```text
.
├── sub01_langchain.py
├── README.md
└── LICENSE
```

## 与上游仓库的对应关系

这个仓库没有照搬上游全部实现，而是把关键概念映射到了 LangChain：

| 上游思路 | 当前仓库中的 LangChain 实现 |
| --- | --- |
| Agent 主循环 | `agent_loop(messages)` |
| 系统提示词 | `SystemMessage(content=systemPrompt)` |
| 工具注册 | `Tools = [run_bash]` |
| 工具 Schema | `@tool` 装饰器 |
| 工具调用回写 | `llm.bind_tools(Tools)` + `ToolMessage` |
| 交互式命令行 | `__main__` 中的 REPL 循环 |

## `sub01_langchain.py` 做了什么

脚本的执行流程很直接：

1. 读取 `.env`
2. 构造 coding agent 的系统提示词
3. 定义一个 bash 工具 `run_bash(command: str)`
4. 初始化支持工具调用的聊天模型
5. 将用户输入追加到历史消息
6. 当模型发出工具调用时执行命令，并把结果作为 `ToolMessage` 回写
7. 当模型停止调用工具时输出最终回答

这个版本里的 `run_bash` 只做了很基础的危险命令拦截，仍然只是开发阶段原型，不应被视为真正的安全沙箱。

## 这个 LangChain 版本已经改进了什么

相对于更原始的手写工具调用逻辑，这个版本已经修正或优化了几个关键点：

- 使用 `@tool` 自动生成工具描述，减少 JSON Schema 手写错误
- 使用正确的 `max_tokens` 参数
- 工具名与 LangChain 注册名保持一致，即 `run_bash`
- `ToolMessage` 使用正确的 `tool_call_id`
- 消息历史统一为 LangChain 消息对象，避免字典与对象混用
- 工具调用结束后，能够正确读取并输出最终 `AIMessage`

## 安装

### 1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install langchain langchain-openai python-dotenv
```

## 环境变量

在项目根目录创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL_ID=your_model_name
OPENAI_BASE_URL=https://api.openai.com/v1
```

说明：

- `OPENAI_BASE_URL` 用于兼容 OpenAI 协议的模型服务，直连 OpenAI 时也可以按实际情况设置
- `OPENAI_MODEL_ID` 需要选择支持工具调用的模型

## 运行方式

```bash
python sub01_langchain.py
```

运行后在终端输入任务，例如：

```text
s01 >> 列出当前目录下的所有文件
```

退出方式：

- 输入 `q`
- 输入 `exit`
- 直接回车空行
- 按 `Ctrl+C`

## 适合做什么

- 学习 LangChain 工具调用的最小实现
- 快速搭一个命令行 coding agent 原型
- 作为把上游仓库迁移到 LangChain 的第一步
- 继续扩展成支持文件、Git、搜索、网络访问的多工具 Agent

## 当前局限

- 目前只有一个工具：`run_bash`
- 命令安全策略只是简单黑名单，不是真正的权限系统
- 没有文件读写工具、Git 工具、浏览器工具、网络工具
- 对话历史只保存在进程内存中
- 还没有测试
- 所有逻辑还集中在一个文件里
- 还没有 tracing、streaming、retry、人工审批等机制

## 下一步建议的重构方向

如果你准备继续把这个仓库往 LangChain 方向推进，建议优先做这些事：

1. 把单文件拆成 `config.py`、`agent.py`、`tools/bash.py`、`main.py`
2. 把危险命令黑名单改成更严格的 allowlist 或审批机制
3. 增加文件读取、文件写入、`git status`、`git diff`、代码搜索等工具
4. 给工具执行和消息循环补上单元测试
5. 接入日志或 LangSmith tracing，便于排查问题
6. 如果需要持久化状态、可中断执行、人工确认节点，可以进一步迁移到 LangGraph

## 为什么用 LangChain 重构

对于这个项目，LangChain 的价值主要在于：

- 工具定义更规范
- 消息类型更清晰
- 模型与工具调用接口更统一
- 后续扩展到更复杂工作流时成本更低

换句话说，这个仓库的目标不是用 LangChain “包装一下” 代码，而是用它把 Agent Harness 的结构整理得更清楚、更容易扩展。

## 致谢

灵感来源于上游项目：

- [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)

如果后续继续迁移更多能力，建议始终围绕上游仓库最核心的设计思想来做：重点不是堆 prompt，而是把模型真正放进一个可操作、可观察、可约束的 Harness 里。
