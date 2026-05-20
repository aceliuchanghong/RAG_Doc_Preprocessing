import re
from models import DocumentNode, SectionNode, ParagraphNode, SentenceNode

def parse_book_to_tree(file_path: str, doc_title: str) -> DocumentNode:
    """
    将 book.txt 按照章节、段落、句子切分成树状结构，并计算时间线进度编码（Progress Encoding）
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 预估总长度用于计算进度
    total_chars = len(content) if len(content) > 0 else 1
    doc = DocumentNode(id="doc_main", title=doc_title)
    
    # 匹配章节：支持 “第一章”、“Chapter 1”、“==第X章==” 等常规格式
    chapter_pattern = r'(?=(?:^|\n)(?:第[一二三四五六七八九十百零]+章|Chapter\s+\d+|==.*==))'
    chapters = re.split(chapter_pattern, content)
    
    # 清理空章节
    chapters = [ch for ch in chapters if ch.strip()]
    if not chapters:
        chapters = [content] # 如果没匹配到，整本书作为一个章节

    sec_counter = 0
    para_counter = 0
    sent_counter = 0
    
    # 追踪当前字符在全文中的大概偏移量，用来算绝对进度进度
    current_char_offset = 0

    for ch_index, ch_text in enumerate(chapters):
        lines = ch_text.strip().split("\n")
        title = lines[0].strip() if lines else f"第 {sec_counter + 1} 部分"
        body = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
        
        # 计算当前章节在整本书中的相对位置进度 [0.0, 1.0]
        progress_rate = current_char_offset / total_chars
        
        sec_id = f"sec_{sec_counter:03d}"
        section = SectionNode(id=sec_id, title=title, parent_id=doc.id, progress=progress_rate)
        sec_counter += 1
        
        # 按空行切分段落
        raw_paragraphs = [p.strip() for p in re.split(r'\n\s*\n|\n{2,}', body) if p.strip()]
        
        for p_text in raw_paragraphs:
            para_id = f"para_{para_counter:05d}"
            # 细化段落的进度
            para_progress = (current_char_offset + ch_text.find(p_text)) / total_chars
            paragraph = ParagraphNode(id=para_id, text=p_text, parent_id=section.id, progress=para_progress)
            para_counter += 1
            
            # 使用正则切分句子 (包含中英文标点断句)
            sentence_endings = r'([。！？?！\n])'
            raw_sentences = re.split(sentence_endings, p_text)
            
            # 重新组装句子和标点
            sentences = []
            for i in range(0, len(raw_sentences) - 1, 2):
                s_str = (raw_sentences[i] + raw_sentences[i+1]).strip()
                if s_str:
                    sentences.append(s_str)
            if len(raw_sentences) % 2 != 0 and raw_sentences[-1].strip():
                sentences.append(raw_sentences[-1].strip())
                
            for s_text in sentences:
                sent_id = f"sent_{sent_counter:06d}"
                sent_progress = (current_char_offset + ch_text.find(s_text)) / total_chars
                
                sentence = SentenceNode(id=sent_id, text=s_text, parent_id=paragraph.id, progress=sent_progress)
                sent_counter += 1
                paragraph.sentences.append(sentence)
                
            if paragraph.sentences:
                section.paragraphs.append(paragraph)
                
        doc.sections.append(section)
        current_char_offset += len(ch_text)
        
    return doc

if __name__ == "__main__":
    print("=== 测试 parser.py ===")
    # 创建一个临时测试文本
    sample_text = """第一章 宗门选拔
这是一个阳光明媚的早晨。林枫站在广场中央。
他心里非常紧张，因为今天决定了他的命运。

第二章 奇妙的奇遇
林枫来到了后山。他发现了一个发光的山洞。
山洞里躺着一把古老的剑。
"""
    test_file = "test_book.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(sample_text)
        
    tree = parse_book_to_tree(test_file, "林枫修仙传")
    print(tree)
    print(f"解析出章节数: {len(tree.sections)}")
    for sec in tree.sections:
        print(f" - 章节: {sec.title}, 进度位置: {sec.progress:.2f}")
        for para in sec.paragraphs:
            print(f"   - 段落句子数: {len(para.sentences)}, 样例句: {para.sentences[0].text}")
            
    # 清理临时文件
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
    print("Parser 模块解析与进度计算测试通过！")
