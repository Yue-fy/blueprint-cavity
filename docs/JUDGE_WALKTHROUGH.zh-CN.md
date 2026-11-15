# Blueprint + Cavity：十分钟评审演示与证据指南

> 公开仓库阅读版：本文详细保留产品实现与开发历程。当前安装、运行与评审以 [仓库首页](../README.zh-CN.md) 和 [公开评审路线](REVIEW_GUIDE.md) 为准。标为“开发归档路径”的原始研究、托管或制作文件未随此仓库分发；路径用于说明历史来源，并非可执行入口。配套 PDF 保留交付时的冻结版本。

> 适用评审：AfterQuery 环境挑战；依据用户提供的 `Pasted text.txt` 原文整理。评分为 Gap 30、Meaningful difficulty 30、Reward integrity 25、Craft 15。本文是可直接排练的演示指南，不是自评满分报告。
>
> **版本状态**：现有站点已通过匿名 HTTP 与浏览器验收，用户无需密码访问完整演示与 hBN 数据；本轮新增 Blueprint/Cavity 并列首页和 #cavity 入门，相关新版验收以 DEPLOYMENT.json（开发归档路径：`../hosting/DEPLOYMENT.json`） 为准。84 秒既有影片保持不变，四步 Blueprint 导览仍围绕 bp-01-clean；Cavity 提供同等入口，其证据是预计算研究展示与本地checker，没有hBN Harbor模型评测。历史建筑144条、独立toy16条不改；新allowlist派生任务已实现，Docker/Modal实际出站、三次模型重跑与训练仍未完成。

## 1. 先介绍两条并列路线，再说明证据差异

首页 Cases 同时呈现 Blueprint 与 Cavity。两者共同要求检查数字背后的依据：Blueprint 检查模型如何从建筑图纸作出数量和边界决定；Cavity 检查纳米腔的预计算场谱、测量窗口与粘贴回复中的数值判断。访客不需要先完成建筑任务才能发现科学案例，常驻导航随时可切换。

建议第一句话：

> 这里有两个并列案例。Blueprint 展示 AI 在真实图纸上的历史工具使用与奖励；Cavity 展示怎样探索纳米腔的保存数据、比较测量选择并检查 AI 回复。入口同等，但证据各自单列，我们不会把预计算画面算成新的模型试验。

英文可说：

> “Choose either case. Blueprint exposes recorded AI decisions on real drawings. Cavity lets you inspect precomputed nanocavity data and check numerical claims. They share an evidence-first interface, while their experimental records remain separate.”

Blueprint 的示范任务仍是 Fitness Room：DeepSeek29.1m²、Kimi26.4m²、参考26.9m²。Cavity 的入门则从物理目标、模式、线宽与回复检查进入/hbn/。建筑已有144条历史trial；Cavity尚无hBN Harbor评估矩阵。Boundary lab四道toy另有16条trial，其中8条是学习模型尝试，也不能计入Cavity场模拟证据。

30/30/25/15评审证据主要来自可运行任务、真实行为、奖励与复现。并列展示不改变标准，也不使漂亮场图替代模型重跑。既有84秒影片专讲Blueprint并简述hBN，本轮不重剪；现场应让两个入口在第一分钟都可见。

核查来源：[并列首页](../web/index.html)、[导航与案例逻辑](../web/app.js)、Cavity完整页构建（开发归档路径：`../hbn_demo/build.py`）、[建筑结果](../RESULTS.md)、[独立toy结果](../science_demo/RESULTS.md)、物理边界（开发归档路径：`hbn-integration/PHYSICS_REVIEW.md`）。

## 2. 30/30/25/15：标准、证据与缺口对照

