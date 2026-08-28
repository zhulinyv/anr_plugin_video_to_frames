import os
import re
import subprocess

import cv2
from moviepy import AudioFileClip, VideoFileClip

from utils import download, extract
from utils.logger import logger


def extract_frames(video_path: str, output_dir: str) -> None:
    logger.info("开始拆分...")
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("无法打开视频文件")
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_filename = os.path.join(output_dir, f"frame_{frame_count:04d}.png")
        cv2.imwrite(frame_filename, frame)
        frame_count += 1

    cap.release()

    logger.success(f"成功提取 {frame_count} 帧，保存至: {output_dir}")
    return f"成功提取 {frame_count} 帧，保存至: {output_dir}"


def frames_to_video(images_folder: str, output_dir: str, fps: int = 24, output_filename: str = 'frames_to_video.mp4') -> str:
    logger.info("正在合并帧序列为视频...")
    if not os.path.isdir(images_folder):
        logger.error(f"图片文件夹不存在: {images_folder}")
        return

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    valid_ext = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(valid_ext)]
    if not image_files:
        logger.error(f"文件夹中没有支持的图片文件: {images_folder}")
        return

    image_files.sort(key=natural_sort_key)
    logger.info(f"找到 {len(image_files)} 张图片，将按顺序合成视频...")

    first_img_path = os.path.join(images_folder, image_files[0])
    frame = cv2.imread(first_img_path)
    if frame is None:
        logger.error(f"无法读取图片: {first_img_path}")
        return
    height, width, _ = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 使用 mp4v 编码，输出 .mp4
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for img_file in image_files:
        img_path = os.path.join(images_folder, img_file)
        frame = cv2.imread(img_path)
        if frame is None:
            logger.warning(f"警告：跳过无法读取的图片 {img_file}")
            continue
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
        video_writer.write(frame)

    video_writer.release()
    logger.success(f"视频已生成: {output_path}")
    return f"视频已生成: {output_path}"


def video2audio(video_path, save_path):
    clip = VideoFileClip(video_path)
    audio = clip.audio
    audio.write_audiofile(os.path.join(save_path, "extract_audio.mp3"), logger=None)
    try:
        clip.close()
        audio.close()
    except Exception:
        pass
    return


def audio2video(video_path, audio_path, save_path):
    logger.info("正在合并音频到视频...")
    audio_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
    if audio_path.lower().endswith(audio_extensions):
        logger.info("正在提取音频...")
        clip = VideoFileClip(audio_path)
        ad = clip.audio
    else:
        ad = AudioFileClip(audio_path)
    vd = VideoFileClip(video_path)
    vd2 = vd.with_audio(ad)
    output_path = os.path.join(save_path, "merge_audio_to_video.mp4")
    vd2.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-crf", "15"],  # 设置较高的质量 (数字越小越清晰)
        preset="medium",
        logger=None
    )
    try:
        clip.close()
        ad.close()
        vd.close()
        vd2.close()
    except Exception:
        pass
    logger.success(f"视频已生成: {output_path}")
    return f"视频已生成: {output_path}"


def run_cmd(code):
    try:
        p = subprocess.Popen(code, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        result = (stdout or stderr).decode("gb18030", errors="ignore").strip()
        return result
    except Exception as e:
        logger.error(f"出现错误! {e}")
        return


def rife(frames_path, output_path, x, z, u, model):
    logger.info("开始补帧...")
    if not os.path.exists("./assets/rife-ncnn-vulkan"):
        logger.debug("正在下载 rife-ncnn-vulkan 超分引擎")
        download(
            "https://huggingface.co/datasets/Xytpz/ANR_Upscale_Engine/resolve/main/rife-ncnn-vulkan.zip?download=true",
            "./outputs/temp.zip",
        )
        logger.debug("正在解压 rife-ncnn-vulkan 到 ./assets/rife-ncnn-vulkan")
        extract("./outputs/temp.zip", "./assets/rife-ncnn-vulkan")

    code = f'.\\assets\\rife-ncnn-vulkan\\rife-ncnn-vulkan.exe -i "{os.path.abspath(frames_path)}" -o "{os.path.abspath(output_path)}" -m {model}'

    if x:
        code += " -x"
    if z:
        code += " -z"
    if u:
        code += " -u"

    logger.debug(code)

    result = run_cmd(code)
    logger.info(f"输出: {result}")
    logger.info(f"处理完成: {output_path}")
    return f"处理完成: {output_path}"
