---
categories:
- code-server
cnblogid: 18290792
date: 2024-07-08 22:15 +0800
id: 7e7d5ffd-497a-492e-b8d2-fba3a7cb6f6b
layout: post
tags:
- vscode
- code-server
- ide
title: 离线安装 vscode-server
---

1. 获取当前版本 vscode 的 commit_id：Help - > About -> Commit

2. 根据 commit_id 下载对应版本的 vscode-server：
   https://update.code.visualstudio.com/commit:${commit_id}/server-linux-x64/stable

3. 将下载好的 vscode-server-linux-x64.tar.gz 放在 ~/.vscode-server/bin/${commit_id} 目录下（没有则新建）

4. 将压缩包解压，得到 vscode-server-linux-x64 目录，将该目录下的所有内容移动到~/.vscode-server/bin/${commit_id} 下，并删除 vscode-server-linux-x64 目录和压缩包

5. 一键脚本：

   ```bash
   commit_id=XXX
   PATH_TO_YOUR_VSCODE_SERVER=XXX
   
   mkdir -p ~/.vscode-server/bin/${commit_id}
   cp ${PATH_TO_YOUR_VSCODE_SERVER}/vscode-server-linux-x64.tar.gz ~/.vscode-server/bin/${commit_id}
   
   cd ~/.vscode-server/bin/${commit_id}
   tar -xzf vscode-server-linux-x64.tar.gz && rm vscode-server-linux-x64.tar.gz
   mv vscode-server-linux-x64/* . && rm -r vscode-server-linux-x64
   
   mkdir -p ~/.vscode-server/extensions
   cp -r ${PATH_TO_YOUR_VSCODE_EXTENSIONS}/extensions/* ~/.vscode-server/extensions
   ```