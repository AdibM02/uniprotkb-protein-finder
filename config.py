"""Configuration management for UniProtKB Protein Finder.

Loads environment variables from a .env file (if present) and provides
configuration for API queries and application settings.
"""

import os
from pathlib import Path
from typing import Optional

# Try to load python-dotenv if available; otherwise use fallback
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class Config:
    """Configuration holder for the application."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file if available
        env_path = Path(__file__).parent / '.env'
        if env_path.exists() and DOTENV_AVAILABLE:
            load_dotenv(env_path)

        # Required configuration
        self.contact_email: str = os.getenv(
            'CONTACT_EMAIL',
            'user@example.com'  # Default email for API requests
        )

        # Optional configuration
        self.output_dir: str = os.getenv(
            'OUTPUT_DIR',
            str(Path(__file__).parent / 'output')
        )

        # API configuration
        self.uniprotkb_base_url: str = 'https://rest.uniprot.org/uniprotkb/search'
        self.uniprotkb_entry_url: str = 'https://rest.uniprot.org/uniprotkb'

        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def get_contact_email(self) -> str:
        """Return the configured contact email for API requests."""
        return self.contact_email

    def get_output_dir(self) -> str:
        """Return the output directory path."""
        return self.output_dir


# Global configuration instance
config = Config()
