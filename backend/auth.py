from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth
from firebase_setup import firebase_app

# Bearer token scheme
security = HTTPBearer(auto_error=False)

def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify Firebase ID token
    """
    token = credentials.credentials
    
    try:
        # Verify token with Firebase Admin
        decoded_token = auth.verify_id_token(token)
        return decoded_token
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(user: dict = Depends(verify_firebase_token)):
    """
    Get current authenticated user
    """
    return user

def get_optional_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user (optional) - for guest mode
    """
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        # Verify token with Firebase Admin
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except:
        # If any error occurs (invalid token, expired, etc), return None (Guest)
        return None