| 评审项 | 原文满分重点 | 当前可以直接展示 | 仍不能据此声称完成 |
| --- | --- | --- | --- |
| **Gap · 30 分** | frontier agent 稳定低于已展示的更强参考；重复运行可复现 | 建筑 DeepSeek 0.392409、Kimi 0.807308；privileged oracle 1.0；真实 72 条模型回放 | 160 个历史 trial 不是每题三次独立 agent 重跑；oracle 写入预置参考答案，不证明同信息策略达到 1.0；模型是否符合现场 frontier 指定应确认 |
| **Meaningful difficulty · 30 分** | 失败来自任务决策；信息与可用工具足以改进 | 原图与范围明确；Fitness Room横线/边界决策、尺度与几何；真实JSON、工具观察和数量偏差 | 不能用超时或工具异常单独证明推理困难；不能把没有提交的记录编造成标高误读；失败成因需由具体轨迹支持 |
| **Reward integrity · 25 分** | 完成任务最好；无动作/提前停下分低；评委难以靠漏洞获高分 | 75/15/10 契约、错误值对证据的门控、重复/越界/超大框拒绝；40题×6类离线审计中reference1、no-op0、abstention0.1 | 离线fixture不等于新Harbor运行或十五分钟评委红队；stop-early当前定义是观察后弃权，非强行中断模型；框/数字不证明完整推导 |
| **Craft · 15 分** | 规则合理，README 一条评估命令可复现报告结果 | Harbor/OpenCode 固定版本、镜像、独立离线 verifier、实际 Modal 记录、本地 Docker 配置、离线审计与协议命令、桌面/手机工作台 | 本机未跑 Docker Engine；公开站点/媒体验收须看部署登记；allowlist实际出站未验证；协议不自动汇总新结果 |

**训练项**：原文正文提出训练更小模型，并在 tie-breaker 再次说明偏好。当前没有训练、没有权重 checkpoint、没有训练前后独立结果，不把 prompt 调整、模型切换、oracle 或新视频叫作训练。可以说明环境支持后续训练研究，但不能宣称已满足这一加分条件。

**参考的严谨称呼**：当前 oracle 是 `privileged gold reference / 预置参考答案对照`。它验证奖励可达和评估管线，不能隐去它知道答案的事实。新增科学解析reference从中性参数求解，已实现但尚无新Harbor轨迹；建筑reference仍是gold oracle。若用 Kimi 作为比 DeepSeek 更强的观察到的基线，应说“同一历史任务矩阵中观察到更高奖励”，仍要补独立重跑与相同预算条件，才能支撑稳定差距。

核查来源：[正式建筑结果](../RESULTS.md)、[科学结果](../science_demo/RESULTS.md)、[oracle 脚本](../tasks/bp-10-vector/solution/solve.sh)、[评分测试](../tests/test_scoring.py)、[评委配置](../configs/judge-docker-core-deepseek.json)、[README](../README.md)。

## 3. 十分钟逐分钟脚本

先展示两张同等案例卡，再分别给Blueprint与Cavity一条完整操作路线。下表采用现场演示；如先播84秒Blueprint影片，应删减相同建筑操作，不能用整段影片占掉Cavity的展示时间。完整奖励/协议细节仍可在本指南后续章节展开。

| 时间 | 画面与操作 | 主讲内容 | 必须保留的边界 |
| --- | --- | --- | --- |
| 0:00–1:00 | Cases总览，同时指向Blueprint与Cavity两张Explore case卡和常驻导航 | “任选一个案例，都能检查结论的依据；两案证据记录分别列示。” | 建筑历史benchmark、Cavity预计算/local checker、独立toy不能合并 |
| 1:00–2:00 | Blueprint→The task→The decision，定位房间与橙框 | “agent读图、定位、计算；DeepSeek保存假设把约y2245的线当家具/设备。” | 保存工作，不是现场推理；该决策不是唯一误差来源 |
| 2:00–3:00 | Reveal the comparison→The score | “29.1与26.4对照26.9；Kimi数量满分，证据部分得分，奖励0.88714。” | 参考向访客显式揭示，奖励不是准确率 |
| 3:00–4:00 | 打开真实Replay，再短暂Try it yourself | “可检查原JSON/工具观察，再用人的表单调用同一scorer。” | 人的操作另标；看过参考后不是盲测 |
| 4:00–5:00 | 常驻Cavity→#cavity，读物理目标与入门顺序 | “hBN中红外光耦合晶格振动；先问看什么模式，再问如何量化。” | 简介是操作入口，实际模块位于/hbn/；不启动求解 |
| 5:00–6:00 | 进入/hbn/，查看Mode map与Pick your box，切全/窄窗口 | “保存模式可探索；同谱仅改变窗口，Q可由52.7变96.4。” | 不把窄窗高值说真值；不声称场收敛或检测等价 |
| 6:00–7:00 | AI reviews AI→本地回复检查，演示明确ANSWER与含糊回复 | “解析器只核对固定参数数值或给unscored，公式/证明仍人工复核。” | 不调用AI；九摘要不是Harbor；匹配不是证明 |
| 7:00–8:00 | All cases回总览→Results，展开完整记录；必要时说明/science/ | “建筑144、toy16含对照；Cavity未新增模型trial。” | 160不是三次重复；privileged oracle与真实模型分开 |
| 8:00–9:00 | 展示240个离线fixture与新协议task_snapshot | “奖励有确定规则；新任务仅配置Verda allowlist，原160与任务不改。” | fixture不是新试验；实际Docker/Modal出站未验证，公开答案和记忆污染仍需考虑 |
| 9:00–10:00 | 回Cases，给影片、中文PDF、两案入口与证据索引 | “可从任一案例继续查看；公开功能已验收，新UI版本看部署记录。” | 无训练、无新重跑、无实时科学agent；保留准确后续任务 |

