import os
from base64 import b64decode, b64encode
from typing import Tuple

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash

from deplatformer_webapp.crypto.exceptions import UserKeyNotFoundException

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


def decrypt_master_key(user_derived_key: bytes) -> Tuple[bytes, bytes]:
    master_key = UserKey.query.first()

    if master_key is None:
        raise UserKeyNotFoundException()

    iv = b64decode(master_key.iv)
    enc_master_key = b64decode(master_key.encrypted_key)

    cipher = Cipher(algorithms.AES(user_derived_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    dec_master_key = decryptor.update(enc_master_key) + decryptor.finalize()
    return dec_master_key, iv


def encrypt(plaintext: bytes, user_derived_key: bytes) -> bytes:
    dec_master_key, iv = decrypt_master_key(user_derived_key)

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(dec_master_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    return encryptor.update(padded_plaintext) + encryptor.finalize()


def encrypt_file(filepath: str, user_derived_key: bytes, dest=None) -> bytes:
    """
    Returns the encrypted ciphertext of a file. Also saves to dest if set
    """
    with open(filepath, "rb") as f:
        ciphertext = encrypt(f.read(), user_derived_key)
    if dest:
        with open(dest, "wb") as f:
            f.write(ciphertext)
    return ciphertext


def encrypt_dir(dir: str, key: bytes, recursive=True):
    ...


def decrypt(ciphertext: bytes, user_derived_key: bytes) -> bytes:
    dec_master_key, iv = decrypt_master_key(user_derived_key)

    cipher = Cipher(algorithms.AES(dec_master_key), modes.CBC(iv))
    decryptor = cipher.decryptor()

    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded_plaintext) + unpadder.finalize()


def decrypt_file(filepath: str, user_derived_key: bytes, dest=None) -> bytes:
    """
    Returns the decrypted bytes of an encrypted file. Also saves to dest if set
    """
    with open(filepath, "rb") as f:
        plaintext = decrypt(f.read(), user_derived_key)
    if dest:
        with open(dest, "wb") as f:
            f.write(plaintext)
    return plaintext
