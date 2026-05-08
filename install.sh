#!/bin/bash
# install-vscode-server.sh
# 从 GitHub 仓库克隆并安装 VS Code Server (CLI + Server)
#
# 用法:
#   ./install.sh <版本号> [仓库地址]
#   ./install.sh 1.119.0
#   ./install.sh 1.119.0 https://github.com/afutemp/vscode-ssh.git
#
# 也可以通过环境变量设置:
#   VSCODE_OFFLINE_REPO=https://github.com/afutemp/vscode-ssh.git ./install.sh 1.119.0

set -euo pipefail

VERSION="${1:?用法: $0 <版本号> [仓库地址]}"
REPO="${2:-${VSCODE_OFFLINE_REPO:-https://github.com/afutemp/vscode-ssh.git}}"

BASE_DIR="$HOME/.vscode-server"
SERVER_FILE="vscode-server-linux-x64.tar.gz"
CLI_FILE="vscode_cli_linux_x64_cli.tar.gz"

echo "=== VS Code Server 离线安装 ==="
echo "版本: $VERSION"
echo "仓库: $REPO"

# Clone the version branch (shallow, depth 1)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "正在克隆..."
# Ensure git-lfs is available for large file download
git lfs install 2>/dev/null || true
if ! git clone --depth 1 --branch "$VERSION" "$REPO" "$TMPDIR/repo" 2>&1; then
    echo "错误: 克隆失败，版本 $VERSION 可能不存在"
    echo "可用版本列表: $(git ls-remote --heads "$REPO" | grep -v refs/heads/main | sed 's|.*/||' | tr '\n' ' ')"
    exit 1
fi

# Read commit hash
if [ ! -f "$TMPDIR/repo/commit.txt" ]; then
    echo "错误: 分支中缺少 commit.txt"
    exit 1
fi
COMMIT=$(cat "$TMPDIR/repo/commit.txt")

CLI_PATH="$BASE_DIR/code-$COMMIT"
SERVER_DIR="$BASE_DIR/cli/servers/Stable-$COMMIT/server"

# Skip if already installed
if [ -f "$CLI_PATH" ] && [ -f "$SERVER_DIR/bin/code-server" ]; then
    echo "已安装，跳过: $COMMIT ($VERSION)"
    exit 0
fi

# Check files
if [ ! -f "$TMPDIR/repo/$CLI_FILE" ]; then
    echo "错误: 未找到 $CLI_FILE"
    exit 1
fi
if [ ! -f "$TMPDIR/repo/$SERVER_FILE" ]; then
    echo "错误: 未找到 $SERVER_FILE"
    exit 1
fi

# Install CLI
if [ ! -f "$CLI_PATH" ]; then
    mkdir -p "$BASE_DIR"
    tar -xzf "$TMPDIR/repo/$CLI_FILE" -C "$TMPDIR"
    cp "$TMPDIR/code" "$CLI_PATH"
    chmod +x "$CLI_PATH"
    echo "CLI 已安装: $CLI_PATH"
fi

# Install Server
if [ ! -f "$SERVER_DIR/bin/code-server" ]; then
    mkdir -p "$SERVER_DIR"
    echo "正在解压 server 到 $SERVER_DIR ..."
    tar -xzf "$TMPDIR/repo/$SERVER_FILE" -C "$SERVER_DIR" --strip-components 1
    echo "Server 已安装: $SERVER_DIR"
fi

echo "安装成功: $VERSION ($COMMIT)"
