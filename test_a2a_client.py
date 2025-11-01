"""Test script for A2A Administration Agent client."""
import asyncio
import os
import sys

# Add src to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.administration_tools import call_external_admin_a2a_agent

# Unwrap the tool to get the underlying function
if hasattr(call_external_admin_a2a_agent, 'func'):
    # LangChain tool wrapper
    test_function = call_external_admin_a2a_agent.func
elif hasattr(call_external_admin_a2a_agent, '__wrapped__'):
    # Standard functools.wraps
    test_function = call_external_admin_a2a_agent.__wrapped__
else:
    # Try to access the function directly from the module
    import src.tools.administration_tools as admin_tools_module
    test_function = admin_tools_module.call_external_admin_a2a_agent.func if hasattr(admin_tools_module.call_external_admin_a2a_agent, 'func') else None

# If we can't unwrap, create a direct implementation
if test_function is None:
    # Import the function implementation directly without the @tool decorator
    import importlib.util
    spec = importlib.util.spec_from_file_location("admin_tools", "src/tools/administration_tools.py")
    admin_tools_module = importlib.util.module_from_spec(spec)
    # Read and modify the source to remove @tool
    with open("src/tools/administration_tools.py", "r") as f:
        source = f.read()
    # Replace @tool with a comment
    modified_source = source.replace("@tool", "# @tool (removed for testing)")
    exec(compile(modified_source, "src/tools/administration_tools.py", "exec"), admin_tools_module.__dict__)
    test_function = admin_tools_module.call_external_admin_a2a_agent


async def test_client():
    """Test the A2A client with various queries."""
    
    # Set environment variables if not already set
    if not os.getenv("A2A_BASE_URL"):
        os.environ["A2A_BASE_URL"] = "http://localhost:9999"
    if not os.getenv("A2A_API_KEY"):
        # Optional, only needed for extended card
        os.environ["A2A_API_KEY"] = ""
    
    print("=" * 60)
    print("Testing A2A Administration Agent Client")
    print("=" * 60)
    print(f"A2A_BASE_URL: {os.getenv('A2A_BASE_URL')}")
    print(f"A2A_API_KEY: {'Set' if os.getenv('A2A_API_KEY') else 'Not set'}")
    print("=" * 60)
    print()
    
    # Test queries
    test_queries = [
        "I need to delete my account",
        "What permissions does the Developer role have?",
        "How do I add team members?",
        "I want to change my email address",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}: {query}")
        print(f"{'=' * 60}")
        
        try:
            # Use the underlying function
            if test_function:
                result = await test_function(query)
            else:
                # Fallback: use invoke method if it's a tool
                result = await call_external_admin_a2a_agent.invoke({"query": query})
            
            print("\n✅ Response received:")
            print("-" * 60)
            # If result is a dict, print it nicely, otherwise print as string
            if isinstance(result, dict):
                import json
                print(json.dumps(result, indent=2))
            else:
                print(result)
            print("-" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()


if __name__ == "__main__":
    asyncio.run(test_client())