两张卡主按钮同为Explore case，含义由卡片标题和辅助标签区分；键盘访问同样可用常驻Blueprint/Cavity导航。Blueprint导览进入第三/第四步会请求参考；Cavity完整页的All cases、Blueprint和About Cavity负责跨案例导航，切换不改变保存数据或计数。

核查来源：[首页与导航](../web/index.html)、[导览/路由](../web/app.js)、Cavity页导航（开发归档路径：`../hbn_demo/build.py`）、[原始DeepSeek](../data/trajectories/full-deepseek-bp-01-clean.json)、[原始Kimi](../data/trajectories/full-kimi-bp-01-clean.json)、公开验收（开发归档路径：`../hosting/DEPLOYMENT.json`）。

## 4. Agent 的世界：观察、动作、工具、终止与奖励

### 4.1 建筑环境

**目标**是回答工作要求指定的量，范围必须与题目一致。初始观察包括 instruction、图纸文件、页尺寸/空间、测量约定与答案格式。agent 的工作目录为 `/workspace`。中性输入与agent构建上下文不含trusted gold；但不能据此保证网络上拿不到公开答案。原始任务网络是public，新allowlist尚未实际验证；环境也不应通过故意藏尺度制造不可能题。

**动作**是文件与终端工具使用：列出文件、读图/PDF、提取文本、渲染裁剪图、OCR、分析像素与几何、运行计算、写/编辑答案、选择置信度或弃权。新的**观察**来自命令输出、文件内容、图像与工具错误。agent可以根据新观察修改几何解释和下一步计划。这不是只有一次多选猜测，也不要求每题使用所有工具。

**终止与交接**由agent结束或预算限制决定；评估工件为 `/workspace/answer.json`。agent没有在每一步得到gold reward来爬坡的本项目接口；最后才由独立verifier检查工件。人的网页已获授权公开评分与reveal。原始public网络agent可能主动访问这些答案；新协议通过派生任务配置Verda-only allowlist，但Docker/Modal实际阻断尚未验证。前端按钮或构建上下文都不能替代出站验证，也不能排除记忆污染。

**预算**以冻结task.toml为准：agent 600秒、1 CPU、2 GB内存，verifier 60秒、1 CPU、256 MB且无网络。构建超时与运行超时是不同阶段。超时记录不从分母移除；诊断有意义困难时优先用完成但数值失败的记录，不把资源耗尽自动归为几何推理失败。

**奖励**为0.75数量+0.15证据+0.10校准；证据乘数量分，完整正确可达1，no-op为0，合法零置信弃权最多0.1。正确值但空证据仍可得到较高的数量/校准分，说明当前主要优化目标仍是正确量算，证据不是唯一成功定义。评委若要求“没有过程就不能高分”，应如实讨论这一目标取舍，不能假称已经强制证明所有推导。

### 4.2 已观察到的实际工具

