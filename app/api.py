from langchain.schema import BaseOutputParser
from langserve import add_routes
from fastapi import FastAPI
from typing import Dict, Any
import json
import os
from datetime import datetime
from .agents import create_rebalance_crew
from .tools import load_config

app = FastAPI(title="Shogun Rebalance Engine", version="1.0.0")

class RebalanceOutputParser(BaseOutputParser):
    """Parser for rebalance chain output"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse the output into structured format"""
        try:
            return json.loads(text)
        except:
            return {"error": "Failed to parse output", "raw_output": text}

def run_rebalance_workflow() -> Dict[str, Any]:
    """Execute the complete rebalance workflow"""
    try:
        # Create crew
        crew = create_rebalance_crew()
        
        # Get current allocations (mocked for now)
        current_allocations = {"strategyA": 0.5, "strategyB": 0.5}
        
        # Run the crew workflow
        result = crew.kickoff()
        
        # Compile results
        result = {
            "timestamp": str(datetime.now()),
            "current_allocations": current_allocations,
            "crew_result": result,
            "status": "completed"
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "timestamp": str(datetime.now())
        }

# Create the rebalance chain
rebalance_chain = run_rebalance_workflow

# Add routes
add_routes(
    app,
    rebalance_chain,
    path="/run-rebalance",
    input_type=Dict[str, Any],
    output_parser=RebalanceOutputParser()
)

@app.post("/run-rebalance")
def run():
    result = rebalance_chain.invoke({})
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "shogun-rebalance-engine",
        "version": "1.0.0"
    }

@app.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        config = load_config()
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 