# 在家跑 GLM-5.2：30 token/s 是一道 4.5 万美元的墙

*2026-07-28 — by Auxten Wang*

我想在家跑 GLM-5.2。就是智谱 6 月开源的那个 744B 参数 MoE <a href="#ref-1">[1]</a>。

目标很具体：**单流解码 30 token/s**。

这条线不是拍脑袋画的，有两个参照。其一，OpenRouter 上 GLM-5.2 共 32 家推理供应商，**26 家（81%）的 P50 吞吐在 30 tok/s 以上**，供应商中位数约 41 tok/s——有意思的是 Z.ai 官方 endpoint 只有 21 <a href="#ref-38">[38]</a>。30 tok/s 就是商业推理服务的及格线，本地部署不该比买来的服务慢一个档次。其二，日常在用的闭源模型也在这个量级：GPT-5.6 官方节点 P50 约 37–38 tok/s，GPT-5.5 约 47–48 <a href="#ref-39">[39]</a>。低于 30，你会盯着终端里的字一个个往外蹦，忍不住切出去刷 X，然后思路就断了。

![OpenRouter 上 GLM-5.2 全部 32 家供应商的价格与 P50 吞吐（2026-07-28 截图）](openrouter-glm52-providers.png)

*OpenRouter `z-ai/glm-5.2` 供应商列表（P50 口径，2026-07-28 截图）：26/32 家吞吐 ≥30 tok/s，中位约 41 <a href="#ref-38">[38]</a>。*

![OpenRouter 上 GPT-5.6 Sol 的供应商与 P50 吞吐（2026-07-28 截图）](openrouter-gpt56-providers.png)

*同日的 GPT-5.6 Sol：OpenAI 官方节点 38 tps、Azure 37 tps <a href="#ref-39">[39]</a>。日常在用的闭源模型，体感就是这个量级。*

互联网对此有无数热情推荐：买 Mac Studio、攒 DGX Spark 集群、上四张 3090。我把能找到的社区实测数据全翻了一遍——r/LocalLLaMA、NVIDIA 开发者论坛、Hugging Face 讨论区、X。

结论先放这：**在我统一采用的口径下（batch-1、短到中上下文、全量模型），大多数方案到不了 30 token/s，稳定达标的组合要 4.5 万美元。** 我把结果做成一张表发到 X 上，57K 阅读。评论区补充了一批很有价值的一手实测，其中一些数字比我的表更乐观。把这些 case 消化进来之后，就是这篇文章。

这篇文章讲三件事：完整数据、评论区补充的实测 case（含各自的口径前提）、以及不同数字背后的口径差异。

