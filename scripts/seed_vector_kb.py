"""
Script to seed the Pinecone vector database with sample knowledge base articles.
Run this after setting up your Pinecone account and API key.

Run with: python -m src.scripts.seed_vector_kb
"""

import sys
import json
from pathlib import Path

# Add project root to path (same as LangGraph does)
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_core.documents import Document
from src.tools.vector_store import get_vector_store

load_dotenv()


def load_billing_documents():
    """Load billing documents from external JSON file."""
    script_dir = Path(__file__).parent
    data_file = script_dir / "data" / "billing_kb_documents.json"
    
    if not data_file.exists():
        raise FileNotFoundError(
            f"Billing documents file not found: {data_file}\n"
            f"Please ensure the data file exists."
        )
    
    with open(data_file, "r", encoding="utf-8") as f:
        documents_data = json.load(f)
    
    # Convert JSON data to Document objects
    documents = []
    for doc_data in documents_data:
        # Strip leading whitespace from page_content (from original formatting)
        page_content = doc_data["page_content"].strip()
        documents.append(
            Document(
                page_content=page_content,
                metadata=doc_data.get("metadata", {})
            )
        )
    
    return documents


def seed_billing_kb():
    """Seed billing knowledge base articles."""
    
    vector_store = get_vector_store()
    if vector_store is None:
        print("Vector store not available. Make sure Pinecone is configured.")
        return
    
    # Load billing documents from external file
    try:
        billing_docs = load_billing_documents()
    except FileNotFoundError as e:
        print(f"Error loading documents: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return
    
    # Add documents to vector store
    print("Adding billing documents to vector store...")
    vector_store.add_documents(billing_docs, category="billing")
    print(f"Added {len(billing_docs)} billing documents to the knowledge base.")
    
    print("\nBilling knowledge base seeded successfully!")
    print("\nSample queries to test:")
    print("- 'What are the pricing plans and API credit limits?'")
    print("- 'How do API credits work and when do I get charged overage?'")
    print("- 'Can I use the open source libraries without a paid subscription?'")
    print("- 'How do I cancel my subscription and can I get a refund?'")
    print("- 'My payment failed - what happens to my account?'")
    print("- 'How do I add team members to my Business plan?'")
    print("- 'What's the difference between free and paid features?'")


if __name__ == "__main__":
    print("Seeding Pinecone vector database with billing knowledge base...\n")
    try:
        seed_billing_kb()
    except Exception as e:
        print(f"Error seeding database: {e}")
        print("\nMake sure you have:")
        print("1. Set PINECONE_API_KEY in your environment")
        print("2. Installed dependencies: pip install pinecone-client langchain-pinecone")
        print("3. Created a .env file with your API key")

