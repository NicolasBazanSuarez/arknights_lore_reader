import subprocess
from pathlib import Path

SERVER_USER = "nico"
SERVER_HOST = "192.168.1.139"

SERVER_INCOMING_DIR = (
    "/home/nico/kindle-manga/"
    "incoming/arknights"
)


def send_epub_to_server(
    epub_path: Path
) -> None:

    epub_path = epub_path.resolve()

    if not epub_path.exists():
        raise FileNotFoundError(
            epub_path
        )

    command = [
        "scp",
        str(epub_path),
        (
            f"{SERVER_USER}@"
            f"{SERVER_HOST}:"
            f"{SERVER_INCOMING_DIR}/"
        )
    ]

    subprocess.run(
        command,
        check=True
    )