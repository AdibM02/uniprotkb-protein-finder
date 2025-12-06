# AI Coding Agent Instructions

## Project Overview
**UniProtKB Protein Finder** — A modern Python GUI application for searching and analyzing protein data from UniProtKB. Demonstrates clean architecture, API integration, and responsive threading patterns.

**Repository**: UniProtKB Protein Finder  
**Stack**: Python 3.7+, Tkinter, REST API, Threading

---

## Architecture & Design

### Layer Separation
```
┌─────────────────────────────────────────┐
│         ui.py (GUI Layer)               │
│  • Tkinter widgets & user interaction   │
│  • Event handling & threading triggers  │
│  • Imports from logic.py (no reverse)   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      logic.py (Business Logic)          │
│  • UniProtKBClient (API queries)        │
│  • ProteinSearchService (orchestration) │
│  • ProteinDataExporter (JSON I/O)       │
│  • Custom exceptions                    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│       config.py (Configuration)         │
│  • .env file loading                    │
│  • Environment variables & defaults     │
│  • Output directory management          │
└─────────────────────────────────────────┘
```

### Key Components

**logic.py** — No imports from `ui.py` or `tkinter`:
- `UniProtKBClient.search_protein(protein_name, species)` — REST API query
- `UniProtKBClient.extract_data(entry)` — Parse JSON response for domains/sequences
- `ProteinSearchService.search()` — High-level search orchestration
- `ProteinDataExporter.export_to_json()` — File I/O with proper path handling
- Custom exceptions: `ProteinNotFoundError`, `SpeciesNotFoundError`, `APIError`

**ui.py** — Pure GUI with threading:
- `ProteinFinderGUI._search_worker()` — Background thread for API calls
- `ProteinFinderGUI._update_status()` — Thread-safe GUI updates via `root.after()`
- `ProteinFinderGUI._format_results()` — Format data for display
- No translation/parsing logic here; all calls to `logic.py`

**config.py** — Configuration with graceful degradation:
```python
try:
    from dotenv import load_dotenv
except ImportError:
    # App still works without python-dotenv
```

**main.py** — Entry point ensures module path is correct:
```python
sys.path.insert(0, str(day04_path))  # Allows imports from ui.py
from ui import run_gui
```

---

## Threading Pattern (Critical)

### Problem
API requests block the GUI, making it unresponsive.

### Solution
Run API calls on background threads, update GUI safely from main thread:

```python
# In ui.py _on_search_clicked():
thread = threading.Thread(target=self._search_worker, daemon=True)
thread.start()  # Returns immediately; UI stays responsive

# In _search_worker() (runs on thread):
data = self.service.search(protein_name, species)  # Long operation

# Update GUI safely from worker thread:
self._update_status(message, 'green')  # Calls root.after()

# In _update_status():
self.root.after(0, self._do_update_status, message, color)  # Queues on main thread
```

**Why `root.after()`?** Tkinter GUI updates must happen on the main thread. `after()` queues the update safely.

---

## API Integration

### UniProtKB REST API
- **Search**: `https://rest.uniprot.org/uniprotkb/search?query=...&format=json`
- **Entry fetch**: `https://rest.uniprot.org/uniprotkb/{id}?format=json`
- **Authentication**: None required
- **Rate limiting**: Respects standard HTTP rate limits
- **User-Agent**: Required header with contact email

### Response Parsing
```python
# Search returns: {"results": [...], "facets": [...]}
# Entry returns: {"features": [...], "sequence": {...}, "organism": {...}}

# Domain extraction from features array:
for feature in entry.get('features', []):
    if feature['type'] in ['Domain', 'Region', 'Active site']:
        domain = {
            'name': feature.get('description'),
            'type': feature['type'],
            'start': feature['location']['start']['value'],
            'end': feature['location']['end']['value'],
            'sequence': full_sequence[start-1:end]  # Slice protein sequence
        }
```

---

## File Handling & I/O

### Configuration Loading
**config.py** uses `Path` for cross-platform paths:
```python
from pathlib import Path

env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
output_dir.mkdir(parents=True, exist_ok=True)  # Auto-create
```

### JSON Export
**logic.py** `ProteinDataExporter`:
```python
def export_to_json(data, filename=None):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'protein_{protein_name}_{timestamp}.json'
    
    output_path = Path(config.get_output_dir()) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    return str(output_path)  # Return path for logging
```

**Patterns**:
- Use `Path` for all paths (cross-platform)
- `Path(...).parent.mkdir(parents=True, exist_ok=True)` to ensure directory exists
- Always use `encoding='utf-8'` for text files
- Timestamp in filename prevents collisions

