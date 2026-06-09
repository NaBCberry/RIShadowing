## v1.3.3

### 修复
- 安装版下载模型后无法加载：_find_vosk_model 增加路径日志，下载完成添加验证
- console=False 时 sys.stdout 为 None 导致崩溃（进一步加固）
- 下载对话框提取完成后正确返回模型路径
