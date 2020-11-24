import os
from base64 import b64encode

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash

from ..models.user_models import UserKey


def derive_key_from_usercreds(username, password, length=32):
    ckdf = ConcatKDFHash(
        algorithm=hashes.SHA256(),
        length=length,
        otherinfo=username,
    )
    return ckdf.derive(password)


def generate_new_user_key(username, password):
    if type(username) == str:
        username = username.encode("utf-8")
    if type(password) == str:
        password = password.encode("utf-8")

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(derive_key_from_usercreds(username, password)), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_user_key = encryptor.update(os.urandom(32)) + encryptor.finalize()
    return encrypted_user_key, iv


def create_user_key_if_not_exists(username, password, db):
    user_keys = UserKey.query.all()
    if len(user_keys) == 0:
        enc_user_key, iv = generate_new_user_key(username, password)
        user_key = UserKey(encrypted_key=b64encode(enc_user_key), iv=b64encode(iv))
        db.session.add(user_key)
    db.session.commit()


def replace_or_create_user_key(db, enc_user_key, iv):
    user_keys = UserKey.query.all()
    if len(user_keys) > 0:
        user_keys[0].key = b64encode(enc_user_key)
        user_keys[0].iv = iv
    else:
        user_key = UserKey(encrypted_key=enc_user_key, iv=iv)
        db.session.add(user_key)
    db.session.commit()

def encrypt_dir(recursive=True):
    ...