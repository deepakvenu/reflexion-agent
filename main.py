from typing import List
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import BaseMessage
from langgraph.graph import END, MessageGraph
from chains import first_responder, revisor

MAX_ITERATIONS = 2

# Build the graph
builder = MessageGraph()

# Add nodes
builder.add_node("draft", first_responder)
builder.add_node("revise", revisor)

# Add edge from draft to revise
builder.add_edge("draft", "revise")

def should_continue(state: List[BaseMessage]) -> str:
    # Count number of revisions
    num_iterations = len(state) - 2  # Subtract initial message and first draft
    if num_iterations >= MAX_ITERATIONS:
        return END
    return "revise"

# Add conditional edge from revise
builder.add_conditional_edges("revise", should_continue)
builder.set_entry_point("draft")

# Compile the graph
graph = builder.compile()

# Optional: Generate visualization
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

# Example usage
conversation = """
User: What's the difference between 4G and 5G?
Expert: 5G is the fifth generation of cellular networks. The main differences are:
1. Speed: 5G is much faster, potentially reaching 20Gbps
2. Latency: 5G has much lower latency, around 1ms
3. Device density: 5G can handle many more connected devices
User: How does 5G achieve lower latency?
Expert: 5G achieves lower latency through several technologies:
- Network slicing
- Edge computing
- New radio architecture
- Improved signal processing
User: Could you explain network slicing?
Expert: Network slicing allows creating virtual networks (slices) on the same physical infrastructure. Each slice can be optimized for specific use cases, like one for IoT devices and another for high-speed mobile broadband.
"""

result = graph.invoke(conversation)
print("\nFinal Summary:")
print(result[-1].content)
