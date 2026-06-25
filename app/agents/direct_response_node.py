from google.adk.workflow import node

@node
def direct_response_node(node_input: str) -> str:
    """A simple pass-through node for direct responses to gracefully terminate the branch."""
    return node_input
