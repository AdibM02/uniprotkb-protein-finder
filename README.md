# UniProtKB Protein Finder

A modern, responsive Tkinter GUI application that searches UniProtKB for proteins, retrieves their sequences and domain information, and displays results instantly in the interface. Designed with clean code architecture and API integration best practices.

## Features

- 🔍 **Smart Search Interface**: Enter protein name and optionally select species with dropdown suggestions
- ⚡ **Instant Results**: View search results directly in the GUI with full protein sequences and domain information
- 🧬 **UniProtKB Integration**: Queries the official UniProtKB REST API (free, no authentication needed)
- 📊 **Domain Visualization**: Shows protein domains, regions, binding sites, and active sites with exact positions
- 🚀 **Responsive Threading**: Background API calls keep UI responsive even with slow network
- 🔧 **Configuration Management**: Optional `.env` file support with sensible defaults
- 💾 **Export Capability**: Optional JSON export of search results for further analysis
- ❌ **Robust Error Handling**: User-friendly error messages with troubleshooting tips

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests
pip install python-dotenv  # Optional: For .env file support
```

### 2. Configure Environment (Optional)

Copy `.env.example` to `.env` to customize settings:

```bash
cp .env.example .env
```

Edit `.env` with your email and preferences:
```env
CONTACT_EMAIL=your.email@example.com
OUTPUT_DIR=./output
```

**Why the contact email?**  
UniProtKB API requests require a contact email. This helps them monitor usage and reach out if issues arise. See their [API documentation](https://www.uniprot.org/help/api).

## Usage

### Launch the Application

```bash
python main.py
```

### Using the GUI

1. **Enter Protein Name**: Type the name of a protein (e.g., "hemoglobin", "insulin", "lysozyme")
2. **Select Species** (optional): 
   - Choose from dropdown (Human, Mouse, E. coli, etc.)
   - Or type a custom species name
3. **Click Search**: Queries UniProtKB and displays results instantly in the GUI
4. **View Results**: 
   - Full protein sequence displayed
   - All domains and regions listed with positions and sequences
   - Formatted output showing protein name, species, and domain information

### Example Searches

- **Protein**: "hemoglobin" | **Species**: "Human"
- **Protein**: "TP53" (tumor suppressor) | **Species**: "Human"
- **Protein**: "lactase" | **Species**: "Human"
- **Protein**: "lacZ" | **Species**: "E. coli"

## Results Display Format

Results are displayed directly in the GUI (no file downloads):

```
✓ FOUND: HBB_HUMAN
Species: Homo sapiens
Sequence Length: 146 amino acids

Full Sequence:
MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHG...

============================================================
DOMAINS & REGIONS (7 found):
============================================================

[1] Globin
    Type: Domain
    Position: 1-146
    Sequence: MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHG...

[2] Heme iron coordination
    Type: Active site
    Position: 92-92
    Sequence: H
```

## Project Structure

```
.
├── main.py                 # Application entry point
├── ui.py                   # Tkinter GUI interface
├── logic.py                # API client & business logic
├── config.py               # Configuration & .env loader
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore             # Git ignore rules
├── .github/
│   └── copilot-instructions.md  # AI coding agent guidance
├── output/                 # Export directory (auto-created)
└── README.md              # This file
```

## File Descriptions

### `main.py`
**Entry point** — Sets up module path and launches the GUI application.

### `ui.py`
**GUI Layer** (`ProteinFinderGUI` class):
- Text input for protein name search
- Dropdown combobox with common species suggestions
- Search button with background thread execution
- Live results display (protein sequence + domains)
- Status area with color-coded messages
- Error dialogs for user guidance

**Key pattern**: All long operations run on background threads via `_search_worker()` to keep UI responsive.

### `logic.py`
**Business Logic Layer**:
- `UniProtKBClient`: REST API client for UniProtKB
  - `search_protein()`: Query API, handle species filtering
  - `extract_data()`: Parse protein/domain information
- `ProteinSearchService`: High-level orchestration
  - `search()`: Get protein data for GUI display
  - `search_and_export()`: Search + JSON export (optional)
- `ProteinDataExporter`: JSON file writing
- Custom exceptions: `ProteinNotFoundError`, `SpeciesNotFoundError`, `APIError`
- `SPECIES_MAP`: Common name → scientific name mapping

### `config.py`
**Configuration Management**:
- Loads `.env` file if `python-dotenv` installed
- Provides `contact_email` (required for API) and `output_dir` (optional)
- Auto-creates output directory
- Fallback defaults ensure functionality without config file

## API Integration

The application uses the **UniProtKB REST API** (free, no authentication required):
- Base search: `https://rest.uniprot.org/uniprotkb/search`
- Entry fetch: `https://rest.uniprot.org/uniprotkb/{id}`

