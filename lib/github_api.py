import logging
import time

import requests

GITHUB_API_BASE = "https://api.github.com"
GITHUB_UPLOAD_BASE = "https://uploads.github.com"

logger = logging.getLogger("vscode-sync")


class GitHubClient:
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _url(self, path: str) -> str:
        return f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}{path}"

    def _check_rate_limit(self, resp: requests.Response):
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining and int(remaining) <= 1:
            reset = int(resp.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - int(time.time()), 1)
            logger.warning("GitHub API 速率限制，等待 %d 秒...", wait)
            time.sleep(wait)

    def repo_exists(self) -> bool:
        resp = self.session.get(f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}")
        return resp.status_code == 200

    def create_repo(self, description: str = "VS Code Server offline packages"):
        resp = self.session.post(
            f"{GITHUB_API_BASE}/user/repos",
            json={
                "name": self.repo,
                "description": description,
                "private": True,
                "auto_init": False,
            },
        )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"创建仓库失败: {resp.status_code} {resp.text}")
        logger.info("已创建私有仓库 %s/%s", self.owner, self.repo)

    def list_releases(self) -> list[str]:
        """List all release tag names."""
        tags = []
        page = 1
        while True:
            resp = self.session.get(
                self._url("/releases"),
                params={"per_page": 100, "page": page},
            )
            self._check_rate_limit(resp)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            tags.extend(r["tag_name"] for r in data)
            if len(data) < 100:
                break
            page += 1
        return tags

    def delete_release(self, tag: str) -> None:
        """Delete a release (and its tag) by tag name."""
        resp = self.session.get(self._url(f"/releases/tags/{tag}"))
        if resp.status_code != 200:
            logger.debug("Release %s 不存在，跳过删除", tag)
            return
        release_id = resp.json()["id"]
        resp = self.session.delete(self._url(f"/releases/{release_id}"))
        self._check_rate_limit(resp)
        if resp.status_code == 204:
            logger.debug("已删除 release %s", tag)
        # Also delete the tag
        self.session.delete(
            self._url(f"/git/refs/tags/{tag}")
        )

    def create_release(self, tag: str, title: str, body: str = "") -> dict:
        """Create a new release. Returns the release JSON."""
        resp = self.session.post(
            self._url("/releases"),
            json={
                "tag_name": tag,
                "name": title,
                "body": body,
                "draft": False,
                "prerelease": False,
            },
        )
        self._check_rate_limit(resp)
        resp.raise_for_status()
        logger.info("已创建 release %s", tag)
        return resp.json()

    def upload_asset(self, release: dict, file_path: str, name: str | None = None, content_type: str = "application/octet-stream") -> dict:
        """Upload a file as a release asset."""
        upload_url = release["upload_url"].split("{")[0]  # Remove {?name,label} template
        filename = name or file_path.rsplit("/", 1)[-1]

        with open(file_path, "rb") as f:
            resp = requests.post(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.session.headers['Authorization'].replace('Bearer ', '')}",
                    "Accept": "application/vnd.github+json",
                    "Content-Type": content_type,
                },
                params={"name": filename},
                data=f,
                timeout=600,
            )

        self._check_rate_limit(resp)
        resp.raise_for_status()
        size_mb = resp.json().get("size", 0) / 1024 / 1024
        logger.info("已上传 %s (%.1f MB)", filename, size_mb)
        return resp.json()
