import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")
SECRET = os.getenv("SECRET_KEY", "development-only-secret-change-before-production-32")
def hash_password(p:str): return pwd.hash(p)
def verify_password(p:str, h:str): return pwd.verify(p,h)
def create_token(user:User): return jwt.encode({"sub":str(user.id),"role":user.role,"exp":datetime.now(timezone.utc)+timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","480")))}, SECRET, algorithm="HS256")
def current_user(token:str=Depends(oauth2), db:Session=Depends(get_db)):
    try: uid=int(jwt.decode(token,SECRET,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(status_code=401,detail="Invalid or expired token")
    u=db.get(User,uid)
    if not u: raise HTTPException(status_code=401,detail="User not found")
    return u
def manager_required(u:User=Depends(current_user)):
    if u.role != "manager": raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Manager access required")
    return u
def admin_required(u:User=Depends(current_user)):
    if u.role != "admin": raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Admin access required")
    return u
