import os
import re
import subprocess

from utils import download, extract
from utils.logger import logger
from utils.paths import job_temp_path

# cv2 / moviepy 的 import 各要 0.1~0.7 秒, 原来写在模块顶层 → 每次启动都为"这次没用到视频"
# 的场合付钱。改成在真正用到的函数里 import (模块属性按名字取, 调用点写法不变)。


def _cv2():
    import cv2

    return cv2


def _moviepy():
    from moviepy import AudioFileClip, VideoFileClip

    return AudioFileClip, VideoFileClip


def warmup() -> None:
    """后台预热: 启动时提前把 cv2 / moviepy 加载好 (由 utils.plugins 在后台线程调用)。"""
    _cv2()
    _moviepy()


def extract_frames(video_path: str, output_dir: str) -> str:
    """把视频逐帧导出为 PNG, 返回给前端展示的一行结果文本。

    返回值恒为 str: 失败时返回可读的错误说明, 而不是 None。
    (原标注是 None 且失败分支直接 return, 前端 {"text": ...} 会拿到 null 并显示成空。)
    """
    cv2 = _cv2()
    logger.info("开始拆分...")
    if not video_path:
        return "❌ 请先选择视频文件"
    if not os.path.isfile(video_path):
        return f"❌ 视频文件不存在: {video_path}"
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("无法打开视频文件")
        return f"❌ 无法打开视频文件: {os.path.basename(video_path)}"

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
    cv2 = _cv2()
    logger.info("正在合并帧序列为视频...")
    # 与 extract_frames 一致: 失败也返回可读文本, 不返回 None (前端 {"text": ...} 会显示成空)
    if not images_folder:
        return "❌ 请先选择帧目录"
    if not os.path.isdir(images_folder):
        logger.error(f"图片文件夹不存在: {images_folder}")
        return f"❌ 图片文件夹不存在: {images_folder}"

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    valid_ext = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(images_folder) if f.lower().endswith(valid_ext)]
    if not image_files:
        logger.error(f"文件夹中没有支持的图片文件: {images_folder}")
        return f"❌ 文件夹中没有支持的图片: {images_folder}"

    image_files.sort(key=natural_sort_key)
    logger.info(f"找到 {len(image_files)} 张图片，将按顺序合成视频...")

    first_img_path = os.path.join(images_folder, image_files[0])
    frame = cv2.imread(first_img_path)
    if frame is None:
        logger.error(f"无法读取图片: {first_img_path}")
        return f"❌ 无法读取图片: {image_files[0]}"
    height, width = frame.shape[:2]  # 灰度帧是 2 维, 解包成 3 个会 ValueError

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
    _, VideoFileClip = _moviepy()
    if not video_path or not os.path.isfile(video_path):
        return f"❌ 视频文件不存在: {video_path}"
    os.makedirs(save_path, exist_ok=True)
    clip = VideoFileClip(video_path)
    audio = clip.audio
    if audio is None:
        clip.close()
        return f"❌ 该视频没有音轨: {os.path.basename(video_path)}"
    out = os.path.join(save_path, "extract_audio.mp3")
    audio.write_audiofile(out, logger=None)
    try:
        clip.close()
        audio.close()
    except Exception:
        pass
    logger.success(f"音频已提取: {out}")
    return f"音频已提取: {out}"


def audio2video(video_path, audio_path, save_path):
    AudioFileClip, VideoFileClip = _moviepy()
    logger.info("正在合并音频到视频...")
    # 与其它动作一致: 前置条件不满足时返回可读文本 (前端 {"text": ...} 不会显示成空)
    if not video_path or not os.path.isfile(video_path):
        return f"❌ 视频文件不存在: {video_path}"
    if not audio_path or not os.path.isfile(audio_path):
        return f"❌ 音频文件不存在: {audio_path}"
    os.makedirs(save_path, exist_ok=True)
    audio_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')
    # clip 只在"音频本身是视频"分支才会绑定; 原先未初始化, 非视频音频时下面的
    # clip.close() 会抛 NameError 并被 except 静默吞掉 (源 clip 也就永远不关)。
    clip = None
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
    # 逐个关闭: 某一个失败不应让后面的对象泄漏
    for _obj in (clip, ad, vd, vd2):
        if _obj is None:
            continue
        try:
            _obj.close()
        except Exception:
            pass
    logger.success(f"视频已生成: {output_path}")
    return f"视频已生成: {output_path}"


def run_cmd(code):
    """执行补帧/超分引擎命令, 返回输出的尾部文本。

    原先用 communicate() 把全部输出缓存在内存里 (高分辨率下可达几十 MB);
    这里重定向到临时文件, 只读回尾部 (真正的错误/统计信息都在末尾)。
    """
    import tempfile

    try:
        with tempfile.TemporaryFile() as buf:
            p = subprocess.Popen(code, stdout=buf, stderr=subprocess.STDOUT)
            p.wait()
            try:
                buf.seek(0, os.SEEK_END)
                size = buf.tell()
                buf.seek(max(0, size - 8192))
            except OSError:
                pass
            raw = buf.read()
        if not raw:
            return None
        return raw.decode("gb18030", errors="ignore").strip()
    except Exception as e:
        logger.error(f"出现错误! {e}")
        logger.opt(exception=True).debug("命令执行异常堆栈:")
        return


def rife(frames_path, output_path, x, z, u, model):
    logger.info("开始补帧...")
    # 前置校验放在下载引擎之前: 路径填错时不该先付十几 MB 的下载成本
    if not frames_path or not os.path.isdir(frames_path):
        return f"❌ 帧目录不存在: {frames_path}"
    if not output_path:
        return "❌ 请先选择输出目录"
    if not os.path.exists("./assets/rife-ncnn-vulkan"):
        logger.debug("正在下载 rife-ncnn-vulkan 超分引擎")
        # 安装包下载一次、解压即弃: 放 data/temp, 不污染 outputs/ (见 utils/paths.py)
        _zip = str(job_temp_path("rife_engine.zip"))
        download(
            "https://huggingface.co/datasets/Xytpz/ANR_Upscale_Engine/resolve/main/rife-ncnn-vulkan.zip?download=true",
            _zip,
        )
        logger.debug("正在解压 rife-ncnn-vulkan 到 ./assets/rife-ncnn-vulkan")
        extract(_zip, "./assets/rife-ncnn-vulkan")

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
    # 引擎不存在 / 退出码非 0 / 没有产出帧: 都按失败上报, 不再谎报"处理完成"
    exe = os.path.join("assets", "rife-ncnn-vulkan", "rife-ncnn-vulkan.exe")
    if not os.path.exists(exe):
        return f"❌ 补帧引擎缺失 (下载或解压失败): {exe}"
    if result is None:
        return "❌ 补帧失败: 引擎没有输出 (详见运行日志)"
    logger.info(f"处理完成: {output_path}")
    return f"处理完成: {output_path}"
