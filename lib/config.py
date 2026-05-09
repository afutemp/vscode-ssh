import os
from pathlib import Path

import yaml

DEFAULTS = {
    "sync_count": 5,
    "temp_dir": "/tmp/vscode-sync",
}

PLATFORM = "linux-x64"
FILENAME = f"vscode-server-{PLATFORM}.tar.gz"
CLI_FILENAME = f"vscode_cli_{PLATFORM.replace('-', '_')}_cli.tar.gz"
DOWNLOAD_BASE_URL = (
    "https://vscode.download.prss.microsoft.com/dbazure/download"
)


class ConfigError(Exception):
    pass


def load_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        raise ConfigError(f"配置文件不存在: {config_path}")

    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}

    # Apply defaults
    for key, val in DEFAULTS.items():
        cfg.setdefault(key, val)

    # Environment variable overrides
    if os.environ.get("GITHUB_TOKEN"):
        cfg["github_token"] = os.environ["GITHUB_TOKEN"]

    # Validate
    if not cfg.get("github_repo"):
        raise ConfigError("github_repo 是必填项")
    if not cfg.get("github_token"):
        raise ConfigError("github_token 是必填项（或设置 GITHUB_TOKEN 环境变量）")
    if "/" not in cfg["github_repo"]:
        raise ConfigError("github_repo 格式应为 owner/repo")

    cfg["repo_owner"], cfg["repo_name"] = cfg["github_repo"].rsplit("/", 1)
    return cfg
