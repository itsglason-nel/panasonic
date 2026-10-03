import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.services.pdf_generator import generate_tag_pdf

app = create_app()

with app.app_context():
    # Attempt to generate PDF for serial CW9-U-0001
    serial = 'CW9-U-0001'
    print(f"Generating PDF for {serial}...")
    success = generate_tag_pdf(serial)
    if success:
        print("PDF generated successfully!")
    else:
        print("Failed to generate PDF.")
