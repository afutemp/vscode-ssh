#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== VS Code Server 离线同步工具 - 环境初始化 ==="

# 1. Install git-lfs if not present
if ! command -v git-lfs &>/dev/null; then
    echo "安装 git-lfs..."
    if command -v apt-get &>/dev/null; then
        curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
        sudo apt-get install -y git-lfs
    elif command -v brew &>/dev/null; then
        brew install git-lfs
    else
        echo "错误: 无法自动安装 git-lfs，请手动安装"
        echo "  https://git-lfs.github.com/"
        exit 1
    fi
fi
git lfs install
echo "git-lfs 已就绪"

# 2. Install Python dependencies via uv
if command -v uv &>/dev/null; then
    echo "安装 Python 依赖 (uv)..."
    uv sync
elif command -v pip3 &>/dev/null; then
    echo "安装 Python 依赖 (pip)..."
    pip3 install pyyaml requests rich
else
    echo "错误: 需要安装 uv 或 pip3"
    exit 1
fi

# 3. Create config from example if not present
if [ ! -f "${SCRIPT_DIR}/config.yaml" ]; then
    if [ -f "${SCRIPT_DIR}/config.example.yaml" ]; then
        cp "${SCRIPT_DIR}/config.example.yaml" "${SCRIPT_DIR}/config.yaml"
        echo "已从模板创建 config.yaml，请编辑填写实际配置"
    fi
else
    echo "config.yaml 已存在"
fi

echo ""
echo "=== 初始化完成 ==="
echo "下一步: 编辑 config.yaml 填写 GitHub 仓库和 Token"
echo "运行同步: uv run sync.py"
