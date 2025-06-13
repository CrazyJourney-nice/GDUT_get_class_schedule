# 获取GDUT课表， 并生成可导入手机日历的.ics文件

## 简介
该Python脚本会自动爬取该学期的课表，获取课程信息，并且生成一份可让你将课表导入手机日历的.ics文件，这样你就可以在手机日历中查看课表了



## 使用方法
### 下载release中的可执行文件
1. 在**release**中下载**可执行文件(.exe文件)**
2. 运行该**可执行文件(.exe文件)**

### 获取Cookie
1. 登录登录[广东工业大学教务系统(jxfw.gdut.edu.cn)](https://jxfw.gdut.edu.cn/login!welcome.action)
2. 打开浏览器的**开发者工具(点击键盘上的F12)**,切换到**网络(Network)**标签
3. 点击**课表查询**
4. 找到名为"**sgrkbcx!getKbRq.action?xnxqdm=**"的请求，并在**Headers**标签中的**Request Headers**栏找到**Cookie**(注意, 一定不能泄露cookie给其他任何人)
5. 复制整个Cookie字符串


### 运行应用程序
1. 将复制的内容粘贴到本程序中，并按提示输入你的Cookie

### 导入手机
1. 待程序运行完毕后, 请在与**get_your_schedule.exe**文件相同的目录中找到名为**my_schedule**的**.ics文件**
2. 将名为**my_schedule**的**.ics文件;发送至手机(将**.ics文件**作为附件, 给自己发邮件, 并在手机端接收邮件, 即可将**.ics文件**发送至手机)
3. 导入手机
- **苹果**： 把.ics文件发送给手机(必须以邮件的方式发送给自己，并用系统自带的邮件APP打开), 在邮件中打开附件，即可导入。
- **安卓**： 把.ics文件发送给手机, 并使用系统自带的日历程序打开(如华为系统叫"华为日历"), 即可导入。

如有任何问题, 请提**issue**或者[联系我](https://github.com/CrazyJourney-nice)


