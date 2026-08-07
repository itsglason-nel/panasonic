"""
PMPC Data Logger — Barcode Parser
Decodes safety part 2D barcodes into part number, lot, etc.
"""

def decode_safety_part_qr(raw_qr):
    """
    Parse safety part 2D barcode.
    Format varies by supplier. This is a generic implementation
    that handles common delimited formats (| or ,).
    
    Example expected format: PartNumber|LotNumber|Date
    
    Returns: dict with part_number, lot_number
    """
    if not raw_qr:
        return None
        
    raw_qr = str(raw_qr).strip()
    
    # Common delimiters
    for delimiter in ['|', ',', ';']:
        if delimiter in raw_qr:
            parts = raw_qr.split(delimiter)
            if len(parts) >= 2:
                return {
                    'part_number': parts[0].strip(),
                    'lot_barcode': parts[1].strip(),
                    'raw': raw_qr
                }
                
    # If no known delimiter, treat the whole thing as part number
    return {
        'part_number': raw_qr,
        'lot_barcode': None,
        'raw': raw_qr
    }
