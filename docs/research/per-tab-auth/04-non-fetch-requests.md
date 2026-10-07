Base commit: 0d7b700

# A4 NON-FETCH AUTHENTICATED REQUESTS

1. **File Downloads (PDFs, CSVs)**: 
   - `window.open('/admin/export_csv')` relies on the shared cookie.
   - Proposed conversion: Change to `fetch` with token, then trigger download via Blob URL. Risk: Memory overhead for very large files.
2. **Standard Form Posts**: 
   - Login form uses standard POST.
   - Proposed conversion: Convert to `fetch` or keep public.
3. **Iframes/Images**: 
   - No authenticated images found, but if any exist, they would rely on cookies.
