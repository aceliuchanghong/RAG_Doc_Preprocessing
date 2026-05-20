import os
import sys

from langfuse import Langfuse
from dotenv import load_dotenv

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../")),
)

from z_utils.logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)

_langfuse_client = None


def get_langfuse_client():
    # 从环境变量读取配置
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    global _langfuse_client
    if _langfuse_client is None:
        try:
            _langfuse_client = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
            )
            logger.info(f"Langfuse tracing enabled, host={langfuse_host}")
            return _langfuse_client
        except Exception as e:
            logger.warning(f"Langfuse init failed, continue without tracing: {e}")
            _langfuse_client = None
    else:
        return _langfuse_client


langfuse_client = get_langfuse_client()
