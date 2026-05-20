import numpy as np
from typing import List, Dict, Any, Optional

class SentenceNode:
    def __init__(self, id: str, text: str, parent_id: str, progress: float):
        self.id = id
        self.text = text
        self.parent_id = parent_id
        self.progress = progress  # Chronological progress encoding [0.0, 1.0]
        self.entities: List[str] = []  # GraphRAG-Light: extracted entities
        self.embedding: Optional[np.ndarray] = None

    def __repr__(self):
        return f"SentenceNode(id={self.id}, progress={self.progress:.3f}, text={self.text[:15]}...)"

class ParagraphNode:
    def __init__(self, id: str, text: str, parent_id: str, progress: float):
        self.id = id
        self.text = text
        self.parent_id = parent_id
        self.progress = progress
        self.sentences: List[SentenceNode] = []
        self.summary: str = ""  # RAPTOR: Abstractive summary
        self.summary_embedding: Optional[np.ndarray] = None  # RAPTOR: Summary vector
        self.embedding: Optional[np.ndarray] = None         # Kohaku: Aggregated vector

    def __repr__(self):
        return f"ParagraphNode(id={self.id}, sentences_count={len(self.sentences)})"

class SectionNode:
    def __init__(self, id: str, title: str, parent_id: str, progress: float):
        self.id = id
        self.title = title
        self.parent_id = parent_id
        self.progress = progress
        self.paragraphs: List[ParagraphNode] = []
        self.summary: str = ""  # RAPTOR: Macro chapter summary
        self.summary_embedding: Optional[np.ndarray] = None
        self.embedding: Optional[np.ndarray] = None

    def __repr__(self):
        return f"SectionNode(id={self.id}, title={self.title}, paragraphs_count={len(self.paragraphs)})"

class DocumentNode:
    def __init__(self, id: str, title: str):
        self.id = id
        self.title = title
        self.sections: List[SectionNode] = []

    def __repr__(self):
        return f"DocumentNode(title={self.title}, sections_count={len(self.sections)})"

if __name__ == "__main__":
    print("=== 测试 models.py ===")
    doc = DocumentNode("doc_001", "测试书籍")
    sec = SectionNode("sec_001", "第一章 起源", doc.id, 0.0)
    para = ParagraphNode("para_001", "这是测试段落。", sec.id, 0.0)
    sent = SentenceNode("sent_001", "这是测试句子。", para.id, 0.0)
    
    para.sentences.append(sent)
    sec.paragraphs.append(para)
    doc.sections.append(sec)
    
    print(doc)
    print(doc.sections[0])
    print(doc.sections[0].paragraphs[0])
    print(doc.sections[0].paragraphs[0].sentences[0])
    print("Models 模块定义正确，测试通过！")
