PDC Sprint 4.2.2a - TME connection fix

Copy these files into the project root, preserving the folder structure:

1. config.py
   -> <project root>/config.py

2. tme_connectivity_check.py
   -> <project root>/tme_connectivity_check.py

3. providers/tme/client.py
   -> <project root>/providers/tme/client.py

4. providers/tme/__init__.py
   -> <project root>/providers/tme/__init__.py

Allow the files to replace the current Sprint 4.2.2a versions.

No .env change is required. Keep:
TME_TOKEN=...
TME_APPLICATION_SECRET=...

Run from the project root:
python tme_connectivity_check.py

This update first calls POST /auth/token and then calls
GET /products/search with phrase and scope[]=products.

If it fails, retain the complete TmeApiError response text. The script now
prints the server response body, which should identify any remaining mismatch
in the authentication contract.
