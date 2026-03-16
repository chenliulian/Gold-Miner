# 系统命令

## 名称
system_command

## 描述
在项目目录中执行系统命令，支持文件检索、目录操作等。

## 参数
- command: 要执行的命令 (支持: grep, find, ls, cat, pwd, tree 等)

## 支持的命令

### 1. 文件搜索 (grep)
```
command: "grep -rn 'pattern' --include='*.py' ."
```
在项目中搜索包含特定内容的文件。

### 2. 列出文件 (ls)
```
command: "ls -la src/gold_miner/"
```

### 3. 查看文件 (cat)
```
command: "cat src/gold_miner/agent.py"
```

### 4. 项目结构 (tree)
```
command: "tree -L 2 src/"
```

## 输出
返回命令执行结果或错误信息。

## 注意事项
- 只允许安全的只读命令
- 不允许危险命令 (rm -rf, dd, mkfs 等)
- 只能在项目目录内操作
