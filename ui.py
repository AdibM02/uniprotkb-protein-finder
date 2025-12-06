"""Tkinter GUI for UniProtKB Protein Finder.

Provides a user-friendly interface for searching proteins and retrieving their
sequence and domain information from UniProtKB.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from logic import (
    ProteinSearchService,
    ProteinNotFoundError,
    SpeciesNotFoundError,
    APIError,
    UniProtKBClient
)


class ProteinFinderGUI:
    """Tkinter GUI for protein search and data retrieval."""

    def __init__(self, root: tk.Tk):
        """Initialize the GUI.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title('UniProtKB Protein Finder')
        self.root.geometry('700x500')
        self.root.resizable(True, True)

        self.service = ProteinSearchService()
        self.is_searching = False

        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text='UniProtKB Protein Finder',
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Protein name input
        ttk.Label(main_frame, text='Protein Name:').grid(
            row=1, column=0, sticky='w', padx=(0, 10)
        )
        self.protein_entry = ttk.Entry(main_frame, width=40)
        self.protein_entry.grid(row=1, column=1, sticky='ew', padx=(0, 10))
        self.protein_entry.bind('<Return>', lambda e: self._on_search_clicked())

        # Species selection
        ttk.Label(main_frame, text='Species:').grid(
            row=2, column=0, sticky='w', padx=(0, 10), pady=(10, 0)
        )

        species_frame = ttk.Frame(main_frame)
        species_frame.grid(row=2, column=1, sticky='ew', pady=(10, 0))
        species_frame.columnconfigure(0, weight=1)

        # Dropdown with common species
        self.species_var = tk.StringVar()
        self.species_dropdown = ttk.Combobox(
            species_frame,
            textvariable=self.species_var,
            values=UniProtKBClient.get_common_species(),
            state='normal',
            width=37
        )
        self.species_dropdown.grid(row=0, column=0, sticky='ew')
        self.species_dropdown.bind('<<ComboboxSelected>>', lambda e: None)

        # Search button
        search_button = ttk.Button(
            main_frame,
            text='Search',
            command=self._on_search_clicked
        )
        search_button.grid(
            row=3, column=0, columnspan=2, pady=15, sticky='ew'
        )

        # Status area
        ttk.Label(main_frame, text='Status:').grid(
            row=4, column=0, sticky='nw', padx=(0, 10), pady=(10, 0)
        )

        # Text widget with scrollbar for status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=1, sticky='nsew', pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(status_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self.status_text = tk.Text(
            status_frame,
            height=15,
            width=40,
            state='disabled',
            yscrollcommand=scrollbar.set
        )
        self.status_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.status_text.yview)

        # Footer info
        footer_label = ttk.Label(
            main_frame,
            text='Tip: Enter a protein name and optionally select a species.',
            font=('Helvetica', 8),
            foreground='gray'
        )
        footer_label.grid(row=5, column=0, columnspan=2, pady=(10, 0))

    def _on_search_clicked(self):
        """Handle search button click."""
        if self.is_searching:
            messagebox.showwarning('Busy', 'A search is already in progress.')
            return

        protein_name = self.protein_entry.get().strip()
        species = self.species_var.get().strip() or None

        if not protein_name:
            messagebox.showerror('Input Error', 'Please enter a protein name.')
            return

        # Start search in background thread to keep UI responsive
        thread = threading.Thread(
            target=self._search_worker,
            args=(protein_name, species),
            daemon=True
        )
        thread.start()

    def _search_worker(self, protein_name: str, species: Optional[str]):
        """Worker thread for protein search.

        Args:
            protein_name: Name of the protein
            species: Species (optional)
        """
        self.is_searching = True
        self._update_status('Searching...', 'blue')

        try:
            # Search without exporting
            data = self.service.search(protein_name, species)
            
            # Format and display results
            message = self._format_results(data)
            self._update_status(message, 'green')

        except ProteinNotFoundError as e:
            self._update_status(f'❌ {str(e)}', 'red')

        except SpeciesNotFoundError as e:
            self._update_status(f'❌ {str(e)}', 'red')

        except APIError as e:
            self._update_status(
                f'❌ API Error: {str(e)}\n\n'
                'Please check your internet connection and try again.',
                'red'
            )

        except Exception as e:
            self._update_status(
                f'❌ Unexpected error: {str(e)}',
                'red'
            )

        finally:
            self.is_searching = False

    def _format_results(self, data: dict) -> str:
        """Format protein data for display.

        Args:
            data: Dictionary with protein information

        Returns:
            Formatted string for display
        """
        result = f"✓ FOUND: {data['protein_name']}\n"
        result += f"Species: {data['species']}\n"
        result += f"Sequence Length: {data['sequence_length']} amino acids\n"
        result += f"\nFull Sequence:\n{data['full_sequence']}\n"
        result += f"\n{'='*60}\n"
        result += f"DOMAINS & REGIONS ({len(data['domains'])} found):\n"
        result += f"{'='*60}\n"

        for i, domain in enumerate(data['domains'], 1):
            result += f"\n[{i}] {domain['name'] or domain['type']}\n"
            result += f"    Type: {domain['type']}\n"
            result += f"    Position: {domain['start']}-{domain['end']}\n"
            if domain['sequence']:
                seq_preview = domain['sequence'][:50]
                seq_preview += "..." if len(domain['sequence']) > 50 else ""
                result += f"    Sequence: {seq_preview}\n"

        return result

    def _update_status(self, message: str, color: str = 'black'):
        """Update status text area.

        Args:
            message: Status message to display
            color: Text color ('black', 'green', 'red', 'blue')
        """
        self.root.after(0, self._do_update_status, message, color)

    def _do_update_status(self, message: str, color: str):
        """Actually update the status text (must run on main thread).

        Args:
            message: Message to display
            color: Text color
        """
        self.status_text.config(state='normal')
        self.status_text.delete('1.0', 'end')
        self.status_text.insert('1.0', message)
        self.status_text.tag_configure('status_color', foreground=color)
        self.status_text.tag_add('status_color', '1.0', 'end')
        self.status_text.config(state='disabled')


def run_gui():
    """Launch the GUI application."""
    root = tk.Tk()
    app = ProteinFinderGUI(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
