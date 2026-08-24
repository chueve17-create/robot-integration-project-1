#!/bin/bash
# 数据集精简脚本：从抽帧结果中均匀间隔采样，减少冗余图片
# 均匀间隔采样能保留视频从头到尾的角度变化多样性，而不是简单截取前N张

set -e

BASE_DIR="$HOME/robot-integration-project-1/E4_object_detection"
FRAMES_DIR="$BASE_DIR/extracted_frames"
SAMPLED_DIR="$BASE_DIR/sampled_frames"

# ====== 每个类别的目标数量（按需修改）======
declare -A TARGETS
TARGETS[comb]=180
TARGETS[mouse]=180
TARGETS[together]=120
TARGETS[negative]=40
# ============================================

echo "开始精简采样..."
echo ""

for category in comb mouse together negative; do
    input_dir="$FRAMES_DIR/$category"
    output_dir="$SAMPLED_DIR/$category"

    if [ ! -d "$input_dir" ]; then
        echo "跳过 $category（源文件夹不存在）"
        continue
    fi

    mkdir -p "$output_dir"

    target=${TARGETS[$category]}

    # 获取所有jpg文件，按文件名排序（保证同一视频的帧是连续的）
    files=($(ls "$input_dir"/*.jpg 2>/dev/null | sort))
    total=${#files[@]}

    if [ "$total" -eq 0 ]; then
        echo "$category: 没有找到图片，跳过"
        continue
    fi

    if [ "$total" -le "$target" ]; then
        # 如果现有数量已经小于等于目标，全部保留
        echo "$category: 现有 $total 张，已小于等于目标 $target 张，全部保留"
        cp "${files[@]}" "$output_dir/"
        actual_count=$total
    else
        # 均匀间隔采样：计算步长，按步长选取
        step=$(awk "BEGIN { print $total / $target }")
        echo "$category: 现有 $total 张，目标 $target 张，采样步长约 $step"

        selected_count=0
        idx=0
        pos=0
        while [ "$selected_count" -lt "$target" ] && [ "$idx" -lt "$total" ]; do
            idx=$(awk "BEGIN { printf \"%d\", $pos }")
            if [ "$idx" -ge "$total" ]; then
                break
            fi
            cp "${files[$idx]}" "$output_dir/"
            selected_count=$((selected_count + 1))
            pos=$(awk "BEGIN { print $pos + $step }")
        done
        actual_count=$selected_count
    fi

    echo "  -> $category 精简完成，实际保留 $actual_count 张"
    echo ""
done

echo "===== 精简完成，最终统计 ====="
for category in comb mouse together negative; do
    output_dir="$SAMPLED_DIR/$category"
    if [ -d "$output_dir" ]; then
        count=$(ls "$output_dir"/*.jpg 2>/dev/null | wc -l)
        echo "  $category: $count 张"
    fi
done
