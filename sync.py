#!/usr/bin/env python3
"""VS Code Server 离线同步工具 - 将 tar.gz 同步到 GitHub Releases。"""

import argparse
import sys
from pathlib import Path

from lib.config import CLI_FILENAME, FILENAME, load_config
from lib.downloader import download_vscode_cli, download_vscode_server
from lib.github_api import GitHubClient
from lib.utils import setup_logging
from lib.vscode_api import fetch_commit_for_version, fetch_version_commit_pairs

logger = setup_logging()


def sync_version(
    pair: dict,
    github: GitHubClient,
    temp_dir: Path,
    force: bool = False,
) -> bool:
    """Sync a single version to GitHub Release. Returns True on success."""
    version = pair["version"]
    commit = pair["commit"]
    commit_short = commit[:12]

    logger.info("同步版本 %s (%s)...", version, commit_short)

    # Download server from Microsoft
    server_path = temp_dir / f"vscode-server-linux-x64-{commit_short}.tar.gz"
    try:
        download_vscode_server(commit, server_path)
    except Exception as e:
        logger.error("下载 server 失败 %s: %s", commit_short, e)
        return False

    # Download CLI from Microsoft
    cli_path = temp_dir / f"vscode-cli-linux-x64-{commit_short}.tar.gz"
    try:
        download_vscode_cli(commit, cli_path)
    except Exception as e:
        logger.error("下载 CLI 失败 %s: %s", commit_short, e)
        return False

    # Delete existing release if force-syncing
    if force:
        github.delete_release(version)

    # Create release
    try:
        release = github.create_release(
            tag=version,
            title=version,
            body=f"Commit: {commit}",
        )
    except Exception as e:
        logger.error("创建 release 失败 %s: %s", version, e)
        return False

    # Upload assets
    commit_file = temp_dir / f"commit-{commit_short}.txt"
    commit_file.write_text(commit)
    try:
        github.upload_asset(release, str(server_path), name=FILENAME)
        github.upload_asset(release, str(cli_path), name=CLI_FILENAME)
        github.upload_asset(release, str(commit_file), name="commit.txt")
    except Exception as e:
        logger.error("上传失败 %s: %s", version, e)
        github.delete_release(version)
        return False

    # Clean up temp files
    server_path.unlink(missing_ok=True)
    cli_path.unlink(missing_ok=True)
    commit_file.unlink(missing_ok=True)

    logger.info("同步完成: %s (%s)", version, commit_short)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="VS Code Server 离线同步工具 - 将 tar.gz 同步到 GitHub Releases"
    )
    parser.add_argument("--config", default=None, help="配置文件路径 (默认: ./config.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要执行的操作")
    parser.add_argument("--force", action="store_true", help="重新同步已存在的版本")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
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

    sync_count = cfg["sync_count"]
    temp_dir = Path(cfg["temp_dir"])
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch version/commit pairs
    try:
        pairs = fetch_version_commit_pairs(sync_count)
    except Exception as e:
        logger.error("获取版本列表失败: %s", e)
        sys.exit(1)

    if not pairs:
        logger.warning("没有获取到版本信息")
        sys.exit(0)

    # 1.5. Resolve extra versions from config
    extra_versions = cfg.get("extra_versions") or []
    if extra_versions:
        logger.info("解析额外固定版本...")
        existing_versions = {p["version"] for p in pairs}
        for ver in extra_versions:
            if ver in existing_versions:
                logger.debug("  %s 已在近期版本中，跳过", ver)
                continue
            commit = fetch_commit_for_version(ver)
            if commit:
                pairs.append({"version": ver, "commit": commit})

    # 2. Initialize GitHub client
    github = GitHubClient(cfg["repo_owner"], cfg["repo_name"], cfg["github_token"])

    if args.dry_run:
        print(f"\n将同步以下 {len(pairs)} 个版本:")
        for p in pairs:
            print(f"  {p['version']} ({p['commit'][:12]})")
        return

    # 3. Check existing releases
    try:
        existing_releases = set(github.list_releases())
    except Exception as e:
        logger.error("获取 release 列表失败: %s", e)
        sys.exit(1)

    logger.info("已有 %d 个 release", len(existing_releases))

    # 4. Determine which versions need syncing
    if args.force:
        needed = pairs
    else:
        needed = [p for p in pairs if p["version"] not in existing_releases]

    if not needed:
        logger.info("所有版本均已同步，无需操作")
        return

    logger.info("需要同步 %d 个版本", len(needed))

    # 5. Sync each version
    success_count = 0
    fail_count = 0
    for pair in needed:
        try:
            if sync_version(pair, github, temp_dir, force=args.force):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error("同步失败 %s: %s", pair["commit"][:12], e)
            fail_count += 1

    # 6. Summary
    print(f"\n同步完成: {success_count} 成功, {fail_count} 失败")
    if fail_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