**Note**: The API respects rate limits. For high-volume queries, consider implementing retry logic or caching.

## Error Handling

The application handles several error scenarios:

| Error | User Message | Action |
|-------|--------------|--------|
| Protein not found | Clear message with suggestion to check name | Stays open for retry |
| Species not found in results | Suggests trying different name/species | Stays open for retry |
| Network error | Shows API error with troubleshooting tip | Stays open for retry |
| Missing input | Error dialog requires input | No API call made |
| Unexpected error | Shows error details | Stays open for retry |

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### "Connection timeout" or "Failed to connect"
1. Verify internet connection
2. Check UniProtKB API status: https://rest.uniprot.org
3. Check your firewall/proxy settings
4. Try searching again after a delay (respects rate limits)

### GUI doesn't appear
- **Windows/macOS**: Tkinter usually included; ensure Python installed from official source
- **Linux**: `sudo apt-get install python3-tk`
- Test Tkinter: `python -c "import tkinter; print('OK')"`

### "Output directory issues"
- Verify `OUTPUT_DIR` path in `.env` is writable
- Default: `./output` (auto-created if missing)
- Check file permissions if JSON export fails

### Results not showing for a valid protein
- Try exact protein ID instead of name (e.g., "HBB_HUMAN" instead of "hemoglobin")
- Species filter may be too restrictive; try leaving it empty
- Check UniProtKB website directly to confirm protein exists

## Code Architecture

### Separation of Concerns
- **ui.py**: Only handles GUI rendering and user interaction
- **logic.py**: Only handles API communication and data processing
- **config.py**: Centralized configuration
- **main.py**: Application entry point

### Key Design Patterns
- **Threading**: UI remains responsive during API calls
- **Exception Hierarchy**: Custom exceptions for clear error handling
- **Service Layer**: `ProteinSearchService` orchestrates high-level workflows
- **Graceful Degradation**: Optional dependencies (dotenv, Biopython) don't break core functionality

## Future Enhancements

- [ ] Add sequence alignment visualization
- [ ] Support batch queries from CSV
- [ ] Cache results locally to avoid redundant API calls
- [ ] Export to FASTA format
- [ ] Add protein structure visualization (PDB integration)
- [ ] Implement search history
- [ ] Add protein interaction network display

## References

- [UniProtKB REST API Documentation](https://www.uniprot.org/help/api)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Biopython](https://biopython.org/)

## Learning & Development

### Architecture Highlights
This project demonstrates professional Python patterns:
- **Separation of Concerns**: Logic/UI/Config layers independent
- **Threading Pattern**: Background API calls with thread-safe GUI updates
- **Error Handling**: Custom exceptions with meaningful messages
- **Configuration**: Environment-based config with sensible defaults
- **RESTful API**: Modern async-style design
- **File I/O**: JSON export with proper path handling

### Testing the API
Test the UniProtKB API directly:
```bash
curl "https://rest.uniprot.org/uniprotkb/search?query=hemoglobin&format=json"
```

### Contributing
Feel free to fork, modify, and extend this project for your use cases.

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review UniProtKB API docs: https://www.uniprot.org/help/api
3. Open an issue on GitHub
