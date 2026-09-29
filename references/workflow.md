# 运行与文件约定

## 环境

需要 Apple Silicon macOS、Python 3.12、Node、Playwright/Chromium、FFmpeg/FFprobe 和中文字体（macOS 默认 PingFang SC）。优先复用已存在的依赖环境；在 Codex 桌面端可通过 `load_workspace_dependencies` 找 Node/Python/Playwright 的可用路径。不要把某台机器的绝对路径写进新项目脚本。

本流程已验证的 Python 包版本：

```sh
uv venv /absolute/workdir/.venv --python 3.12
uv pip install --python /absolute/workdir/.venv/bin/python \
  'mlx-audio==0.5.6' 'mlx==0.32.2' 'mlx-whisper==0.4.3' \
  'soundfile==0.14.0' 'opencc-python-reimplemented==0.1.7'
```

这些是复现版本，不是要求将已有环境降级。首次使用需下载 TTS 模型与 `mlx-community/whisper-small-mlx`；缓存齐全后可用 `HF_HUB_OFFLINE=1`。模型文件不随技能复制。声音参数固定为 Serena / Chinese，seed 42，temperature 0.7；自然讲解的 instruct 已在 `voice.py` 内指定。

Node 能直接 `require('playwright')` 时不需要额外变量。否则将 `PLAYWRIGHT_MODULE` 设为现有 Playwright 包绝对路径；自带浏览器无法找到时，将 `CHROMIUM_EXECUTABLE` 设为本机 Chromium 可执行文件。环境变量的值是文件路径，不是 shell 命令。

## 每个版式一个工作目录

```text
workdir/
  project.json
  narration.json
  capture.json
  assets/screen-recording.webm
  assets/voice-<id>.wav           # voice.py 生成
  assets/voice-<id>.json          # 配音缓存签名
  alignment.json                # align.py 的实际语音词时间
  alignment-warnings.json
  subtitles.json
  layout.json                   # frames.cjs 生成
  output/master.mp4
  output/demo-landscape-1.2x.mp4
  output/subtitles.srt
  output/timeline.json
  output/verification.json
```

`project.json`：

```json
{"title":"产品演示","urlLabel":"product.example","profile":"landscape","speed":1.2,"tailSeconds":0.24,"note":"姓名已匿名"}
```

`profile` 是 `landscape` 或 `portrait`。只有确实做了匿名处理才写该 note；未裁掉等待就不加相应说明。可在单个分镜中设置 `note`。默认 `voice` 不用配置；用户明确指定变化时可覆盖模型、音色、instruct 等。

`narration.json` 中每段包含 `id`、`text`、`chapter`，可选 `chunks`、`note`。id 只用小写字母、数字、连字符和下划线。`chunks` 拼接必须与 text 完全一致；用它调整自然断句，不改写内容。配音脚本填入正常语速的 `audioDuration`、`duration`。缓存签名包含文本与语音配置，避免旧音频被误复用。

```json
[{"id":"contact","text":"想联系？一键生成专属联系信。","chapter":"一键生成联系信","chunks":["想联系？","一键生成专属联系信。"],"note":"生成等待已剪辑"}]
```

## 命令顺序

将 `$SKILL_DIR`、`$WORK_DIR`、`$DEMO_PYTHON` 设为实际绝对路径。以下变量为便于阅读的示例，不是系统环境变量。

```sh
"$DEMO_PYTHON" "$SKILL_DIR/scripts/voice.py" "$WORK_DIR"
"$DEMO_PYTHON" "$SKILL_DIR/scripts/align.py" "$WORK_DIR"
node "$SKILL_DIR/scripts/frames.cjs" "$WORK_DIR"
"$DEMO_PYTHON" "$SKILL_DIR/scripts/compose.py" "$WORK_DIR"
```

查看 `alignment-warnings.json`，尤其是短句边界被估计、识别覆盖不足、某一字幕过短。短中文音频的 ASR 可能把“选”识别成“玄”、简体识别成繁体；脚本统一简繁并保留原稿，只取时间。低置信度时重识别或人工核对音频波形/停顿，修正字幕时间。不要把提示文件当成已经验证过的结论。

不要给 Whisper 加上整段原文作为 initial_prompt；该做法曾在短音频上诱发无关识别。当前脚本使用 `temperature=0, condition_on_previous_text=False`。

## 合成逻辑

1. 每段真实录屏按正常语速口播长度剪辑；音频只 `apad` 补齐短尾音，不先变速。
2. 摄像机对原录屏做两倍分辨率采样，以三次 smoothstep 插值运行 `zoompan`，合入窗口、遮罩、章节和逐句字幕。
3. 合并为 master，统一响度 `loudnorm=I=-16:TP=-1.5:LRA=9`。
4. 整片一次 `setpts=(PTS-STARTPTS)/1.2` + `atempo=1.2`。最终 H.264、AAC、48kHz、30fps，`+faststart`。

`verification.json` 检查正常版/交付版时长比例；视频帧量化和 AAC 尾部会带来少量差异。字幕已烧录在视频里，会和画面一起加速。不要再在播放器里叠加 1.2 倍。

## 交付前核对

检查缩放到最大时字段标签、报告首尾和姓名遮罩；检查生成结果是否真的出现；检查编辑器是否因自动 scrollIntoView 只留下正文下半段。抽看最长字幕、联系信起草与复制、最后 slogan。确认原稿与字幕逐段完全相等，实际音频没有漏词、错读或异常生成。若拿不到可试听通道，明确区分 ASR 内容核验与人工听感检查，不声称已经听过。

需要改字幕或文案时，先改源 JSON，再重跑相应脚本。背景与字幕 PNG 不使用图像生成服务。影片无需重新录制时复用已有录屏，避免重复创建线上数据。
