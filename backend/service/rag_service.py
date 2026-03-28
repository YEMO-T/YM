import os
import shutil
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    UnstructuredWordDocumentLoader, 
    UnstructuredPowerPointLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# 获取后端项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 核心文件夹路径定义
DATA_DIRS = {
    "data": os.path.join(BASE_DIR, "data"),                 # 教材/课标/优秀课件
    "template": os.path.join(BASE_DIR, "template"),         # 系统PPT模板
    "user_data": os.path.join(BASE_DIR, "user_data"),       # 用户上传文件
    "user_template": os.path.join(BASE_DIR, "user_template"), # 用户上传模板
}

# 2. 向量数据库存储目录
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

class RAGService:
    """
    教学备课智能体 RAG 核心服务类
    提供知识库构建、文件上传管理、向量检索功能
    """
    
    def __init__(self):
        # 初始化目录结构
        self._init_directories()
        
        # 初始化 Embedding 模型 (适配 m3e-base)
        # NOTE: 首次由 HuggingFace 自动下载，约 400MB，请保持网络连接
        self.embeddings = HuggingFaceEmbeddings(
            model_name="moka-ai/m3e-base",
            model_kwargs={'device': 'cpu'} # 若有 GPU 可改为 'cuda'
        )
        
        # 初始化向量数据库 (Chroma)
        self.vector_db = Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=self.embeddings
        )
        
        # 初始化文本分割器 (300字/块)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50, # 适当重叠保证语意连续
            length_function=len,
            add_start_index=True,
        )

    def _init_directories(self):
        """自动创建核心业务目录"""
        for folder_path in DATA_DIRS.values():
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"// NOTE: 已自动创建目录: {folder_path}")
        
        # 确保向量库目录存在
        if not os.path.exists(CHROMA_DB_DIR):
            os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    def _get_loader(self, file_path: str):
        """根据文件扩展名返回对应的加载器"""
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == '.pdf':
            return PyPDFLoader(file_path)
        elif ext == '.docx':
            return UnstructuredWordDocumentLoader(file_path)
        elif ext == '.pptx':
            return UnstructuredPowerPointLoader(file_path)
        elif ext == '.txt':
            return TextLoader(file_path, encoding='utf-8')
        else:
            print(f"// WARNING: 不支持的文件格式: {ext}")
            return None

    def build_knowledge_base(self):
        """
        核心函数 1: 重新构建向量库
        自动读取指定文件夹下的所有文件，提取内容并向量化存入 Chroma
        """
        all_documents = []
        
        for category, dir_path in DATA_DIRS.items():
            print(f"正在扫描目录: {category}...")
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    loader = self._get_loader(file_path)
                    if loader:
                        try:
                            # 1. 加载文件内容
                            docs = loader.load()
                            
                            # 2. 标题注入策略：将文件名作为标题注入到元数据中，并拼接到正文头部
                            title = os.path.splitext(filename)[0]
                            for doc in docs:
                                doc.metadata["title"] = title
                                doc.metadata["category"] = category
                                # FIXME: 注入标题以增强 RAG 索引的上下文关联
                                doc.page_content = f"标题：{title}\n内容：{doc.page_content}"
                            
                            all_documents.extend(docs)
                        except Exception as e:
                            print(f"// ERROR: 解析文件 {filename} 失败: {str(e)}")

        if not all_documents:
            print("// NOTE: 未在目录中发现可处理的文件。")
            return False

        # 3. 文本分块 (300字/块)
        split_chunks = self.text_splitter.split_documents(all_documents)
        
        # 4. 存入向量库
        # TODO: 这里可以使用 vector_db.delete_collection() 清空后再重建，实现“重新构建”
        self.vector_db.add_documents(split_chunks)
        print(f"// SUCCESS: 向量库重建完成，共处理 {len(all_documents)} 个文件，生成 {len(split_chunks)} 个知识块。")
        return True

    def upload_file(self, source_file_path: str, target_category: str) -> Optional[str]:
        """
        核心函数 2: 支持用户上传文件自动存入对应目录
        并动态完成向量化存入向量库
        
        :param source_file_path: 源文件路径 (如临时上传路径)
        :param target_category: 目标目录分类 (data, template, user_data, user_template)
        """
        if target_category not in DATA_DIRS:
            print(f"// ERROR: 目标目录分类 {target_category} 不存在。")
            return None
            
        filename = os.path.basename(source_file_path)
        dest_path = os.path.join(DATA_DIRS[target_category], filename)
        
        try:
            # 1. 存储文件
            shutil.copy2(source_file_path, dest_path)
            
            # 2. 实时向量化并更新到 Chroma
            loader = self._get_loader(dest_path)
            if loader:
                docs = loader.load()
                title = os.path.splitext(filename)[0]
                for doc in docs:
                    doc.metadata["title"] = title
                    doc.metadata["category"] = target_category
                    doc.page_content = f"标题：{title}\n内容：{doc.page_content}"
                
                chunks = self.text_splitter.split_documents(docs)
                self.vector_db.add_documents(chunks)
                print(f"// SUCCESS: 文件 {filename} 已存入 {target_category} 并同步更新向量库。")
                return dest_path
        except Exception as e:
            print(f"// ERROR: 上传处理失败: {str(e)}")
            
        return None

    def retrieve_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        核心函数 3: 向量检索
        默认返回 Top 5 最相关内容
        """
        # 检索 top_k 个最相似的块
        # 使用相似度得分（某些版本使用的是相似度，值越大越相关）
        results = self.vector_db.similarity_search_with_score(query, k=top_k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score) # 距离分数，越小越相关（针对 Chroma 默认 L2）
            })
            
        return formatted_results

# === 适配阿里云大模型模块 (需在 .env 配置文件中设置 DASHSCOPE_API_KEY) ===
def get_alicloud_llm():
    """
    获取适配阿里云通义千问的大模型对象
    用于后续 RAG 链条的问答生成
    """
    from langchain_community.llms import Tongyi
    import os
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("// WARNING: 未检测到 DASHSCOPE_API_KEY，请在 .env 中配置。")
        
    return Tongyi(dashscope_api_key=api_key)

# ---------------------------------------------------------
# 直接运行脚本进行快速验证
# ---------------------------------------------------------
if __name__ == "__main__":
    # 实例化服务 (会自动创建目录)
    rag = RAGService()
    
    print("\n--- RAG 知识库功能测试 ---")
    
    # 示例 1: 模拟构建知识库
    # rag.build_knowledge_base()
    
    # 示例 2: 检索测试
    # query = "如何进行小学语文备课？"
    # results = rag.retrieve_knowledge(query)
    # for i, res in enumerate(results):
    #     print(f"[{i+1}] 相关度: {res['score']}\n内容摘要: {res['content'][:100]}...\n")