| 工具 | 代表参数 | 对任务的意义 | 检查方法 |
| --- | --- | --- | --- |
| `read` | `filePath` | 观察输入或中间结果 | 同时看返回内容，不能只看调用名 |
| `bash` | `command` | 执行PDF/OCR/渲染/计算与检查命令 | 查看命令、exit/observation和生成文件 |
| `write` | `filePath, content` | 生成脚本或最终answer.json | 查看保存工件是否与提交一致 |
| `edit` | `filePath, oldString, newString` | 依据新观察修改脚本/答案 | 修改不是自动正确，仍由结果检查 |
| `glob` | `pattern, path` | 发现可用文件 | 只在允许目录内定位输入 |
| `grep` | `pattern, path` | 检索文本信息 | 不能替代图形尺度与边界判断 |
| `todowrite` | `todos` | 组织长流程 | 不是任务完成证据或奖励来源 |

72条正式建筑模型轨迹记录的tool-call事件数为：bash3701、read348、todowrite106、write53、glob35、edit4、grep4。它们是保存事件计数，不是成功执行计数，也不是OpenCode所有平台工具的完整清单。镜像另外提供Poppler、Tesseract、PyMuPDF、Pillow、NumPy、Shapely与OpenCV；框架层与命令层工具要分开讲。

评审原文提到Harbor/OpenCode通过MCP与环境连接。当前可核查交付是Harbor文件/容器任务与OpenCode工具使用；不能据原文措辞反向声称已实现一个自定义MCP科研工具服务器。若标准harness要求额外接口，应以实际适配与重跑证据补充。

### 4.3 数学 toy 与 hBN 的区别

toy agent接收定义、固定参数和格式，可推导或用工具数值检查，提交value/confidence/rationale；90%数值、10%校准，rationale语义不评分。这个环境确实有Harbor任务和官方结果。

hBN页面让人切换预计算场、扫频切片、观测量代理、拟合窗口，并本地计算一个toy或检查粘贴文本。它没有定义并执行新的“科学agent自动选仿真—调用COMSOL—取得观测—学习策略”闭环，也没有hBN Harbor reward矩阵。可把它当作后续科学环境设计动机，但当前不把规划叫成果。

核查来源：[task.toml](../tasks/bp-10-vector/task.toml)、[建筑镜像工具](../tasks/bp-10-vector/environment/Dockerfile)、[主API](../blueprint_gym/server.py)、[科学环境](../science_demo/ENVIRONMENT.md)、[科学评分](../science_demo/scoring.py)、hBN构建（开发归档路径：`../hbn_demo/build.py`）、[手册工具详表](PRODUCT_MANUAL.zh-CN.md)。

## 5. 有意义难度：把错误连接到决策，不编造因果

| 决策 | 为什么值得学 | agent已有的信息/工具 | 可展示证据与限制 |
| --- | --- | --- | --- |
| 定位目标与排除对象 | “西立面窗”不能把门或框中线重复计数 | 明确方向约定、整页图、裁剪/放大、图形/文字检索 | Kimi bp-06-clean的逐段排除、18框与高奖励支持成功策略 |
| 恢复尺度与选取内边界 | 同一像素长度需转换物理量，墙面选择影响结果 | 比例尺、尺寸串、页尺寸、PyMuPDF/Pillow/计算 | DeepSeek bp-01-clean保存了34.48px/m与118×293像素推导，最终数值偏差仍在；不能只因有尺度计算就说已完成 |
| 合并尺寸链与限定楼板范围 | 相邻板型、gross/net与凸出stair bay影响面积 | 题目排除规则、板型标注、尺寸串、矢量几何 | DeepSeek bp-08-vector保存588m²、27框，gross与inner-face假设混合；这是可见决策问题，完整成因仍需图纸核查 |
| 证据选择 | 大量宽泛框不能替代相关元素定位 | 页坐标与证据规则、绘图/文本工具 | 数值错误使证据分归零；无关框受罚；不要把命中框叫完整证明 |
| 置信度与弃权 | 不确定时应避免自信编数 | 可重查图纸、追加工具、合法null契约 | 校准只占0.1；可检查高置信错误与低置信失败的不同结果 |
| toy边界展开 | 从局部表达提取常数项影响极限 | 完整数学定义与参数、计算工具 | 非零A区分，A=0不区分；结果不能直接归因为锚定 |

