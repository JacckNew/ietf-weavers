⸻

🧠 Project Summary: IETF Weavers

Goal:
To visualize the social and discursive dynamics of Internet standard-making by analyzing IETF mailing lists and draft authorship. This project uses social network analysis (SNA) and natural language processing (NLP), rendered as interactive visualisations with D3.js.

⸻

📁 Repository Overview: ietf-weavers

ietf-weavers/
├── agent/                      # Backend logic (AI-driven processing engine)
│   ├── graph_builder.py        # Builds sender–replier social graph
│   ├── metrics.py              # Calculates centrality and network features
│   ├── topic_model.py          # Runs BERTopic to extract discussion themes
│   ├── formatter.py            # Outputs D3.js-ready JSON files
│   ├── utils.py                # Email parsing, NER, cleaning
│   └── README.md               # Agent responsibilities & usage
│
├── src/                        # Main pipeline script
│   └── main.py                 # Orchestrates graph + NLP + export
│
├── data/                       # Raw and processed IETF data
│   └── (mailing list files, metadata)
│
├── notebooks/                  # Prototyping, EDA, and manual validation
│
├── visualisation/              # D3.js frontend prototype
│   ├── index.html              # Interactive force-directed graph UI
│   └── data.json               # Graph + topic data rendered by D3
│
├── docs/                       # Documentation or academic figures
│
├── requirements.txt            # Python environment setup
├── LICENSE                     # MIT License (for software only)
└── README.md                   # Project overview, usage, and credits


⸻

🔍 What the Agent Needs to Do

Phase 1: Data Collection & Cleaning
	•	Load IETF public mailing list archive (.txt or .mbox)
	•	Parse headers for sender, date, subject, message ID, and reply reference
	•	Normalize identities using Datatracker metadata (match senders)

Phase 2: Social Graph Construction
	•	Build a directed graph:
	•	Nodes: unique participants
	•	Edges: inferred reply relationships from threads
	•	Compute:
	•	Degree, betweenness, closeness centrality
	•	Community detection using Louvain
	•	Participation duration, area coverage, and mail volume

Phase 3: Topic Modeling (BERTopic)
	•	Concatenate each user’s emails into one document per user per time window
	•	Run BERTopic to extract:
	•	50–100 topics
	•	Participant–topic distributions
	•	Calculate topic entropy for each participant

Phase 4: Output for Visualisation
	•	Format graph as:

{
  "nodes": [
    {"id": "user@example.com", "group": "community1", "centrality": 0.34, ...}
  ],
  "links": [
    {"source": "userA", "target": "userB", "weight": 3}
  ],
  "topics": [
    {"topic_id": 0, "keywords": ["privacy", "security"], "top_participants": [...]}
  ]
}


	•	Save as visualisation/data.json

⸻

🖼️ D3.js Visualisation Prototype

UI Elements in index.html:
	•	Force-directed Graph:
	•	Node size = centrality
	•	Node color = community or working group
	•	Hover tooltip = name, centrality, entropy, participation years
	•	Timeline Filter (TBD):
	•	Slide bar for selecting time windows (e.g., 2000–2005)
	•	Topic Filter Panel (TBD):
	•	Clickable legend of topics to highlight related participants
	•	Heatmap (optional):
	•	Cross-tab for role vs. linguistic behavior, rendered in matrix

⸻

✅ Agent Pipeline Overview (Orchestration)
	1.	Load emails and metadata
	2.	Build graph via graph_builder
	3.	Calculate metrics via metrics
	4.	Run topic modeling via topic_model
	5.	Format and export via formatter
	6.	Render in index.html

⸻

🧠 Agent Must Know
	•	Use Python (with networkx, pandas, bertopic, scikit-learn)
	•	Export only publicly safe and anonymized data
	•	Follow modular design (one module per task)
	•	Enable reproducibility for visual snapshots

⸻