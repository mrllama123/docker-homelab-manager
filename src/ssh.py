import functools
from io import StringIO

import paramiko

from src.models import SshKeyTypes


def generate_ssh_key(
    ssh_key_type: SshKeyTypes, ssh_key: str
) -> paramiko.Ed25519Key | paramiko.RSAKey | paramiko.DSSKey:
    if ssh_key_type == SshKeyTypes.ED25519:
        return paramiko.Ed25519Key.from_private_key(StringIO(ssh_key))
    if ssh_key_type == SshKeyTypes.RSA:
        return paramiko.RSAKey.from_private_key(StringIO(ssh_key))
    if ssh_key_type == SshKeyTypes.DSA:
        return paramiko.DSSKey.from_private_key(StringIO(ssh_key))
    msg = f"ssh key type {ssh_key_type} is not supported"
    raise NotImplementedError(msg)


@functools.lru_cache
def sftp_client(
    host: str,
    port: int,
    username: str,
    password: str,
    ssh_key_type: SshKeyTypes | None = None,
    ssh_key: str | None = None,
) -> paramiko.SFTPClient:
    if not password and not ssh_key:
        raise ValueError("You must provide either a password or an SSH key")

    auth_params = {"pkey": generate_ssh_key(ssh_key_type, ssh_key)} if ssh_key else {"password": password}
    client = paramiko.SSHClient()
    client.connect(hostname=host, port=port, username=username, **auth_params)
    return client.open_sftp()
