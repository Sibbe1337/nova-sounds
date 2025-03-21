import os
import dotenv
from pathlib import Path

# Load .env file
env_path = Path('.') / '.env'
dotenv.load_dotenv(dotenv_path=env_path)

# Print environment variables
print(f"DEV_MODE environment variable: {os.environ.get('DEV_MODE')}")
print(f"DEV_MODE as boolean: {os.environ.get('DEV_MODE', 'true').lower() == 'true'}")

# Check other variables
print("\nOther environment variables:")
for key in ['GOOGLE_API_KEY', 'GOOGLE_CLOUD_PROJECT', 'API_URL']:
    print(f"{key}: {os.environ.get(key)}") 