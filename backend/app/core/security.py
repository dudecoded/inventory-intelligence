import base64, hashlib, hmac, json, os, time
from app.core.config import settings
def hash_password(password: str) -> str:
 salt=os.urandom(16); digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1)
 return "scrypt$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()
def verify_password(password: str, encoded: str) -> bool:
 try:
  scheme,salt_b64,digest_b64=encoded.split("$")
  if scheme!="scrypt": return False
  salt=base64.urlsafe_b64decode(salt_b64); expected=base64.urlsafe_b64decode(digest_b64)
  return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1),expected)
 except Exception: return False
def create_access_token(subject: str, expires_seconds:int=604800)->str:
 header={"alg":"HS256","typ":"JWT"}; payload={"sub":subject,"exp":int(time.time())+expires_seconds}
 enc=lambda obj:base64.urlsafe_b64encode(json.dumps(obj,separators=(",",":")).encode()).rstrip(b"=").decode()
 unsigned=enc(header)+"."+enc(payload)
 sig=base64.urlsafe_b64encode(hmac.new(settings.secret_key.encode(),unsigned.encode(),hashlib.sha256).digest()).rstrip(b"=").decode()
 return unsigned+"."+sig
def decode_access_token(token:str)->str|None:
 try:
  h,p,s=token.split("."); unsigned=h+"."+p
  expected=base64.urlsafe_b64encode(hmac.new(settings.secret_key.encode(),unsigned.encode(),hashlib.sha256).digest()).rstrip(b"=").decode()
  if not hmac.compare_digest(s,expected):return None
  payload=json.loads(base64.urlsafe_b64decode(p+"==="))
  if payload.get("exp",0)<time.time():return None
  return payload.get("sub")
 except Exception:return None
