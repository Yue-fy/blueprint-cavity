Blueprint + Cavity — 提交包使用说明

本包用于评审展示与准备 YouTube 上传。视频尚未上传到 YouTube；当前没有可填入表单的真实 YouTube URL。网站已经公开，无需登录。请使用本人有权操作的 YouTube 账号完成上传，并在取得实际视频链接后填写提交表单。本包不会替你发布或提交。

一、评委入口

总览（Blueprint 与 Cavity 并列）：
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/

Blueprint 四步导览：
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#tour/1

Cavity 入门及完整实验室：
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/#cavity
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/hbn/

网页播放现有 84 秒影片：
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/film/

中文产品手册：
https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/guide/

建议评委先选任一案例进入，再按 judge-walkthrough.zh-CN.pdf 的 10 分钟指南核对具体操作、奖励与限制。影片重点讲 Blueprint 的一项房间面积任务；网站中的 Cavity 与 Blueprint 是平行入口。

二、压缩包清单

压缩包：blueprint-cavity-submission.zip

影片与字幕：
- blueprint-cavity-film.mp4：84 秒，1920×1080，30 fps；英文字幕已烧录，只有配乐、无旁白。
- captions.en.vtt：英文字幕源。
- captions.en.srt：同时间码的 UTF-8 SRT，供 YouTube 上传。
- youtube-thumbnail.jpg：横版 YouTube 封面。
- cover-square.jpg：方形展示封面，不替代横版视频。

文档与可复制文案：
- product-manual.zh-CN.pdf：详细中文产品手册。
- judge-walkthrough.zh-CN.pdf：10 分钟评审操作与证据边界。
- youtube-title.txt：直接复制到 YouTube 标题。
- youtube-description.txt：直接复制到 YouTube 说明，保留其中全部署名。
- submission.en.txt：英文表单的 Project name、Punchline、Description；只复制对应字段内容。
- README.zh-CN.txt：本说明。
- CREDITS.txt：音乐、论文背景图、图纸的来源与授权说明。

核查文件：
- links.txt：公开入口。
- MANIFEST.json：包内交付元数据。
- SHA256SUMS.txt：文件 SHA-256 校验值。

本次公开 ZIP 不包含私有评测源码包、密钥或原始未公开研究文件。评测源码包作为单独本地交付。文件完整性以本包 MANIFEST.json 与 SHA256SUMS.txt 为准。

三、上传到 YouTube

1. 登录有权使用的 YouTube 账号，进入 YouTube Studio，选择“创建 / Create”→“上传视频 / Upload videos”，上传 blueprint-cavity-film.mp4。复制 youtube-title.txt 与 youtube-description.txt；如实完成受众等必填设置。上传步骤官方说明：
https://support.google.com/youtube/answer/57407?hl=en

2. 封面使用 youtube-thumbnail.jpg。自定义封面要求账号已验证；未验证时可以先选择 YouTube 自动生成的封面，或完成验证后再上传自定义图。官方说明：
https://support.google.com/youtube/answer/72431?hl=en

3. 添加独立英文字幕：在 Studio 的“字幕 / Subtitles”选择该视频，添加 English，上传 captions.en.srt，并选择“带时间码 / With timing”。也可上传受支持的 VTT。影片没有旁白，不应依靠语音自动识别来恢复这些屏幕字幕。检查字幕首尾与画面同步，并查看 CC 开关后的实际显示。官方说明：
https://support.google.com/youtube/answer/2734796?hl=en
https://support.google.com/youtube/answer/2734698?hl=en

4. 评审建议选择“不公开 / Unlisted”：拿到链接的人无需 Google 账号即可观看，并可转发链接。如希望被搜索发现，可选择“公开 / Public”。不要选择“私享 / Private”作为普通评审链接，因为其访问需要单独邀请。保存后才会取得可分享的实际视频链接；在这里没有预先生成的 YouTube 地址。官方可见性说明：
https://support.google.com/youtube/answer/157177?hl=en

5. 等待 1080p 处理完成后，从退出登录的浏览器或无痕窗口打开实际视频链接；检查整段 84 秒可播放、音乐、英文字幕、封面，以及说明中的网站和署名链接。把确认可访问的真实 YouTube URL 粘贴到比赛表单的视频字段。网站 /film/ 是网页播放入口，不应填写成“YouTube 链接”。

四、填写英文提交表单

submission.en.txt 中三个字段已按 Project name ≤ 30 字符、Punchline ≤ 200 字符、Description ≤ 5000 字符准备；修改后应重新计数。名称统一为 Blueprint + Cavity。

两案例并列不代表证据成熟度相同：
- Blueprint：36 题，144 个历史 trials；其中 72 个是真实模型运行与回放，其余为特权 gold reference 与 no-op。奖励不是准确率。
- Cavity：预计算 hBN 科研展示与浏览器本地粘贴回复数字检查，不是在线科学 agent、实时模型 API 或新实验验证。
- 尚未完成三次独立 agent 重跑，未训练模型权重。不要将历史单次矩阵、240 个离线验证器 fixtures 或四题数学玩具结果改写为已完成这些工作。

保留 youtube-description.txt 的音乐与图片来源段落。Scott Buckley 的音乐署名必须出现在 YouTube 说明中，不能只留在视频画面或本包 CREDITS.txt。论文 Figure 1a 是裁切后的背景概念图，几何与本项目不同，不是本项目测量。

五、当前交付边界

这里提供可上传的现有影片、说明与字幕；没有代替用户上传、建立 YouTube 连接、发布外部消息或提交比赛表单。网站实际部署记录见项目 hosting/DEPLOYMENT.json；详细产品、操作、实现与已知限制见两份中文 PDF。不要把待执行的独立评估计划表述成已经获得的新结果。

YouTube 操作依据为上述官方帮助页，核验日期：2026-11-15。
