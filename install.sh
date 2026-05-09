#!/bin/bash
# install-vscode-server.sh
# 从 GitHub Releases 下载并安装 VS Code Server (CLI + Server)
#
# 用法:
#   ./install.sh <版本号> [仓库地址]
#   ./install.sh 1.119.0
#   ./install.sh 1.119.0 https://github.com/afutemp/vscode-ssh
#
# 也可以通过环境变量设置:
#   VSCODE_OFFLINE_REPO=https://github.com/afutemp/vscode-ssh ./install.sh 1.119.0

set -euo pipefail

VERSION="${1:?用法: $0 <版本号> [仓库地址]}"
REPO="${2:-${VSCODE_OFFLINE_REPO:-https://github.com/afutemp/vscode-ssh}}"
BASE_DIR="$HOME/.vscode-server"

# Resolve repo to download/release API base URL (strip .git suffix if present)
REPO="${REPO%.git}"
DL_BASE="${REPO}/releases/download/${VERSION}"
API_BASE="${REPO/api.github.com/repos}"
API_BASE="${API_BASE/https:\/\/github.com/https://api.github.com/repos}"

echo "=== VS Code Server 离线安装 ==="
echo "版本: $VERSION"
echo "下载: $DL_BASE"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Get commit hash from release body
COMMIT=$(curl -sL "${API_BASE}/releases/tags/${VERSION}" | grep -oP '(?<=Commit: )([0-9a-f]{40})' || true)
if [ -z "$COMMIT" ]; then
    echo "错误: 无法获取 commit hash（版本 $VERSION 可能不存在）"
    exit 1
fi
echo "Commit: $COMMIT"

CLI_PATH="$BASE_DIR/code-${COMMIT}"
SERVER_DIR="$BASE_DIR/cli/servers/Stable-${COMMIT}/server"

# Skip if already installed
if [ -f "$CLI_PATH" ] && [ -f "$SERVER_DIR/bin/code-server" ]; then
    echo "已安装，跳过: ${VERSION} (${COMMIT:0:12})"
    exit 0
fi

# Download
echo "正在下载 server..."
curl -fSL -o "$TMPDIR/vscode-server-linux-x64.tar.gz" \
    "${DL_BASE}/vscode-server-linux-x64.tar.gz"

echo "正在下载 CLI..."
curl -fSL -o "$TMPDIR/vscode_cli_linux_x64_cli.tar.gz" \
    "${DL_BASE}/vscode_cli_linux_x64_cli.tar.gz"

# Install CLI
if [ ! -f "$CLI_PATH" ]; then
    mkdir -p "$BASE_DIR"
    tar -xzf "$TMPDIR/vscode_cli_linux_x64_cli.tar.gz" -C "$TMPDIR"
    cp "$TMPDIR/code" "$CLI_PATH"
    chmod +x "$CLI_PATH"
    echo "CLI 已安装: $CLI_PATH"
fi

# Install Server
if [ ! -f "$SERVER_DIR/bin/code-server" ]; then
    mkdir -p "$SERVER_DIR"
    echo "正在解压 server..."
    tar -xzf "$TMPDIR/vscode-server-linux-x64.tar.gz" -C "$SERVER_DIR" --strip-components 1
    echo "Server 已安装: $SERVER_DIR"
fi

echo "安装成功: $VERSION ($COMMIT)"
