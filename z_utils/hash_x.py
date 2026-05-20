import hashlib
import uuid

from hashlib import md5
from datetime import datetime


def timestamp_now() -> int:
    return int(datetime.now().timestamp() * 1000)


def compute_mdhash_id(content, prefix: str = ""):
    return prefix + md5(content.encode()).hexdigest()


def convert_md5_hash(input_str: str) -> str:
    try:
        salt = str(uuid.uuid4())
        combined_input = input_str + salt

        # 创建 MD5 对象并进行哈希
        md5_obj = hashlib.md5()
        md5_obj.update(combined_input.encode("utf-8"))

        # 获取 16 进制表示的字符串 (32位)
        return md5_obj.hexdigest()

    except Exception as e:
        print(f"Error generating MD5 hash: {e}")
        return input_str


if __name__ == "__main__":
    """
    uv run z_utils/hash_x.py
    """
    from datetime import datetime

    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(convert_md5_hash(f"hello lch,{current_time_str}"))
