import sys
import os

# Ensure project root and cloud_deployment are on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cloud_deployment'))

from cloud_deployment.main import app

# Vercel serverless entrypoint
