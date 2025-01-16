from typing import Optional, List, Dict
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import json
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

@dataclass
class CRNotes:
    cr_id: str
    notes: List[str]
    status: str = "pending"  # pending, completed, failed

class CRNotesCollection:
    def __init__(self):
        self.cr_notes: List[CRNotes] = []

    def add_cr(self, cr_id: str, notes: List[str], status: str = "completed"):
        self.cr_notes.append(CRNotes(cr_id=cr_id, notes=notes, status=status))

    def to_dict(self) -> Dict:
        return {
            "cr_data": [
                {"cr_id": cr.cr_id, "notes": cr.notes, "status": cr.status}
                for cr in self.cr_notes
            ]
        }

class CRSummary(BaseModel):
    cr_id: str = Field(description="The MOLY ID of the CR being summarized")
    summary: str = Field(description="Detailed analysis of the CR notes")

class CRAnalysisResponse(BaseModel):
    summaries: List[CRSummary] = Field(description="List of CR summaries")    

async def fetch_notes_async(cr_id: str) -> Optional[CRNotes]:
    """Async version of fetch_notes"""
    try:
        with open('input_json/Updated_CR_data.json', 'r') as f:
            cr_data = json.load(f)
            
        for cr in cr_data:
            if cr['CR_ID'] == cr_id:
                return CRNotes(cr_id=cr_id, notes=cr['notes'], status="completed")
        return CRNotes(cr_id=cr_id, notes=[], status="failed")
    except Exception as e:
        print(f"Error reading CR data for {cr_id}: {e}")
        return CRNotes(cr_id=cr_id, notes=[], status="failed")

def request_parser(state: List[BaseMessage]) -> List[BaseMessage]:
    """Parse the initial request and identify CR IDs"""
    # Get the input text
    input_text = state[0].content
    
    # Find all MOLY IDs
    moly_ids = re.findall(r'MOLY\d+', input_text)
    
    # Create a structured message with the findings
    result_message = f"""
Original Request: {input_text}
Found CR IDs: {', '.join(moly_ids) if moly_ids else 'No CR IDs found'}
"""
    
    return state + [HumanMessage(content=result_message)]

async def note_processor(state: List[BaseMessage]) -> List[BaseMessage]:
    """Process multiple CR IDs in parallel and fetch their notes"""
    # Get the last message which should contain the CR IDs
    last_message = state[-1].content
    
    # Extract MOLY IDs using regex, but only from the "Found CR IDs:" line
    cr_line = re.search(r'Found CR IDs: (.*)', last_message)
    if cr_line:
        moly_ids = re.findall(r'MOLY\d+', cr_line.group(1))
    else:
        moly_ids = []
    
    # Create tasks for parallel execution
    tasks = [fetch_notes_async(moly_id) for moly_id in moly_ids]
    
    # Wait for all tasks to complete
    cr_results = await asyncio.gather(*tasks)
    
    # Collect results
    collection = CRNotesCollection()
    for result in cr_results:
        if result:
            collection.add_cr(result.cr_id, result.notes, result.status)
    
    # Convert to structured message
    return state + [HumanMessage(content=str(collection.to_dict()))]

def first_responder(state: List[BaseMessage]) -> List[BaseMessage]:
    """Generate initial response based on CR notes using structured output"""
    system_prompt = """You are an expert wireless systems researcher. 
    Analyze the CR data and provide summaries in a structured format.
    Your response MUST be valid JSON that matches the following Pydantic structure:

    {
        "summaries": [
            {
                "cr_id": "MOLY ID",
                "summary": "Detailed analysis"
            },
            ...
        ]
    }
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please analyze the following CR data and provide structured summaries: {state[-1].content}")
    ]
    
    # Use JSON mode to ensure structured output
    response = ChatOpenAI(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"}
    ).invoke(messages)
    
    try:
        # Parse the response into our Pydantic model
        analysis = CRAnalysisResponse.model_validate_json(response.content)
        
        # Format the response in the desired text format
        formatted_response = "\n\n".join([
            f"CR_ID: {summary.cr_id}\nSummary: {summary.summary}"
            for summary in analysis.summaries
        ])
        
        return state + [HumanMessage(content=formatted_response)]
    except Exception as e:
        print(f"Error parsing response: {e}")
        return state + [HumanMessage(content="Error: Failed to generate structured response")]

def revisor(state: List[BaseMessage]) -> List[BaseMessage]:
    """Revise and improve the previous response"""
    messages = [
        SystemMessage(content="You are an expert wireless systems researcher. Review and improve the previous analysis."),
        HumanMessage(content=f"Previous analysis: {state[-1].content}\nPlease provide an improved version.")
    ]
    
    response = ChatOpenAI(model="gpt-3.5-turbo-1106").invoke(messages)
    return state + [response]

# Create the tool
fetch_notes_tool = StructuredTool.from_function(
    func=fetch_notes_async,
    name="fetch_notes",
    description="Fetch notes for a given CR ID"
)
