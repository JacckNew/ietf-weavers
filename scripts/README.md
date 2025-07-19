# Scripts Documentation

This directory contains standalone utility scripts for the IETF Weavers project.

## Available Scripts

### `fetch_ietf_data.py`

**Purpose**: High-performance IETF mailing list data fetcher with SQL-based direct database access

**Usage**:
```bash
# Fetch data from specific lists with multi-threading
python scripts/fetch_ietf_data.py --lists ietf cfrg --max-messages 500 --threads 4

# Fetch with date range
python scripts/fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --end-date 2024-12-31T23:59:59

# Quick test with limited messages
python scripts/fetch_ietf_data.py --lists ietf --max-messages 100 --output data/test_data.json
```

**Key Features**:
- Direct SQLite database access (bypasses API issues)
- Multi-threaded parallel processing for speed
- Configurable date ranges and message limits
- JSON output compatible with main pipeline
- 1000+ messages/second performance

### `serve_visualization.py`

**Purpose**: Local web server for the visualization interface

**Usage**:
```bash
# Start server on default port (8000)
python scripts/serve_visualization.py

# Start server on custom port
python scripts/serve_visualization.py --port 8080
```

**Key Features**:
- Serves the D3.js visualization interface
- Automatically opens browser
- Checks for required data files
- Simple HTTP server for development

## Integration with Main Pipeline

These scripts work seamlessly with the main pipeline:

1. **Data Collection**: Use `fetch_ietf_data.py` to gather IETF data
2. **Analysis**: Run `src/main.py` with the collected data
3. **Visualization**: Use `serve_visualization.py` to view results

## Examples

### Complete Workflow

```bash
# 1. Fetch IETF data
python scripts/fetch_ietf_data.py --lists ietf cfrg --output data/ietf_recent.json

# 2. Run analysis
python src/main.py data/ietf_recent.json

# 3. View results
python scripts/serve_visualization.py
```

### Large-Scale Data Collection

```bash
# Fetch 25 years of IETF data
python scripts/fetch_ietf_data.py --lists ietf --start-date 2000-01-01T00:00:00 --end-date 2024-12-31T23:59:59 --output data/ietf_25years.json
```
