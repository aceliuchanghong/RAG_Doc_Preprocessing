import json
import re
from typing import Any, Callable, List, Dict, Optional


def _replace_new_line(match: re.Match[str]) -> str:
    value = match.group(2)
    value = re.sub(r"\n", r"\\n", value)
    value = re.sub(r"\r", r"\\r", value)
    value = re.sub(r"\t", r"\\t", value)
    value = re.sub(r'(?<!\\)"', r"\"", value)

    return match.group(1) + value + match.group(3)


def _custom_parser(multiline_string: str) -> str:
    """
    用于对特殊字符进行预处理和修复。
    """
    # 如果输入是字节流，则解码为字符串
    if isinstance(multiline_string, (bytes, bytearray)):
        multiline_string = multiline_string.decode()

    # 将单引号形式的键转换为双引号形式（符合 JSON 标准）
    # 例如：'action': -> "action":
    multiline_string = re.sub(r"'(\w+)'\s*:", r'"\1":', multiline_string)

    # 将单引号形式的值转换为双引号形式
    # 例如：: 'search_query' -> : "search_query"
    multiline_string = re.sub(r":\s*'([^']*)'", r': "\1"', multiline_string)

    # 针对 "action_input" 字段内部的特殊内容进行处理
    # 使用 re.DOTALL 标志来匹配包括换行符在内的所有内容
    # 它会将匹配到的内容传递给 _replace_new_line 函数进行内部转义处理
    multiline_string = re.sub(
        r'("action_input"\:\s*")(.*?)(")',
        _replace_new_line,
        multiline_string,
        flags=re.DOTALL,
    )

    return multiline_string


def parse_partial_json(s: str, *, strict: bool = False) -> Any:
    """解析可能缺失闭合括号的 JSON 字符串。

    参数:
        s: 要解析的 JSON 字符串。
        strict: 是否使用严格模式解析。默认为 False。

    返回:
        解析后的 JSON 对象（通常为 Python 字典或列表）。
    """
    # 尝试直接按原样解析字符串
    try:
        return json.loads(s, strict=strict)
    except json.JSONDecodeError:
        # 如果解析失败，进入容错处理逻辑
        pass

    # 初始化变量
    new_chars = []  # 存储处理后的字符
    stack = []  # 栈：用于记录需要补全的闭合符号 (] 或 })
    is_inside_string = False  # 标记是否在字符串内部
    escaped = False  # 标记当前字符是否被转义

    # 逐个字符处理字符串
    for char in s:
        if is_inside_string:
            # 如果在字符串内部
            if char == '"' and not escaped:
                is_inside_string = False
            elif char == "\n" and not escaped:
                char = "\\n"  # 将原始换行符替换为转义序列，防止解析报错
            elif char == "\\":
                escaped = not escaped
            else:
                escaped = False
        else:
            # 如果在字符串外部
            if char == '"':
                is_inside_string = True
                escaped = False
            elif char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char == "}" or char == "]":
                # 如果遇到闭合符号，检查是否与栈顶匹配
                if stack and stack[-1] == char:
                    stack.pop()
                else:
                    # 闭合符号不匹配，说明输入格式严重错误
                    return None

        # 将处理后的字符添加到列表中
        new_chars.append(char)

    # 如果处理结束时仍处于字符串内部，需要补上引号
    if is_inside_string:
        new_chars.append('"')

    # 反转栈，以获取正确的闭合顺序
    stack.reverse()

    # 尝试不断修改字符串直到成功解析或字符被删光
    while new_chars:
        # 将当前已处理的字符与栈中剩余的闭合符号拼接
        try:
            return json.loads("".join(new_chars + stack), strict=strict)
        except json.JSONDecodeError:
            # 如果拼接后仍无法解析（例如末尾有冗余逗号或不完整的键值对），
            # 则移除最后一个字符并重试
            new_chars.pop()

    # 如果运行到这里说明完全无法解析，返回原始字符串的解析错误
    return json.loads(s, strict=strict)


_json_markdown_re = re.compile(r"```(json)?(.*)", re.DOTALL)


