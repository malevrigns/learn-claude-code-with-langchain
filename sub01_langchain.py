import os
import subprocess
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

load_dotenv(override=True)


systemPrompt = f"you are a coding agent at {os.getcwd()},use bash to solve task,and act ,do not explain anything about my question"

# 1. 使用 @tool 装饰器：LangChain 会自动通过函数的类型提示和文档字符串生成 JSON Schema，极大减少出错概率。
@tool
def run_bash(command: str) -> str:
    """run a bash command"""

    dangerous = ["rm -rf", "sudo", "shutdown", "reboot", "> /dev/"]

    if any(d in command for d in dangerous):
         return f"dangerous command:{command} was blocked"
    
    try:
        r = subprocess.run(command, shell=True, cwd=os.getcwd(), capture_output=True, text=True, timeout=120)
        output = (r.stdout + r.stderr).strip()
        return output if output else "{no output}"
    except subprocess.TimeoutExpired:
        return "{time out}"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}" 

# 将工具直接放入列表中
Tools = [run_bash]

def agent_loop(messages: list):
    llm = init_chat_model(
          model=os.getenv("OPENAI_MODEL_ID"),
          base_url=os.getenv("OPENAI_BASE_URL"),
          model_provider="openai",
          api_key=os.getenv("OPENAI_API_KEY"),
          max_tokens=8000 # 2. 修正拼写：max_token -> max_tokens
      )
    
    llm_with_tools = llm.bind_tools(Tools)

    if not messages or getattr(messages[0], "type", "") != "system":
        messages.insert(0, SystemMessage(content=systemPrompt))
    
    while True:
        response = llm_with_tools.invoke(messages)

        messages.append(response) 
        print(f"response:{response}")
        if not response.tool_calls:
            return
            
        for tool_call in response.tool_calls:
            print(tool_call)
            # 3. 工具名称匹配修复：因为用了 @tool，工具名称就是函数名 "run_bash"
            if tool_call["name"] == "run_bash":
                command = tool_call["args"]["command"]
                print(f"\033[33m$ {command}\033[0m") # 加个颜色让终端显示更好看
                
                # 直接调用工具函数
                output = run_bash.invoke({"command": command})
                print(output) 

                messages.append(
                    ToolMessage(
                        content=str(output),
                        tool_call_id=tool_call["id"], # 4. 修正拼写：tools_call_id -> tool_call_id
                        name=tool_call["name"]
                    )
                )  

            

if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
            
        # 5. 统一消息格式：不要混用字典 {"role": "user"} 和 LangChain 对象。
        # 这里统一转用 HumanMessage。
        history.append(HumanMessage(content=query))
        
        agent_loop(history)
        
        # 6. 正确读取并打印 AI 的最终回复
        last_message = history[-1]
        if isinstance(last_message, AIMessage) and last_message.content:
            print(last_message.content)
        print()