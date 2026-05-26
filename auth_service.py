from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import supabase_auth, supabase_admin

security = HTTPBearer()


def org_signup_service(email: str, password: str, org_id: str, org_name: str):
    """
    Creates:
    1. Supabase Auth user
    2. Organization row
    3. Profile row linking user to organization
    """

    existing_org = (
        supabase_admin
        .table("organizations")
        .select("*")
        .eq("org_id", org_id)
        .execute()
    )

    if existing_org.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization already exists"
        )

    try:
        # 1. Create Supabase Auth user
        auth_response = supabase_auth.auth.sign_up({
            "email": email,
            "password": password
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User signup failed"
            )

        user_id = auth_response.user.id

        # 2. Create organization
        supabase_admin.table("organizations").insert({
            "org_id": org_id,
            "org_name": org_name
        }).execute()

        # 3. Create profile mapping user -> org
        supabase_admin.table("profiles").insert({
            "id": user_id,
            "email": email,
            "org_id": org_id,
            "role": "org_admin"
        }).execute()

        return {
            "success": True,
            "message": "Organization signup successful",
            "org_id": org_id,
            "org_name": org_name,
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def signin_service(email: str, password: str):
    """
    Signs in user using Supabase Auth.
    Returns access_token to be used as Bearer token on protected routes.
    """

    try:
        response = supabase_auth.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        return {
            "success": True,
            "message": "Signin successful",
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verifies the Bearer token issued by Supabase on signin.
    Returns the user's profile row (includes org_id, role).
    """

    token = credentials.credentials

    try:
        user_response = supabase_auth.auth.get_user(token)

        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user_id = user_response.user.id

        profile = (
            supabase_admin
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        if not profile.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found"
            )

        return profile.data[0]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def check_org_access(request_org_id: str, current_user: dict):
    """
    Prevents one organization from accessing another organization's data.
    """

    if current_user["org_id"] != request_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )