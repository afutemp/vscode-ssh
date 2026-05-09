import re
import logging

COMMIT_HASH_RE = re.compile(r"^[0-9a-f]{40}$")


def is_valid_commit_hash(s: str) -> bool:
    return bool(COMMIT_HASH_RE.match(s))


def human_size(size_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def setup_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("vscode-sync")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
    return logger
