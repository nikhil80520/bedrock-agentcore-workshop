"""
FAISS Vector Database Helper for Tax Documents
Handles document loading, chunking, embedding, and retrieval using FAISS
"""

import os
import pickle
from typing import List, Dict
import faiss
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
import boto3


class FAISSVectorStore:
    """Local FAISS vector store for tax regulation documents"""
    
    def __init__(self, index_path: str = "faiss_index", region: str = "us-west-2"):
        """
        Initialize FAISS vector store
        
        Args:
            index_path: Path to save/load FAISS index
            region: AWS region for Bedrock embeddings
        """
        self.index_path = index_path
        self.region = region
        self.index = None
        self.documents = []
        self.embeddings_model = None
        
    def _initialize_embeddings(self):
        """Initialize Bedrock embeddings model"""
        if self.embeddings_model is None:
            self.embeddings_model = BedrockEmbeddings(
                model_id="amazon.titan-embed-text-v1",
                region_name=self.region
            )
        return self.embeddings_model
    
    def load_documents_from_directory(self, directory: str) -> List[Dict]:
        """
        Load and chunk documents from directory
        
        Args:
            directory: Path to directory containing text files
            
        Returns:
            List of document chunks with metadata
        """
        documents = []
        
        # Text splitter for chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        
        # Load all .txt files
        for filename in os.listdir(directory):
            if filename.endswith('.txt'):
                filepath = os.path.join(directory, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split into chunks
                    chunks = text_splitter.split_text(content)
                    
                    # Create document objects
                    for i, chunk in enumerate(chunks):
                        documents.append({
                            'text': chunk,
                            'metadata': {
                                'source': filename,
                                'chunk_id': i,
                                'total_chunks': len(chunks)
                            }
                        })
                    
                    print(f"✅ Loaded {len(chunks)} chunks from {filename}")
                    
                except Exception as e:
                    print(f"⚠️ Error loading {filename}: {e}")
        
        print(f"\n📄 Total documents loaded: {len(documents)}")
        return documents
    
    def create_index(self, documents: List[Dict]):
        """
        Create FAISS index from documents
        
        Args:
            documents: List of document chunks with metadata
        """
        print("🔄 Creating embeddings...")
        embeddings_model = self._initialize_embeddings()
        
        # Extract texts
        texts = [doc['text'] for doc in documents]
        
        # Generate embeddings
        embeddings = embeddings_model.embed_documents(texts)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        # Store documents
        self.documents = documents
        
        print(f"✅ FAISS index created with {len(documents)} vectors")
    
    def save_index(self):
        """Save FAISS index and documents to disk"""
        os.makedirs(self.index_path, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, os.path.join(self.index_path, 'index.faiss'))
        
        # Save documents
        with open(os.path.join(self.index_path, 'documents.pkl'), 'wb') as f:
            pickle.dump(self.documents, f)
        
        print(f"✅ Index saved to {self.index_path}")
    
    def load_index(self):
        """Load FAISS index and documents from disk"""
        index_file = os.path.join(self.index_path, 'index.faiss')
        docs_file = os.path.join(self.index_path, 'documents.pkl')
        
        if not os.path.exists(index_file) or not os.path.exists(docs_file):
            raise FileNotFoundError(f"Index not found at {self.index_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(index_file)
        
        # Load documents
        with open(docs_file, 'rb') as f:
            self.documents = pickle.load(f)
        
        print(f"✅ Index loaded from {self.index_path} ({len(self.documents)} documents)")
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with scores
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() or create_index() first.")
        
        # Generate query embedding
        embeddings_model = self._initialize_embeddings()
        query_embedding = embeddings_model.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['score'] = float(1 / (1 + distances[0][i]))  # Convert distance to similarity score
                results.append(doc)
        
        return results


def setup_faiss_knowledge_base(data_directory: str, index_path: str = "faiss_index", force_rebuild: bool = False) -> FAISSVectorStore:
    """
    Setup or load FAISS knowledge base
    
    Args:
        data_directory: Directory containing text documents
        index_path: Path to save/load index
        force_rebuild: Force rebuild even if index exists
        
    Returns:
        Initialized FAISSVectorStore
    """
    vector_store = FAISSVectorStore(index_path=index_path)
    
    # Check if index exists
    index_exists = os.path.exists(os.path.join(index_path, 'index.faiss'))
    
    if index_exists and not force_rebuild:
        print("📂 Loading existing FAISS index...")
        vector_store.load_index()
    else:
        print("🔨 Building new FAISS index...")
        documents = vector_store.load_documents_from_directory(data_directory)
        vector_store.create_index(documents)
        vector_store.save_index()
    
    return vector_store
