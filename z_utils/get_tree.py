import argparse

from pathlib import Path
from fnmatch import fnmatch
from collections.abc import Iterable

DEFAULT_EXCLUDES = {
    ".git",
    ".vscode",
    "__pycache__",
    "node_modules",
    "*.pyc",
    "*.swp",
}


def read_gitignore(root: Path) -> set[str]:
    """
    读取根目录下的 .gitignore，返回忽略规则集合。
    注意：这里是 fnmatch 风格的简化支持，不是完整 gitignore 语法解析。
    """
    gitignore = root / ".gitignore"
    patterns = set()

    if not gitignore.is_file():
        return patterns

    with gitignore.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            patterns.add(line)

    return patterns


def is_excluded(path: Path, root: Path, patterns: Iterable[str]) -> bool:
    """
    判断某个路径是否需要被排除。

    支持：
    - 文件名匹配：node_modules、*.pyc
    - 相对路径匹配：src/cache/*
    - 目录规则：examples/
    """
    rel_path = path.relative_to(root).as_posix()
    name = path.name
    is_dir = path.is_dir()

    for pattern in patterns:
        pattern = pattern.strip().replace("\\", "/")

        if not pattern:
            continue

        dir_only = pattern.endswith("/")
        clean_pattern = pattern.rstrip("/")

        if dir_only and not is_dir:
            continue

        if "/" in clean_pattern:
            if fnmatch(rel_path, clean_pattern):
                return True
        else:
            if fnmatch(name, clean_pattern):
                return True

    return False


def generate_tree(
    startpath: str | Path,
    exclude_patterns: Iterable[str] | None = None,
    use_gitignore: bool = True,
) -> str:
    """
    生成目录树字符串。

    :param startpath: 要扫描的根目录
    :param exclude_patterns: 自定义排除规则
    :param use_gitignore: 是否读取根目录下的 .gitignore
    :return: 目录树字符串
    """
    root = Path(startpath).resolve()

    if not root.exists():
        raise FileNotFoundError(f"路径不存在: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"不是目录: {root}")

    patterns = set(DEFAULT_EXCLUDES)

    if exclude_patterns:
        patterns.update(exclude_patterns)

    if use_gitignore:
        patterns.update(read_gitignore(root))

    lines = [f"{root.name}/"]
    lines.extend(_build_tree(root, root, patterns))

    return "\n".join(lines)


def _build_tree(
    directory: Path,
    root: Path,
    patterns: set[str],
    prefix: str = "",
) -> list[str]:
    """
    递归构建目录树。
    """
    try:
        children = [
            child
            for child in directory.iterdir()
            if not is_excluded(child, root, patterns)
        ]
    except OSError as e:
        return [f"{prefix}└── [Error: {e}]"]

    # 文件在前，目录在后；同类按名称排序
    children.sort(key=lambda p: (p.is_dir(), p.name.lower()))

    lines = []

    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        display_name = f"{child.name}/" if child.is_dir() else child.name
        lines.append(f"{prefix}{connector}{display_name}")

        if child.is_dir():
            lines.extend(_build_tree(child, root, patterns, prefix + extension))

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成项目目录树，支持 .gitignore 和自定义排除规则。"
    )

    parser.add_argument(
        "-p",
        "--path",
        default=".",
        help="要生成目录树的根路径，默认是当前目录。",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        nargs="*",
        default=[],
        help="额外排除的文件或目录规则，例如: --exclude .env uv.lock dist/",
    )

    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="不读取 .gitignore 文件。",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    exclude_patterns = {
        ".env",
        ".gitignore",
        ".python-version",
        "pyproject.toml",
        "LICENSE",
        "uv.lock",
        "prompt.md",
        "package-lock.json",
        "node_modules",
        "z_using_files",
        "z_utils",
    }

    exclude_patterns.update(args.exclude)

    tree = generate_tree(
        startpath=args.path,
        exclude_patterns=exclude_patterns,
        use_gitignore=not args.no_gitignore,
    )

    print(tree)


if __name__ == "__main__":
    """
    uv run z_utils/get_tree.py --path ../qt_log/
    uv run z_utils/get_tree.py --path ../qt_log/verticle_domain/Skills/restaurant_ad_prompt_skill
    """
    main()
