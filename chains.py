from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

def first_responder(state: List[BaseMessage]) -> List[BaseMessage]:
    messages = [
        SystemMessage(content="You are an expert wireless systems researcher"),
        HumanMessage(content=f"Please summarize the following conversation concisely and professionally: {state[0].content}")
    ]
    
    response = ChatOpenAI(model="gpt-4").invoke(messages)
    return state + [response]

def revisor(state: List[BaseMessage]) -> List[BaseMessage]:
    # Get the last response
    last_response = state[-1].content
    
    messages = [
        SystemMessage(content="You are an expert wireless systems researcher. Your task is to improve the previous summary by making it more accurate, concise, and well-structured."),
        HumanMessage(content=f"""
        Previous summary: {last_response}

        Please revise this summary to:
        1. Be more concise and clear
        2. Better capture the key technical points
        3. Improve the overall structure and flow
        4. Ensure technical accuracy

        Provide the revised summary only.""")
    ]
    
    response = ChatOpenAI(model="gpt-4").invoke(messages)
    return state + [response]
