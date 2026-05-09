#!/usr/bin/env python3
"""从 GitHub 仓库下载指定版本的 VS Code Server tar.gz 文件。"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from lib.config import FILENAME, load_config
from lib.utils import setup_logging

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(
        description="从 GitHub 仓库下载 VS Code Server tar.gz"
    )
    parser.add_argument(
        "--version", required=True,
        help="VS Code 版本号 (如 1.119.0)",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出文件路径 (默认: ./vscode-server-linux-x64-{version}.tar.gz)",
    )
    parser.add_argument(
        "--config", default=None,
        help="配置文件路径 (默认: ./config.yaml)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="详细输出",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.getLogger("vscode-sync").setLevel(logging.DEBUG)

    # Load config
    try:
        cfg = load_config(args.config)
    except Exception as e:
        logger.error("配置加载失败: %s", e)
        sys.exit(1)

    version = args.version
    output = args.output or f"vscode-server-linux-x64-{version}.tar.gz"
    output = Path(output)

    clone_url = f"https://{cfg['github_token']}@github.com/{cfg['github_repo']}.git"

    # Clone the specific branch with depth 1
    with tempfile.TemporaryDirectory(prefix="vscode-download-") as tmp:
        clone_dir = Path(tmp) / "repo"
        logger.info("克隆分支 %s...", version)
        result = subprocess.run(
            [
                "git", "clone", "--depth", "1",
                "--branch", version,
                clone_url,
                str(clone_dir),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(
                "克隆失败（分支可能不存在）: %s",
                result.stderr.strip(),
            )
            sys.exit(1)

        # Copy the tar.gz file
        src = clone_dir / FILENAME
        if not src.exists():
            logger.error("文件不存在: %s", FILENAME)
            sys.exit(1)

        shutil.copy2(src, output)
        logger.info("已下载到: %s (%s)", output, output.stat().st_size)


if __name__ == "__main__":
    main()
