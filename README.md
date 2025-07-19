![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
# IETF Weavers

**Social and Discursive Dynamics of Internet Standard-making**

A comprehensive analysis and visualization tool for understanding collaboration patterns, influence networks, and community dynamics within the Internet Engineering Task Force (IETF) through email communication analysis.

## 📋 Project Overview

IETF Weavers combines social network analysis (SNA) and natural language processing (NLP) to visualize how Internet standards are developed through human collaboration. The project analyzes IETF mailing lists and Datatracker metadata to reveal:

- **Social Networks**: Who collaborates with whom in Internet standard development
- **Influence Patterns**: Key connectors and opinion leaders in technical communities  
- **Community Structure**: Working group boundaries and cross-pollination
- **Topic Evolution**: How technical discussions emerge and evolve over time
- **Knowledge Transfer**: Patterns of information flow and expertise sharing

## � Key Features

- **Real IETF Data Integration**: Direct integration with IETF Datatracker and mail archives via [glasgow-ipl/ietfdata](https://github.com/glasgow-ipl/ietfdata)
- **Automated Data Pipeline**: End-to-end processing from raw emails to interactive visualizations
- **Social Network Analysis**: Comprehensive metrics including centrality, community detection, and influence scoring
- **Topic Modeling**: BERTopic-based analysis of discussion themes and evolution
- **Interactive Visualization**: D3.js dashboard with filtering, search, and drill-down capabilities
- **Modular Architecture**: Pluggable agent-based system for easy extension and customization

## �🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- Internet connection (for fetching IETF data)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/ietf-weavers.git
   cd ietf-weavers
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### Usage Options

#### Option 1: Fetch Real IETF Data (Recommended)

1. **List available mailing lists**

   ```bash
   python scripts/fetch_ietf_data.py --list-available
   ```

2. **Fetch data from specific mailing lists**

   ```bash
   # Fetch recent data from popular lists
   python scripts/fetch_ietf_data.py --lists ietf cfrg --output data/ietf_recent.json

   # Fetch with specific date range
   python scripts/fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --max-messages 1000
   ```

3. **Run analysis pipeline**

   ```bash
   python src/main.py data/ietf_recent.json
   ```

4. **View results**

   ```bash
   python scripts/serve_visualization.py
   ```
   
   Then open <http://localhost:8000> in your browser, or directly open `visualisation/index.html`

#### Option 2: Use Sample Data

1. **Run with sample data**

   ```bash
   python src/main.py data/sample_emails.json
   ```

2. **View results**

   ```bash
   python scripts/serve_visualization.py
   ```
   
   Then open <http://localhost:8000> in your browser, or directly open `visualisation/index.html`

#### Option 3: Integrated Workflow

Fetch IETF data and run analysis in one command:

```bash
# Fetch and analyze specific mailing lists
python src/main.py --fetch-ietf --mailing-lists ietf cfrg --max-messages 500

# List available mailing lists
python src/main.py --list-available
```

## � Current Data Status

### ✅ Downloaded IETF Data (Complete)

The repository now contains comprehensive IETF mailing list data across three tiers:

#### **Tier 1 - Core Technical Lists** (10 lists, 345,525 messages)

- `cfrg` - Crypto Research Group (14,249 messages)
- `quic` - QUIC Protocol (11,711 messages)
- `tls` - TLS Security (37,056 messages)
- `oauth` - OAuth Authentication (26,623 messages)
- `dnsop` - DNS Operations (35,492 messages)
- `v6ops` - IPv6 Operations (78,645 messages)
- `rtgwg` - Routing Working Group (15,499 messages)
- `tsvwg` - Transport Services (51,248 messages)
- `saag` - Security Area Advisory Group (17,134 messages)
- `netmod` - Network Modeling (57,868 messages)

#### **Tier 2 - Extended Technical Lists** (10 lists, 120,664 messages)

- `netconf` - Network Configuration (20,344 messages)
- `opsawg` - Operations & Management (13,255 messages)
- `anima` - Autonomic Networking (7,935 messages)
- `spring` - Source Packet Routing (12,345 messages)
- `ace` - Authentication & Authorization (5,934 messages)
- `http` - HTTP (1 message)
- `httpapi` - HTTP API (1,506 messages)
- `mmusic` - Multiparty Multimedia (23,880 messages)
- `iptel` - IP Telephony (1,241 messages)
- `sip` - Session Initiation Protocol (34,223 messages)

#### **Tier 3 - Specialized Technical Lists** (10 lists, 135,450 messages)

- `asrg` - Anti-Spam Research Group (34,658 messages)
- `bmwg` - Benchmarking Working Group (5,881 messages)
- `dhcwg` - DHCP Working Group (56,637 messages)
- `hiprg` - Host Identity Protocol RG (1,663 messages)
- `iccrg` - Congestion Control RG (3,716 messages)
- `icnrg` - Information-Centric Networking RG (4,029 messages)
- `isis-wg` - ISIS Working Group (13,433 messages)
- `krb-wg` - Kerberos Working Group (14,257 messages)
- `nfvrg` - Network Function Virtualization RG (972 messages)
- `tewg` - Traffic Engineering WG (204 messages)

### 💾 **Data Storage**

- **Total Messages**: 601,639 across 30 mailing lists
- **Cache Database**: 9.02GB SQLite file (`cache/ietfdata.sqlite`)
- **Exported JSON**: 2.73GB across 3 tier files (`data/` directory)
- **Coverage Period**: 1992-2025 (complete historical archive)

### 📁 **Cache Files Explained**

- **`cache/ietfdata.sqlite`** (9.02GB): MailArchive3 email data cache containing all downloaded message content, headers, and metadata
- **`cache/ietf-dt-cache.sqlite`** (24KB): DataTracker metadata cache with working group information, RFC data, and organizational structure

### 🚀 **Batch Download Tool**

For downloading additional data or replicating the dataset:

```bash
# Download specific tiers
python batch_download.py --tier 1    # Core lists
python batch_download.py --tier 2    # Extended lists  
python batch_download.py --tier 3    # Specialized lists

# Download all tiers at once
python batch_download.py --all

# Download custom selection
python batch_download.py --custom cfrg quic tls

# List all available mailing lists
python batch_download.py --list-available
```

**Note**: The data is already downloaded and ready for analysis! 🎉

## �📁 Repository Structure

```text
ietf-weavers/
├── agent/                      # Core data processing modules
│   ├── data_acquisition.py     # IETF data fetching using ietfdata library
│   ├── formatter.py            # Outputs D3.js-ready JSON files
│   ├── graph_builder.py        # Builds sender–replier social graph
│   ├── metrics.py              # Calculates centrality and network features
│   ├── topic_model.py          # Runs BERTopic to extract discussion themes
│   ├── utils.py                # Email parsing, NER, cleaning utilities
│   ├── __init__.py             # Package initialization
│   └── README.md               # Agent module documentation
│
├── cache/                      # Cache files (SQLite, temporary data)
│   ├── ietfdata.sqlite         # IETF mail data cache (9.02GB) - COMPLETE
│   └── ietf-dt-cache.sqlite    # DataTracker metadata cache (24KB)
│
├── data/                       # Downloaded IETF data (2.73GB total)
│   ├── ietf_batch_tier1_core_technical_lists_20250717_132702.json      # Tier 1 (1.57GB)
│   ├── ietf_batch_tier2_extended_technical_lists_20250717_132710.json  # Tier 2 (596MB)  
│   ├── ietf_batch_tier3_specialized_technical_lists_20250718_184653.json # Tier 3 (564MB)
│   └── ietf_large_sample.json  # Sample data for testing
│
├── scripts/                    # Standalone utility scripts
│   ├── fetch_ietf_data.py      # Command-line IETF data acquisition
│   ├── serve_visualization.py  # Local web server for visualization
│   └── README.md               # Scripts documentation
│
├── src/                        # Main pipeline orchestration
│   └── main.py                 # End-to-end workflow coordinator
│
├── visualisation/              # Interactive web visualization
│   ├── index.html              # D3.js force-directed graph interface
│   ├── data.json               # Network graph data for visualization
│   ├── individual_features.csv # Participant feature export
│   └── topic_analysis.json     # Topic modeling results
│
├── venv/                       # Python virtual environment
│
├── batch_download.py           # Multi-tier IETF data downloader
├── batch_download.log          # Download process logs
├── requirements.txt            # Python dependencies
├── LICENSE                     # MIT License
├── README.md                   # This file
├── systemdesign.png            # System architecture diagram
├── instruction.md              # Project instructions
├── PROJECT_COMPLETION.md       # Project completion status
├── IETF_INTEGRATION_SUMMARY.md # Integration summary
└── *.md                        # Additional documentation files
```

## 🔧 Core Features

### Data Processing Pipeline

1. **Data Collection & Cleaning**
   - Fetch IETF mailing list data using glasgow-ipl/ietfdata library
   - Parse email headers and normalize identities
   - Filter automated vs. individual emails
   - Build comprehensive person-email mappings

2. **Social Graph Construction**
   - Create directed graphs with participants as nodes
   - Infer reply relationships from email threads
   - Build co-participation networks from shared activities
   - Track temporal participation patterns

3. **Network Analysis**
   - Calculate centrality measures (degree, betweenness, closeness, eigenvector)
   - Detect communities using Louvain algorithm
   - Generate individual and relationship-level features
   - Analyze network structural properties

4. **Topic Modeling**
   - Apply BERTopic to extract 50-100 discussion themes
   - Create participant-topic distributions
   - Calculate topic entropy for diversity analysis
   - Identify top participants per topic

5. **Visualization Export**
   - Format data for D3.js interactive visualization
   - Generate node-link diagrams with rich metadata
   - Export CSV files for further analysis
   - Create summary statistics and reports

### Interactive Visualization

The D3.js frontend provides:

- **Force-directed Network Graph**
  - Node size represents centrality or activity level
  - Node color indicates community or working group
  - Interactive tooltips with participant details
  - Drag-and-drop node positioning

- **Dynamic Filtering**
  - Adjust minimum degree threshold
  - Change node sizing and coloring attributes
  - Filter by time periods or communities
  - Control link strength and visibility

- **Topic Integration**
  - Topic-based participant highlighting
  - Keyword clouds for discussion themes
  - Participant-topic relationship exploration

## 📊 Analysis Capabilities

### Individual Level
- Communication volume and patterns
- Network position and centrality scores
- Temporal activity (duration, peak periods)
- Influence metrics (response rates, thread initiation)
- Collaboration breadth across mailing lists
- Topic diversity and specialization

### Relationship Level  
- Interaction frequency between participants
- Response patterns and latency
- Thread co-participation
- Reciprocity and relationship strength
- Topic overlap and shared interests

### Network Level
- Community structure and boundaries
- Cross-group collaboration patterns
- Leadership networks and hierarchies
- Newcomer integration patterns
- Information flow and bottlenecks
- Network evolution over time

## 📈 Visualization Features

### Network Graph
- Interactive force-directed layout
- Configurable node sizing (centrality, activity, diversity)
- Community-based coloring schemes
- Adjustable link filtering and strength
- Tooltip details on hover
- Zoom and pan navigation

### Controls and Filters
- **Node Size**: Degree centrality, betweenness, email count, topic entropy
- **Node Color**: Community, mailing list count, activity duration
- **Link Filtering**: Minimum degree, interaction strength
- **Time Windows**: Filter by activity periods (future enhancement)

### Statistics Panel
- Real-time network statistics
- Community counts and sizes
- Topic distribution summaries
- Centrality measure distributions

## 🛠️ Configuration

The pipeline can be configured through command-line arguments:

```bash
python src/main.py [data_source] [options]

Options:
  --output-dir DIR       Output directory (default: visualisation)
  --n-topics N          Number of topics for modeling (default: 50)
  --time-window N       Time window in months (default: 6)
```

Advanced configuration can be done by modifying the config dictionary in `src/main.py`.

## 📋 Data Format

### Input Email Data
The system expects JSON files with email records:

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

### Output Visualization Data
The system produces D3.js-ready JSON:

```json
{
  "nodes": [
    {
      "id": "person_001",
      "email": "user@example.com", 
      "name": "User Name",
      "degree_centrality": 0.34,
      "community": 1,
      "email_count": 45,
      "topic_entropy": 2.1
    }
  ],
  "links": [
    {
      "source": "person_001",
      "target": "person_002", 
      "weight": 3,
      "type": "reply"
    }
  ],
  "topics": [
    {
      "topic_id": 0,
      "keywords": ["security", "encryption"],
      "top_participants": [...]
    }
  ]
}
```

## 🔬 Methodology

This implementation is based on comprehensive research methodology for analyzing large-scale email communication networks in technical communities. Key methodological components include:

- **Email Classification**: Automated detection of system vs. individual emails using pattern matching
- **Identity Resolution**: Multi-source person identity linking across email addresses
- **Thread Reconstruction**: Graph-based analysis of email conversation structures  
- **Network Analysis**: Multiple centrality measures and community detection algorithms
- **Topic Modeling**: Time-windowed BERTopic analysis for theme extraction
- **Feature Engineering**: Comprehensive participant and relationship feature vectors

## 🔒 Privacy and Ethics

- **Public Data Focus**: Only analyzes publicly available mailing list archives
- **Data Anonymization**: Supports anonymization for sensitive analyses  
- **Aggregation Standards**: Implements minimum group sizes for reporting
- **Consent Frameworks**: Respects participant preferences where applicable

## 🚧 Future Enhancements

### Advanced Analytics
- **Real-time Analysis**: Live dashboards for current communication patterns
- **Trend Detection**: Identify emerging topics and communities
- **Anomaly Detection**: Flag unusual communication patterns
- **Predictive Modeling**: Forecast collaboration patterns and outcomes

### Enhanced Visualization
- **Timeline View**: Dynamic network evolution over time
- **Geographic Mapping**: Collaboration patterns across institutions/countries
- **Multi-layer Networks**: Simultaneous visualization of different relationship types
- **Heatmaps**: Cross-tabulation of roles vs. linguistic behavior

### External Integration
- **GitHub Activity**: Correlate email patterns with code contributions
- **Conference Data**: Link to meeting attendance and presentation records
- **Citation Networks**: Connect to academic publication patterns
- **Document Networks**: RFC and draft collaboration analysis

## 📚 Dependencies

Core libraries:
- **networkx**: Graph construction and analysis
- **pandas**: Data manipulation and export  
- **bertopic**: Advanced topic modeling with transformers
- **scikit-learn**: Machine learning utilities
- **numpy**: Numerical computations
- **sentence-transformers**: Text embeddings for semantic analysis
- **python-louvain**: Community detection algorithms

Visualization:
- **D3.js v7**: Interactive network visualization
- **Modern web standards**: HTML5, CSS3, JavaScript ES6+

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable  
5. Submit a pull request

### Areas for Contribution
- Additional data source connectors (mbox, XML, databases)
- Enhanced visualization components and interactions
- Performance optimizations for large datasets
- Additional network analysis metrics
- Documentation and examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project builds upon extensive research in social network analysis, computational social science, and Internet governance. Special thanks to the IETF community for maintaining open and accessible communication archives that enable this type of research.

## 📞 Contact

For questions, suggestions, or collaboration opportunities, please open an issue or contact the maintainers.

---

**🚀 Ready to explore Internet governance networks? Start with `python src/main.py data/sample_emails.json` and open `visualisation/index.html`!**

---

## 🚀 Quick Start

### 1. Clone this repository
```bash
git clone https://github.com/jaccknew/ietf-weavers.git
cd ietf-weavers
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run preprocessing pipeline
```bash
python src/main.py
```

### 4. Open the visualisation
Open `visualisation/index.html` in your browser to explore the prototype.

---

## 🛠️ Tech Stack

- **Python**: Data processing, NLP modeling (BERTopic, BERT, LIWC)
- **NetworkX**: Social network computation
- **D3.js**: Force-directed graphs, timelines, and heatmaps
- **SQLite/CSV**: Lightweight data storage

---

## 📖 License

This project’s code and visualisation system are licensed under the MIT License.  
See the [LICENSE](./LICENSE) file for details.

---

## 🙌 Acknowledgements

Inspired by “The Web We Weave” (Khare et al., 2022) and built on open data from [ietf.org](https://ietf.org).

---

## 🎉 Current Status: **FULLY FUNCTIONAL**

**✅ Complete End-to-End Pipeline Working**

The IETF Weavers project is now fully operational with all core features implemented:

### ✅ Completed Features

- **📧 Email Processing**: Robust parsing, cleaning, and normalization of mailing list data
- **🔗 Social Graph Construction**: Thread-based interaction network building with proper email threading
- **📊 Network Analysis**: Complete centrality metrics, community detection, and graph properties
- **🏷️ Topic Modeling**: Advanced BERTopic integration with sentence transformers (working!)
- **📈 Interactive Visualization**: D3.js-powered network graph with real-time filtering
- **💾 Comprehensive Export**: Multiple output formats (JSON, CSV) for downstream analysis
- **🛡️ Error Handling**: Graceful degradation when dependencies are missing
- **🧪 Testing**: Basic functionality verification and sample data validation

### � Ready for Production

The project is now ready for real IETF data processing:

```bash
# Fetch real IETF data
python scripts/fetch_ietf_data.py --lists ietf cfrg --output data/ietf_recent.json

# Run analysis pipeline
python src/main.py data/ietf_recent.json --n-topics 10

# Start visualization server
python scripts/serve_visualization.py
```

**Next Steps**: The system is production-ready for large-scale IETF data analysis!

