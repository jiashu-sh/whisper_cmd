# whisper_cmd
SST - Speech to Text (Chinese)

目前由于本人的开发笔记本是6G显存的，所以默认的包是medium的包，具体可根据您的环境作修改。

以下为运行效果（还包括了个在线翻译的，效果不好，但也未删除）：
![Image text](https://github.com/jiashu-sh/whisper_cmd/blob/main/docs/whispercmd-01.png?raw=true)

视频演示见：

[我的B站:基于whisper的叮当打字小助手](https://www.bilibili.com/video/BV1U84y1T7oP/?spm_id_from=333.999.0.0&vd_source=4d1c50aefebc3049c1aab4af0be6b6d6)

本人代码水平不行，仅仅是能让它跑起来，见谅。

使用方法：
命令行：
python whisper_cmd.py
可以进行STT语音识别，并复制内容文本，自动粘贴到当前窗体

20230415 update:
命令行：
python whisper_cmd.py translate:on showin:on 
可以弹出翻译窗口
注意：
翻译功能使用微软翻译，使用前需要把 config-2.ini 改名为config.ini,并在以下配置中将值替换为您申请的微软翻译api的区域代码以及key
location=<YOUR-RESOURCE-LOCATION>
key=<your-translator-key>
