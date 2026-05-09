# VS Code Server 离线部署指南

## 背景

VS Code 通过 SSH 远程连接时，会在远端自动下载并安装一个与本地 VS Code 版本严格对应的 **VS Code Server**。在内网或无法访问外网的环境中，这个自动下载会失败，导致连接无法建立。

**新版 VS Code（1.93+）Remote SSH 流程：**

1. 下载 CLI 二进制 `code-{commit}` (~30MB) → `~/.vscode-server/`
2. CLI 自行下载并管理 server → `~/.vscode-server/cli/servers/Stable-{commit}/server/`

因此离线部署需要 **两个包**：CLI tar.gz + Server tar.gz。

---

## 1. 查询版本与 Commit Hash

### 1.1 获取最新版本的 commit hash

```bash
curl -s https://update.code.visualstudio.com/api/releases/stable > /tmp/versions.json
curl -s https://update.code.visualstudio.com/api/commits/stable > /tmp/commits.json
```

查看映射关系：

```bash
python3 -c "
import json
with open('/tmp/versions.json') as f:
    versions = json.load(f)
with open('/tmp/commits.json') as f:
    commits = json.load(f)
print(f'{'版本号':<14} {'Commit Hash':<42}')
print('-' * 56)
for i in range(min(10, len(versions), len(commits))):
    print(f'{versions[i]:<14} {commits[i]}')
"
```

### 1.2 从本地已安装的 VS Code 获取

```bash
code --version
```

输出中第二行即为 commit hash。

---

## 2. 下载离线包

每个版本需要下载 **两个文件**。

### 2.1 下载地址

**Server 包**（~107MB）：
```
https://vscode.download.prss.microsoft.com/dbazure/download/stable/{COMMIT}/vscode-server-linux-x64.tar.gz
```

**CLI 包**（~30MB）：
```
https://vscode.download.prss.microsoft.com/dbazure/download/stable/{COMMIT}/vscode_cli_linux_x64_cli.tar.gz
```

PLATFORM 取值：

| 远端系统架构 | Server 文件名中的 PLATFORM | CLI 文件名中的 PLATFORM |
|-------------|--------------------------|----------------------|
| Linux x64 | `linux-x64` | `linux_x64` |
| Linux ARM64 | `linux-arm64` | `linux_arm64` |
| Linux ARM32 | `linux-armhf` | `linux_armhf` |

### 2.2 单个版本下载

```bash
COMMIT="8b640eef5a6c6089c029249d48efa5c99adf7d51"

# Server 包
wget "https://vscode.download.prss.microsoft.com/dbazure/download/stable/${COMMIT}/vscode-server-linux-x64.tar.gz" \
     -O "vscode-server-linux-x64.tar.gz"

# CLI 包
wget "https://vscode.download.prss.microsoft.com/dbazure/download/stable/${COMMIT}/vscode_cli_linux_x64_cli.tar.gz" \
     -O "vscode_cli_linux_x64_cli.tar.gz"
```

### 2.3 验证下载完整性

```bash
# 检查文件大小
ls -lh *.tar.gz
# server: ~107MB, cli: ~30MB

# 验证 tar 包完整性
tar -tzf vscode-server-linux-x64.tar.gz | head -5
tar -tzf vscode_cli_linux_x64_cli.tar.gz
```

---

## 3. 传输到远端服务器

```bash
scp vscode-server-linux-x64.tar.gz vscode_cli_linux_x64_cli.tar.gz user@remote-server:~/
```

---

## 4. 远端安装

### 4.1 手动安装单个版本

```bash
COMMIT="8b640eef5a6c6089c029249d48efa5c99adf7d51"

# 1. 安装 CLI 二进制
mkdir -p ~/.vscode-server
tar -xzf vscode_cli_linux_x64_cli.tar.gz -C /tmp/
cp /tmp/code ~/.vscode-server/code-${COMMIT}
chmod +x ~/.vscode-server/code-${COMMIT}

# 2. 安装 Server
mkdir -p ~/.vscode-server/cli/servers/Stable-${COMMIT}/server
tar -xzf vscode-server-linux-x64.tar.gz \
    -C ~/.vscode-server/cli/servers/Stable-${COMMIT}/server/ \
    --strip-components 1

# 3. 验证
ls ~/.vscode-server/code-${COMMIT}
ls ~/.vscode-server/cli/servers/Stable-${COMMIT}/server/bin/remote-server
```

### 4.2 批量安装脚本

