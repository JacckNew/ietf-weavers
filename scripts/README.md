# Scripts Documentation

This directory contains standalone utility scripts for the IETF Weavers project.

## Available Scripts

### `fetch_ietf_data.py`

**Purpose**: Command-line tool for fetching IETF mailing list data

**Usage**:
```bash
# List available mailing lists
python scripts/fetch_ietf_data.py --list-available

# Fetch data from specific lists
python scripts/fetch_ietf_data.py --lists ietf cfrg --output data/ietf_data.json

# Fetch with date range and limits
python scripts/fetch_ietf_data.py --lists ietf --start-date 2024-01-01T00:00:00 --max-messages 1000
```

**Key Features**:
- Direct integration with IETF Datatracker and mail archives
- SQLite caching for efficient data retrieval
- Configurable date ranges and message limits
- JSON output compatible with main pipeline

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
