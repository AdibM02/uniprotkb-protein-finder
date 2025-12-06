# UniProtKB Protein Finder – Instructions

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Required packages:**
- `requests` – HTTP client for UniProtKB REST API
- `python-dotenv` – Optional, for loading `.env` configuration

### 2. Configure (Optional)
Create a `.env` file in the project root:
```env
CONTACT_EMAIL=your_email@example.com
OUTPUT_DIR=./output
```

Or use defaults (no `.env` needed):
- `CONTACT_EMAIL` defaults to `user@example.com`
- `OUTPUT_DIR` defaults to `./output`

### 3. Run the Application
```bash
python main.py
```

This launches the Tkinter GUI application.

---

## How It Works

### Application Architecture

```
┌──────────────────────────────────┐
│   ui.py (Tkinter GUI)            │
│   • Search dialog                │
│   • Results display              │
│   • Threading for API calls      │
└─────────────┬────────────────────┘
              │
┌─────────────▼────────────────────┐
│   logic.py (Business Logic)      │
│   • UniProtKBClient (REST API)   │
│   • ProteinSearchService         │
│   • ProteinDataExporter          │
│   • Search history logging       │
└─────────────┬────────────────────┘
              │
┌─────────────▼────────────────────┐
│   config.py (Configuration)      │
│   • Environment variables        │
│   • Path management              │
└──────────────────────────────────┘
```

### Search Flow

1. **Enter protein name & species** in the GUI
2. **Click "Search"** – API call runs on background thread
3. **Results display** with:
   - Protein name & UniProtKB ID
   - Organism information
   - Sequence length
   - Domains (with start/end positions)
4. **Export option** – Save detailed data to JSON
5. **Search history** – Logged to `output/search_history.csv`

### Features

| Feature | Description |
|---------|-------------|
| **Live Search** | Query UniProtKB for any protein name |
| **Species Filter** | Search within specific organisms (Human, Mouse, Yeast, etc.) |
| **Domain Extraction** | Automatically extract functional domains from proteins |
| **Sequence Data** | Retrieve full protein sequences |
| **JSON Export** | Save detailed search results with timestamp |
| **Search History** | CSV log of all searches (success/failure) |
| **Threading** | Non-blocking GUI during API calls |

---

## Using the GUI

### Main Window

1. **Protein Name** – Enter any protein (e.g., "hemoglobin", "insulin")
2. **Species** – Select from dropdown (optional, uses first match if empty)
3. **Search Button** – Initiates query
4. **Status Bar** – Shows search progress and results

### Results Display

Shows:
- Protein accession ID
- UniProtKB link (clickable)
- Organism scientific name
- Sequence length
- Domains list with:
  - Domain name & type
  - Position (start–end)
  - Sequence snippet

### Export Results

Click **"Export to JSON"** to save:
- File: `output/protein_<name>_<timestamp>.json`
- Contains: Full protein data, domains, sequences, metadata

---

## Configuration

### Environment Variables (.env)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONTACT_EMAIL` | `user@example.com` | Required by UniProtKB API (for user-agent header) |
| `OUTPUT_DIR` | `./output` | Directory for JSON exports & search history |

**Example `.env`:**
```env
CONTACT_EMAIL=researcher@institution.org
OUTPUT_DIR=/home/user/protein_data
```

### Application Defaults

If `.env` is missing or incomplete:
- Runs with default values
- Creates `output/` directory automatically
- Logs search history to `output/search_history.csv`

---

## Output Files

### Search History

**File:** `output/search_history.csv`

**Format:**
```csv
timestamp,protein_name,species,success
2025-12-06 10:30:45,hemoglobin,Human,True
2025-12-06 10:31:12,insulin,Mouse,True
2025-12-06 10:32:01,unknown_protein,,False
```

**Purpose:** Track all searches for analysis and debugging

### JSON Export

**File:** `output/protein_<name>_<YYYYMMDD_HHMMSS>.json`

**Example content:**
```json
{
  "protein_name": "hemoglobin",
  "uniprot_id": "P69905",
  "organism": "Homo sapiens",
  "sequence_length": 146,
  "domains": [
    {
      "name": "Globin",
      "type": "Domain",
      "start": 1,
      "end": 146,
      "sequence": "MVLSPADKTN..."
    }
  ],
  "full_sequence": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLFTYP...",
  "search_timestamp": "2025-12-06 10:30:45"
}
```

---

## Troubleshooting

### "API Error: Connection failed"

**Causes:**
- No internet connection
- UniProtKB API is down (rare)
- Firewall/proxy blocking requests

**Solution:**
1. Check internet connection
2. Verify UniProtKB API status: https://rest.uniprot.org/
3. Update `CONTACT_EMAIL` in `.env`
4. Try again with a different protein name

### "Protein not found"

