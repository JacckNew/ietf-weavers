![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
# 🧠 IETF Weavers

**Social and Discursive Dynamics of Internet Standard-making**

A high-performance analysis and visualization tool for understanding collaboration patterns, influence networks, and community dynamics within the Internet Engineering Task Force (IETF) through large-scale email communication analysis.

## 📋 Project Overview

IETF Weavers provides real-time social network analysis of IETF collaboration patterns, processing 345k+ emails to reveal how Internet standards are developed through human collaboration. The system features a modern FastAPI backend with SQLite database and an interactive D3.js frontend.

### Key Insights Revealed
- **Social Networks**: Collaboration patterns among Internet standard developers
- **Influence Patterns**: Key connectors and opinion leaders in technical communities  
- **Community Structure**: Working group boundaries and cross-pollination
- **Topic Evolution**: Technical discussion themes and their evolution over time
- **Knowledge Transfer**: Information flow and expertise sharing patterns

## 🎯 Current Features

### ⚡ **High-Performance Processing**
- **Fast Data Pipeline**: Process 345k emails in ~37 seconds (vs 10+ hours previously)
- **Intelligent Sampling**: Stratified sampling for representative network analysis
- **Optimized Algorithms**: LDA topic modeling for efficient large-scale processing

### 🖥️ **Modern Web Architecture**
- **FastAPI Backend**: RESTful API with auto-generated documentation
- **SQLite Database**: Indexed database with 540 nodes, 63 links, 15 topics  
- **D3.js Frontend**: Interactive network visualization with real-time filtering
- **Dual Data Sources**: Live API mode + static JSON fallback

### 🎛️ **Advanced Controls**
- **Server-side Filtering**: Efficient database queries for large datasets
- **Real-time Updates**: Instant visualization updates without page reloads
- **Flexible Parameters**: Filter by email count, degree centrality, community, topics
- **Visual Feedback**: Loading states, error handling, API status indicators

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation

1. **Clone and Setup**
   ```bash
   git clone https://github.com/JacckNew/ietf-weavers.git
   cd ietf-weavers
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On Linux/Mac
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the System

1. **Initialize the Network Database** (first time only)
   ```bash
   python scripts/create_network_db.py
   ```

2. **Start the API Backend**
   ```bash
   python -m uvicorn server.api:app --reload --port 8000
   ```

3. **Start the Frontend Server** (in a new terminal)
   ```bash
   cd visualisation
   python -m http.server 8080
   ```

4. **Access the Application**
   - Open http://localhost:8080 in your browser
   - The system will automatically detect if the API is available
   - Use the controls to filter and explore the network

## 🏗️ Project Structure

```
ietf-weavers/
├── server/                     # FastAPI backend
│   ├── api.py                 # Main API endpoints
│   └── __init__.py           
├── scripts/                    # Data processing scripts
│   ├── sql_fetch_ietf_data.py # Database manager
│   ├── fetch_ietf_data.py     # Data fetching
│   └── serve_visualization.py # Development server
├── src/                       # Core processing
│   ├── main.py               # Original processor
│   └── fast_main.py          # Optimized processor
├── agent/                     # Analysis modules
│   ├── data_acquisition.py   # Data fetching
│   ├── graph_builder.py      # Network construction
│   ├── topic_model.py        # Topic analysis
│   └── metrics.py            # Network metrics
├── visualisation/            # Frontend
│   ├── index.html           # Main visualization
│   ├── data.json           # Sample data
│   └── individual_features.csv
├── data/                    # Processed data files
│   ├── data.json           # Visualization data (fallback mode)
│   ├── ietf_large_sample.json # Sample data for development
│   └── *_tier*.json        # Large tier files (ignored by git)
├── cache/                   # Database and cache
│   ├── ietfdata.sqlite     # Raw IETF email data (9.02GB, ignored)
│   └── ietf_network.db     # Processed network database (0.12MB)
└── requirements.txt        # Python dependencies
```

## 📊 API Endpoints

The FastAPI backend provides the following endpoints:

- `GET /api/health` - Health check
- `GET /api/graph` - Get filtered graph data
  - Parameters: `limit`, `min_emails`, `min_degree`, `community`, `topic`
- `GET /api/stats` - Network statistics
- `GET /api/topics` - Topic information
- `GET /api/communities` - Community data

API documentation is available at http://localhost:8000/docs when the server is running.

## 🎨 Visualization Features

### Interactive Network Graph
- **Node Sizing**: By degree centrality, email count, or betweenness centrality
- **Node Coloring**: By community, mailing lists, or activity duration
- **Filtering**: Real-time filtering with immediate visual updates
- **Interactivity**: Drag nodes, zoom, pan, hover for details
- **Physics Simulation**: Force-directed layout with collision detection

### Advanced Controls
- **Data Source Selector**: Switch between API and static data
- **Filtering Sliders**: Min emails (0-100), Max nodes (50-1000), Degree threshold
- **Refresh Button**: Reload data with current filter settings
- **Status Indicators**: Visual API connection status

## 🔬 Data Processing

### Data Architecture
The system uses a **dual-format approach** for optimal performance and flexibility:

#### **Raw Data Sources**
- **`cache/ietfdata.sqlite`** (9.02GB): Complete IETF email archive from ietfdata library
- **Large JSON files** (`data/*_tier*.json`, 2.73GB): Processed tier data (local only)

#### **Production Data**  
- **`cache/ietf_network.db`** (0.12MB): Optimized network database for API queries
- **`data/data.json`** (25KB): Visualization data for fallback mode

#### **Development Data**
- **`data/ietf_large_sample.json`** (21KB): Sample dataset for testing

### Performance Optimizations
- **Stratified Sampling**: 2% sampling maintains network structure
- **Efficient Algorithms**: LDA instead of BERTopic for topic modeling
- **Database Indexing**: Optimized queries for filtering operations
- **Caching**: Smart data caching for repeated operations

### Analysis Capabilities
- **Network Metrics**: Degree, betweenness, closeness centrality
- **Community Detection**: Louvain algorithm for community identification
- **Topic Modeling**: LDA-based topic extraction and analysis
- **Temporal Analysis**: Activity duration and timeline analysis

## 📈 Performance Metrics

- **Processing Speed**: 345k emails → 37 seconds
- **Network Size**: 540 nodes, 63 links
- **Database**: SQLite with indexed queries
- **Memory Efficiency**: Optimized for large datasets
- **Response Time**: Sub-second API responses

## 🛠️ Development

### Database Management

```bash
# Create the network database from processed data
python scripts/create_network_db.py

# Initialize database with current data (alternative method)
python scripts/sql_fetch_ietf_data.py

# Run fast processing pipeline
python src/fast_main.py
```

### API Development
```bash
# Start with auto-reload
python -m uvicorn server.api:app --reload --port 8000

# Access interactive docs
# http://localhost:8000/docs
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📊 Status

**Current Status**: ✅ **FULLY FUNCTIONAL**

- **Backend**: FastAPI + SQLite database operational
- **Frontend**: Enhanced D3.js visualization with API integration
- **Data Pipeline**: Optimized processing for large datasets
- **Performance**: Production-ready with efficient filtering

**Architecture**: Backend (FastAPI + SQLite) ↔ Frontend (D3.js + Enhanced Controls)
