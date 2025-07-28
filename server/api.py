"""
FastAPI server for IETF Weavers visualization backend.
Provides RESTful API endpoints for graph data, statistics, and filtering.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
import uvicorn

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.sql_fetch_ietf_data import IETFDatabaseManager

app = FastAPI(
    title="IETF Weavers API",
    description="API for IETF email network visualization",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (visualization frontend)
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visualisation")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Initialize database manager
db_manager = IETFDatabaseManager()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        db_manager.initialize_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

@app.get("/")
async def root():
    """Redirect to visualization."""
    return FileResponse(os.path.join(static_path, "index.html"))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "IETF Weavers API"}

@app.get("/api/graph")
async def get_graph(
    limit: int = Query(default=500, ge=1, le=2000, description="Maximum number of nodes"),
    min_degree: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum degree centrality"),
    min_emails: int = Query(default=0, ge=0, description="Minimum email count"),
    community: Optional[List[int]] = Query(default=None, description="Community IDs to filter by"),
    topic: Optional[int] = Query(default=None, description="Topic ID to filter by")
) -> Dict[str, Any]:
    """
    Get filtered graph data for visualization.
    
    Returns:
        Dict containing nodes and links arrays
    """
    try:
        graph_data = db_manager.get_filtered_graph(
            limit=limit,
            min_degree=min_degree,
            min_emails=min_emails,
            community=community,
            topic=topic
        )
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph data: {str(e)}")

@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get network statistics.
    
    Returns:
        Dict containing various network metrics and metadata
    """
    try:
        stats = db_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")

@app.get("/api/topics")
async def get_topics() -> List[Dict[str, Any]]:
    """
    Get topic analysis data.
    
    Returns:
        List of topics with words and top participants
    """
    try:
        topics = db_manager.get_topics()
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch topics: {str(e)}")

@app.get("/api/communities")
async def get_communities() -> List[Dict[str, Any]]:
    """
    Get community statistics.
    
    Returns:
        List of communities with size and average email metrics
    """
    try:
        communities = db_manager.get_communities()
        return communities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch communities: {str(e)}")

@app.post("/api/import")
async def import_data(
    json_path: str = Query(default="../visualisation/data.json", description="Path to data.json file")
) -> Dict[str, Any]:
    """
    Import data from JSON file into database.
    
    Returns:
        Import statistics and status
    """
    try:
        # Resolve relative path
        if not os.path.isabs(json_path):
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_path, json_path.lstrip("./"))
        
        result = db_manager.import_data_from_json(json_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import data: {str(e)}")

@app.get("/api/node/{node_id}")
async def get_node_details(node_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific node.
    
    Args:
        node_id: The ID of the node to fetch
        
    Returns:
        Node details including connections and metrics
    """
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # Get node details
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        node = cursor.fetchone()
        
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        node_dict = dict(node)
        
        # Get connections
        cursor.execute("""
            SELECT target as connected_node, weight 
            FROM links WHERE source = ?
            UNION
            SELECT source as connected_node, weight 
            FROM links WHERE target = ?
            ORDER BY weight DESC
        """, (node_id, node_id))
        
        connections = [dict(row) for row in cursor.fetchall()]
        node_dict["connections"] = connections
        
        db_manager.close()
        return node_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch node details: {str(e)}")

if __name__ == "__main__":
    # For development - run with uvicorn in production
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
