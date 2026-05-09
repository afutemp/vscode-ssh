import json
import logging
import urllib.request

from lib.utils import human_size

logger = logging.getLogger("vscode-sync")

RELEASES_URL = "https://update.code.visualstudio.com/api/releases/stable"
COMMITS_URL = "https://update.code.visualstudio.com/api/commits/stable"


def _fetch_json(url: str) -> list:
    """Fetch JSON array from URL with retry."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_version_commit_pairs(count: int) -> list[dict]:
    """Fetch the N most recent (version, commit) pairs from Microsoft API.

    Returns:
        [{"version": "1.119.0", "commit": "8b640eef..."}, ...]
    """
    logger.info("从 Microsoft API 获取版本列表...")
    releases = _fetch_json(RELEASES_URL)
    commits = _fetch_json(COMMITS_URL)

    # Two arrays are parallel-indexed but may differ in length
    max_pairs = min(len(releases), len(commits))
    logger.debug("获取到 %d 个版本, %d 个 commit", len(releases), len(commits))

    if count > max_pairs:
        logger.warning(
            "请求 %d 个版本，但只有 %d 个 commit 可用，将使用 %d 个",
            count, max_pairs, max_pairs,
        )
        count = max_pairs

    pairs = []
    for i in range(count):
        pairs.append({
            "version": releases[i],
            "commit": commits[i],
        })

    for p in pairs:
        logger.info("  %s (%s)", p["version"], p["commit"][:12])

    return pairs


def fetch_commit_for_version(version: str) -> str | None:
    """Fetch the commit hash for a specific version number."""
    # Build the mapping from the full releases/commits lists
    releases = _fetch_json(RELEASES_URL)
    commits = _fetch_json(COMMITS_URL)
    mapping = dict(zip(releases, commits))
    commit = mapping.get(version)
    if commit:
        logger.info("  %s -> %s", version, commit[:12])
    else:
        logger.warning("  %s 未在 Microsoft API 中找到", version)
    return commit
