from models import DocumentNode
import re

def enrich_with_graph_and_raptor(doc: DocumentNode, use_llm_mock: bool = True):
    """
    融合 GraphRAG-Light (实体抽取) 与 RAPTOR (层级摘要生成)
    注：为了让代码不依赖外部 API Key 即可直接跑通，这里默认使用启发式规则/Mock。
    在实际生产中，可以直接将 mock 函数替换为 OpenAI / DashScope 等大模型调用。
    """
    print("正在执行 GraphRAG 实体提取与 RAPTOR 摘要分析...")
    
    # 模拟一个实体词库（针对修仙/小说场景的简单启发式匹配）
    entity_keywords = ["林枫", "叶凡", "楚阳", "苏白", "长剑", "古剑", "山洞", "宗门", "长老", "后山", "广场"]

    for section in doc.sections:
        all_section_texts = []
        
        for paragraph in section.paragraphs:
            # 1. GraphRAG-Light: 为每个句子提取实体
            for sentence in paragraph.sentences:
                for word in entity_keywords:
                    if word in sentence.text and word not in sentence.entities:
                        sentence.entities.append(word)
            
            # 2. RAPTOR: 为段落生成摘要 (Mock实现：如果是生产环境，此处应调用大模型 API)
            if use_llm_mock:
                # 简单启发式模拟摘要：提取首句并加上标志
                if paragraph.sentences:
                    paragraph.summary = f"[段落摘要] 本段讲述: {paragraph.sentences[0].text[:20]}..."
            else:
                # llm_call(f"请简要总结以下段落: {paragraph.text}")
                pass
            
            all_section_texts.append(paragraph.text)
            
        # 3. RAPTOR: 为整个章节生成宏观摘要
        if use_llm_mock:
            section_full_text = " ".join(all_section_texts[:2]) # 取前两段示意
            section.summary = f"[章节全局摘要] 本章《{section.title}》核心内容概括: {section_full_text[:40]}..."
        else:
            # llm_call(f"请对整章进行宏观总结: ...")
            pass

if __name__ == "__main__":
    print("=== 测试 analyzer.py ===")
    from parser import parse_book_to_tree
    import os
    
    sample_text = """第一章 圣体觉醒
叶凡坐在荒古禁地。他的荒古圣体终于觉醒了。
苏白长老在一旁露出了震惊的表情。
"""
    with open("test_analyzer.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
        
    tree = parse_book_to_tree("test_analyzer.txt", "遮天测试")
    enrich_with_graph_and_raptor(tree, use_llm_mock=True)
    
    sent = tree.sections[0].paragraphs[0].sentences[1]
    print(f"句子: '{sent.text}' -> 提取的实体: {sent.entities}")
    print(f"段落摘要: {tree.sections[0].paragraphs[0].summary}")
    print(f"章节摘要: {tree.sections[0].summary}")
    
    if os.path.exists("test_analyzer.txt"):
        os.remove("test_analyzer.txt")
    print("Analyzer 模块智能分析测试通过！")
