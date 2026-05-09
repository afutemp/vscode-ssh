# VS Code Server 离线安装

通过 GitHub Releases 托管 VS Code Server 离线包，在无外网的服务器上一键安装。

## 前置条件

- curl

## 安装

```bash
# 下载并运行安装脚本
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh | bash -s <版本号>

# 例如安装 1.119.0
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh | bash -s 1.119.0
```

如果网络不通，可以先在有网的机器上下载脚本和安装包，再传到服务器执行：

```bash
# 有网机器：下载脚本
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh -o install.sh

# 有网机器：下载安装包
VERSION="1.119.0"
curl -L -o vscode-server-linux-x64.tar.gz \
    "https://github.com/afutemp/vscode-ssh/releases/download/${VERSION}/vscode-server-linux-x64.tar.gz"
curl -L -o vscode_cli_linux_x64_cli.tar.gz \
    "https://github.com/afutemp/vscode-ssh/releases/download/${VERSION}/vscode_cli_linux_x64_cli.tar.gz"

# 传到服务器后手动安装（参见下方手动安装）
```

## 自定义仓库地址

```bash
# 通过参数
bash install.sh 1.119.0 https://github.com/your-fork/vscode-ssh

# 或通过环境变量
VSCODE_OFFLINE_REPO=https://github.com/your-fork/vscode-ssh bash install.sh 1.119.0
```

## 手动安装

不需要 install.sh，直接用 curl 下载：

```bash
VERSION="1.119.0"

# 下载（commit.txt 包含对应的 commit hash）
curl -L -o commit.txt \
    "https://github.com/afutemp/vscode-ssh/releases/download/${VERSION}/commit.txt"
COMMIT=$(cat commit.txt)

curl -L -o vscode-server-linux-x64.tar.gz \
    "https://github.com/afutemp/vscode-ssh/releases/download/${VERSION}/vscode-server-linux-x64.tar.gz"
curl -L -o vscode_cli_linux_x64_cli.tar.gz \
    "https://github.com/afutemp/vscode-ssh/releases/download/${VERSION}/vscode_cli_linux_x64_cli.tar.gz"

# 安装 CLI
mkdir -p ~/.vscode-server
tar -xzf vscode_cli_linux_x64_cli.tar.gz -C /tmp/
cp /tmp/code ~/.vscode-server/code-${COMMIT}
chmod +x ~/.vscode-server/code-${COMMIT}

# 安装 Server
mkdir -p ~/.vscode-server/cli/servers/Stable-${COMMIT}/server
tar -xzf vscode-server-linux-x64.tar.gz \
    -C ~/.vscode-server/cli/servers/Stable-${COMMIT}/server/ \
    --strip-components 1
```

## 查看可用版本

```bash
curl -sL https://api.github.com/repos/afutemp/vscode-ssh/releases | python3 -c "
import json, sys
for r in json.load(sys.stdin):
    print(r['tag_name'], '-', r['body'])
"
```

## 离线同步新版本

使用项目中的 `sync.py` 将新版本同步到 GitHub Releases：

```bash
python3 sync.py          # 同步最近版本
python3 sync.py --force  # 强制重新同步
python3 sync.py --dry-run # 预览
```