另一条因果定位更直接的例子来自科学toy：`science-kimi-four / science-a-03` 保存提交为0.0057988165680473375、confidence1、reward0，completed而非timeout。rationale在 `E=e0+g(h(u)+h(v))` 中令 `e0=E(0,0)=0.35`，但 `h(0)=1`，已把常数重复计入；正确常数是 `g(c+2A)=0.21`，参考极限0.003925652940233937，偏差约+47.7%。这条真实错误值与hBN历史故事中的0.002318354554951627不同。演示可直接展示保存rationale和输入，不需推测模型心态。[保存提交与分项](../science_demo/results.json)、[证明](../science_demo/proof.md)。

讲失败时采用三层句式：“记录显示X；与题目要求Y不一致；这提示需要改进Z，但目前没有独立消融证明唯一原因。”例如，真实楼板失败的保存假设已经足够说明需要更严谨的范围/计量约定；没有必要把它改写成更戏剧性的“把标高10000当面积”。

对超时则另说：“该trial在600秒预算内未形成有效终局，按规则为零并保留warning。它证明当前运行失败，不单独证明模型不会数学/几何。”这能避免把broken tools、过短预算或基础设施错误包装成meaningful difficulty。

核查来源：[健身房失败回放](../data/trajectories/full-deepseek-bp-01-clean.json)、[楼板失败回放](../data/trajectories/full-deepseek-bp-08-vector.json)、[西立面成功回放](../data/trajectories/full-kimi-bp-06-clean.json)、[来源和计量约定](../LICENSES.md)、[完整结果警告](../RESULTS.md)。

## 6. 给十五分钟奖励利用检查准备什么

本节是可复核的测试入口和预期行为，不预判评委找不到新漏洞。演示使用隔离的本地答案文件或测试对象，不修改冻结gold和历史模型提交。所有手工攻击应标明是评分器测试，而不是模型自发行为。

| 候选利用方式 | 当前预期行为 | 现有证据/仍需解释 |
| --- | --- | --- |
| 什么都不交 | 0 | 历史no-op矩阵；漏交与合法弃权分开 |
| 停止前只写合法null、confidence0 | 最高0.1 | scorer规则可检查；这不等于已跑独立stop-early策略 |
| 完全错值加任意框 | value=0，evidence=0，总分最多0.1 | 明确数量门控与trap bound单测 |
| 同一框重复或>32个框 | 无效，0 | 唯一性/数量限制测试 |
| 框整页、越界、零宽高 | 无效，0 | 单框>90%页面积拒绝；所有坐标以原页空间检查 |
| 错单位、布尔数值、NaN、重复JSON键 | 无效或维度不匹配不给值/证据分 | 区分unsupported unit与合法但错误维度 |
| 格式正确、答案正确、无证据 | 数量/校准可得分，证据0 | 是当前契约，不应说已消除此路径；正确数字并非“无任务工作”的自动证明 |
| 引用相关大区域但没有真实推导 | 框可命中，推导未独立验证 | annotated框验证相关范围；不把它说成证明系统 |
| 反复问本地人的score/reveal以猜gold | 人类演示API确实允许评分/reveal；正式agent必须隔离 | 检查容器实际可达网络、输入边界；UI禁用不是安全证明 |
| 尝试读gold、solution或原始研究 | agent上下文不应包含；生产原始路由拒绝 | 检查task build context和部署allowlist，不能只靠口头承诺 |

如果发现新的漏洞，记录输入、任务版本、输出、成功条件和修复建议；若修复改变奖励含义或接受答案，应新建版本并重评，不在正式演示前静默修改冻结规则。当前Python对抗测试是可靠起点，正式judge攻击是新的证据。

核查来源：[评分契约测试](../tests/test_scoring.py)、[严格文件解析](../blueprint_gym/verify.py)、[环境隔离测试](../tests/test_tasks.py)、[API边界测试](../tests/test_api.py)、远端访问验证（开发归档路径：`hbn-integration/FINAL_REVIEW.zh-CN.md`）。

## 7. 重跑、强参考与复现的交接清单

