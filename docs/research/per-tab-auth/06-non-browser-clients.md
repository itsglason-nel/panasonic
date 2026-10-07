Base commit: 0d7b700

# A6 NON-BROWSER CLIENTS
VERIFIED: Weight reader, tools/, and PLC observers do not make HTTP calls to the Flask application. They connect directly to MySQL or PLC hardware. Only browsers call the Flask app.
