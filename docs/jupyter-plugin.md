


## 为何需要 此vscode 插件

大部分专业python 程序员都不会选择Juypter notebook 作为项目开发的IDE
但是notebook 在presentation 和技术文档编写领域有自己独特的优势。

但是， jupyter notebook当前难以集成好用的AI 插件
所以用有这个需求


下面就是具体步骤：

<br><br><br>

## 安装vscode 的相关 juypter notebook 插件
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/ee0dc051b8494ca1bd0dcdf59e76088c.png)

<br><br><br>



## 如果要运行 ipynb文件里的代码块， 还需要安装python库 ipykernel

```bash
(.venv) gateman@MoreFine-S500: python-poc$ pip install ipykernel
....
(.venv) gateman@MoreFine-S500: python-poc$ .venv/bin/pip list | grep ipykernel
ipykernel                    7.1.0
```

<br><br><br>
## 配置jupyter notebook的PYTHONPATH

默认下， vscode 的jypyter 环境并不集成项目中的.env配置

如果ipynb 文件并不在项目根目录下， 大概率会遇到下面的import error:

==No module named 'src'==

所以我们需要找地方配置PYTHONPATH



根据jypter 开发者(之一)的指引

我们可以配置jupyter 的启动脚本

正确方法：
编辑 vscode的User setting.json文件加上

~/.config/Code/User/settings.json
```json
    "jupyter.runStartupCommands": [
        "import sys",
        "if '${workspaceFolder}' not in sys.path:",
        "    sys.path.insert(0, '${workspaceFolder}')"
    ]
```



## 测试
好了， 现在相信juypter notebook 就work within vscode了， 而且还有cline等ai tool的加持！


## 为何需要 此vscode 插件

大部分专业python 程序员都不会选择Juypter notebook 作为项目开发的IDE
但是notebook 在presentation 和技术文档编写领域有自己独特的优势。

但是， jupyter notebook当前难以集成好用的AI 插件
所以用有这个需求


下面就是具体步骤：

<br><br><br>

## 安装vscode 的相关 juypter notebook 插件

<br><br><br>


## 如果要运行 ipynb文件里的代码块， 还需要安装python库 ipykernel

```bash
(.venv) gateman@MoreFine-S500: python-poc$ pip install ipykernel
....
(.venv) gateman@MoreFine-S500: python-poc$ .venv/bin/pip list | grep ipykernel
ipykernel                    7.1.0
```

<br><br><br>
## 配置jupyter notebook的PYTHONPATH

默认下， vscode 的jypyter 环境并不集成项目中的.env配置

如果ipynb 文件并不在项目根目录下， 大概率会遇到下面的import error:

==No module named 'src'==

所以我们需要找地方配置PYTHONPATH



根据jypter 开发者(之一)的指引

我们可以配置jupyter 的启动脚本

正确方法：
编辑 vscode的User setting.json文件加上

~/.config/Code/User/settings.json
```json
    "jupyter.runStartupCommands": [
        "import sys",
        "if '${workspaceFolder}' not in sys.path:",
        "    sys.path.insert(0, '${workspaceFolder}')"
    ]
```



## 测试
好了， 现在相信juypter notebook 就work within vscode了， 而且还有cline等ai tool的加持！
