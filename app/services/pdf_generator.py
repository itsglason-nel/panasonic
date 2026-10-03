import os
import subprocess
from flask import current_app

def get_pdf_filepath(serial):
    """
    Determine the deep folder hierarchy for the given serial based on database records.
    Hierarchy: TAG_PDF_PATH / [Line No] / [Year] / [Month] / [Day] / <serial>_TAG.pdf
    """
    from app.models.fit import FIT
    from app.models.crs import CRS

    tag_pdf_path = current_app.config.get('TAG_PDF_PATH', r'C:\Users\DELL\Desktop\Product Info Tag')
    
    # Defaults
    lineno = "UNKNOWN_LINE"
    year, month, day = "YYYY", "MM", "DD"

    try:
        crs_data = CRS.query.filter_by(serial=serial).first()
        if crs_data and crs_data.lineno:
            lineno_val = str(crs_data.lineno).strip().upper()
            if lineno_val.startswith('L') and len(lineno_val) > 1 and lineno_val[1:].isdigit():
                lineno = lineno_val.replace('L', 'Line ')
            else:
                lineno = lineno_val

        fit_data = FIT.query.filter_by(serial=serial).first()
        if fit_data and fit_data.time:
            year = fit_data.time.strftime('%Y')
            month = fit_data.time.strftime('%B')
            day = fit_data.time.strftime('%d')
    except Exception as e:
        current_app.logger.warning(f"Error fetching hierarchy data for {serial}: {e}")

    hierarchy_path = os.path.join(tag_pdf_path, lineno, year, month, day)
    os.makedirs(hierarchy_path, exist_ok=True)
    
    return os.path.join(hierarchy_path, f"{serial}_TAG.pdf")

def generate_tag_pdf(serial, port=8080):
    """
    Generate a PDF of the Production Information Tag for the given serial.
    Uses headless Microsoft Edge to render the page and save it to the dynamically nested TAG_PDF_PATH.
    
    Args:
        serial (str): The unit serial number.
        port (int): The local server port (default 8080).
        
    Returns:
        bool: True if successful, False otherwise.
    """
    output_pdf = get_pdf_filepath(serial)
    url = f"http://127.0.0.1:{port}/internal/print-tag/{serial}"
    
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    browser_exe = next((p for p in edge_paths if os.path.exists(p)), None)
    
    if not browser_exe:
        current_app.logger.error("No compatible headless browser (Edge/Chrome) found on this system.")
        return False
        
    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={output_pdf}",
        "--no-margins",
        "--run-all-compositor-stages-before-draw",
        url
    ]
    
    try:
        # Give the browser time to render Javascript.
        cmd.extend(["--virtual-time-budget=2000"])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
            current_app.logger.info(f"Successfully generated PDF for {serial} at {output_pdf}")
            return True
        else:
            current_app.logger.error(f"Failed to generate PDF for {serial}. Output file empty or missing.")
            return False
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Failed to generate PDF for {serial}: {e.stderr}")
        return False