先坦白调研方法，免得显得比实际更严谨：所有数字都来自社区公开实测，不是我自己买了 23 套硬件回来跑分——我没有 5 万美元的业余爱好预算。数据汇总用 [Manus](https://manus.im/invitation/CHF60YMO7MS3T?utm_source=invitation&utm_medium=social&utm_campaign=copy_link) 跑的，我人工核对了关键数字和出处。价格是 2026 年 7 月的行情，正值内存危机，波动剧烈。逐条出处见文末[参考文献](#references)。

---

## 先算物理账

GLM-5.2 是 744B 总参数的 MoE，每个 token 激活约 40B <a href="#ref-1">[1]</a>。想跑它，只有两条硬标准。

**第一，装得下。** 各量化级别的内存需求（Unsloth Dynamic GGUF 实测 <a href="#ref-2">[2]</a>）：

| 量化级别 | 内存占用 | 质量 |
|---|---|---|
| 1-bit（UD-IQ1_S） | ~223 GB | top-1 准确率 ~76%，明显降智 |
| 2-bit（UD-IQ2_M） | ~245 GB | ~82%，可用但有损 |
| 3-bit（UD-Q3_K_XL） | 290–360 GB | 较好 |
| 4-bit（UD-Q4_K_XL） | 372–475 GB | 接近无损 |
| NVFP4（官方） | ~465 GB | 接近无损，仅限 Blackwell |
| FP8（官方） | ~750 GB | 原生精度 |

也就是说，**245 GB 是入场券，370 GB 起步才谈得上"不降智"**。你的 128 GB「AI 小钢炮」，连量化最狠的版本都装不进去。

**第二，读得快。** 解码是带宽游戏：每生成一个 token，都要把约 40B 激活参数的权重完整读一遍，4-bit 下约 20–22 GB。想要 30 tok/s，需要 **600 GB/s 以上的有效带宽**。作为参照：DGX Spark 是 273 GB/s，M3 Ultra 是 819 GB/s，RTX PRO 6000 是 1.79 TB/s。

还有两个变量在搅局，后面几乎每个数字的分歧都和它们有关。

**MTP 投机解码。** GLM-5.2 内置多 token 预测，每步草拟 5 个 token <a href="#ref-1">[1]</a>，能把有效速度拉高 1.5–2.5 倍。但 llama.cpp 至今没实现 GLM 的 MTP，只有 vLLM/SGLang（以及它们的社区补丁版）能用上 <a href="#ref-3">[3]</a>。同一台机器换个软件栈，速度差一倍，就是这个原因。

**REAP 剪枝版。** 社区用 Cerebras 的 REAP 方法把 256 个专家砍到 168 个，内存需求降 34%。代价是 Terminal-Bench 从 81 分掉到 70.5 <a href="#ref-4">[4]</a>。省钱，但降智是实打实的。

---

## 一张表看全部

这是我发到 X 上的那张汇总表：

![GLM-5.2 各硬件方案成本与实测解码速度对照表](glm52-table.jpg)

*注意读法：各行测的量化并不相同，且全部为社区实测、非我本人复测。逐行的量化、引擎与出处见下表的「量化 / 引擎」「来源」两列。*

### 每行测的是哪个版本？谁测的？ {#quant-versions}

写完初版之后我意识到一个问题：这张表（包括调研报告本身）没把「每个数字到底测的是哪个量化」说透。这里补上，因为它直接影响横向比较是否公平。

**这不是同一场考试。** 每类硬件只能跑它装得下的最好量化，所以速度天然对应不同版本。读表前先分三档：

- **原生 FP8（~750 GB）**：家用设备里只有 8× RTX PRO 6000（768 GB VRAM，~$95k 起）装得下——bs=1 约 106 tok/s，出自 r/LocalLLaMA 的 llamaCTO <a href="#ref-10">[10]</a>，这是全调研唯一一个「家用 FP8」实测（DGX Station GB300 的 784 GB 一致性内存理论上也装得下，但社区目前只有 REAP 剪枝版的数字 <a href="#ref-3">[3]</a>）。官方 vLLM recipe 的 FP8 部署是 8× H200/B200 的数据中心参考口径 <a href="#ref-19">[19]</a>；后文并发一节里 GH200 的 FP8 数据则来自 dnhkng 的实测 <a href="#ref-34">[34]</a>。**本文主表和「达标」判定不基于 FP8。**
- **接近无损档（4-bit 类：NVFP4、IQ4_XS、AWQ-INT4、MLX 4-bit、Q4/Q5_K）**：本文「达标 / 擦线 / 未达标」判定的主口径，质量与全量 FP8 差距很小 <a href="#ref-2">[2]</a>。
- **降质档（3-bit 以下，及 REAP 剪枝版）**：能跑，但已经是另一个产品。表里凡是只有 1/2-bit 数据的行（2× Spark、4× 3090、Strix Halo），不是测的人偷懒——是那套硬件连 4-bit 都装不下，这本身就是结论的一部分。值得一提：4× 3090 从 2-bit 换到 1-bit 速度纹丝不动 <a href="#ref-14">[14]</a>，瓶颈在 CPU，低 bit 并没有帮这些方案虚高。

判定规则一句话：**每行按「该硬件装得下的最好量化」的社区实测来判**。带着这个前提看核心数据：

| 方案 | 内存 | 量化 / 引擎 | 实测解码 tok/s | 整机成本 | 判定 | 来源 |
|---|---|---|---|---|---|---|
| 4× RTX PRO 6000 Blackwell | 384 GB GDDR7 | REAP NVFP4·vLLM+MTP ／ 全量 IQ4_XS·llama.cpp | 45–60 ／ 38→29 | $45k–55k | **达标**（全量为擦线） | <a href="#ref-5">[5]</a><a href="#ref-6">[6]</a> |
| DGX Station GB300（单机） | 288 GB HBM3e + 496 GB LPDDR5X | REAP-504B | ~60 | ~$100k+ | 达标（剪枝版） | <a href="#ref-3">[3]</a><a href="#ref-43">[43]</a> |
| 8× GB10 集群（ASUS GX10） | 1 TB 统一 | 全量 AWQ-INT4·vLLM 补丁+MTP ／ INT4/INT8 混合 | 26–27 ／ 33–54（代码） | ~$28k–30k | 擦线 | <a href="#ref-7">[7]</a><a href="#ref-8">[8]</a> |
| 2× Mac Studio M3 Ultra | 1 TB 统一 | 全量 MLX 4-bit 分布式 | 23.4 | ~$28k+（二手） | 未达标 | <a href="#ref-11">[11]</a> |
| 4× DGX Spark | 512 GB 统一 | NVFP4 DCP4@128K ／ AWQ-INT4+15%剪 ／ NF3 混合 | 14.5–15.2 ／ 20–22 ／ 20–33 | $14k–20k | 未达标 | <a href="#ref-10">[10]</a><a href="#ref-7">[7]</a><a href="#ref-9">[9]</a> |
| 1× Mac Studio M3 Ultra 512GB | 512 GB 统一 | 全量 MLX 4-bit | 16–18.8 | ~$14.2k（二手） | 未达标 | <a href="#ref-11">[11]</a> |
| 2× RTX PRO 6000 + 1TB DDR5 | 192 GB VRAM + offload | 全量 Q4_K_XL·llama.cpp | 13–15 | ~$30k | 未达标 | <a href="#ref-3">[3]</a> |
| 2× RTX 5090 + 512GB RAM | 64 GB VRAM + offload | Q5_K_S·llama.cpp | ~12 | ~$10k | 未达标 | <a href="#ref-12">[12]</a> |
| 2× DGX Spark（互联） | 256 GB 统一 | UD-IQ1_S（1-bit）·RPC | 8.1 | ~$9.4k | 未达标 | <a href="#ref-13">[13]</a> |
| 4× RTX 3090 + 192GB RAM | 96 GB VRAM + offload | UD-IQ2_M（2-bit） | 7.3 | ~$4.5k | 未达标 | <a href="#ref-14">[14]</a> |
| 2× AMD Strix Halo（互联） | 256 GB 统一 | UD-IQ2_M（2-bit）·RPC | 7.2 | ~$5.2k | 未达标 | <a href="#ref-15">[15]</a> |
| EPYC/Xeon 纯 CPU | 512–768 GB DDR | Q2–Q4_K_XL | 1.7–5.5 | $2.5k–4k | 未达标 | <a href="#ref-16">[16]</a><a href="#ref-17">[17]</a> |
| 1× DGX Spark | 128 GB 统一 | 装不下，极限剪枝 | 1–4 | $4.7k | 未达标 | <a href="#ref-18">[18]</a> |
| AMD MI300X / Intel Gaudi | — | 无软件或渠道路径 | — | B2B only | 无路径 | <a href="#ref-19">[19]</a><a href="#ref-20">[20]</a> |

规律一句话就能说完：**只有把全部权重放进高带宽显存、并用上 MTP 的方案，才摸得到 30。** 所有依赖 CPU 内存 offload 的方案——无论显卡多强——都被系统内存带宽和 llama.cpp 缺失的 MTP 锁死在 15 以下。

![成本与解码速度散点图：只有右上角的深绿色点过线](cost-vs-speed.jpg)

*散点图同样混合了各行不同的量化配方，适合看「成本–速度」的整体格局；单点对比请回到上面的表格看量化列。*

---

## 逐条拆开看

### DGX Spark：单台是玩具，八台是方案

单台 Spark 128 GB，装不下任何可用量化，实测 1–4 tok/s <a href="#ref-18">[18]</a>。273 GB/s 的内存带宽是它先天的天花板。价格方面，内存短缺让 NVIDIA 把它从 $3,999 涨到 $4,699 <a href="#ref-21">[21]</a>；顺带一提，GB10 芯片有一整个 OEM 克隆家族，ASUS Ascent GX10 只要 $3,499，是同规格最便宜的入口 <a href="#ref-20">[20]</a>。

真正的玩法是用 ConnectX-7 组集群。4 台跑 AWQ-INT4 加 15% 剪枝加 MTP 是 20–22 tok/s <a href="#ref-7">[7]</a>；128K 上下文的 DCP4 配方掉到 14.5–15.2 <a href="#ref-10">[10]</a>；NF3 混合配方在短上下文能冲到 20–33 <a href="#ref-9">[9]</a>。

8 台 GB10（~$28k）是这条线的顶配：全量模型加 MTP 稳定 26–27 <a href="#ref-7">[7]</a>，另一个 INT4/INT8 配方在代码类输出上报告 33–54 <a href="#ref-8">[8]</a>——**在 3 万美元以内的方案里，这是唯一有实测数字越过 30 的**。代价是部署门槛全场最高：100G 交换机、手工打补丁的 vLLM、Triton 内核 hack，社区论坛里全是踩坑记录 <a href="#ref-8">[8]</a><a href="#ref-10">[10]</a>。

它还有一张隐藏王牌：prefill 有 500–1,200 tok/s <a href="#ref-8">[8]</a>。跑 agent 工作流时，这比解码速度更救命。后面讲 Mac 的时候你会明白。

### Mac Studio：曾经的王，输给了 prefill 和内存危机

M3 Ultra 有 819 GB/s 统一内存带宽，曾是大 MoE 的性价比之王。2026 年它挨了两刀。

第一刀：内存危机。Apple 直接下架了 256/512GB 配置 <a href="#ref-22">[22]</a>，512GB 机器只剩二手，约 $14,200 起，一度被炒到 $25,000 <a href="#ref-20">[20]</a>。

第二刀：实测不够快。单机 MLX 4-bit 跑全量是 16–18.8 tok/s；两台用 Thunderbolt 5 互联（Ivan Fioravanti 的实测）也只有 23.4 <a href="#ref-11">[11]</a>。256GB 机型只能塞 2-bit（3–9 tok/s）或明显降智的 1-bit（~21.6）<a href="#ref-23">[23]</a>。MLX 还没有 GLM 的 MTP 支持，未来若实现可能再提 30–50%，antirez 等人正在盯这个方向 <a href="#ref-24">[24]</a>——但那是未来。

真正的硬伤是 prefill。llama.cpp 下 33K token 的 prompt 要处理近 10 分钟 <a href="#ref-10">[10]</a>。你想用它跑 coding agent？动辄 50–100K 上下文，首 token 等 10 分钟起，实际不可用。

### 4× RTX PRO 6000：唯一稳定过线，NVIDIA 也知道

四张卡 384 GB GDDR7，1.79 TB/s 每张。全部权重驻留高带宽显存，vLLM 原生 MTP——这是唯一物理上凑齐所有条件的个人可购组合。

实测：REAP 剪枝版 NVFP4 短上下文约 60 tok/s，64k–100k 上下文仍有 ~45，prefill 5,100 <a href="#ref-5">[5]</a>；全量不剪枝 IQ4_XS 从 38 起步，40k 上下文降到 29，擦线 <a href="#ref-6">[6]</a>。

代价明码标价。NVIDIA 今年 6 月把这张卡官方涨价 55% 至 $13,250 <a href="#ref-25">[25]</a>，早期 $8,500 的街价一去不返。四卡整机 $45,000–55,000，满载 2.2 kW，需要专用电路。**这就是那道墙的价格。**

想要原生 FP8（~750 GB）得上 8 张卡（768 GB VRAM，~$95k 起）：llamaCTO 实测 bs=1 约 106 tok/s <a href="#ref-10">[10]</a>——预算翻倍，买的主要是精度而不是速度。

顺带避坑：两张卡（192 GB）装不下任何全量量化，只能 offload 到内存，13–15 tok/s <a href="#ref-3">[3]</a>。$30k 买个高不成低不就。

### DGX Station GB300：一台顶四张卡，价格也顶八张

今年刚开卖的新变量。GB300 Grace Blackwell 超级芯片单机给到 **288 GB HBM3e（约 8 TB/s）加 496 GB LPDDR5X 的一致性内存** <a href="#ref-44">[44]</a>，REAP-504B 剪枝版社区实测约 60 tok/s <a href="#ref-3">[3]</a>——和 4× RTX PRO 6000 同一个速度档，但单机塔式、1,600 W 电源就够，不用折腾四卡供电和专线。

价格同样直接。经销商 pi3g 汇总的渠道行情：**约 $100k 不含税起，各 OEM（Dell、ASUS、Supermicro、HP 等）报 $99.5k–123k**，交期 4–13 周，最早 8 月到手；页面还特别提醒「内存行情会继续推高价格」<a href="#ref-43">[43]</a>。一句话：钱翻倍，买到的主要是省事和 HBM 带宽余量，解码速度并不比 4× PRO 6000 快。

（细节备注：不同渠道页的内存数字略有出入——pi3g 标 748 GB（252+496）<a href="#ref-43">[43]</a>，NVIDIA 官方标 784 GB（288+496）<a href="#ref-44">[44]</a>。）

### 消费级多卡：最热闹，也最令人失望

这是社区尝试最多的路线，结论最残酷。4× 3090 加 192GB DDR5：7.3 tok/s。换成 1-bit 量化，速度居然不变——瓶颈根本不在带宽，在 CPU <a href="#ref-14">[14]</a>。

更反直觉的：6× 3090 是 7.8 <a href="#ref-26">[26]</a>，而 1× 5090 加 Xeon 大内存是 11 <a href="#ref-3">[3]</a>。**在 offload 路线上，多买显卡几乎无用。** $4,000 到 $10,000 的投入换来 7–12 tok/s <a href="#ref-12">[12]</a><a href="#ref-14">[14]</a><a href="#ref-26">[26]</a>，且没有任何升级路径。

### AMD 与 Intel：一个买不到，一个跑不了

双 Strix Halo 互联跑 2-bit：7.2 tok/s，机主自己的结论是「不值得」<a href="#ref-15">[15]</a>。Instinct MI300X 系列软件上其实可行，vLLM/SGLang 有官方 ROCm recipe <a href="#ref-19">[19]</a>，但只走 B2B 渠道，单卡 $25,000 起 <a href="#ref-20">[20]</a>，个人基本买不到原厂保修货。

Intel 这边，调研没有找到 GLM-5.2 的 GlmMoeDsa 新架构在 IPEX/SYCL 栈上的任何支持记录，Gaudi 3 个人渠道买不到。最现实的是 Xeon AMX 加 ktransformers（官方有 GLM-5.2 教程 <a href="#ref-27">[27]</a>），个人配置推算 10–16 tok/s，未达标。

### 服务器 CPU：3,000 美元的门票，进场看个热闹

二手 EPYC 加 512 GB DDR4 约 $2,500–3,500，是「能跑起来」的最低门槛：纯 CPU 1.7–5.5 tok/s <a href="#ref-16">[16]</a><a href="#ref-17">[17]</a>，加两张 3090 做 offload 后 6–11 <a href="#ref-16">[16]</a>。这条路线的意义是花 $3k 体验 744B 模型本身，而不是达到 30 tok/s。

---

## 评论区补上的拼图

表发出去之后，X 评论区补充了一批一手信息，最集中的都在 DGX Spark 集群这条线上——这正是调研最需要的东西：更多真实 case。我把它们原样列在这里，每条补了口径备注：

<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:24px 0;">
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">KING JEW <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@0xSero · 蓝 V</span></p>
<p style="margin:0 0 8px;">"GLM-5.2 runs in 4 sparks at 30 tok/s"</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：未注明量化与上下文。他是 REAP 剪枝版与 sm120 配方的作者 <a href="#ref-4">[4]</a><a href="#ref-5">[5]</a>，若跑的是剪枝版，4 台 Spark 到 30 与带宽账相符。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">3.2K 阅读 · 55 赞 · <a href="https://x.com/0xSero/status/2081473238173925508" target="_blank" rel="noopener">原回复</a> <a href="#ref-28">[28]</a></p>
</div>
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">Jim McPherson <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@JamesMcPherson · 蓝 V</span></p>
<p style="margin:0 0 8px;">自己的 4 台 Spark 跑到 40–41 tok/s，后又补充：现在超过 40 了。他同时认为，8 台不该比 4 台慢，怀疑表中 8× 数据的配置。</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：未注明配置。若是剪枝版 + 短上下文 + MTP 代码负载，与表中全量模型 256K 上下文的 26–27 <a href="#ref-7">[7]</a> 并不冲突，两者测的不是同一件事。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">650 阅读 · 9 赞 · <a href="https://x.com/JamesMcPherson/status/2081476483797889461" target="_blank" rel="noopener">原回复</a> <a href="#ref-29">[29]</a></p>
</div>
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">Dave Charland <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@Dave_Charland · 蓝 V</span></p>
<p style="margin:0 0 8px;">正在用 4 台 Spark 跑，8 台用户的反馈是「fantastic」。他也点出了取舍的另一面：RTX 6000 方案体验肯定很好，前提是不介意噪音、发热和大得多的初始投入。</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：定性体验，未报具体数字。他补充的维度（噪音、散热、初始投入）是我的表里没有的列，确实该算进决策。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">1.3K 阅读 · 13 赞 · <a href="https://x.com/Dave_Charland/status/2081469046218686749" target="_blank" rel="noopener">原回复</a> <a href="#ref-30">[30]</a></p>
</div>
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">Austin S. Lin <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@siraustin · 蓝 V</span></p>
<p style="margin:0 0 8px;">给出一套成本账：4 台 Spark 加 MikroTik 交换机加线材，约 $20k。</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：成本 case，与表中 4× Spark 的 $14k–20k 区间上沿一致（含网络设备），互相印证。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">191 阅读 · <a href="https://x.com/0xSero/status/2081473238173925508" target="_blank" rel="noopener">原回复</a> <a href="#ref-31">[31]</a></p>
</div>
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">Taimur Ayaz <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@taimurayaz · 蓝 V</span></p>
<p style="margin:0 0 8px;">提到那些机器跑的是 fp16。</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：若指权重精度，fp16 需约 1.5 TB，4 台 Spark 的 512 GB 装不下；更可能指的是计算精度（权重量化、激活 fp16）。原帖未展开，存档待考。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">285 阅读 · <a href="https://x.com/0xSero/status/2081473238173925508" target="_blank" rel="noopener">原回复</a> <a href="#ref-32">[32]</a></p>
</div>
<div style="border:2px solid var(--border);background:var(--card-bg);box-shadow:var(--shadow);padding:16px;">
<p style="margin:0 0 6px;font-weight:700;">Kristoph <svg viewBox="0 0 22 22" width="16" height="16" style="vertical-align:-2px;"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></svg> <span style="color:var(--text-tertiary);font-weight:400;">@kristoph · 蓝 V</span></p>
<p style="margin:0 0 8px;">把口径问题一句话点破：能不能跑没有争议——图里写了能跑；争议只在按什么标准算达标。</p>
<p style="margin:0 0 8px;font-size:0.9em;color:var(--text-secondary);">口径备注：这正是本文的主题——下面两节就是把「标准」这件事拆开算。</p>
<p style="margin:0;font-size:0.85em;color:var(--text-tertiary);">112 阅读 · <a href="https://x.com/Dave_Charland/status/2081469046218686749" target="_blank" rel="noopener">原回复</a> <a href="#ref-33">[33]</a></p>
</div>
</div>

有一个背景值得单独说：**@0xSero 不是路人。** 我调研里引用的 REAP 剪枝版模型（GLM-5.2-504B <a href="#ref-4">[4]</a>）和 4× RTX PRO 6000 的 sm120 vLLM 配方 <a href="#ref-5">[5]</a>，都出自他手。这样背景的人给出的一手数字，值得放在最前面认真消化。

把所有数字画在同一根轴上，各自的位置就清楚了：

<figure>
<svg viewBox="0 0 760 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;font-family:inherit;">
<line x1="50" y1="270" x2="730" y2="270" stroke="var(--text-tertiary)" stroke-width="1.5"/>
<g fill="var(--text-tertiary)" font-size="12" text-anchor="middle">
<text x="50" y="290">0</text><text x="201" y="290">10</text><text x="352" y="290">20</text><text x="503" y="290">30</text><text x="654" y="290">40</text>
<text x="730" y="290">tok/s</text>
</g>
<g stroke="var(--text-tertiary)" stroke-width="1">
<line x1="50" y1="266" x2="50" y2="274"/><line x1="201" y1="266" x2="201" y2="274"/><line x1="352" y1="266" x2="352" y2="274"/><line x1="503" y1="266" x2="503" y2="274"/><line x1="654" y1="266" x2="654" y2="274"/>
</g>
<line x1="503" y1="30" x2="503" y2="270" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 5"/>
<text x="510" y="26" fill="var(--accent)" font-size="13" font-weight="700">目标 30 tok/s</text>
<rect x="269" y="60" width="113" height="26" fill="var(--blue)" opacity="0.75" stroke="var(--border)" stroke-width="1.5"/>
<text x="260" y="77" fill="var(--text)" font-size="13" text-anchor="end">公开配方实测 14.5–22（4-bit 类）[7][10]</text>
<rect x="352" y="110" width="196" height="26" fill="var(--blue)" opacity="0.35" stroke="var(--border)" stroke-width="1.5" stroke-dasharray="4 3"/>
<text x="344" y="127" fill="var(--text)" font-size="13" text-anchor="end">NF3 配方短上下文 20–33 [9]</text>
<circle cx="503" cy="185" r="8" fill="var(--accent)" stroke="var(--border)" stroke-width="1.5"/>
<g transform="translate(374,176) scale(0.82)"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></g>
<text x="368" y="190" fill="var(--text)" font-size="13" text-anchor="end">@0xSero：30 [28]</text>
<rect x="654" y="228" width="15" height="14" fill="var(--accent)" stroke="var(--border)" stroke-width="1.5"/>
<g transform="translate(524,221) scale(0.82)"><path fill="#1d9bf0" fill-rule="evenodd" d="M20.396 11c-.018-.646-.215-1.275-.57-1.816-.354-.54-.852-.972-1.438-1.246.223-.607.27-1.264.14-1.897-.131-.634-.437-1.218-.882-1.687-.47-.445-1.053-.75-1.687-.882-.633-.13-1.29-.083-1.897.14-.273-.587-.704-1.086-1.245-1.44S11.647 1.62 11 1.604c-.646.017-1.273.213-1.813.568s-.969.854-1.24 1.44c-.608-.223-1.267-.272-1.902-.14-.635.13-1.22.436-1.69.882-.445.47-.749 1.055-.878 1.688-.13.633-.08 1.29.144 1.896-.587.274-1.087.705-1.443 1.245-.356.54-.555 1.17-.574 1.817.02.647.218 1.276.574 1.817.356.54.856.972 1.443 1.245-.224.606-.274 1.263-.144 1.896.13.634.433 1.218.877 1.688.47.443 1.054.747 1.687.878.633.132 1.29.084 1.897-.136.274.586.705 1.084 1.246 1.439.54.354 1.17.551 1.816.569.647-.016 1.276-.213 1.817-.567s.972-.854 1.245-1.44c.604.239 1.266.296 1.903.164.636-.132 1.22-.447 1.68-.907.46-.46.776-1.044.908-1.681s.075-1.299-.165-1.903c.586-.274 1.084-.705 1.439-1.246.354-.54.551-1.17.569-1.816zM9.662 14.85l-3.429-3.428 1.293-1.302 2.072 2.072 4.4-4.794 1.347 1.246z"/></g>
<text x="518" y="240" fill="var(--text)" font-size="13" text-anchor="end">@JamesMcPherson：40–41 [29]</text>
</svg>
<figcaption>4× DGX Spark 的各方数字放在同一根轴上：色带为公开可复现配方的实测区间 <a href="#ref-7">[7]</a><a href="#ref-9">[9]</a><a href="#ref-10">[10]</a>，圆点为评论区补充的一手数字（量化与上下文未注明）<a href="#ref-28">[28]</a><a href="#ref-29">[29]</a>。注意各配方量化并不相同（NVFP4 DCP4 / AWQ-INT4+剪枝 / NF3 混合），全部为社区实测、非本人复测。</figcaption>
</figure>

把口径对齐之后，我的判断是：**这些数字和我的表大概率都是真的，它们测的是不同的东西。** 有四个变量足以造成这种差距：

**上下文长度。** NF3 配方在短上下文能冲到 33，128K 上下文的 DCP4 配方只有 14.5 <a href="#ref-9">[9]</a><a href="#ref-10">[10]</a>。同一套硬件，速度差一倍多。

**MTP 接受率。** 投机解码在代码类输出上接受率高，速度是自由文本的 1.5–2 倍 <a href="#ref-8">[8]</a>。跑 coding agent 测出的数，和通用口径记录的数，天然不可比。

**全量还是剪枝。** 这可能是最关键的一条。REAP 剪枝版少读约三分之一的权重 <a href="#ref-4">[4]</a>，20–22 tok/s 的 4× Spark <a href="#ref-7">[7]</a> 换上剪枝版，冲到 30 在带宽账上完全成立。0xSero 本人就是剪枝版作者——他说的「GLM-5.2」和我表里的「GLM-5.2 全量」，很可能不是同一个模型，而两个数字都对。

**单流还是聚合。** 多请求并发的总吞吐是另一套算法，值得单独一节，就是下一节。

至于 40–41 <a href="#ref-29">[29]</a>：我还没能在公开配方里给它对上号——最接近的是 NF3 短上下文的 33 <a href="#ref-9">[9]</a>。这更可能说明公开资料滞后于一线玩家的手工调优，而不是数字有问题。等拿到 vLLM 参数、量化版本和上下文长度，我会把它作为新配方并进表里。这也是本地 LLM benchmark 的现状：**大家都在测，但很少测的是同一个东西。** 我的表统一取 batch-1、短到中上下文、来源可溯源的口径——好处只是你确切知道我在测什么。

---

## 如果把并发算进来呢？

评论区补充的数字里，很可能有一部分是聚合口径：两个请求各 20 tok/s，合计 40。这个口径完全正当——多 agent 并行本来就是很多人的真实负载——所以我专门为它做了补充调研，结论比直觉有意思。

对稠密模型来说，并发几乎免费：batch=2 时权重读一遍服务两个请求，吞吐接近翻倍。**但 GLM-5.2 的 MoE 结构把这个红利砍掉了大半。** 每层从 256 个专家里激活 8 个，两个并发请求命中的专家几乎不重叠，路由专家的权重读取量随并发线性增长。能复用的只有注意力和共享专家，约占三分之一。算下来 batch=2 的聚合增益只有 1.2–1.4 倍，不是 2 倍。

实测锚点也支持这个推算：双 GH200 重度 offload 跑 FP8，batch=4 的聚合增益只有 1.16 倍 <a href="#ref-34">[34]</a>；Apple Silicon 上 MoE 模型 5 路并发是 1.89 倍 <a href="#ref-35">[35]</a><a href="#ref-36">[36]</a>。而全显存方案完全是另一个世界：8× RTX PRO 6000 从 bs=1 的 106 到 bs=8 的约 420，接近 4 倍 <a href="#ref-10">[10]</a>。

所以聚合口径下的格局是：

**$28k 档确实翻身了。** 8× GB10 并发 2–4 时聚合 34–46，从擦线变达标；双 M3 Ultra 摸到 29–40；4× Spark 在 bs=4 下勉强够到聚合 30（均为按 MoE scaling 系数的推算，误差 ±20%）。如果你的真实负载就是多个 agent 并行，每个流 15–25 tok/s 也能接受，$14k–28k 就够了。评论区部分 case 的数字，可能正是这个口径下测出来的。

**低价 offload 阵营依然没救。** 瓶颈在系统内存带宽和 CPU，MoE 的专家不重叠让它们的并发增益全场垫底，batch=4 也就从 7 提到 10 出头。地基太慢，并发救不了。

**最反直觉的：4× RTX PRO 6000 反而更划算了。** 单流口径下它是「最贵的达标方案」；聚合口径下它并发 4 预计 150–200，按每单位聚合吞吐算成本约 $300–350 每 tok/s，比 8× GB10 的 $650–700 便宜一半。它可以同时喂 5–8 个 agent，每个还保持 25+ tok/s。

两个工程注意点：并发挤占 KV cache，长上下文和高并发在 128GB/节点的 Spark 上不可兼得（4× Spark 的 128K 配方干脆设了 MAX_NUM_SEQS=1 <a href="#ref-10">[10]</a>）；MTP 和并发存在竞争，GH200 上开 MTP 后并发 4 的聚合反而从 23.6 掉到 15.2——但同机的 AWQ 配方又是正收益 <a href="#ref-34">[34]</a>。逐配置实测，别想当然。

---

## 把关键硬件的参数摆在一起 {#hw-specs}

跑分讲完了，把候选平台的原始规格放进同一张表，很多结论会自己浮出来。算力列统一取厂商公布的稀疏 FP4 AI 算力（3090 没有 FP4，给 INT8；Apple/AMD 口径不同，已标注）：

| 平台 | 架构 | 典型方案 GPU 数 | 单 GPU 算力 | 单 GPU 显存/内存带宽 | 卡间/节点间互联 | 2026-07 市场价 |
|---|---|---|---|---|---|---|
| RTX PRO 6000 Blackwell | Blackwell | 4–8 张 | ~4,000 AI TOPS（FP4） | 96 GB GDDR7 @ 1.79 TB/s | PCIe 5.0 x16（无 NVLink）≈ 64 GB/s | $13,250/张 <a href="#ref-25">[25]</a> |
| DGX Station GB300 | Blackwell Ultra + Grace | 1（超级芯片） | ~20 PFLOPS（FP4） | 288 GB HBM3e @ ~8 TB/s（另 496 GB LPDDR5X @ 396 GB/s） | NVLink-C2C（CPU↔GPU 900 GB/s）；对外 ConnectX-8 800 Gb/s | ~$100k+/台 <a href="#ref-43">[43]</a><a href="#ref-44">[44]</a> |
| DGX Spark / GB10 | Blackwell（GB10） | 4–8 台 | ~1 PFLOP（FP4） | 128 GB LPDDR5x @ 273 GB/s | ConnectX-7 200 GbE ≈ 25 GB/s | $3,499–4,699/台 <a href="#ref-20">[20]</a><a href="#ref-21">[21]</a> |
| Mac Studio M3 Ultra | Apple M3 Ultra（SoC） | 1–2 台 | ~28 TFLOPS（FP32，GPU 估算） | 512 GB 统一 @ 819 GB/s | Thunderbolt 5 ≈ 10 GB/s | 二手 ~$14.2k/台 <a href="#ref-20">[20]</a><a href="#ref-45">[45]</a> |
| AMD Strix Halo（AI Max+ 395） | Zen 5 + RDNA 3.5（SoC） | 2 台 | ~126 TOPS（平台合计） | 128 GB 统一 @ 256 GB/s | ≤10 GbE RPC ≈ 1.25 GB/s | ~$2.6k/台 <a href="#ref-20">[20]</a><a href="#ref-46">[46]</a> |
| RTX 5090 | Blackwell | 1–2 张 | ~3,352 AI TOPS（FP4） | 32 GB GDDR7 @ 1.79 TB/s | PCIe 5.0，无 NVLink | ~$3k/张（行情） <a href="#ref-20">[20]</a> |
| RTX 3090 | Ampere | 4–6 张 | ~285 TOPS（INT8） | 24 GB GDDR6X @ 936 GB/s | NVLink 桥 112.5 GB/s（限两卡） | 二手 ~$800/张 <a href="#ref-20">[20]</a> |

规格取自各厂商官方页 <a href="#ref-44">[44]</a><a href="#ref-45">[45]</a><a href="#ref-46">[46]</a>，价格为 2026-07 行情，出处见各行标注。

两条读表结论。**第一，解码速度基本是「单 GPU 带宽」那一列的函数**：~8 TB/s 的 GB300 和 1.79 TB/s 的 PRO 6000 过线，273 GB/s 的 Spark 和 256 GB/s 的 Strix Halo 出局；算力列反而没那么重要——20 PFLOPS 和 1 PFLOP 在 batch=1 解码里跑出的差距远小于 200 倍，LLM 解码不缺算力，缺搬运。

**第二，互联那一列解释了「堆节点」为什么难**：Spark 集群节点间只有 25 GB/s，比自家那本就不宽裕的显存带宽还低一个数量级；堆节点堆的是容量，不是带宽。同理，3090 的 NVLink 桥只连两卡，四卡方案照样要走 PCIe——这也是消费级多卡路线撞墙的硬件原因。

---

## 算总账

按你愿意接受什么，分层推荐：

| 你的要求 | 方案 | 预期速度 | 预算 |
|---|---|---|---|
| 严格单流 ≥30，全量模型质量 | 4× RTX PRO 6000（IQ4_XS）<a href="#ref-6">[6]</a> | 29–38 | ~$50k |
| 严格单流 ≥30，接受 REAP 剪枝 | 4× RTX PRO 6000 + NVFP4 <a href="#ref-5">[5]</a> | 45–60 | ~$45k–55k |
| ≥30 且主要跑代码，接受折腾 | 8× ASUS GX10 + INT4/INT8 + MTP <a href="#ref-8">[8]</a> | 26–27 稳定 / 33–54 峰值 | ~$28k–30k |
| 聚合 ≥30，有真实并发负载 | 8× GB10 或 2× M3 Ultra | 单流 15–25 | ~$28k |
| 接受 ~20，要长上下文 agent | 4× GB10（ASUS 版）<a href="#ref-7">[7]</a> | 20–22，prefill 500+ | ~$14k–16k |
| 接受 ~17–23，要安静省电 | 二手 M3 Ultra 512GB ×1 或 ×2 <a href="#ref-11">[11]</a> | 16–19 / 23.4 | ~$14k / $28k |
| 只想体验 744B 跑起来 | 二手 EPYC 512GB + 1–2 张 3090 <a href="#ref-16">[16]</a> | 6–11 | ~$3k–4.5k |
| 理性经济人 | API 或按小时租卡 <a href="#ref-20">[20]</a><a href="#ref-37">[37]</a> | 44+ | $3/M token 或 $2–6/时 |

三点提醒，都是数据里最容易被忽略的。

**第一，30 tok/s 的成本是非线性的。** 20 tok/s 只要 $14k，23 tok/s 要 $28k，「稳定 30+」直接跳到 $45k。最后那 7 个 tok/s 比前面 23 个加起来还贵。想清楚你是不是真的需要 30。

**第二，现在是买 AI 硬件的最差时点。** 内存危机让 Spark 涨了 18% <a href="#ref-21">[21]</a>、RTX PRO 6000 涨了 55% <a href="#ref-25">[25]</a>、Mac 大内存直接停售 <a href="#ref-22">[22]</a>。同时 M5 Ultra 传闻 10 月发布，llama.cpp 的 GLM MTP 支持若落地，所有 offload 方案都会提速 50% 以上。如果不急，观望一个季度。

**第三，别只盯着解码，prefill 会杀人。** 30 tok/s 只描述了往外吐字的速度。跑 coding agent 动辄塞 50–100K 上下文：Mac 系 prefill 只有 60–90 tok/s，首 token 要等 10–20 分钟，实际不可用 <a href="#ref-10">[10]</a>；GB10 集群是 500–1,200 <a href="#ref-8">[8]</a>；RTX PRO 6000 是 5,000 <a href="#ref-5">[5]</a>。这个维度上的差距比解码速度更悬殊。

最后是那笔让所有硬件都尴尬的账。GLM-5.2 官方 API 定价 $1.40/M 输入、$4.40/M 输出 <a href="#ref-37">[37]</a>；OpenRouter 上供应商标价低至 $2.42/M 输出，算上缓存后的全网加权实付价约 $0.39/M 输入、$3.31/M 输出 <a href="#ref-38">[38]</a>。**4× RTX PRO 6000 的购机款，够在 API 上买大约 100 亿个输出 token。**

### 200 美元一个月能买到什么 {#usd200}

同一张 $200 的钞票，三种花法。全部是粗算，假设直接写在表里（2026-07 行情）：

| 花法 | 能得到什么 | 依据与假设 |
|---|---|---|
| Claude Code Max 20x 订阅（$200/月） | 官方周限：每周 240–480 小时 Sonnet + 24–40 小时 Opus <a href="#ref-40">[40]</a>。重度用户实际卡的是周限而非 5 小时窗口：按 ccusage 口径的 token 流量折算，**打满周限 ≈ $1,100/周 API 等值 <a href="#ref-41">[41]</a>，一个月 4.33 个周 ≈ $4,700**。很多人的体感在 $4,000 上下——正对应「窗口打不满、周限打满」的用法 | 等值按 Anthropic API 牌价折算 <a href="#ref-41">[41]</a>；补贴率约 20 倍 |
| 同样 $200 打给 GLM-5.2 API | 官方价 ≈ 45M 输出 tokens；按 OpenRouter 加权实付 $3.31/M ≈ 60M 输出。若是输入为主的 agent 负载——该模型全网流量 prompt:completion ≈ 100:1——$200 能推 ≈ 500M 输入 tokens。作为对照：Max 20x 满额那篮 token 按 GLM-5.2 牌价折算约 $1,000/月（Opus 牌价约为 GLM 的 4–6 倍），$200 大约只够覆盖五分之一 | 价格取 2026-07-28 快照 <a href="#ref-38">[38]</a> |
| 自建 4× RTX PRO 6000，只算电费 | 满载 2.2 kW 跑 24/7 ≈ 1,600 kWh ≈ **$300/月电费，比订阅本身还贵**；每天跑 8 小时 ≈ $100/月 | 美国居民电价均值 18.8¢/kWh <a href="#ref-42">[42]</a>；$50k 硬件本金与折旧未计 |

顺带补两个电费参照：8× GB10 满载约 1.9 kW，24/7 约 $260/月；双 M3 Ultra 按 ~0.5 kW 算只有 ~$70——Mac 的省电在月账单上是真金白银。

当然，Opus 和 GLM-5.2 不是同档模型，这张表比的不是模型智商，是三种计价方式：**订阅是 20 倍上下的补贴价，API 是市场价，自建连电费都打不过补贴价。** 所以本地部署的理由只剩四个：隐私、离线、无限调用、研究癖。我承认我主要是最后一种。

---

## 所以，我买了吗？

还没有。

我在等三件事：M5 Ultra 的大内存版本、llama.cpp 的 GLM MTP、内存价格从危机里回落。三件事里任何一件落地，上面那张表的半壁江山都要重写。这也是本地 LLM 硬件最迷人和最劝退的地方：**结论的保质期以季度计。**

如果你等不了，按推荐表买，别买中间档——两张 RTX PRO 6000 和两张 5090 是全场性价比最差的位置。

这张表也不是终点。如果你手上有新的实测——尤其是 Spark 集群的 vLLM 参数、量化版本和上下文长度——欢迎发到 [X 原帖](https://x.com/auxten/status/2081289965892170033)下面，我会持续把新 case 合并进来。

---

## 参考文献 {#references}

数据底稿：本文全部数字的汇总与核对过程见[完整调研报告（23 行数据表 + 并发口径重评估）](https://manus.im/share/9oL67aZfJNMupcL7HG9VW6)，由 [Manus](https://manus.im/invitation/CHF60YMO7MS3T?utm_source=invitation&utm_medium=social&utm_campaign=copy_link) 协作完成；社区 case 见 [X 原帖与全部回复](https://x.com/auxten/status/2081289965892170033)。以下为分条来源，全部条目均已附原始链接（以 2026-07-28 可访问为准）：

1. <span id="ref-1"></span>Z.ai 官方博客 — [GLM-5.2: Built for Long-Horizon Tasks](https://z.ai/blog/glm-5.2)（744B 总参/40B 激活、MTP 每步 5 token、1M 上下文、MIT 开源；[官方 Hugging Face 镜像](https://huggingface.co/blog/zai-org/glm-52-blog)同文）
2. <span id="ref-2"></span>Unsloth 文档 — [GLM-5.2 – How to Run Locally](https://unsloth.ai/docs/models/glm-5.2)（各量化级别内存需求实测）
3. <span id="ref-3"></span>atcyrus.com — [GLM 5.2 local hardware requirements: reported paths by quant](https://www.atcyrus.com/stories/glm-5-2-local-hardware-requirements)（社区实测路径汇总表；含引擎 MTP 支持现状与混合配置行情）
4. <span id="ref-4"></span>Hugging Face — [0xSero/GLM-5.2-504B](https://huggingface.co/0xSero/GLM-5.2-504B)（REAP 剪枝版模型卡，Terminal-Bench 70.5）
5. <span id="ref-5"></span>GitHub — [0xSero/glm-5.2-sm120](https://github.com/0xSero/glm-5.2-sm120)（4× RTX PRO 6000 REAP-469B NVFP4 vLLM 配方：~60 tok/s，64k–100k 上下文 ~45，prefill ~5,100）
6. <span id="ref-6"></span>Hugging Face — [lukealonso/GLM-5.2-NVFP4 讨论区](https://huggingface.co/lukealonso/GLM-5.2-NVFP4/discussions/1)（回帖中 Ununnilium 报 4× RTX PRO 6000 全量 IQ4_XS：38 → 35 → 29 tok/s @ 0/10k/40k 上下文）
7. <span id="ref-7"></span>NVIDIA 开发者论坛 — [GLM-5.2 on a 4x GB10 cluster: ~22 tok/s decode, 256K ctx (recipe)](https://forums.developer.nvidia.com/t/glm-5-2-on-a-4x-gb10-cluster-22-tok-s-decode-256k-ctx-recipe/374125)（含 8× GB10 全量 AWQ-INT4 + MTP 26–27 tok/s 回帖）
8. <span id="ref-8"></span>NVIDIA 开发者论坛 — [GLM-5.2-Int4-Int8 on 8× GB10: ~1,200 t/s prefill, 33–54 t/s avg decode](https://forums.developer.nvidia.com/t/glm-5-2-int4-int8-on-8x-gb10-1-200-t-s-prefill-33-54-t-s-avg-decode-generic-coding-structured/376831)（代码类负载均值；部署补丁细节）
9. <span id="ref-9"></span>NVIDIA 开发者论坛 — [GLM-5.2 (unpruned) at 800K max context on 4x DGX Spark (NF3 hybrid)](https://forums.developer.nvidia.com/t/glm-5-2-unpruned-at-800k-max-context-on-4x-dgx-spark-20-33-tok-s-nf3-hybrid-checkpoint/375909)（NF3 混合配方 20–33 tok/s）
10. <span id="ref-10"></span>Reddit r/LocalLLaMA — [High-quality GLM-5.2 Quant on 4x DGX Spark – Guide, Results, and Comps](https://www.reddit.com/r/LocalLLaMA/comments/1uidtb8/)（llamaCTO；DCP4 128K 上下文 14.5–15.2 tok/s、MAX_NUM_SEQS=1；8× RTX PRO 6000 bs=1 约 106 / bs=8 约 420；M3 Ultra 长上下文 prefill 数据；同配方在 NVIDIA 论坛有作者镜像帖）
11. <span id="ref-11"></span>X @ivanfioravanti — [MLX GLM 5.2 Distributed on two M3 Ultra 512GB](https://x.com/ivanfioravanti/status/2068722319913066603)（单台 18.8 tok/s、双机 23.4 tok/s；16 tok/s 下沿见 [10] 的 llama.cpp 口径）
12. <span id="ref-12"></span>Reddit r/LocalLLaMA — [GLM 5.2 on consumer hardware](https://www.reddit.com/r/LocalLLaMA/comments/1ufd4g8/glm_52_on_consumer_hardware/)（2× RTX 5090 + 512GB Q5_K_S 约 12 tok/s）
13. <span id="ref-13"></span>NVIDIA 开发者论坛 — [GLM 5.2 on 2x DGX Spark (GB10) nodes: 1-bit UD-IQ1_S, RPC llama.cpp, 256K context, ~8 tok/s](https://forums.developer.nvidia.com/t/academic-glm-5-2-on-2x-dgx-spark-gb10-nodes-crazy-1-bit-ud-iq1-s-rpc-llama-cpp-256k-context-8-tok-s/374523)（勘误：本文初版沿用调研报告将此条记为 howtospark.com，核对后实际出处为该论坛帖）
14. <span id="ref-14"></span>Reddit r/LocalLLaMA — [GLM5.2 744B 2-bit at 7.3 tok/s on 4x3090 + 192GB, and why](https://www.reddit.com/r/LocalLLaMA/comments/1u9mpty/glm52_744b_2bit_at_73_toks_on_43090_192gb_and_why/)（1-bit 换量化速度不变的 CPU 瓶颈结论）
15. <span id="ref-15"></span>Framework 社区 — [GLM 5.2 on Dual Strix Halo (256GB): Worth it?](https://community.frame.work/t/glm-5-2-on-dual-strix-halo-256gb-worth-it/83201)（llama.cpp RPC 实测 7.2 tok/s，机主结论「不值得」）
16. <span id="ref-16"></span>Hacker News — [GLM-5.2 – How to Run Locally 讨论帖](https://news.ycombinator.com/item?id=48636377)（EPYC 512GB + 2× 3090 实测 ~6 tok/s 可调到 9–11；电费与 API 成本对比）
17. <span id="ref-17"></span>Reddit r/LocalLLaMA — [CPU-only GLM 5.2: Epyc and 512GB RAM](https://www.reddit.com/r/LocalLLaMA/comments/1uiqiqc/cpuonly_glm_52_epyc_and_512gb_ram/)（EPYC 7452，UD-Q4_K_XL 实测 1.73 tok/s）
18. <span id="ref-18"></span>NVIDIA 开发者论坛 — [GLM 5.2 on 1x Spark](https://forums.developer.nvidia.com/t/glm-5-2-on-1x-spark/376996)（单机 offload 起步 1 tok/s，调优后 4 tok/s）
19. <span id="ref-19"></span>vLLM 官方 Recipes — [zai-org/GLM-5.2](https://recipes.vllm.ai/zai-org/GLM-5.2)（8× H200/H20/B200 与 AMD ROCm 部署参考）
20. <span id="ref-20"></span>llmrequirements.com — [State of Local AI](https://llmrequirements.com/state-of-local-ai/)（2026-07 硬件价格、功耗、云租价全景：ASUS GX10 $3,499、二手 M3 Ultra 行情、MI325X/MI355X 价格等）
21. <span id="ref-21"></span>Tom's Hardware — [Nvidia DGX Spark gets 18% price increase as memory shortages bite](https://www.tomshardware.com/desktops/mini-pcs/nvidia-dgx-spark-gets-18-percent-price-increase-as-memory-shortages-bite-founders-edition-now-usd4-699-up-from-usd3-999)（$3,999 → $4,699）
22. <span id="ref-22"></span>MacRumors — [Apple Cuts More Mac Studio and Mac Mini RAM Options as Memory Shortage Worsens](https://www.macrumors.com/2026/05/05/apple-mac-studio-mac-mini-ram-cuts/)
23. <span id="ref-23"></span>rentamac.io — [Run GLM 5.2 on a Mac: The Memory You Need](https://rentamac.io/run-glm-on-mac/)（256GB 机型：2-bit 3–9 tok/s、1-bit 约 21.6 tok/s）
24. <span id="ref-24"></span>X @antirez — [GLM 5.2 4-bit 在 M3 Ultra 上「可用了，但硬件买不到了」](https://x.com/antirez/status/2068736130757857529)（引用 [11] 的实测；后续跟帖讨论 MTP 实现方向）
25. <span id="ref-25"></span>Tom's Hardware — [Nvidia raises RTX Pro 6000 Blackwell GPU pricing to $13,250 — 55% increase over MSRP](https://www.tomshardware.com/pc-components/gpus/nvidia-raises-rtx-pro-6000-blackwell-gpu-pricing-to-usd13-250-55-percent-increase-over-msrp-in-a-years-time)
26. <span id="ref-26"></span>Reddit r/LocalLLaMA — [GLM 5.2, what speeds are we getting locally?](https://www.reddit.com/r/LocalLLaMA/comments/1ub69xu/glm_52_what_speeds_are_we_getting_locally/)（楼主 6× 3090 实测 7.8 tok/s 等汇报）
27. <span id="ref-27"></span>GitHub — [Running GLM-5.2 with SGLang and KT-Kernel（ktransformers 官方教程）](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/kt-kernel/GLM-5.2-Tutorial.md)（CPU-GPU 异构 MoE offload，CPU 侧为 AMX 内核）
28. <span id="ref-28"></span>X [@0xSero 的回复](https://x.com/0xSero/status/2081473238173925508)（4× Spark 30 tok/s）
29. <span id="ref-29"></span>X [@JamesMcPherson 的回复](https://x.com/JamesMcPherson/status/2081476483797889461)（4× Spark 40–41 tok/s）
30. <span id="ref-30"></span>X [@Dave_Charland 的回复](https://x.com/Dave_Charland/status/2081469046218686749)（4 台在用体验与取舍）
31. <span id="ref-31"></span>X [@siraustin 的回复](https://x.com/0xSero/status/2081473238173925508)（4× Spark + MikroTik 约 $20k）
32. <span id="ref-32"></span>X [@taimurayaz 的回复](https://x.com/0xSero/status/2081473238173925508)（fp16 之说）
33. <span id="ref-33"></span>X [@kristoph 的回复](https://x.com/Dave_Charland/status/2081469046218686749)（口径之辩总结）
34. <span id="ref-34"></span>dnhkng.github.io — [2x GH200 for LLM inference, Part 3: GLM-5.2, expert offload, and the CPU question](https://dnhkng.github.io/posts/gh200-benchmarking-part-3-glm52/)（batch 1/2/4 聚合实测；MTP 与并发的正负收益对照）
35. <span id="ref-35"></span>Reddit r/MacStudio — [you probably have no idea how much throughput your Mac Studio is leaving on the table…](https://www.reddit.com/r/MacStudio/comments/1rvgyin/you_probably_have_no_idea_how_much_throughput/)（M4 Max：MoE 30B 5 并发 1.89×、dense 3B 1.04×；LM Studio MLX 引擎尚无连续 batching）
36. <span id="ref-36"></span>arXiv [2601.19139](https://arxiv.org/abs/2601.19139) — *Native LLM and MLLM Inference at Scale on Apple Silicon*（连续 batching 提升 21–87% 吞吐）
37. <span id="ref-37"></span>ofox.ai — [Run GLM 5.2 Locally (2026): 2-bit on a 256GB Mac or 4090 box](https://ofox.ai/blog/glm-5-2-run-locally-gguf-2026/)（本地 vs API 成本；官方 $1.40/M 输入、$4.40/M 输出）
38. <span id="ref-38"></span>OpenRouter — [z-ai/glm-5.2 模型页](https://openrouter.ai/z-ai/glm-5.2)（32 家供应商价格与 P50 吞吐、加权实付价、流量构成；正文数字与截图为 2026-07-28 快照）
39. <span id="ref-39"></span>OpenRouter — [openai/gpt-5.6](https://openrouter.ai/openai/gpt-5.6)、[openai/gpt-5.5](https://openrouter.ai/openai/gpt-5.5) 模型页（官方节点 P50 吞吐 37–38 / 47–48 tps，2026-07-28 快照）
40. <span id="ref-40"></span>Anthropic Help Center — [About Claude Max plan usage](https://support.anthropic.com/en/articles/11014257-about-claude-max-plan-usage)（Max 20x 每周与 5 小时窗口限额的官方描述）
41. <span id="ref-41"></span>Botfarm — [The True Price of a Claude Max Weekly Limit (in API Dollars)](https://botfarm.run/blog/claude-max-true-price/)（用 ccusage 真实 token 流量折算：Max 20x 打满周限 ≈ $1,100/周 API 等值，约 20 倍补贴）
42. <span id="ref-42"></span>U.S. EIA — [Electric Power Monthly](https://www.eia.gov/electricity/monthly/)（2026 年 4 月全美居民电价均值 18.8¢/kWh）
43. <span id="ref-43"></span>pi3g — [NVIDIA DGX Station available now for purchase](https://pi3g.com/nvidia-dgx-station-available-now-for-purchase-from-us/)（GB300 渠道行情：约 $100k 不含税起、各 OEM $99.5k–123k、交期 4–13 周；748 GB 一致性内存与 ConnectX-8 规格）
44. <span id="ref-44"></span>NVIDIA — [DGX Station（GB300）产品页](https://www.nvidia.com/en-us/products/workstations/dgx-station/)、[DGX Spark](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)、[RTX PRO 6000 Blackwell](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/) 官方规格页
45. <span id="ref-45"></span>Apple — [Mac Studio 技术规格](https://www.apple.com/mac-studio/specs/)（M3 Ultra 819 GB/s 统一内存带宽）
46. <span id="ref-46"></span>AMD — [Ryzen AI Max+ 395 规格页](https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html)（Strix Halo 平台）