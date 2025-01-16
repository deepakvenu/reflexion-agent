from typing import List
from dotenv import load_dotenv
import asyncio
load_dotenv()

from langchain_core.messages import BaseMessage
from langgraph.graph import END, MessageGraph
from chains import first_responder, revisor, request_parser, note_processor

MAX_ITERATIONS = 2

# Build the graph
builder = MessageGraph()

# Add nodes
builder.add_node("request", request_parser)
builder.add_node("notes", note_processor)
builder.add_node("draft", first_responder)
builder.add_node("revise", revisor)

# Add edges
builder.add_edge("request", "notes")
builder.add_edge("notes", "draft")
builder.add_edge("draft", "revise")

def should_continue(state: List[BaseMessage]) -> str:
    num_iterations = len(state) - 2
    if num_iterations >= MAX_ITERATIONS:
        return END
    return "revise"

# Add conditional edge from revise
builder.add_conditional_edges("revise", should_continue)
builder.set_entry_point("request")

# Compile the graph
graph = builder.compile()

# Example usage with async execution
async def main():
    cr_request = "Could you please analyse CRs MOLY97243503 and MOLY94819931"
    result = await graph.ainvoke(cr_request)
    print("\nFinal Summary:")
    print(result[-1].content)

if __name__ == "__main__":
    asyncio.run(main())