当前新增了纯离线审计 `scripts/judge_check.py`、评审协议生成器 `scripts/judge_protocol.py` 与 `blueprint_gym/judge_agents.py` 中的两项可执行控制策略。下表将“有文件”“离线验证”和“真实Harbor轨迹”分开，避免通过文档更新制造实验。

| 检查项 | 已确认状态 | 达到评审要求还需要什么 |
| --- | --- | --- |
| 36题×4 agent/model | 历史144条完成，含2个warning | 新三次agent独立attempt的结果、trial身份与共同配置 |
| 四toy×4 agent/model | 历史16条完成，含2个timeout零分 | 若作为评审任务，应同样定义重复运行口径 |
| 建筑Privileged oracle | 预置gold脚本与36条1.0 | 若评审要求同信息建筑reference，需要可复现求解策略与运行 |
| 科学同输入解析reference | 已实现，仅读取中性input.json，用解析式和有理数计算 | 属于已知task-family解析策略，不是学习模型；新Harbor运行尚待执行 |
| No-op | 历史36条0 | 标准harness重跑日志 |
| Stop-early | 已实现读取目录一次后写合法零置信弃权；40题离线fixture均0.1 | 新Harbor策略运行尚待执行；不能称为time-truncated模型实验 |
| 单命令入口 | 离线check、协议生成与显式execute入口已实现 | 目标机器执行、依赖/凭据/资源前置条件与实际结果检查 |
| 本地Docker | schema校验，当前服务器未运行 | 评委机器或其他合适主机实际执行 |
| 学习改进 | 未训练 | 真实训练经验、checkpoint与独立训练前后评测；没有则坦诚留空 |

重复运行应固定任务集合、工作要求、工具、预算和评分版本，整组使用新job ID与目录、每次attempt保留不同trial身份；保存计划分母、全部终局、warning和缺失记录。不能把vector/clean/scan当同一输入的三次随机复跑，也不能把smoke、被中断oracle和正式矩阵混起来凑次数。

新协议为每题计划六条运行：reference一次、所选agent三次、no-op一次、stop-early一次；建筑216条，科学24条。agent三次由Harbor的 `n_attempts=3` 定义，均处于新的协议结果目录，不改写既有160条。默认输出 `prepared_not_executed`，同时创建独立网络派生任务、原/派生文件SHA与task_snapshot；只有显式 `--execute` 才启动模型与容器。进程结束也只记 `processes_finished_inspect_harbor_results`，仍需检查每条结果与警告，不能把退出码当作稳定差距。

离线审计命令（不启动模型、Harbor或仿真）：

```sh
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/judge_check.py
```

报告覆盖36建筑+4科学题，每题reference/noop/stop_early/confident_wrong/duplicate_keys/overflow_number六类fixture。当前保存报告为pass：reference1，noop0，显式弃权0.1，后三类0。建筑reference使用gold；科学reference从中性参数推导。它同时核对历史导出、hash与36/4个任务的完整计划分母；缺失、重复、pending时不发布均值。不把240个fixture说成240个新模型trial。

安全预览新协议：

```sh
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python scripts/judge_protocol.py --suite science --model kimi \
  --environment docker --run-id judge-science-preview
```

输入目录和结果目录必须是新的；同一run-id准备后再次使用会拒绝。实际执行要用新的run-id，并显式增加 `--execute`；所需凭据/资源前置条件见代码与README。已有执行授权也不会使默认预览暗中调用服务。

以下单项Docker命令仅保留历史复现用途：原任务网络是public，公开答案后可能污染结果。未来评审应使用上面的派生协议并验证出站，不把该命令当作隔离完成证据：

```sh
nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/harbor run --config configs/judge-docker-core-deepseek.json \
  --job-name judge-core-deepseek-new --yes
```

对应历史参考配置为 `judge-docker-core-oracle.json`，也是public网络原任务和privileged reference。模型需要 `VERDA_INFERENCE_API_KEY`；不要在投影终端中打开环境文件、打印密钥或展示带凭据的服务设置。Modal是已执行历史路径；凭据与资源授权应从已有受保护配置使用，指南本身不执行作业。