**Causes:**
- Typo in protein name
- Protein doesn't exist in UniProtKB
- Species mismatch (searched for "Human" but protein is "Mouse")

**Solution:**
1. Double-check spelling
2. Search UniProtKB directly: https://www.uniprot.org/
3. Leave species empty to search all organisms
4. Try alternative protein names (e.g., "hemoglobin" vs "Hb")

### "GUI is frozen"

**This shouldn't happen** – all API calls run on background threads.

**If it occurs:**
1. Close the application
2. Check if `.env` is correct (especially `CONTACT_EMAIL`)
3. Restart the application
4. Report the issue with details (protein name, species, error message)

### "Export failed"

**Causes:**
- `output/` directory doesn't exist (auto-created on first export)
- Permission denied on output directory
- Disk full

**Solution:**
1. Manually create `output/` folder: `mkdir output`
2. Check folder permissions: should be writable
3. Try different `OUTPUT_DIR` path in `.env`

### "CSV history file locked"

**Cause:** File is open in another application while the app tries to write

**Solution:**
1. Close the CSV file in spreadsheet application
2. Restart the protein finder application
3. Try search again

---

## API Reference

### UniProtKB REST API

**Base URL:** `https://rest.uniprot.org/uniprotkb/`

**Endpoints used:**
- `GET /search?query=...&format=json` – Search for proteins
- `GET /{id}?format=json` – Fetch entry details

**Authentication:** None required (public API)

**Rate limiting:** Respects standard HTTP limits (no API key needed)

**Rate limit headers:** Returned in response

### Species Mapping

**Common species names supported:**
- Human → `Homo sapiens`
- Mouse → `Mus musculus`
- Yeast → `Saccharomyces cerevisiae`
- Zebrafish → `Danio rerio`
- Fruit fly → `Drosophila melanogaster`
- C. elegans → `Caenorhabditis elegans`
- Arabidopsis → `Arabidopsis thaliana`
- Rice → `Oryza sativa`

See `logic.py` for complete `SPECIES_MAP` dictionary.

---

## Development

### Project Structure

```
uniprotkb-protein-finder/
├── main.py                    # Entry point
├── ui.py                      # Tkinter GUI
├── logic.py                   # API client & business logic
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example               # Configuration template
├── .gitignore                 # Git ignore rules
├── LICENSE                    # MIT License
├── README.md                  # Project overview
├── INSTRUCTIONS.md            # This file
├── .github/
│   └── copilot-instructions.md  # AI agent guidance
└── output/                    # Search history & exports
    ├── search_history.csv
    └── protein_*.json
```

### Key Functions

#### logic.py

- `UniProtKBClient.search_protein(name, species)` – API search
- `UniProtKBClient.extract_data(entry)` – Parse response
- `ProteinSearchService.search(name, species)` – High-level search
- `ProteinDataExporter.export_to_json(data, filename)` – Save results
- `ProteinDataExporter.log_search_to_history(name, species, success)` – CSV logging

#### ui.py

- `ProteinFinderGUI._on_search_clicked()` – Search button handler
- `ProteinFinderGUI._search_worker()` – Background thread
- `ProteinFinderGUI._update_status()` – Thread-safe GUI update
- `ProteinFinderGUI._format_results()` – Display formatting

### Running with Custom Species Map

Edit `SPECIES_MAP` in `logic.py` to add more organisms:

```python
SPECIES_MAP = {
    'Human': 'Homo sapiens',
    'Arabidopsis': 'Arabidopsis thaliana',  # Add here
}
```

### Debugging

**Enable verbose output:**
1. Edit `ui.py`
2. Uncomment debug prints in `_search_worker()`
3. Run with `python main.py`

**API response debugging:**
1. In `logic.py`, add: `print(json.dumps(data, indent=2))`
2. Restart application
3. Search and check console output

---

## System Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.7+ |
| Operating System | Windows, macOS, Linux |
| Tkinter | Built-in with Python |
| Internet | Required (REST API) |
| Memory | ~50 MB (minimal) |
| Disk | ~10 MB (application + output) |

### Linux Note

On Linux, install tkinter separately:
```bash
sudo apt-get install python3-tk
```

---

## License

MIT License – See `LICENSE` file

---

## Support & References

| Link | Purpose |
|------|---------|
| [UniProtKB API Docs](https://www.uniprot.org/help/api) | Official API reference |
| [UniProtKB Search](https://www.uniprot.org/) | Manual search interface |
| [Python Tkinter](https://docs.python.org/3/library/tkinter.html) | GUI framework docs |
| [Requests Library](https://requests.readthedocs.io/) | HTTP client docs |

---

## Contact & Contributions

**Project:** UniProtKB Protein Finder  
**Repository:** https://github.com/AdibM02/uniprotkb-protein-finder  
**Issues:** Use GitHub Issues for bug reports  
**Contributions:** Pull requests welcome

---

**Last Updated:** December 6, 2025