---

## Error Handling

### Custom Exception Hierarchy
```python
class ProteinNotFoundError(Exception): pass
class SpeciesNotFoundError(Exception): pass
class APIError(Exception): pass
```

### In UI Layer
Catch exceptions separately, show user-friendly messages:
```python
try:
    data = self.service.search(protein_name, species)
except ProteinNotFoundError as e:
    self._update_status(f'❌ {str(e)}', 'red')
except APIError as e:
    self._update_status(
        f'❌ API Error: {str(e)}\n\nCheck internet & try again.',
        'red'
    )
```

### In API Layer
Wrap requests errors with meaningful context:
```python
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    raise APIError(f"API request failed: {str(e)}")
```

---

## Development Workflow

### Running the Application
```bash
python main.py
```

### Testing Changes
1. **Logic changes** (logic.py): Test API client directly
   ```python
   client = UniProtKBClient()
   data = client.search_protein('hemoglobin', 'Human')
   ```

2. **GUI changes** (ui.py): Run app, trigger search, check threading

3. **Config changes** (config.py): Update `.env`, reload app

### Debugging API Issues
1. Check `.env` has valid `CONTACT_EMAIL`
2. Test endpoint directly:
   ```bash
   curl "https://rest.uniprot.org/uniprotkb/search?query=hemoglobin&format=json&size=1"
   ```
3. Add logging to `_search_worker()`:
   ```python
   print(json.dumps(data, indent=2))
   ```
4. Check UniProtKB status: https://rest.uniprot.org

---

## Common Tasks

### Adding a New Species
Edit `SPECIES_MAP` in `logic.py`:
```python
SPECIES_MAP = {
    'Human': 'Homo sapiens',
    'Zebrafish': 'Danio rerio',  # Add here
}
```

### Changing JSON Export Format
Modify `ProteinDataExporter.export_to_json()` in `logic.py`:
```python
json_data = {
    'protein_name': data['protein_name'],
    'sequence': data['full_sequence'],
    # Add custom fields here
}
```

### Improving Responsiveness
If API calls still block UI:
1. Add timeout: `requests.get(..., timeout=5)`
2. Show "Searching..." status before thread starts
3. Add progress updates (domain count as they load)

### Adding Caching
```python
class ProteinSearchService:
    def __init__(self):
        self.cache = {}  # Add cache
    
    def search(self, protein_name, species):
        key = f"{protein_name}:{species}"
        if key in self.cache:
            return self.cache[key]
        data = self.client.search_protein(protein_name, species)
        self.cache[key] = data
        return data
```

---

## Code Quality Standards

1. **Type hints** — Use in docstrings for function parameters/returns
2. **Docstrings** — Module & function level; describe API contracts
3. **Path handling** — Always use `Path(__file__).parent` for relative paths
4. **Error messages** — User-friendly in UI; technical in logs
5. **Thread safety** — Never update GUI from worker thread directly
6. **File I/O** — Always use `with` statements; handle encoding
7. **Configuration** — Externalize all paths/emails/API URLs to config.py

---

## Dependencies

| Package | Purpose | Required | Location |
|---------|---------|----------|----------|
| requests | HTTP requests to API | Yes | logic.py |
| python-dotenv | Load .env files | No | config.py (optional) |
| tkinter | GUI framework | Yes | ui.py (built-in) |

If optional dependency unavailable, app should gracefully degrade.

---

## Key Files Reference

| File | Purpose | When to Modify |
|------|---------|----------------|
| `main.py` | Entry point | Adding initialization steps |
| `ui.py` | GUI & threading | UI changes, new dialogs, event handlers |
| `logic.py` | API & business logic | Search behavior, export format, error handling |
| `config.py` | Configuration | Adding new config options, defaults |
| `.env.example` | Config template | Documenting required variables |
| `requirements.txt` | Dependencies | Adding external packages |

---

## References

- [UniProtKB API](https://www.uniprot.org/help/api)
- [Python Tkinter threading](https://docs.python.org/3/library/threading.html)
- [Requests library](https://requests.readthedocs.io/)
- [Pathlib](https://docs.python.org/3/library/pathlib.html)

---

## Project Health Checklist

Before deploying changes:
- [ ] Threading doesn't block UI (test with slow network)
- [ ] Error messages are user-friendly
- [ ] Paths use `Path` not string concatenation
- [ ] File operations use `with` statements
- [ ] `.env` example matches expected variables
- [ ] API timeout set (10s default)
- [ ] Output directory created on first export
- [ ] No hardcoded paths/emails in code