核查来源：[离线审计](../scripts/judge_check.py)、[已保存审计](judge-audit.json)、[评审协议](../scripts/judge_protocol.py)、[解析reference与stop-early](../blueprint_gym/judge_agents.py)、[README](../README.md)、[Docker模型配置](../configs/judge-docker-core-deepseek.json)、[Docker oracle配置](../configs/judge-docker-core-oracle.json)、[导出规则](../scripts/export_results.py)。

### 7.1 公开答案后的网络检查

用户已授权完整演示与hBN数据匿名公开，参考/replay因此是可被取得的答案来源。原smoke/full/direct-local配置仍选择public网络任务；不要继续说“agent永远看不到gold”。新`blueprint_gym/judge_network.py`只在独立副本中改agent environment为allowlist `inference.verda.com`，verifier保持separate/no-network，任务其他字节不改；每文件原始/派生SHA与整个manifest可查。

来源中的符号链接/特殊文件、重复任务、冻结树内输出、不同control任务集合和未审查provider配置都会被拒绝。生成配置使用绝对派生路径。镜像构建下载和运行agent出站是不同阶段；若缺依赖导致失败，不能静默改回public。

`runtime_egress_verified:false` 表示Docker/Modal的实际阻断、Verda连接与相关daemon/kernel能力尚未执行验证。配置通过不是防火墙证明；即使未来阻断有效，也不能消除模型先前记忆。应把这组新网络版本的结果与原160条分开，保留完整计划分母。[网络实现](../blueprint_gym/judge_network.py)、[协议](../scripts/judge_protocol.py)、[原任务](../tasks/bp-01-clean/task.toml)、[授权](../hbn_demo/authorization.json)。

## 8. 保留的84秒影片、音乐与外部科研背景

本轮不修改既有84秒影片。它以单条Fitness Studio案例解释Blueprint，按任务→保存AI工具/边界决策→DeepSeek29.1/Kimi26.4/参考26.9→反馈→hBN独立扩展→人的Try it yourself→品牌与公共URL展开。片尾不再显示Python命令或交付清单。保存轨迹动画标为`Saved AI run · visualized`，人工UI另行标注；没有新模型推理、训练或在线仿真。旧90秒/72秒/79.84秒版本是历史，不能混用哈希、音轨与QA。当前treatment（开发归档路径：`../video/blueprint-launch/treatment.md`）、[当前成品清单](../video/DELIVERY.json)。

