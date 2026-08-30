"""视频处理插件: 拆分 / 合并 / 音频合成 / 补帧。"""
from __future__ import annotations

from plugins.anr_plugin_video_to_frames.utils import audio2video, extract_frames, frames_to_video, rife
from utils.plugins import Action, Field, Panel, Plugin


def register(plugin: Plugin):
    plugin.title = "视频处理"
    plugin.description = "视频拆帧、合并、音频合成与 AI 补帧"
    plugin.icon = "🎬"

    # 视频拆分
    extract_panel = Panel(
        id="extract",
        title="视频拆分",
        icon="✂️",
        fields=[
            Field(id="video", label="视频文件", type="filearea", accept=".mp4, .avi, .mov, .mkv, .webm"),
            Field(id="save_path", label="保存目录", type="path", folder=True, file=False),
        ],
        actions=[
            Action(id="run", label="✂️ 拆分", inputs=["video", "save_path"], uses_novelai=False, handler=lambda v: {"text": extract_frames(v.get("video", ""), v.get("save_path", ""))}),
        ],
    )

    # 视频合并
    merge_panel = Panel(
        id="merge",
        title="视频合并",
        icon="🔗",
        fields=[
            Field(id="frames_path", label="帧目录", type="path", folder=True, file=False),
            Field(id="fps", label="FPS", type="slider", min=1, max=144, step=1, default=24),
            Field(id="save_path", label="保存目录", type="path", folder=True, file=False),
        ],
        actions=[
            Action(id="run", label="🔗 合并", inputs=["frames_path", "save_path", "fps"], uses_novelai=False, handler=lambda v: {"text": frames_to_video(v.get("frames_path", ""), v.get("save_path", ""), int(v.get("fps", 24)))}),
        ],
    )

    # 音频合并
    audio_panel = Panel(
        id="audio",
        title="音频合并",
        icon="🎵",
        fields=[
            Field(id="video", label="视频文件", type="filearea", accept=".mp4, .avi, .mov, .mkv, .webm"),
            Field(id="audio", label="音频/视频文件", type="filearea", accept=".mp3, .wav, .aac, .flac, .ogg, .mp4, .avi, .mov, .mkv"),
            Field(id="save_path", label="保存目录", type="path", folder=True, file=False),
        ],
        actions=[
            Action(id="run", label="🎵 合并", inputs=["video", "audio", "save_path"], uses_novelai=False, handler=lambda v: {"text": audio2video(v.get("video", ""), v.get("audio", ""), v.get("save_path", ""))}),
        ],
    )

    # 补帧
    rife_panel = Panel(
        id="rife",
        title="补帧",
        icon="⚡",
        fields=[
            Field(id="video", label="帧目录", type="path", folder=True, file=False),
            Field(id="save_path", label="保存目录", type="path", folder=True, file=False),
            Field(id="spatial_tta", label="enable spatial tta mode", type="checkbox", default=False),
            Field(id="temporal_tta", label="enable temporal tta mode", type="checkbox", default=False),
            Field(id="uhd", label="enable UHD mode", type="checkbox", default=False),
            Field(id="model", label="插帧模型", type="select", options=["rife","rife-anime","rife-HD","rife-UHD","rife-v2","rife-v2.3","rife-v2.4","rife-v3.0","rife-v3.1","rife-v4","rife-v4.6"], default="rife-v2.3"),
        ],
        actions=[
            Action(
                id="run",
                label="⚡ 补帧",
                uses_novelai=False,  # 本地 RIFE 补帧
                inputs=["video", "save_path", "spatial_tta", "temporal_tta", "uhd", "model"],
                handler=lambda v: {"text": rife(v.get("video", ""), v.get("save_path", ""), v.get("spatial_tta", False), v.get("temporal_tta", False), v.get("uhd", False), v.get("model", "rife-v2.3"))},
            ),
        ],
    )

    plugin.panels.extend([extract_panel, merge_panel, audio_panel, rife_panel])