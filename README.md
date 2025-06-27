![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
# IETF Weavers

**Visualising the social and discursive architecture of Internet standard-making**

This project explores how technical standards are created within the Internet Engineering Task Force (IETF), by analyzing communication patterns, social structures, and thematic discussions through the lens of social network analysis (SNA) and natural language processing (NLP). The visualisations are rendered using D3.js to make influence, collaboration, and language dynamics visible and explorable.

---

## 🔍 Project Goals

- Analyze participant influence and interaction structure within IETF working groups
- Detect and model dominant discussion topics and how they diffuse over time
- Compare linguistic behavior and roles using dialogue act and stylistic analysis
- Present all insights through a fully interactive web-based dashboard

---

## 🗂️ Project Structure

```
ietf-weavers/
├── data/               # Raw and processed data
├── src/                # Python scripts for data processing and modeling
├── notebooks/          # Jupyter notebooks for EDA and development
├── visualisation/      # D3.js interactive network visualisations
├── docs/               # Documentation and supporting materials
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

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

