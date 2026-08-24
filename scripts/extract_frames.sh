#!/bin/bash
# 批量视频抽帧脚本
# 用法：在 raw_videos 同级目录下运行，或者修改下面的 BASE_DIR

set -e  # 出错就停止

# ====== 配置区（按需修改）======
BASE_DIR="$HOME/robot-integration-project-1/E4_object_detection"
RAW_VIDEOS_DIR="$BASE_DIR/raw_videos"
FRAMES_DIR="$BASE_DIR/extracted_frames"
FPS=3  # 抽帧频率，每秒3张
# ================================

echo "开始批量抽帧..."
echo "视频目录: $RAW_VIDEOS_DIR"
echo "输出目录: $FRAMES_DIR"
echo "抽帧频率: ${FPS} FPS"
echo ""

# 遍历4个类别文件夹
for category in comb mouse together negative; do
    input_dir="$RAW_VIDEOS_DIR/$category"
    output_dir="$FRAMES_DIR/$category"

    if [ ! -d "$input_dir" ]; then
        echo "跳过 $category（文件夹不存在）"
        continue
    fi

    mkdir -p "$output_dir"

    echo "===== 处理 $category 类别 ====="

    # 遍历该文件夹下所有mp4视频
    for video in "$input_dir"/*.mp4; do
        if [ ! -f "$video" ]; then
            continue
        fi

        # 获取不带扩展名的文件名，例如 comb-v1
        filename=$(basename "$video" .mp4)

        echo "  正在抽帧: $filename"

        # 抽帧，输出文件名格式：comb-v1_0001.jpg, comb-v1_0002.jpg ...
        ffmpeg -i "$video" -vf "fps=${FPS}" -q:v 2 \
            "$output_dir/${filename}_%04d.jpg" \
            -loglevel error -y

        # 统计这段视频抽出了多少张
        count=$(ls "$output_dir/${filename}"_*.jpg 2>/dev/null | wc -l)
        echo "    -> 抽出 $count 张图片"
    done

    total=$(ls "$output_dir"/*.jpg 2>/dev/null | wc -l)
    echo "  $category 类别总计: $total 张图片"
    echo ""
done

echo "===== 全部完成 ====="
echo ""
echo "各类别图片统计："
for category in comb mouse together negative; do
    output_dir="$FRAMES_DIR/$category"
    if [ -d "$output_dir" ]; then
        count=$(ls "$output_dir"/*.jpg 2>/dev/null | wc -l)
        echo "  $category: $count 张"
    fi
done
