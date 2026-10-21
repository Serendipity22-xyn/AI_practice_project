AI_chat_companion：

	vibecoding实战项目
	将使用claudecode(后端调用deepseek大模型api接口）从零制作一个AI智能聊天伴侣
	搭建现有Agent模型，利用大模型记忆机制保存用户数据并调用数据库
	目的：熟悉vibecoding，大模型记忆机制，调用数据库
	
	网址http://localhost:5173/#/
Git_commit_Subagent：

```
vibecoding实战项目
一个自动提交的Agent，通过Claudecode直接提交文件到GitHub账号

流程如下：
	1. 调用 git_save_skill 发起提交流程
	2. 捕获 git_commit_hook_check 的拦截结果：
    		如果没有被钩子拦截：直接往下走
   			如果被钩子拦截：并行启动 code_test_agent、quality_test_agent，同时调用 handoff skill，等待三者全部执行完成并产出对应标识/报告文件，再次尝试通过钩子校验
	3. 钩子校验放行后：读取 handoff 输出的报告文件，提取改动总结，作为本次 git commit 的 commit message
	4. 执行 git push，确认推送成功
	5. 推送成功收尾：清理 code_test_agent 标识文件、quality_test_agent 标识文件、handoff 报告文件

必要Subagent，skill说明：
	code_test_agent：专门负责代码单元测试、静态分析、用例生成、执行校验
	quality_test_agent：专门负责代码质量检查、代码质检、规范扫描需求
	handoff：确定当前项目进度，总结本次改动
	git_save_skill：收到调用指令后，在当前工作目录执行 git 一键保存推送流程
	git_commit_hook_check：作为 git commit 前置拦截钩子，commit 触发时执行校验，校验通过才放行提交，不通过直接阻断 commit，不拦截手动提交。
	
目的：通过该项目熟悉通过vibecoding开发skill，Subagent以及熟悉workflow【提示词规范（Prompt），规则配置（clooud.md），强制校验（hooks)】
```

