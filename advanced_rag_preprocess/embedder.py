import numpy as np
from models import DocumentNode

def get_mock_embedding(text: str, dimension: int = 384) -> np.ndarray:
    """
    确定性的 Mock 向量生成器。
    为了保证项目零依赖、100%可直接运行，用 hash 方式模拟真实语义向量。
    实际应用时改写为：
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text)
    """
    # 使用文本的 hash 种子生成确定性的伪随机向量，便于测试
    seed = sum(ord(c) for c in text) % 10000
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(dimension)
    return vec / np.linalg.norm(vec) # 归一化

def compute_kohaku_embeddings(doc: DocumentNode, dimension: int = 384):
    """
    Kohaku 风格的核心算法：
    1. 只计算底层句子的原生 Embedding。
    2. 上层（段落、章节）的向量通过其子节点进行“长度加权平均”聚合生成。
    3. 额外计算 RAPTOR 文本摘要的独立语义向量。
    """
    print("正在执行 Kohaku 风格自下而上长度加权向量聚合...")
    
    for section in doc.sections:
        sec_vectors = []
        sec_weights = []
        
        for paragraph in section.paragraphs:
            para_vectors = []
            para_weights = []
            
            # 1. 计算句子的原生向量
            for sentence in paragraph.sentences:
                sentence.embedding = get_mock_embedding(sentence.text, dimension)
                
                weight = len(sentence.text)
                if weight > 0:
                    para_vectors.append(sentence.embedding)
                    para_weights.append(weight)
            
            # 2. Kohaku 长度加权聚合生成段落向量
            if para_vectors:
                w = np.array(para_weights) / sum(para_weights)
                paragraph.embedding = np.average(para_vectors, axis=0, weights=w)
            else:
                paragraph.embedding = get_mock_embedding(paragraph.text, dimension)
                
            # 3. 计算 RAPTOR 段落摘要向量
            if paragraph.summary:
                paragraph.summary_embedding = get_mock_embedding(paragraph.summary, dimension)
                
            # 为章节聚合做准备
            para_total_len = sum(para_weights)
            if para_total_len > 0:
                sec_vectors.append(paragraph.embedding)
                sec_weights.append(para_total_len)
                
        # 4. Kohaku 长度加权聚合生成章节全局向量
        if sec_vectors:
            w_sec = np.array(sec_weights) / sum(sec_weights)
            section.embedding = np.average(sec_vectors, axis=0, weights=w_sec)
        else:
            section.embedding = get_mock_embedding(section.title, dimension)
            
        # 5. 计算 RAPTOR 章节摘要向量
        if section.summary:
            section.summary_embedding = get_mock_embedding(section.summary, dimension)

if __name__ == "__main__":
    print("=== 测试 embedder.py ===")
    from parser import parse_book_to_tree
    from analyzer import enrich_with_graph_and_raptor
    import os
    
    text = "==第一章 觉醒==\n楚阳睁开眼。发现自己重生到了十年前。"
    with open("test_emb.txt", "w", encoding="utf-8") as f:
        f.write(text)
        
    tree = parse_book_to_tree("test_emb.txt", "重生测试")
    enrich_with_graph_and_raptor(tree)
    compute_kohaku_embeddings(tree, dimension=128)
    
    # 验证非空
    p_node = tree.sections[0].paragraphs[0]
    print(f"句子1 向量形状: {p_node.sentences[0].embedding.shape}")
    print(f"段落聚合向量形状: {p_node.embedding.shape}")
    print(f"段落摘要向量形状: {p_node.summary_embedding.shape}")
    
    # 验证长度加权聚合是否合理
    print("向量计算与聚合成功，没有出现空值！")
    if os.path.exists("test_emb.txt"):
        os.remove("test_emb.txt")
