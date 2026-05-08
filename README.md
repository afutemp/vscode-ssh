# VS Code Server 离线安装

通过 GitHub 托管 VS Code Server 离线包，在无外网的服务器上一键安装。

## 前置条件

- Git >= 2.0
- Git LFS（用于下载大文件）
- curl 或 wget

## 安装

```bash
# 下载并运行安装脚本
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh | bash -s <版本号>

# 例如安装 1.119.0
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh | bash -s 1.119.0
```

如果网络不通，可以先在有网的机器上下载脚本，再传到服务器执行：

```bash
# 有网机器
curl -sL https://raw.githubusercontent.com/afutemp/vscode-ssh/main/install.sh -o install.sh

# 传到服务器后执行
bash install.sh 1.119.0
```

## 自定义仓库地址

默认从 `https://github.com/afutemp/vscode-ssh.git` 拉取。如需使用 fork 或镜像：

```bash
# 通过参数
bash install.sh 1.119.0 https://your-mirror.com/vscode-ssh.git

# 或通过环境变量
VSCODE_OFFLINE_REPO=https://your-mirror.com/vscode-ssh.git bash install.sh 1.119.0
```

## 查看可用版本

```bash
git ls-remote --heads https://github.com/afutemp/vscode-ssh.git | grep -v main | awk -F/ '{print $NF}'
```

## 安装了什么

脚本会在 `~/.vscode-server/` 下安装两个组件：

| 组件 | 路径 | 说明 |
|------|------|------|
| CLI 二进制 | `~/.vscode-server/code-{commit}` | VS Code Remote SSH 入口 |
| Server | `~/.vscode-server/cli/servers/Stable-{commit}/server/` | 远端 server 运行时 |

安装完成后，VS Code Remote SSH 连接时会自动识别，无需再下载。

## 离线同步新版本

使用项目中的 `sync.py` 将新版本同步到此仓库：

```bash
python3 sync.py          # 同步最近版本
python3 sync.py --force  # 强制重新同步
python3 sync.py --dry-run # 预览
```
