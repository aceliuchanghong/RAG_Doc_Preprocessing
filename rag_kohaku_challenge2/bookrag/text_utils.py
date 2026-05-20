from __future__ import annotations

import re

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_heading(line: str) -> bool:
    """Heuristic heading detector for plain book.txt / markdown."""
    line = line.strip()
    if not line or len(line) > 100:
        return False
    patterns = [
        r"^#{1,6}\s+.+$",
        r"^第[一二三四五六七八九十百千万0-9]+[章节卷回部篇].{0,70}$",
        r"^(Chapter|CHAPTER)\s+([0-9IVXLCDM]+|[A-Za-z]+).{0,70}$",
        r"^\d+(\.\d+){0,5}\s+\S.{0,70}$",
    ]
    return any(re.match(p, line) for p in patterns)


def split_sections(text: str) -> list[tuple[str, str]]:
    lines = normalize_text(text).splitlines()
    sections: list[tuple[str, list[str]]] = []
    title = "Front Matter"
    buf: list[str] = []
    seen_heading = False

    for line in lines:
        clean = line.strip()
        if is_heading(clean):
            if buf or seen_heading:
                sections.append((title, buf))
            title = re.sub(r"^#{1,6}\s+", "", clean).strip()
            buf = []
            seen_heading = True
        else:
            buf.append(line)

    if buf or not sections:
        sections.append((title, buf))

    result = []
    for t, body_lines in sections:
        body = "\n".join(body_lines).strip()
        if body:
            result.append((t, body))
    return result or [("Document", normalize_text(text))]


def join_lines_as_paragraph(block: str) -> str:
    lines = [x.strip() for x in block.splitlines() if x.strip()]
    if not lines:
        return ""
    # 中文书籍经常一行一句，直接拼接更自然；英文保留空格。
    cjk_ratio = len(CJK_RE.findall(block)) / max(1, len(block))
    return ("".join(lines) if cjk_ratio > 0.15 else " ".join(lines)).strip()


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # 简单句切。教学版：够用，但不是分词器级别。
    parts = re.findall(r".+?(?:[。！？!?\.]+|$)", text, flags=re.S)
    return [p.strip() for p in parts if p.strip()] or [text]


def pack_spans(units: list[str], max_chars: int) -> list[str]:
    spans: list[str] = []
    buf = ""
    for u in units:
        if len(buf) + len(u) > max_chars and buf:
            spans.append(buf.strip())
            buf = u
        else:
            sep = "" if CJK_RE.search(buf + u) else " "
            buf = (buf + sep + u).strip() if buf else u
    if buf.strip():
        spans.append(buf.strip())
    return spans


def split_paragraphs(section_text: str, max_chars: int = 1200) -> list[str]:
    blocks = re.split(r"\n\s*\n+", section_text)
    paragraphs: list[str] = []
    for block in blocks:
        p = join_lines_as_paragraph(block)
        if not p:
            continue
        if len(p) <= max_chars:
            paragraphs.append(p)
        else:
            paragraphs.extend(pack_spans(split_sentences(p), max_chars=max_chars))
    return paragraphs


def split_sentence_spans(paragraph: str, max_chars: int = 320) -> list[str]:
    return pack_spans(split_sentences(paragraph), max_chars=max_chars) or [paragraph]


def bm25_tokenize(text: str) -> list[str]:
    # 中文按字，英文数字按词。对于教学版足够；生产可换 jieba / tantivy / elasticsearch。
    return re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9_\-]+", text.lower())


def main() -> None:
    sample = """
# 第一章 检索
这是第一段。它介绍向量检索。它还介绍BM25。

这是第二段，包含 parent retrieval 的思想。

第二章 图谱
GraphRAG 会抽取实体和关系。
"""
    print("Sections:")
    for title, body in split_sections(sample):
        print("TITLE:", title)
        print("PARAS:", split_paragraphs(body))
    print("Tokens:", bm25_tokenize("GraphRAG 与 向量检索 vector-search"))


if __name__ == "__main__":
    main()
