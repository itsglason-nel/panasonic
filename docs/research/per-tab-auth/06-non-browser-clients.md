Base commit: 0d7b700

# A6 NON-BROWSER CLIENTS

- **Weight Reader**: Connects directly via serial/TCP to PLC or runs locally. No HTTP API calls to the Flask app found in the repository.
- **Tools**: `alter_db.py` connects directly to MySQL. It does NOT use HTTP.
- **Conclusion**: VERIFIED. Only browsers call the Flask HTTP application.
