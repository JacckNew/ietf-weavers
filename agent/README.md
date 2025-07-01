# IETF Weavers Agent

This directory contains the backend logic for the IETF Weavers project - an AI-driven processing engine for analyzing social and discursive dynamics in IETF email communications.

## Architecture

The agent follows a modular design with specialized components for each phase of the analysis pipeline:

### Core Modules

#### `utils.py` - Email parsing, NER, and cleaning
- **EmailParser**: Normalizes email addresses and classifies email types (automated, role-based, individual)
- **PersonIdentityResolver**: Multi-step identity linking process following methodology
- **ThreadAnalyzer**: Email thread reconstruction and interaction extraction
- **Text Cleaning**: Utilities for cleaning email content

Key Features:
- Email address normalization and validation  
- Automated email detection using pattern matching
- Person identity resolution across multiple email addresses
- Thread structure analysis for interaction mapping

#### `graph_builder.py` - Social graph construction
- **SocialGraphBuilder**: Builds directed social graphs from email interactions
- **Multi-layer Networks**: Creates different network types (reply, co-participation)
- **Temporal Tracking**: Monitors participation patterns over time

Key Features:
- Directed graph construction with nodes as participants, edges as interactions
- Reply relationship inference from email thread analysis
- Co-participation network based on shared mailing list activity
- Temporal activity tracking and duration calculations

#### `metrics.py` - Network analysis and centrality calculation
- **NetworkMetrics**: Comprehensive network metrics calculation
- **Centrality Measures**: Degree, betweenness, closeness, eigenvector centrality
- **Community Detection**: Louvain algorithm for community identification
- **Feature Engineering**: Individual, relationship, and network-level features

Key Features:
- Multiple centrality measures for influence analysis
- Community detection with modularity scoring
- Individual feature vectors for participants
- Relationship-level interaction analysis

#### `topic_model.py` - BERTopic-based topic modeling  
- **TopicModeler**: BERTopic implementation for discussion theme extraction
- **Document Preparation**: User email concatenation by time windows
- **Participant-Topic Distributions**: Topic engagement analysis
- **Topic Entropy**: Diversity metrics for participants

Key Features:
- 50-100 topic extraction using BERTopic
- Time-windowed document creation per participant
- Topic probability distributions and entropy calculation
- Top participant identification per topic

#### `formatter.py` - D3.js data formatting
- **D3Formatter**: Formats network and topic data for visualization
- **JSON Export**: Creates D3.js-ready data structures
- **Multi-format Output**: Supports various visualization requirements

Key Features:
- D3.js-compatible node-link data formatting
- Topic data integration with network visualization
- Metadata and statistics inclusion
- Timeline data support for temporal analysis

#### `data_acquisition.py` - IETF data fetching and normalization
- **IETFDataAcquisition**: Real IETF data fetching using glasgow-ipl/ietfdata library
- **DataTracker Integration**: Person metadata from IETF Datatracker
- **MailArchive Integration**: Email data from IETF mail archives  
- **Data Normalization**: Converts raw IETF data to pipeline format

Key Features:
- Direct integration with IETF Datatracker and mail archives
- Automatic data caching for repeated analysis
- Person metadata enrichment from Datatracker
- Support for date ranges and message limits
- Normalized JSON output compatible with pipeline

## Data Processing Pipeline

### Phase 1: Data Collection & Cleaning
- Load IETF mailing list archives (JSON, CSV, directory formats)
- Parse email headers (from, to, date, message-id, in-reply-to)
- Classify emails (automated, role-based, individual)
- Normalize email addresses and resolve person identities

### Phase 2: Social Graph Construction  
- Build directed interaction graph from email threads
- Create nodes for unique participants
- Add edges for reply relationships and co-participation
- Calculate temporal activity patterns

### Phase 3: Network Metrics Calculation
- Compute centrality measures for all participants
- Detect communities using Louvain algorithm  
- Generate individual and relationship feature vectors
- Analyze network structural properties

### Phase 4: Topic Modeling
- Concatenate participant emails by time windows
- Apply BERTopic for theme extraction
- Calculate participant-topic distributions
- Compute topic entropy for diversity analysis

### Phase 5: Data Formatting & Export
- Format network data for D3.js visualization
- Combine topic analysis with network metrics
- Export JSON files and CSV feature matrices
- Generate metadata and summary statistics

## Data Formats

### Input Data
The agent expects email data in JSON format with the following structure:
```json
{
  "from": "user@example.com",
  "to": ["list@ietf.org"],
  "date": "2020-01-15T10:30:00Z",
  "message_id": "<msg123@example.com>",
  "in_reply_to": "<msg122@example.com>",
  "subject": "Re: Topic discussion",
  "content": "Email body text...",
  "mailing_list": "security"
}
```

### Output Data
The agent produces several output files:

#### Network Data (`data.json`)
```json
{
  "nodes": [{"id": "person_001", "centrality": 0.34, ...}],
  "links": [{"source": "person_001", "target": "person_002", ...}],
  "topics": [{"topic_id": 0, "keywords": [...], ...}],
  "metadata": {...}
}
```

#### Person Mappings
- `emailID_pid_dict.json`: Email to person ID mapping
- `pid_emailID_dict.json`: Person to email addresses mapping  
- `pid_name_dict.json`: Person ID to names mapping
- `pid_datatracker_dict.json`: Person to IETF Datatracker URI mapping

#### Feature Matrices  
- `individual_features.csv`: Comprehensive participant features
- `topic_analysis.json`: Detailed topic modeling results

## Dependencies

Core requirements:
- `networkx`: Graph construction and analysis
- `pandas`: Data manipulation and CSV export
- `bertopic`: Topic modeling with transformers
- `scikit-learn`: Machine learning utilities
- `numpy`: Numerical computations
- `sentence-transformers`: Text embeddings
- `python-louvain`: Community detection

## Usage

The agent is designed to be used through the main pipeline script, but individual modules can be imported and used independently:

```python
from agent.graph_builder import SocialGraphBuilder
from agent.metrics import NetworkMetrics
from agent.topic_model import TopicModeler
from agent.formatter import D3Formatter

# Build graph
builder = SocialGraphBuilder()
# ... add emails ...
graph = builder.get_graph()

# Calculate metrics
metrics = NetworkMetrics(graph)
results = metrics.generate_comprehensive_report()

# Format for visualization
formatter = D3Formatter()
viz_data = formatter.format_network_data(graph, results, builder.get_person_resolver())
```

## Methodology

This implementation follows the comprehensive methodology developed for IETF email network analysis, including:

- **Email Classification**: Automated detection of system vs. individual emails
- **Identity Resolution**: Multi-source person identity linking
- **Thread Reconstruction**: Graph-based email conversation analysis
- **Network Analysis**: Multiple centrality measures and community detection
- **Topic Modeling**: Time-windowed BERTopic analysis
- **Feature Engineering**: Comprehensive participant and relationship features

## Privacy and Ethics

The agent follows privacy-preserving practices:
- Only processes publicly available mailing list archives
- Supports data anonymization for sensitive analyses
- Implements configurable aggregation thresholds
- Provides comprehensive audit logging

## Performance Considerations

The agent is designed to handle large-scale email datasets:
- Efficient graph construction with NetworkX
- Memory-optimized topic modeling with batching
- Incremental processing support for new data
- Configurable parameters for resource management