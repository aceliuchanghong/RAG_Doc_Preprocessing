import os
import json
from parser import parse_book_to_tree
from analyzer import enrich_with_graph_and_raptor
from embedder import compute_kohaku_embeddings

def run_full_preprocessing_pipeline(file_path: str, book_title: str) -> list:
    """
    全流程整合管线：
    1. Parser 树状切分 + 时序编码
    2. Analyzer 分析提取 (GraphRAG 实体 + RAPTOR 摘要)
    3. Embedder 向量计算 (Kohaku 自下而上加权聚合)
    4. 组装输出符合 RAG-Challenge-2 标准的打平高密度 Payload 结构。
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"未找到目标书籍文件: {file_path}")
        
    # Step 1: 解析成四层语义树
    tree = parse_book_to_tree(file_path, book_title)
    
    # Step 2: 提取图谱实体与生成各级摘要
    enrich_with_graph_and_raptor(tree, use_llm_mock=True)
    
    # Step 3: 计算并自下而上级联聚合向量
    compute_kohaku_embeddings(tree, dimension=384)
    
    # Step 4: 【RAG-Challenge-2 风格】打平并打包高密度数据，准备写入向量数据库
    rag_payload_dataset = []
    
    print("正在打包最终的 RAG-Challenge-2 风格父子高密度数据结构...")
    for section in tree.sections:
        for paragraph in section.paragraphs:
            for sentence in paragraph.sentences:
                
                # 核心设计：每个子检索单元（句子）不仅有自己的特征，还冗余绑定了完整的父级上下文
                data_entry = {
                    "id": sentence.id,
                    "text": sentence.text,
                    "vector": sentence.embedding.tolist(), # 密集检索入口
                    "chronological_progress": sentence.progress, # 【新特性3】时序进度位置
                    "graph_entities": sentence.entities,         # 【新特性2】图谱实体标签
                    
                    # 父级及祖先上下文回溯索引（RAG-Challenge-2 与 RAPTOR 的核心支撑）
                    "context_metadata": {
                        "book_title": tree.title,
                        "section_title": section.title,
                        "section_summary": section.summary,
                        "section_summary_vector": section.summary_embedding.tolist() if section.summary_embedding is not None else [],
                        
                        "parent_paragraph_id": paragraph.id,
                        "parent_paragraph_text": paragraph.text,    # 召回句子时直接返回整段上下文
                        "parent_paragraph_summary": paragraph.summary, # RAPTOR 摘要
                        "parent_paragraph_summary_vector": paragraph.summary_embedding.tolist() if paragraph.summary_embedding is not None else []
                    }
                }
                rag_payload_dataset.append(data_entry)
                
    return rag_payload_dataset

if __name__ == "__main__":
    print("=========================================")
    print("=== 执行主工程完整管线测试 (Pipeline) ===")
    print("=========================================")
    
    # 1. 自动生成一本模拟的高维 book.txt 供系统运行
    mock_book_content = """==第一章 震动玄幻界==
大千世界，强者林立。林枫自幼在青云宗长大。
今天就是宗门大比的日子。所有弟子都聚集在中央大广场。
长老看了一眼林枫，摇了摇头，充满不屑。

==第二章 神秘古卷的认主==
深夜，林枫一个人来到后山寒潭清洗伤口。
突然，寒潭底部泛起万丈金光。一把刻满符文的古剑破空而出。
古剑化作流光直接没入林枫的额头。脑海中展现出一本金色的神秘古卷。
林枫狂喜：“这是我的逆天改命之机！”
"""
    book_filename = "book.txt"
    with open(book_filename, "w", encoding="utf-8") as f:
        f.write(mock_book_content)
    print(f"成功在当前目录下创建模拟书籍: '{book_filename}'")
    
    # 2. 跑通完整工程管道
    try:
        final_dataset = run_full_preprocessing_pipeline(book_filename, "太古神王林枫传")
        print("\n=========================================")
        print("🎉 恭喜！全套创新融合预处理管线运行成功！")
        print(f"生成最终可直接写入向量库的打平子单元(数据条数): {len(final_dataset)} 条")
        
        # 打印其中一条高密度 Payload 结构看效果
        sample_node = final_dataset[4] # 挑一条句子
        print("\n=== RAG-Challenge-2 高密度Payload样例展示 ===")
        print(f"子单元ID: {sample_node['id']}")
        print(f"子单元文本: {sample_node['text']}")
        print(f"时间线绝对进度(Progress): {sample_node['chronological_progress']:.4f}")
        print(f"GraphRAG实体识别: {sample_node['graph_entities']}")
        print(f"绑定的父级段落正文(Parent Context): {sample_node['context_metadata']['parent_paragraph_text']}")
        print(f"绑定的父级段落摘要(RAPTOR Summary): {sample_node['context_metadata']['parent_paragraph_summary']}")
        print(f"向量字段(Vector Length): {len(sample_node['vector'])} dimensions")
        print("=========================================")
        
        # 保存为 JSON 结果文件
        output_json = "rag_processed_output.json"
        with open(output_json, "w", encoding="utf-8") as jf:
            json.dump(final_dataset, jf, ensure_ascii=False, indent=2)
        print(f"最终高密度数据集已成功固化保存至: '{output_json}'")
        
    except Exception as e:
        print(f"管道运行失败，报错详情: {e}")
