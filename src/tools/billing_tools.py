"""Billing-related tools for the agent network."""
from langchain_core.tools import tool
from src.tools.vector_store import retrieve_and_format_kb_results


@tool
def search_billing_kb(query: str) -> str:
    """Search billing knowledge base for relevant information."""
    result = retrieve_and_format_kb_results(query, "billing")
    return result if result else "No specific knowledge base articles found."