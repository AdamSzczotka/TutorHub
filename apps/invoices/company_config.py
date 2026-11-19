"""Seller details printed on invoices.

Defaults are placeholders. Set the real values on the server via environment
variables (COMPANY_NAME, COMPANY_NIP, COMPANY_BANK_ACCOUNT, ...), e.g. in .env.
"""

import os

_DEFAULTS = {
    'name': 'Na Piątkę - Szkoła Korepetycji',
    'address': 'ul. Edukacyjna 123',
    'city': 'Warszawa',
    'postal_code': '00-001',
    'nip': '1234567890',
    'regon': '123456789',
    'phone': '+48 123 456 789',
    'email': 'kontakt@napiatke.pl',
    'website': 'www.napiatke.pl',
    'bank_account': 'PL 12 3456 7890 1234 5678 9012 3456',
    'bank_name': 'Bank Example SA',
}

COMPANY_DETAILS = {
    key: os.environ.get(f'COMPANY_{key.upper()}', default)
    for key, default in _DEFAULTS.items()
}
