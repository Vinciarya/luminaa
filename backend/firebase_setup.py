import firebase_admin
from firebase_admin import credentials
import os
import json
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """
    Initialize Firebase Admin SDK
    """
    try:
        # Check if already initialized
        if firebase_admin._apps:
            return firebase_admin.get_app()
        
        # Try to get credentials from environment variable (JSON string)
        firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
        
        if firebase_creds_json:
            try:
                creds_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(creds_dict)
                app = firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin initialized with environment variables")
                return app
            except json.JSONDecodeError:
                print("❌ Invalid JSON in FIREBASE_CREDENTIALS")
        
        # Try to get credentials from file path
        service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            app = firebase_admin.initialize_app(cred)
            print(f"✅ Firebase Admin initialized with {service_account_path}")
            return app
            
        # Fallback to default (for Google Cloud environment)
        app = firebase_admin.initialize_app()
        print("⚠️ Firebase Admin initialized with default credentials")
        return app
        
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        return None

# Initialize on import
firebase_app = initialize_firebase()
