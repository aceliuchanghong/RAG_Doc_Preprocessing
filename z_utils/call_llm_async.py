import os
import sys
import asyncio

from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from tenacity import retry, wait_fixed, stop_after_attempt
from typing import List, Dict, Any, Union

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../")),
)

from z_utils.logging_config import get_logger
from z_utils.llm_factory import LLMFactory

load_dotenv()
logger = get_logger(__name__)


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
async def get_llm_response_async(
    messages: List[Dict[str, Any]], llm: Union[OpenAI, AsyncOpenAI, None] = None
):
    """
    异步获取 LLM 响应。
    传入 AsyncOpenAI 实例（直接 await）或 OpenAI 实例（通过线程池异步化执行）。
    """
    # 优先使用异步客户端
    if llm is None:
        try:
            llm = LLMFactory.get_async_llm()
        except AttributeError:
            llm = LLMFactory.get_llm()

    # 提取公共请求参数
    request_kwargs = {
        "model": os.getenv("MODEL", "gpt-3.5-turbo"),
        "messages": messages,
        "temperature": float(os.getenv("TEMPERATURE", 0.7)),
        "max_tokens": int(os.getenv("MAX_TOKENS", 4096)),
    }

    try:
        if isinstance(llm, AsyncOpenAI):
            response = await llm.chat.completions.create(**request_kwargs)
        elif isinstance(llm, OpenAI):
            logger.warning(
                "检测到传入的是同步 OpenAI 实例，已自动转换为线程池异步执行。"
            )
            response = await asyncio.to_thread(
                llm.chat.completions.create, **request_kwargs
            )
        else:
            raise TypeError("传入的 llm 实例类型无法识别，必须为 OpenAI 或 AsyncOpenAI")
        return response

    except Exception as e:
        logger.error(f"ERR: 异步模型调用异常: {str(e)}", exc_info=True)
        raise e


if __name__ == "__main__":
    """
    uv run z_utils/call_llm_async.py
    """
    system_messages = [{"role": "system", "content": "你叫 sisconsavior"}]
    input_messages = {"role": "user", "content": "hello,我是 llch,你是谁?"}

    full_messages = system_messages + [input_messages]

    async def main():
        result = await get_llm_response_async(full_messages)

        print(result.choices[0].message.content)

    asyncio.run(main())
