import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def register_documentation_resources(mcp):
    """
    Register documentation resources with the MCP server.
    
    Exposes llms.txt as an MCP resource for LLM to read and interpret directly.
    """

    llms_txt_path = Path(__file__).parent / "llms.txt"

    @mcp.resource("andes://docs/llms.txt")
    def get_llms_txt() -> str:
        """
        ANDES Documentation Index (llms.txt format)
        
        **IMPORTANT: When prompted to research ANDES, use documentation, explain 
        concepts, or answer questions about ANDES functionality, READ THIS RESOURCE 
        FIRST to discover relevant documentation URLs.**
        
        This resource provides the complete ANDES documentation index in llms.txt
        format, optimized for LLM interpretation. It includes:
        
        - Overview of ANDES and CURENT LTB
        - Getting Started guides with installation methods
        - Examples and tutorials with links
        - Model Reference categories (power system components)
        - API Reference structure
        - Development and modeling guides
        - Additional resources and citation info
        
        Workflow:
        1. Read this resource to explore the documentation structure
        2. Identify relevant documentation URLs for the user's question
        3. Use web search/fetch on those URLs to get detailed content
        4. Answer the user's question with authoritative information
        
        Format: Follows llmstxt.org standard with markdown formatting
        """
        try:
            if llms_txt_path.exists():
                return llms_txt_path.read_text(encoding='utf-8')
            else:
                logger.warning(f"llms.txt not found at {llms_txt_path}")
                return f"# ANDES Documentation\n\n> llms.txt file not found at: {llms_txt_path}\n\nPlease ensure the file exists in the andes/mcp/ directory."
        except Exception as e:
            logger.error(f"Error reading llms.txt: {e}")
            return f"# Error\n\nFailed to read llms.txt: {str(e)}"

