# Product Demo Video Skill

自动制作带关键区域缩放、中文配音和同步字幕的真实产品演示视频。

## 效果与默认配置

- macOS 风格窗口、鼠标点击提示、关键区域平滑放大缩小。
- Qwen3-TTS 1.7B CustomVoice，MLX 8-bit，Serena 中文音色。
- 配音原文逐句同步，大号白字黑色描边字幕。
- 横屏 1920×1080 / 竖屏 1080×1920；完整成片一次性加速至 1.2 倍。
- 支持按需匿名、真实生成过程剪辑、可复用录屏素材和文案缓存失效。

## 安装到 Codex

将本仓库放入本地技能目录：

```sh
git clone https://github.com/amourlion/product-demo-video.git ~/.codex/skills/product-demo-video
```

如该目录已有此技能，先确认本地修改，再更新对应文件。

调用示例：

> 使用 $product-demo-video，为这个产品制作带关键区域缩放、中文配音和同步字幕的演示视频。

## 使用与依赖

默认语音运行时面向 Apple Silicon macOS。需要 Python 3.12、Node、Playwright/Chromium、FFmpeg/FFprobe 与中文字体；模型首次使用时下载。

- [技能入口](SKILL.md)：默认风格、执行步骤和交付要求。
- [运行说明](references/workflow.md)：已验证依赖、文件格式及脚本命令。
- [录屏与摄像机](references/capture-and-camera.md)：镜头关键帧、时间校准、横竖版式和匿名处理。

项目适配器负责真实产品的登录、选择器和操作。仓库只包含技能、脚本与配置模板，不包含账号、模型权重或产品录屏。

## 脚本

| 文件 | 用途 |
| --- | --- |
| `assets/record-template.cjs` | 真实浏览器录屏及鼠标操作模板 |
| `scripts/voice.py` | 中文配音，按文案与配置管理缓存 |
| `scripts/align.py` | 语音时间对齐，保留原文字幕 |
| `scripts/frames.cjs` | 窗口、字幕与遮罩渲染 |
| `scripts/compose.py` | 平滑缩放、合成和整片加速导出 |

已在本地完成录屏点击、配音缓存变更、横竖屏合成及倍速导出的试跑。
