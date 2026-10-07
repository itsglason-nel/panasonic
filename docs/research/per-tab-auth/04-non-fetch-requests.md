Base commit: 0d7b700

# A4 NON-FETCH AUTHENTICATED REQUESTS
- `app/templates/admin/components/modals.html` uses `window.open` for generating PDFs and exporting CSVs. (e.g. `window.open('/admin/api/trigger-pdf/' + serial)`).
- The `href` links to downloads (if any) bypass JS `fetch`.
- The Login form (`auth.login`) is a standard `POST`.
