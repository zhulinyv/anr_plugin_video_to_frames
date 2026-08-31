# 🎬 视频处理插件 (anr_plugin_video_to_frames)

[Auto-NovelAI-Refactor](https://github.com/zhulinyv/Auto-NovelAI-Refactor) 的视频处理插件, 提供视频拆帧、帧序列合并、音频合成与 AI 补帧 (RIFE) 功能, 可配合自动打码、超分降噪等功能使用。

## ✨ 功能特性

- ✂️ **视频拆分**: 将视频逐帧提取为 PNG 图片序列
- 🔗 **视频合并**: 将图片帧序列按自然排序合成视频, 可设置 FPS (1 ~ 144)
- 🎵 **音频合成**: 为视频替换 / 合并音轨 (支持从视频中提取音频或直接使用音频文件)
- ⚡ **AI 补帧**: 基于 RIFE 的本地插帧, 支持多种模型与 TTA / UHD 模式
- 🎞️ **格式广泛**: 支持 mp4 / avi / mov / mkv / webm 等常见视频格式

## 📦 依赖

- moviepy
- opencv-python (cv2)

## 🚀 使用方法

在 [Auto-NovelAI-Refactor](https://github.com/zhulinyv/Auto-NovelAI-Refactor) 的插件商店中安装本插件, 打开「视频处理」面板:

### ✂️ 视频拆分

1. 选择「视频文件」, 填写「保存目录」
2. 点击 **拆分**, 逐帧保存为 `frame_0000.png` 格式

### 🔗 视频合并

1. 选择「帧目录」, 设置 FPS, 填写「保存目录」
2. 点击 **合并**, 输出为 `frames_to_video.mp4`

### 🎵 音频合并

1. 选择「视频文件」与「音频/视频文件」(mp3 / wav / aac / flac / ogg 等, 或直接传视频自动提取音轨)
2. 填写「保存目录」, 点击 **合并**, 输出为 `merge_audio_to_video.mp4`

### ⚡ 补帧

1. 选择「帧目录」, 填写「保存目录」
2. 按需开启 spatial tta / temporal tta / UHD 模式, 选择插帧模型
3. 点击 **补帧**, 首次使用会自动下载 rife-ncnn-vulkan 引擎

## 🧠 RIFE 模型说明

| 模型 | 说明 |
| --- | --- |
| rife / rife-anime | 通用 / 动画优化 |
| rife-HD / rife-UHD | 高清 / 超高清优化 |
| rife-v2 ~ rife-v4.6 | 各版本迭代模型, 默认 rife-v2.3 |
