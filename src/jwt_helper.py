from flask_jwt_extended import get_jwt_identity, get_jwt

def current_identity():
    """Return an identity dict with keys: id, role, username.

    Works whether the JWT identity was stored as a dict (legacy) or a scalar
    (new behavior where sub must be string). If scalar, additional claims
    'role' and 'username' are read from the token claims.
    
    Returns None if no valid JWT token is present.
    """
    try:
        idv = get_jwt_identity()
        
        # No token present
        if idv is None:
            return None
            
        if isinstance(idv, dict):
            return idv

        # else assemble from sub + additional claims
        claims = get_jwt() or {}

        # Prefer explicit 'id' claim if provided (created via additional_claims)
        claim_id = claims.get('id')
        if claim_id is not None:
            try:
                claim_id = int(claim_id)
            except Exception:
                pass
            user_id = claim_id
        else:
            # try to coerce numeric subject back to int
            try:
                if isinstance(idv, str) and idv.isdigit():
                    user_id = int(idv)
                else:
                    user_id = idv
            except Exception:
                user_id = idv

        return {
            'id': user_id,
            'role': claims.get('role'),
            'username': claims.get('username')
        }
    except Exception:
        # Token invalid or expired
        return None
