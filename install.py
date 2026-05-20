import os
from dotenv import load_dotenv
from termcolor import colored

from z_utils.logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)

if __name__ == "__main__":
    """
    如果安装缓慢:
    - linux
        export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
    - win
        $env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"

    修改 pyproject.toml 里面的 name
    cp .env.example .env
    uv run install.py
    nohup uv run install.py > no_git_oic/install.log 2>&1 &
    """
    # fmt: off
    os.makedirs("no_git_oic", exist_ok=True)
    logger.info(colored(f"Env install successfullly!", "green"))
    logger.info(colored("DEV_ENV" if os.getenv("DEV_ENV", "").lower() == "true" else "PROD_ENV", "green"))
    # fmt: on
