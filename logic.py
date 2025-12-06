"""Business logic for UniProtKB Protein Finder.

This module handles:
- UniProtKB API queries
- Protein and domain data extraction
- JSON output generation
- Error handling and validation
"""

import json
import re
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import requests
except ImportError:
    requests = None

try:
    from Bio.SeqIO import uniprot_rest_client
except ImportError:
    uniprot_rest_client = None

from config import config


class ProteinNotFoundError(Exception):
    """Raised when a protein is not found in UniProtKB."""
    pass


class SpeciesNotFoundError(Exception):
    """Raised when a species is not found in the search results."""
    pass


class APIError(Exception):
    """Raised when the UniProtKB API returns an error."""
    pass


class UniProtKBClient:
    """Client for querying UniProtKB API."""

    # Common species names with their NCBI Taxonomy IDs
    SPECIES_MAP = {
        'Human': 'Homo sapiens',
        'Mouse': 'Mus musculus',
        'Rat': 'Rattus norvegicus',
        'Yeast': 'Saccharomyces cerevisiae',
        'E. coli': 'Escherichia coli',
        'Arabidopsis': 'Arabidopsis thaliana',
        'Zebrafish': 'Danio rerio',
        'Drosophila': 'Drosophila melanogaster',
        'C. elegans': 'Caenorhabditis elegans',
        'Chicken': 'Gallus gallus',
    }

    def __init__(self):
        """Initialize the UniProtKB client."""
        if requests is None:
            raise ImportError(
                "The 'requests' library is required. "
                "Install it with: pip install requests"
            )
        self.base_url = config.uniprotkb_base_url
        self.entry_url = config.uniprotkb_entry_url
        self.contact_email = config.get_contact_email()
        self.headers = {'User-Agent': f'ProteinFinder/1.0 ({self.contact_email})'}

    def search_protein(
        self,
        protein_name: str,
        species: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for a protein in UniProtKB.

        Args:
            protein_name: Name of the protein to search for
            species: Common or scientific species name (optional, for UI only)

        Returns:
            Dictionary containing protein information

        Raises:
            ProteinNotFoundError: If protein not found
            SpeciesNotFoundError: If species not found in results
            APIError: If API call fails

        Note:
            The species filter is applied by the UI; the API query only uses protein name
            for reliability. Users should refine results by examining the returned protein's
            species information.
        """
        # Build query - use only protein name for API reliability
        query = protein_name

        try:
            # Query UniProtKB
            params = {
                'query': query,
                'format': 'json',
                'size': 10  # Get top 10 results to filter by species
            }
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if not data.get('results'):
                raise ProteinNotFoundError(
                    f"Protein '{protein_name}' not found in UniProtKB. "
                    "Check the protein name and try again."
                )

            # If species is specified, try to find a matching result
            entry = None
            if species:
                species_sci = self.SPECIES_MAP.get(species, species)
                for result in data['results']:
                    organism = result.get('organism', {})
                    result_species = organism.get('scientificName', '')
                    if species_sci.lower() in result_species.lower():
                        entry = result
                        break

                if not entry:
                    # Fall back to first result if species not found
                    entry = data['results'][0]
                    first_species = entry.get('organism', {}).get('scientificName', 'Unknown')
                    # Don't fail, just inform user
            else:
                # No species specified, use first result
                entry = data['results'][0]

            uniprot_id = entry['primaryAccession']

            # Fetch full entry data (includes domains and regions)
            full_entry = self._fetch_entry(uniprot_id)

            return full_entry

        except requests.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")

    def _fetch_entry(self, uniprot_id: str) -> Dict[str, Any]:
        """Fetch full UniProtKB entry data.

        Args:
            uniprot_id: UniProt accession ID

        Returns:
            Dictionary with entry data
        """
        try:
            url = f'{self.entry_url}/{uniprot_id}'
            params = {'format': 'json'}
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Failed to fetch entry {uniprot_id}: {str(e)}")

    def extract_data(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract protein name, sequence, and domains from a UniProtKB entry.

        Args:
            entry: Full UniProtKB entry JSON

        Returns:
            Dictionary with extracted data
        """
        # Extract basic info
        protein_name = entry.get('uniProtkbId', 'Unknown')
        organism = entry.get('organism', {})
        species = organism.get('scientificName', 'Unknown')
        sequence = entry.get('sequence', {}).get('value', '')

        # Extract features (domains and regions)
        domains = []
        features = entry.get('features', [])

        for feature in features:
            feature_type = feature.get('type', '')
            # Look for domain, region, and active site annotations
            if feature_type in ['Domain', 'Region', 'Active site', 'Binding site']:
                location = feature.get('location', {})
                start = location.get('start', {}).get('value')
                end = location.get('end', {}).get('value')

                if start is not None and end is not None:
                    # Extract domain sequence
                    domain_seq = sequence[start - 1:end] if sequence else ''

                    description = feature.get('description', feature_type)

                    domains.append({
                        'name': description,
                        'type': feature_type,
                        'start': start,
                        'end': end,
                        'sequence': domain_seq
                    })

        return {
            'protein_name': protein_name,
            'species': species,
            'full_sequence': sequence,
            'sequence_length': len(sequence),
            'domains': domains
        }

    @staticmethod
    def get_common_species() -> List[str]:
        """Return list of common species names."""
        return list(UniProtKBClient.SPECIES_MAP.keys())


class ProteinDataExporter:
    """Export protein data to JSON format and manage search history."""

    # Search history file path
    HISTORY_FILE = Path(__file__).parent / 'output' / 'search_history.csv'

    @staticmethod
    def export_to_json(
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export protein data to a JSON file.

        Args:
            data: Dictionary with protein data
            filename: Output filename (optional; auto-generated if not provided)

        Returns:
            Path to the created JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            protein_name = data.get('protein_name', 'protein').replace('_', '-')
            filename = f'protein_{protein_name}_{timestamp}.json'

        output_path = Path(config.get_output_dir()) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare JSON structure
        json_data = {
            'protein_name': data.get('protein_name', ''),
            'species': data.get('species', ''),
            'full_sequence': data.get('full_sequence', ''),
            'sequence_length': data.get('sequence_length', 0),
            'domains': data.get('domains', []),
            'exported_at': datetime.now().isoformat()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return str(output_path)

    @staticmethod
    def log_search_to_history(
        protein_name: str,
        species: Optional[str] = None,
        success: bool = True
    ) -> None:
        """Log search query to CSV history file for tracking.

        Args:
            protein_name: Name of protein searched
            species: Species filter used (optional)
            success: Whether search succeeded

        File format: timestamp, protein_name, species, success
        """
        history_file = Path(config.get_output_dir()) / 'search_history.csv'
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists to determine if we need headers
        file_exists = history_file.exists()

        try:
            with open(history_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header if file is new
                if not file_exists:
                    writer.writerow(['timestamp', 'protein_name', 'species', 'success'])

                # Write search record
                writer.writerow([
                    datetime.now().isoformat(),
                    protein_name,
                    species or 'All',
                    'Yes' if success else 'No'
                ])
        except IOError as e:
            # Silently fail to avoid blocking UI if file write fails
            print(f"Warning: Could not log search to history: {e}")


class ProteinSearchService:
    """High-level service for protein searching."""

    def __init__(self):
        """Initialize the service."""
        self.client = UniProtKBClient()
        self.exporter = ProteinDataExporter()

    def search(
        self,
        protein_name: str,
        species: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for a protein and return extracted data.

        Args:
            protein_name: Name of the protein
            species: Species name (optional)

        Returns:
            Dictionary with protein data (name, species, sequence, domains)

        Raises:
            ProteinNotFoundError, SpeciesNotFoundError, APIError
        """
        try:
            # Search for protein
            entry = self.client.search_protein(protein_name, species)

            # Extract and return data
            data = self.client.extract_data(entry)

            # Log successful search
            self.exporter.log_search_to_history(protein_name, species, success=True)

            return data

        except (ProteinNotFoundError, SpeciesNotFoundError, APIError) as e:
            # Log failed search
            self.exporter.log_search_to_history(protein_name, species, success=False)
            raise

    def search_and_export(
        self,
        protein_name: str,
        species: Optional[str] = None
    ) -> tuple[str, str]:
        """Search for a protein and export data to JSON (legacy method).

        Args:
            protein_name: Name of the protein
            species: Species name (optional)

        Returns:
            Tuple of (json_file_path, status_message)

        Raises:
            ProteinNotFoundError, SpeciesNotFoundError, APIError
        """
        data = self.search(protein_name, species)

        # Export to JSON
        json_path = self.exporter.export_to_json(data)

        status_message = (
            f"✓ Successfully found protein '{data['protein_name']}' "
            f"from {data['species']}. "
            f"Data saved to:\n{json_path}"
        )

        return json_path, status_message

