

import gradio as gr

from plugins.anr_plugin_video_to_frames.utils import audio2video, extract_frames, frames_to_video, rife


def plugin():
    with gr.Tab("视频处理"):
        output_info = gr.Markdown("", show_label=False)
        with gr.Tab("视频拆分"):
            video = gr.File(label="视频")
            extract_save_path = gr.Textbox(label="保存目录")
            extract_button = gr.Button("拆分")
            extract_button.click(extract_frames, [video, extract_save_path], output_info)
        with gr.Tab("视频合并"):
            frames_path = gr.Textbox(label="帧目录")
            fps = gr.Slider(1, 144, 24, step=1, label="FPS")
            merge_save_path = gr.Textbox(label="保存目录")
            merge_button = gr.Button("合并")
            merge_button.click(frames_to_video, [frames_path, merge_save_path, fps], output_info)
        with gr.Tab("音频合并"):
            with_video = gr.File(label="视频")
            with_audio = gr.File(label="音频/视频")
            with_save_path = gr.Textbox(label="保存目录")
            with_button = gr.Button("合并")
            with_button.click(audio2video, [with_video, with_audio, with_save_path], output_info)
        with gr.Tab("补帧"):
            rife_video = gr.Textbox(label="帧目录")
            rife_extract_save_path = gr.Textbox(label="保存目录")
            with gr.Row():
                spatial_tta_mode = gr.Checkbox(label="enable spatial tta mode")
                temporal_tta_mode = gr.Checkbox(label="enable temporal tta mode")
                UHD_mode = gr.Checkbox(label="enable UHD mode")
            model = gr.Dropdown(['rife', 'rife-anime', 'rife-HD', 'rife-UHD', 'rife-v2', 'rife-v2.3', 'rife-v2.4', 'rife-v3.0', 'rife-v3.1', 'rife-v4', 'rife-v4.6'], value='rife-v2.3', label="插帧模型")
            rife_button = gr.Button("补帧")

            rife_button.click(rife, [rife_video, rife_extract_save_path, spatial_tta_mode, temporal_tta_mode, UHD_mode, model], outputs=output_info)
