import logging
from pathlib import Path

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from lib.config import DOWNLOAD_BASE_URL, CLI_FILENAME, FILENAME
from lib.utils import human_size

logger = logging.getLogger("vscode-sync")


def _download_file(
    url: str,
    dest: Path,
    desc: str,
    min_size: int = 50 * 1024 * 1024,
) -> Path:
    """Generic download with progress bar, resume support, and size validation."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {}
    existing_size = 0
    if dest.exists():
        existing_size = dest.stat().st_size
        headers["Range"] = f"bytes={existing_size}-"
        logger.info("断点续传，已下载 %s", human_size(existing_size))

    resp = requests.get(url, headers=headers, stream=True, timeout=30)
    if resp.status_code == 416:
        # File already fully downloaded (Range Not Satisfiable)
        resp.close()
        logger.info("文件已完整: %s (%s)", dest.name, human_size(existing_size))
        return dest
    resp.raise_for_status()

    total_size = int(resp.headers.get("Content-Length", 0))
    if existing_size and resp.status_code == 206:
        total_size += existing_size
    elif resp.status_code == 200:
        existing_size = 0

    mode = "ab" if existing_size else "wb"
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    with progress:
        task = progress.add_task(
            desc,
            total=total_size if total_size else None,
            completed=existing_size,
        )
        with open(dest, mode) as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                progress.update(task, advance=len(chunk))

    file_size = dest.stat().st_size
    if file_size < min_size:
        dest.unlink()
        raise RuntimeError(
            f"下载的文件过小 ({human_size(file_size)})，可能损坏"
        )

    logger.info("下载完成: %s (%s)", dest.name, human_size(file_size))
    return dest


def download_vscode_server(
    commit: str,
    dest: Path,
    base_url: str = DOWNLOAD_BASE_URL,
) -> Path:
    """Download a VS Code Server tarball from Microsoft CDN."""
    url = f"{base_url}/stable/{commit}/{FILENAME}"
    return _download_file(url, dest, f"下载 server {commit[:12]}")


def download_vscode_cli(
    commit: str,
    dest: Path,
    base_url: str = DOWNLOAD_BASE_URL,
) -> Path:
    """Download a VS Code CLI tarball from Microsoft CDN."""
    url = f"{base_url}/stable/{commit}/{CLI_FILENAME}"
    return _download_file(url, dest, f"下载 CLI {commit[:12]}", min_size=5 * 1024 * 1024)