音乐改用Scott Buckley的`Catalyst`，官方CC BY4.0。播放器与素材记录保留曲名、作者、来源和许可；不称新版音乐为项目原创合成。YouTube上传还需在视频描述中署名。[作者曲目页](https://www.scottbuckley.com.au/library/catalyst/)、[使用说明](https://www.scottbuckley.com.au/library/using-this-music/)。音轨编码/响度检查不能代替主观试听结论。

hBN背景图为Barra-Burillo等，Nature Communications12,6206(2021)，DOI`10.1038/s41467-021-26060-x`的Fig.1a，CC BY4.0，明确裁剪和外部出处。它说明两个金镜间hBN微腔中的光/晶格振动耦合，几何不同于本项目纳米腔；不标成本项目实验、模型输出或物理验证。[论文](https://www.nature.com/articles/s41467-021-26060-x)、[图例](https://www.nature.com/articles/s41467-021-26060-x/figures/1)。

公共入口为`https://blueprint-takeoff-lab.bronze-crane-2444.chatgpt.site/`，两案总览/#overview、Cavity入门/#cavity、影片/film/、中文手册/guide/、完整Cavity页/hbn/。现有公开能力已通过匿名HTTP/browser检查；本轮并列UI的对应新版验收查DEPLOYMENT.json（开发归档路径：`../hosting/DEPLOYMENT.json`）。源码相对链接需要配套仓库，不代表整份私有仓库都已公开。

核查来源：[播放器与署名](../web/film.html)、影片素材账本（开发归档路径：`../video/blueprint-launch/materials.md`）、hBN物理边界（开发归档路径：`hbn-integration/PHYSICS_REVIEW.md`）。

## 9. 排练、故障降级与交付

演示前打开Cases双卡、Blueprint四步导览、两条bp-01-clean回放、Cavity入门/完整页、人工工作台与Results，并准备README/评分契约。不要提前在主要手工任务里点reveal后声称独立测量；展示参考时明确它已经揭示。

公开入口若临时不可达，使用本地应用或真实录屏；这不抹去既有匿名验收，也不能替代本轮新版状态检查。公开产品无需把后端秘密交给评委。无WebGL时直接展示二维Q/toy和降级提示，不要将浏览器能力问题当科研算法失败。网络不稳定时不要临时发起付费模型作业拖住十分钟。

把最难回答的四个问题预先说清：

1. **参考是不是知道答案？** 是，现有oracle是privileged gold reference。更公平的同信息参考需另外展示。
2. **三次重跑在哪里？** 历史160行不满足该含义；只引用真正新job与结果，没有就说尚未执行。
3. **训练改善在哪里？** 当前没有权重训练或改善证据，不用提示词修改替代。
4. **科研画面是不是agent在控制仿真？** 不是。hBN为预计算浏览器解释；真实科学agent任务是四个数学toy，契约与结果单列。

交给评委的最小证据包应包含任务/依赖/配置、来源许可、正式结果与脱敏轨迹、评分器与对抗测试、复现命令和明确限制。原始秘密、私有研究大文件和浏览器认证材料不进入包。新的电影与手册可作为说明材料，但不能取代真正运行记录。

核查来源：[交付说明](../DELIVERY.md)、[任务包生成](../scripts/build_tasks.py)、[归档脚本](../scripts/package_submission.py)、私有边界（开发归档路径：`../hosting/README.md`）、[中文手册](PRODUCT_MANUAL.zh-CN.md)。

## 10. 交付状态与后续证据

以下表格分别记录已经存在的交付与仍需实际运行的证据：

| 字段 | 当前状态 | 核查证据或下一步 |
| --- | --- | --- |
| 新评审统一命令/报告入口 | 已实现；离线40题×6审计pass | [check](../scripts/judge_check.py)、[protocol](../scripts/judge_protocol.py)、[报告](judge-audit.json)；新模型执行仍待验证 |
| 三次独立agent重跑 | 本指南未核实新记录 | 新job ID、三次独立trial/attempt身份、任务hash、预算、逐次结果 |
| 同信息强参考策略 | 科学解析reference已实现；建筑仍gold oracle | 新Harbor轨迹尚未完成；不把二者权限混同 |
| Stop-early独立基线 | 观察目录后明确弃权策略已实现，离线fixture0.1 | 新Harbor轨迹尚未完成，不称中断学习模型 |
| 论文Fig.1 | 2021 Nature Communications图与CC BY4.0已核查 | 影片/播放器保留署名、许可与crop标签，不是本项目几何 |
| 84秒新版产品片 | 单案例、英文字幕、Catalyst、品牌与公共URL | 源稿（开发归档路径：`../video/blueprint-launch/index.html`）、[当前交付清单](../video/DELIVERY.json) |
| 匿名公开能力 | 现有公开HTTP/browser、影片/PDF/hBN与人的评分已验收 | 本轮并列首页/#cavity另看DEPLOYMENT（开发归档路径：`../hosting/DEPLOYMENT.json`）对应版本 |
| Blueprint与Cavity并列 | 两张同等案例卡、常驻导航与Cavity入门 | 网站层级改变，84秒影片与历史评估记录不改 |
| 新网络策略 | allowlist派生任务与全量来源SHA已实现 | runtime_egress_verified仍false；无新Harbor隔离轨迹 |
| 手册与本指南HTML/PDF | 同一生成器从Markdown重建 | 生成器（开发归档路径：`render_manual.py`）、[机器清单](MANUAL_DELIVERY.json)，含链接/布局/页数检查 |

每次补充都应指向可读取的证据，而不是仅把状态词改成“完成”。评分表中的分值是评委权重，本指南没有给自己预测分数。

生成两份本地 HTML/PDF：在项目根目录执行 `nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python docs/render_manual.py --pdf`。它不会发布或启动模型；PDF 写入 `dist/docs/`，章节、页数与 SHA-256 保存在 [MANUAL_DELIVERY.json](MANUAL_DELIVERY.json)。