```bash
#!/bin/bash
# install-vscode-offline.sh
# 用法: ./install-vscode-offline.sh <commit-hash>
# 将当前目录下的 server + CLI tar.gz 安装到 ~/.vscode-server/

COMMIT="${1:?用法: $0 <commit-hash>}"
BASE="$HOME/.vscode-server"

# CLI
mkdir -p "$BASE"
tar -xzf vscode_cli_linux_x64_cli.tar.gz -C /tmp/
cp /tmp/code "$BASE/code-${COMMIT}"
chmod +x "$BASE/code-${COMMIT}"
echo "CLI 已安装: $BASE/code-${COMMIT}"

# Server
SERVER_DIR="$BASE/cli/servers/Stable-${COMMIT}/server"
if [ -d "$SERVER_DIR" ] && [ -f "$SERVER_DIR/bin/remote-server" ]; then
    echo "Server 已存在，跳过: $COMMIT"
else
    mkdir -p "$SERVER_DIR"
    tar -xzf vscode-server-linux-x64.tar.gz -C "$SERVER_DIR" --strip-components 1
    echo "Server 已安装: $SERVER_DIR"
fi
```

### 4.3 自动检测安装（shell profile）

在远端 `~/.bashrc` 或 `~/.zshrc` 末尾添加：

```bash
_vscode_auto_install() {
    local cache_dir="$HOME/.vscode-server-cache"
    local base="$HOME/.vscode-server"
    [ -d "$cache_dir" ] || return 0

    for dir in "$cache_dir"/*/; do
        [ -d "$dir" ] || continue
        commit=$(basename "$dir")
        [[ "$commit" =~ ^[0-9a-f]{40}$ ]] || continue

        # CLI
        local cli="$base/code-${commit}"
        [ -f "$cli" ] || {
            [ -f "$dir/vscode_cli_linux_x64_cli.tar.gz" ] || continue
            tar -xzf "$dir/vscode_cli_linux_x64_cli.tar.gz" -C /tmp/ 2>/dev/null
            cp /tmp/code "$cli" && chmod +x "$cli"
        }

        # Server
        local server_dir="$base/cli/servers/Stable-${commit}/server"
        [ -f "$server_dir/bin/remote-server" ] || {
            [ -f "$dir/vscode-server-linux-x64.tar.gz" ] || continue
            mkdir -p "$server_dir"
            tar -xzf "$dir/vscode-server-linux-x64.tar.gz" \
                -C "$server_dir" --strip-components 1 2>/dev/null
        }

        echo "[vscode-server] 已从缓存安装: ${commit:0:12}"
    done
}
_vscode_auto_install
```

缓存目录结构：
```
~/.vscode-server-cache/
└── {commit}/
    ├── vscode-server-linux-x64.tar.gz
    └── vscode_cli_linux_x64_cli.tar.gz
```

---

## 5. 通过内网镜像（客户端配置）

在客户端 VS Code 的 `settings.json` 中配置：

```json
{
    "remote.SSH.serverDownloadUrlTemplate": "http://your-internal-mirror:8080/vscode-server/${commit}/vscode-server-linux-x64.tar.gz"
}
```

内网镜像需按对应路径提供文件，VS Code 连接时会自动从此地址下载 server 包。

> 注意：此设置仅覆盖 server 包的下载地址，CLI 二进制的下载不受此设置控制。如需完全离线，仍需预装 CLI。

---

## 6. 注意事项

- **架构匹配**：下载前确认远端服务器的 CPU 架构（`uname -m`），选择对应的 PLATFORM。
- **磁盘空间**：每个版本约占用 400MB 解压后空间（CLI ~30MB + Server ~375MB）。
- **版本共存**：不同版本可以在 `~/.vscode-server/cli/servers/` 下共存。
- **清理旧版本**：
  ```bash
  # 查看 CLI 和 server 版本
  ls ~/.vscode-server/code-*
  ls ~/.vscode-server/cli/servers/

  # 删除指定版本
  rm ~/.vscode-server/code-{commit}
  rm -rf ~/.vscode-server/cli/servers/Stable-{commit}
  ```

---

## 7. 快速参考

```bash
COMMIT="替换为实际hash"

# 1. 下载（在有网机器上）
wget "https://vscode.download.prss.microsoft.com/dbazure/download/stable/${COMMIT}/vscode-server-linux-x64.tar.gz"
wget "https://vscode.download.prss.microsoft.com/dbazure/download/stable/${COMMIT}/vscode_cli_linux_x64_cli.tar.gz"

# 2. 传到远端
scp vscode-server-linux-x64.tar.gz vscode_cli_linux_x64_cli.tar.gz user@server:~/

# 3. 远端安装
tar -xzf vscode_cli_linux_x64_cli.tar.gz -C /tmp/
mkdir -p ~/.vscode-server
cp /tmp/code ~/.vscode-server/code-${COMMIT}
chmod +x ~/.vscode-server/code-${COMMIT}

mkdir -p ~/.vscode-server/cli/servers/Stable-${COMMIT}/server
tar -xzf vscode-server-linux-x64.tar.gz -C ~/.vscode-server/cli/servers/Stable-${COMMIT}/server/ --strip-components 1
```
