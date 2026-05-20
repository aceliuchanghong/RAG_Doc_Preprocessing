import os
import sys
import json
import threading
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../")),
)

from z_utils.logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)


class LLMFactory:
    # 存储同步和异步不同配置实例的字典
    _instances: Dict[str, OpenAI] = {}
    _async_instances: Dict[str, AsyncOpenAI] = {}  # 2. 增加异步缓存字典

    # 存储每个实例对应的默认生成参数
    _instance_configs: Dict[str, Dict[str, Any]] = {}
    # 线程锁
    _lock = threading.Lock()

    @classmethod
    def _build_config(cls, override_params: dict = None) -> dict:
        """抽取公共的配置构建逻辑"""
        override_params = override_params or {}
        return {
            "base_url": override_params.get("BASE_URL")
            or os.getenv("BASE_URL", "https://api.openai.com/v1"),
            "api_key": override_params.get("API_KEY") or os.getenv("API_KEY"),
            "timeout": float(
                override_params.get("TIMEOUT") or os.getenv("TIMEOUT", 60.0)
            ),
            "max_retries": int(
                override_params.get("MAX_RETRIES") or os.getenv("MAX_RETRIES", 3)
            ),
        }

    @classmethod
    def get_llm(cls, override_params: dict = None) -> OpenAI:
        """获取同步 LLM 实例"""
        config = cls._build_config(override_params)
        cache_key = json.dumps(config, sort_keys=True)

        if cache_key not in cls._instances:
            with cls._lock:
                if cache_key not in cls._instances:
                    logger.info(
                        f"正在创建新的 OpenAI 同步客户端实例，BASE_URL: {config['base_url']}"
                    )
                    client = OpenAI(
                        base_url=config["base_url"],
                        api_key=config["api_key"],
                        timeout=config["timeout"],
                        max_retries=config["max_retries"],
                    )
                    cls._instances[cache_key] = client
                    cls._instance_configs[cache_key] = config

        return cls._instances[cache_key]

    @classmethod
    def get_async_llm(cls, override_params: dict = None) -> AsyncOpenAI:
        """
        异步 LLM 实例的方法
        """
        config = cls._build_config(override_params)
        cache_key = json.dumps(config, sort_keys=True)

        if cache_key not in cls._async_instances:
            with cls._lock:
                if cache_key not in cls._async_instances:
                    logger.info(
                        f"正在创建新的 AsyncOpenAI 异步客户端实例，BASE_URL: {config['base_url']}"
                    )
                    # 初始化 AsyncOpenAI SDK 客户端
                    async_client = AsyncOpenAI(
                        base_url=config["base_url"],
                        api_key=config["api_key"],
                        timeout=config["timeout"],
                        max_retries=config["max_retries"],
                    )
                    cls._async_instances[cache_key] = async_client

        return cls._async_instances[cache_key]


if __name__ == "__main__":
    """
    uv run z_utils/llm_factory.py
    """
    llm_client0 = LLMFactory.get_async_llm()
    llm_client1 = LLMFactory.get_llm()

    # 测试通过参数覆盖加载
    custom_params = {"TIMEOUT": 120}
    llm_client2 = LLMFactory.get_llm(override_params=custom_params)

    # 测试相同的参数是否成功复用单例
    llm_client3 = LLMFactory.get_llm(override_params=custom_params)

    print(f"client0 编号: {id(llm_client0)}")
    print(f"client1 编号: {id(llm_client1)}")
    print(f"client1 和 client0 是否为同一实例: {llm_client0 is llm_client1}")
    print(f"client2 编号: {id(llm_client2)}")
    print(f"client1 和 client2 是否为同一实例: {llm_client2 is llm_client1}")
    print(f"client3 编号: {id(llm_client3)}")
    print(f"client2 和 client3 是否为同一实例: {llm_client2 is llm_client3}")
