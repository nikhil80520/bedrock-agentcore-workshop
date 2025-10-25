# FAISS Vector Database Setup

## Overview

This project now uses **FAISS (Facebook AI Similarity Search)** instead of AWS Bedrock Knowledge Base for document retrieval. This change was made to avoid the S3 Vectors metadata size limitation (2048 bytes) that was causing ingestion failures.

## Benefits of Using FAISS

✅ **No metadata size limits** - Process documents of any size without restrictions  
✅ **Local storage** - Vector index stored locally, no S3 dependency  
✅ **Fast retrieval** - Efficient similarity search with FAISS  
✅ **Cost effective** - No AWS Knowledge Base or S3 Vectors costs  
✅ **Full control** - Complete control over chunking, embedding, and indexing  

## Architecture

```
Tax Documents (knowledge_base_data/)
    ↓
Text Splitting & Chunking (500 tokens, 50 overlap)
    ↓
AWS Bedrock Titan Embeddings (amazon.titan-embed-text-v1)
    ↓
FAISS Index (faiss_index/)
    ↓
Semantic Search & Retrieval
```

## Files Added

- **`lab_helpers/faiss_helper.py`** - FAISS vector store implementation
- **`lab_helpers/lab1_strands_agent_faiss.py`** - Updated agent tools using FAISS
- **`faiss_index/`** - Directory containing FAISS index and documents

## Installation

Install additional dependencies:

```bash
pip install faiss-cpu langchain langchain-community langchain-aws tiktoken
```

## Usage

### 1. Setup FAISS Database

```python
from lab_helpers.faiss_helper import setup_faiss_knowledge_base

# Create/load FAISS index from documents
vector_store = setup_faiss_knowledge_base(
    data_directory="knowledge_base_data",
    index_path="faiss_index",
    force_rebuild=True  # Set to False to reuse existing index
)
```

### 2. Search Documents

```python
# Search for relevant information
results = vector_store.search("tax brackets for 2024", k=3)

for result in results:
    print(f"Score: {result['score']}")
    print(f"Source: {result['metadata']['source']}")
    print(f"Text: {result['text']}")
```

### 3. Use with Agent

```python
from lab_helpers.lab1_strands_agent_faiss import (
    get_tax_policy,
    get_tax_information,
    get_tax_code_info,
    web_search,
    SYSTEM_PROMPT
)

# The get_tax_information tool automatically uses FAISS
response = agent("What are the 2024 tax brackets?")
```

## Configuration

### Chunking Parameters

Configured in `faiss_helper.py`:

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # Max tokens per chunk
    chunk_overlap=50,     # Overlap between chunks
    length_function=len,
)
```

### Search Parameters

```python
results = vector_store.search(
    query="your question",
    k=3  # Number of results to return
)
```

### Embedding Model

Uses **Amazon Titan Text Embeddings** via AWS Bedrock:

```python
BedrockEmbeddings(
    model_id="amazon.titan-embed-text-v1",
    region_name="us-west-2"
)
```

## Data Files

Documents in `knowledge_base_data/`:

- `00fcadbd_state-regulations.txt` - State tax regulations
- `bank-secrecy-act.txt` - Bank Secrecy Act documentation
- `irs-pub-55b.txt` - IRS Publication 55B
- `tax-brackets-2023.txt` - 2023 tax brackets
- `tax-brackets-2024.txt` - 2024 tax brackets
- `tax-brackets-2025.txt` - 2025 tax brackets

## Troubleshooting

### Index not found

```python
# Rebuild the index
vector_store = setup_faiss_knowledge_base(
    data_directory="knowledge_base_data",
    force_rebuild=True
)
```

### Poor search results

- Increase chunk size for more context
- Adjust overlap for better continuity
- Increase `k` parameter for more results
- Lower score threshold in `get_tax_information`

### AWS credentials

Ensure AWS credentials are configured for Bedrock embeddings:

```bash
aws configure
```

## Performance

- **Index creation**: ~30-60 seconds for 6 documents
- **Search latency**: <1 second per query
- **Index size**: ~5-10 MB for typical tax document set

## Migration from Bedrock Knowledge Base

The old Bedrock Knowledge Base cells can be safely removed or skipped:

- ❌ ~~Knowledge Base Sync Job~~
- ❌ ~~S3 metadata cleanup~~
- ✅ Use FAISS setup cells instead

## Future Enhancements

- Add document metadata filtering
- Implement hybrid search (keyword + semantic)
- Support for PDF documents
- Multi-language embeddings
- Persistent cache for embeddings

---

**Note**: FAISS index is local and not automatically backed up. Commit `faiss_index/` to version control or implement backup strategy for production use.
