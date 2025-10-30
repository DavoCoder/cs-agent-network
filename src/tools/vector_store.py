import os
from typing import List, Optional
from langchain_core.documents import Document

# Conditional imports - gracefully handle missing dependencies
try:
    from pinecone import Pinecone, ServerlessSpec
    from langchain_openai import OpenAIEmbeddings
    from langchain_pinecone import PineconeVectorStore
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False


class VectorStoreManager:
    """Manager for Pinecone vector store operations."""
    
    def __init__(
        self,
        index_name: str = "customer-support-kb",
        dimension: int = 1536
    ):
        """ Initialize the vector store manager. """
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone packages not installed. Install with: pip install pinecone-client langchain-pinecone")
        
        self.index_name = index_name
        self.dimension = dimension
        
        # Initialize Pinecone client
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.pinecone = Pinecone(api_key=api_key)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        
        # Initialize or get index
        self._setup_index()
        
        # Initialize vector store
        self.vector_store = PineconeVectorStore(
            index=self.index,
            embedding=self.embeddings
        )
    
    def _setup_index(self):
        """Create index if it doesn't exist, or get existing one."""
        if self.index_name not in [idx.name for idx in self.pinecone.list_indexes()]:
            # Create index if it doesn't exist
            self.pinecone.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"Created Pinecone index: {self.index_name}")
        
        self.index = self.pinecone.Index(self.index_name)
    
    def similarity_search(
        self,
        query: str,
        category: str,
        k: int = 3,
        metadata_filter: Optional[dict] = None
    ) -> List[Document]:
        """ Search for relevant documents using semantic search. """
        # Add category to metadata_filter
        search_filter = {"category": category}
        if metadata_filter:
            search_filter.update(metadata_filter)
        
        # Perform similarity search
        results = self.vector_store.similarity_search(
            query,
            k=k,
            filter=search_filter
        )
        
        return results
    
    def add_documents(
        self,
        documents: List[Document],
        category: str,
        metadata: Optional[dict] = None
    ):
        """ Add documents to the vector store. """
        # Add category metadata to each document
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata["category"] = category
            if metadata:
                doc.metadata.update(metadata)
        
        # Add to vector store
        self.vector_store.add_documents(documents)
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: List[dict],
        category: str
    ):
        """ Add texts directly to the vector store. """
        # Add category to each metadata
        for meta in metadatas:
            meta["category"] = category
        
        # Add to vector store
        self.vector_store.add_texts(texts, metadatas)


# Global instance
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store() -> Optional[VectorStoreManager]:
    """Get or create the global vector store manager instance."""
    global _vector_store_manager
    
    if not PINECONE_AVAILABLE:
        return None
    
    if _vector_store_manager is None:
        try:
            _vector_store_manager = VectorStoreManager()
        except Exception as e:
            print(f"Warning: Could not initialize vector store: {e}")
            return None
    
    return _vector_store_manager


def search_vector_kb(
    query: str,
    category: str,
    k: int = 3
) -> List[Document]:
    """ Search the vector knowledge base for relevant information. """
    vector_store = get_vector_store()
    if vector_store is None:
        return []
    return vector_store.similarity_search(query, category, k)


def retrieve_and_format_kb_results(query: str, category: str) -> Optional[str]:
    """ Retrieve knowledge base articles and format them for LLM context. """
    try:
        docs = search_vector_kb(query, category, k=3)
        
        if not docs:
            return None
        
        # Format retrieved documents
        formatted_results = "\n\n--- Knowledge Base Articles ---\n\n"
        for i, doc in enumerate(docs, 1):
            formatted_results += f"Article {i}:\n"
            formatted_results += f"Content: {doc.page_content}\n"
            if doc.metadata:
                formatted_results += f"Metadata: {doc.metadata}\n"
            formatted_results += "\n"
        
        return formatted_results
    
    except Exception as e:
        print(f"Error retrieving from vector KB: {e}")
        return None