def parse_json_markdown(
    json_string: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    """从 Markdown 字符串中提取并解析 JSON 内容。

    参数:
        json_string: 包含 JSON 内容的 Markdown 字符串。
        parser: 用于执行解析的函数，默认为上文定义的 parse_partial_json。

    返回:
        解析后的 JSON 对象（通常为 Python 字典）。
    """
    try:
        # 首先尝试直接解析整个输入字符串
        return _parse_json(json_string, parser=parser)
    except json.JSONDecodeError:
        # 如果解析失败，说明字符串可能被 Markdown 的三反引号 (```) 包裹
        # 使用正则表达式寻找代码块内容
        # 提示：_json_markdown_re 通常匹配类似 ```json\n(.*?)\n``` 的结构
        match = _json_markdown_re.search(json_string)

        if match is None:
            # 如果没找到匹配的代码块，则退而求其次，假定整个字符串就是 JSON
            json_str = json_string
        else:
            # 如果匹配成功，提取代码块内部（第 2 个捕获组）的文本
            json_str = match.group(2)

    # 再次尝试对提取出的字符串进行解析
    return _parse_json(json_str, parser=parser)


_json_strip_chars = " \n\r\t`"


def _parse_json(
    json_str: str, *, parser: Callable[[str], Any] = parse_partial_json
) -> dict:
    # Strip whitespace, newlines, backtick from the start and end
    json_str = json_str.strip(_json_strip_chars)

    # 1. 尝试直接解析（Happy Path）
    # 如果 LLM 返回的是合法的 JSON，不要用正则去乱改它
    try:
        return parser(json_str)
    except Exception:
        # 如果解析失败，说明可能存在格式问题（如 Python 风格的单引号）
        pass

    # 2. 如果直接解析失败，再尝试使用自定义修复逻辑
    json_str = _custom_parser(json_str)

    # 3. 解析修复后的字符串
    return parser(json_str)


def parse_and_check_json_markdown(
    text: str, expected_keys: List[str] = ["is_real_time", "is_nsfw"]
) -> dict:
    """
    从 Markdown 字符串中解析 JSON，并验证其是否包含所有预期的键。

    参数:
        text: 包含 JSON 内容的 Markdown 原始字符串。
        expected_keys: 期望在 JSON 对象中存在的键列表。默认检查 ["is_real_time", "is_nsfw"]。

    返回:
        解析并校验通过后的 Python 字典。

    抛出:
        ValueError: 如果 JSON 格式非法，或者缺少任何一个预期的键。
    """
    try:
        # 调用之前定义的 parse_json_markdown 进行提取和初步解析
        json_obj = parse_json_markdown(text)
    except json.JSONDecodeError as e:
        # 如果解析阶段就报错，抛出包含原始文本的详细错误信息
        raise ValueError(f"获取到无效的 JSON 对象。原始文本: \n{text}, 错误信息: {e}")

    # 遍历检查每一个预期的键是否存在于解析后的字典中
    for key in expected_keys:
        if key not in json_obj:
            raise ValueError(
                f"获取到的返回对象无效。应包含键 `{key}`，"
                f"但实际得到的是: {json_obj}"
                f"。原始文本: \n{text}"
            )

    return json_obj


def parse_and_check_json_list(
    text: str, expected_keys: List[str]
) -> Optional[List[Dict[str, Any]]]:
    """
    从文本中提取 JSON 列表，支持去除尾随逗号，并验证每个 dict 包含 expected_keys。
    """
    # 匹配最外层的数组，从第一个 '[' 开始，到最后一个 ']' 结束
    bracket_stack = []
    start = -1
    for i, char in enumerate(text):
        if char == "[":
            if start == -1:
                start = i
            bracket_stack.append(char)
        elif char == "]":
            if bracket_stack:
                bracket_stack.pop()
                if not bracket_stack:  # 完全匹配
                    json_str = text[start : i + 1]
                    break
    else:
        print("Error: No balanced JSON list found in the text.")
        return None

    # 预处理：去除 JSON 中的尾随逗号（在 }, 后面或 ] 前的 ,）
    # 先去除空格/换行，再匹配
    def remove_trailing_commas(s: str) -> str:
        # 去除在 } 后面、] 前面的逗号，后面是空或空白+]
        s = re.sub(r",\s*(?=\])", "", s)  # ,[空格]]
        s = re.sub(r",\s*(?=\})", "", s)  # ,}
        return s

    cleaned_json_str = remove_trailing_commas(json_str)

    try:
        data = json.loads(cleaned_json_str)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON after cleaning. {e}")
        return None

    if not isinstance(data, list):
        print("Error: Extracted JSON is not a list.")
        return None

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            print(f"Error: Item at index {idx} is not a dictionary.")
            return None
        missing_keys = [key for key in expected_keys if key not in item]
        if missing_keys:
            print(f"Error: Item at index {idx} is missing keys: {missing_keys}")
            return None

    return data


if __name__ == "__main__":
    """
    uv run z_utils/get_json.py
    """

    text = """```json\n{"name":"张三", "age": 27, "爱好": ["羽毛球"""
    text2 = """
    {'translate_result': 'iPad 呢？'}
    """
    text3 = """
        ```json{
      "question": "合同里面SOB或者SOA编号是？格式是SOB20...",
      "answer": "SOB202102-14875"
    }``` 以上就是结果
        """
    text4 = """
    ca`sc
    [
        {"question": "我不太明白，为什么皇帝自己不处理那些奏折，全都丢给他呢？", "answer": "书里提到，皇帝似乎更专注于宏大的天道运行，将具体的日常政务交由宰相来处理，这是一种权力分工。"},
        {"question": "那些神仙听起来好像都在摸鱼，他们都不怕被惩罚吗？", "answer": "从文本来看，天庭似乎缺少严格的监督和惩罚体系，导致大家普遍工作不积极，所以他们看起来并不担心。"}
    ]
    f''c``s
    """
    text5 = """
    ca`sc
    [
        {"question": "我不太明白，为什么皇帝自己不处理那些奏折，全都丢给他呢？", "answer": ["书里提到", "皇帝似乎更专注于宏大的天道运行，将具体的日常政务交由宰相来处理，这是一种权力分工。"]},
        {"question": "那些神仙听起来好像都在摸鱼，他们都不怕被惩罚吗？", "answer": ["从文本来看", "天庭似乎缺少严格的监督和惩罚体系，导致大家普遍工作不积极，所以他们看起来并不担心。"]}
    ]
    f''c``s
    """
    xx = parse_json_markdown(text)
    print(xx)
    yy = parse_json_markdown(text2)
    print(f"{yy}")
    zz = parse_and_check_json_markdown(text3, ["question", "answer"])
    print(zz)
    aa = parse_and_check_json_list(text4, ["question", "answer"])
    print(aa)
    bb = parse_and_check_json_list(text5, ["question", "answer"])
    print(bb)
