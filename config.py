import os

LOGINPASSWD = os.environ.get('PASSWORD', False)
NODE_ID = int(os.environ.get('NODE_ID', False))

TGREEN = '\033[32m' # Green Text
TRED = '\033[31m' # Red Text
TLOAD = '\033[33m'
ENDC = '\033[m'
secondary_ip = False
primary_ip = None
