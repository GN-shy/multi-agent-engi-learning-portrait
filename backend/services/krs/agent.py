"""知识检索Agent —— 多路召回 + 重排序"""

import logging
from shared.schemas import KnowledgeChunk, RetrievalRequest, RetrievalResult, AgentException
from shared.config import settings

logger = logging.getLogger(__name__)

# 模拟知识库（MVP阶段使用内存存储，后续切换ChromaDB）
_MOCK_KNOWLEDGE_BASE: list[KnowledgeChunk] = [
    KnowledgeChunk(
        chunk_id="kb_001",
        document_id="doc_001",
        title="Python变量与数据类型",
        content="Python是动态类型语言，变量不需要声明类型。基本数据类型包括：整数(int)、浮点数(float)、字符串(str)、布尔值(bool)。Python使用赋值语句创建变量，如 x = 10。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_002",
        document_id="doc_001",
        title="Python控制流",
        content="Python使用if-elif-else进行条件判断，使用for和while进行循环。for循环常用于遍历序列(列表、元组、字符串)。range()函数生成整数序列。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_003",
        document_id="doc_001",
        title="Python函数定义",
        content="使用def关键字定义函数。Python函数支持位置参数、关键字参数、默认参数和可变参数(*args, **kwargs)。函数可以有返回值，使用return语句。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_004",
        document_id="doc_002",
        title="Python面向对象编程",
        content="Python支持面向对象编程。使用class关键字定义类。__init__方法是构造函数。类支持继承、多态。实例方法第一个参数必须是self。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_005",
        document_id="doc_002",
        title="Python装饰器",
        content="装饰器是Python的一种设计模式，用于在不修改原函数的情况下增加功能。本质是一个接受函数作为参数并返回新函数的高阶函数。常用@语法糖。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_006",
        document_id="doc_003",
        title="Python列表推导式",
        content="列表推导式是Python中创建列表的简洁方式。语法为 [expression for item in iterable if condition]。它比传统的for循环更高效、更Pythonic。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_007",
        document_id="doc_003",
        title="Python异常处理",
        content="Python使用try-except-finally处理异常。try块包含可能抛出异常的代码，except捕获特定异常，finally无论是否异常都会执行。可以使用raise抛出异常。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_008",
        document_id="doc_004",
        title="Python文件操作",
        content="使用open()函数打开文件。with语句可以自动管理文件资源。文件模式包括'r'(读)、'w'(写)、'a'(追加)、'rb'(二进制读)。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_009",
        document_id="doc_004",
        title="Python多线程与并发",
        content="Python的threading模块支持多线程编程。由于GIL的存在，CPU密集型任务推荐使用multiprocessing。IO密集型任务使用asyncio可以获得更好的性能。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_010",
        document_id="doc_005",
        title="Python常用标准库",
        content="Python标准库包含os(操作系统接口)、sys(系统参数)、json(JSON编解码)、re(正则表达式)、datetime(日期时间)、collections(容器数据类型)。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_011",
        document_id="doc_005",
        title="NumPy数组基础",
        content="NumPy是Python科学计算的基础库。ndarray是多维数组对象。支持向量化运算、广播机制。常用函数：np.array(), np.zeros(), np.arange(), np.reshape()。",
        domain="ai_python",
    ),
    KnowledgeChunk(
        chunk_id="kb_012",
        document_id="doc_006",
        title="Pandas数据处理",
        content="Pandas提供DataFrame和Series数据结构。支持数据读取(CSV/Excel/SQL)、数据清洗(缺失值处理)、数据聚合(groupby)、数据合并(merge/concat)。",
        domain="ai_python",
    ),
]


class KnowledgeRetrievalAgent:
    def __init__(self):
        self._knowledge_base = _MOCK_KNOWLEDGE_BASE

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """多路召回：向量检索(关键词模拟) + 关键词匹配，然后重排序。"""
        try:
            # 向量检索模拟：基于关键词匹配
            chunks_vector = self._vector_search(request.query, request.top_k)
            # 关键词检索：精确匹配
            chunks_keyword = self._keyword_search(request.query, request.top_k)
            # 重排序：合并去重 + 按画像适配度排序
            all_chunks = self._deduplicate_and_rerank(
                chunks_vector + chunks_keyword, request.learner_profile
            )
            logger.info(
                "知识检索完成: 查询='%s', 召回=%d条", request.query[:50], len(all_chunks[:request.top_k])
            )
            return RetrievalResult(
                chunks=all_chunks[:request.top_k],
                query_analysis={"query": request.query, "total_candidates": len(all_chunks)},
            )
        except Exception as e:
            logger.error("知识检索失败: %s", e, exc_info=True)
            raise AgentException("KRS", str(e))

    def _vector_search(self, query: str, top_k: int) -> list[KnowledgeChunk]:
        """模拟向量检索：基于关键词重叠度评分。"""
        query_words = set(query.lower().split())
        scored = []
        for chunk in self._knowledge_base:
            content_words = set(chunk.content.lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                chunk.similarity_score = min(overlap / max(len(query_words), 1), 1.0)
                scored.append(chunk)
        scored.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored[:top_k]

    def _keyword_search(self, query: str, top_k: int) -> list[KnowledgeChunk]:
        """模拟关键词检索：标题中包含关键词直接命中。"""
        query_lower = query.lower()
        hits = [
            c for c in self._knowledge_base
            if any(w in c.title.lower() or w in c.content.lower()[:50]
                   for w in query_lower.split() if len(w) >= 2)
        ]
        for c in hits:
            c.similarity_score = 0.9
        return hits[:top_k]

    def _deduplicate_and_rerank(
        self, chunks: list[KnowledgeChunk], profile
    ) -> list[KnowledgeChunk]:
        """去重并根据学情画像重排序。"""
        seen = set()
        unique = []
        for c in chunks:
            if c.chunk_id not in seen:
                seen.add(c.chunk_id)
                unique.append(c)
        # 按相似度排序（后续可加入画像适配度调整）
        unique.sort(key=lambda x: x.similarity_score, reverse=True)
        return unique


knowledge_retrieval_agent = KnowledgeRetrievalAgent()
