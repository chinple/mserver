# 样例
  参考test目录

# 功能
1. 测试框架：单元测试、基于模型测试
2. 工具API

# 编码约定
1. 类名：TestCaseBase

2. 函数名：setup、beginTestCase
   保护变量前加 _ ，私有变量前加 __

3. 变量名：caseInfo（目前）—> 推荐使用: caseInfo

# 服务启动
   python2.7 -u mtest/run.py server -t httpTool.py -p 8088 -f /data/test/builds/ --uploadFolder /data/test/builds/uploads 