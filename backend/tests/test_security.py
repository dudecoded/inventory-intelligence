from app.core.security import hash_password,verify_password,create_access_token,decode_access_token
def test_password_hash_verifies_and_is_not_plaintext():
 encoded=hash_password('correct horse battery staple')
 assert encoded!='correct horse battery staple'
 assert verify_password('correct horse battery staple',encoded)
 assert not verify_password('wrong password',encoded)
def test_signed_token_roundtrip():
 token=create_access_token('42')
 assert decode_access_token(token)=='42'
 assert decode_access_token(token+'x') is None
