#!/bin/bash
# install-vscode-server.sh
# 从 GitHub 仓库克隆并安装 VS Code Server
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

BIN_DIR="$HOME/.vscode-server/bin"
FILENAME="vscode-server-linux-x64.tar.gz"

echo "=== VS Code Server 离线安装 ==="
echo "版本: $VERSION"
echo "仓库: $REPO"

# Clone the version branch (shallow, depth 1)
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "正在克隆..."
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

# Check tarball
if [ ! -f "$TMPDIR/repo/$FILENAME" ]; then
    echo "错误: 未找到 $FILENAME"
    exit 1
fi

INSTALL_DIR="$BIN_DIR/$COMMIT"

# Skip if already installed
if [ -f "$INSTALL_DIR/bin/code-server" ]; then
    echo "已安装，跳过: $COMMIT ($VERSION)"
    exit 0
fi

# Install
mkdir -p "$INSTALL_DIR"
echo "正在解压到 $INSTALL_DIR ..."
tar -xzf "$TMPDIR/repo/$FILENAME" -C "$INSTALL_DIR" --strip-components 1

# Verify
if [ -f "$INSTALL_DIR/bin/code-server" ]; then
    echo "安装成功: $VERSION ($COMMIT)"
    echo "  路径: $INSTALL_DIR"
else
    echo "错误: 安装后未找到 code-server，可能安装包损坏"
    rm -rf "$INSTALL_DIR"
    exit 1
fi
