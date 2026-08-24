#!/bin/bash
# 合并comb和mouse两个独立Roboflow项目导出的种子数据
# 关键点：Roboflow分开导出的两个项目，标签文件里的类别索引都是从0开始
#         需要重新映射：comb保持0，mouse从0改成1，避免类别混淆

set -e

BASE_DIR="$HOME/robot-integration-project-1/E4_object_detection"
SEED_LABELS_DIR="$BASE_DIR/seed_labels"
MERGED_DIR="$BASE_DIR/seed_dataset"

# 划分比例：85%进train，15%进val
VAL_RATIO=0.15

echo "开始合并种子数据集..."
echo ""

# 建立目标目录结构
mkdir -p "$MERGED_DIR/images/train"
mkdir -p "$MERGED_DIR/images/val"
mkdir -p "$MERGED_DIR/labels/train"
mkdir -p "$MERGED_DIR/labels/val"

# 处理函数：给定类别文件夹名、新的类别索引
process_category() {
    local category=$1
    local new_class_id=$2

    local img_src="$SEED_LABELS_DIR/$category/train/images"
    local label_src="$SEED_LABELS_DIR/$category/train/labels"

    if [ ! -d "$img_src" ]; then
        echo "警告：找不到 $img_src，跳过 $category"
        return
    fi

    # 获取所有图片文件名（不含扩展名），排序后用于稳定的train/val划分
    local files=($(ls "$img_src" | sed 's/\.[^.]*$//' | sort))
    local total=${#files[@]}
    local val_count=$(awk "BEGIN { printf \"%d\", $total * $VAL_RATIO }")

    echo "===== 处理 $category (新类别id=$new_class_id) ====="
    echo "  总计 $total 张，val将取 $val_count 张"

    local idx=0
    for name in "${files[@]}"; do
        # 找到对应的图片文件（可能是.jpg或.jpeg等）
        img_file=$(ls "$img_src/$name".* 2>/dev/null | head -n 1)
        label_file="$label_src/$name.txt"

        if [ -z "$img_file" ]; then
            echo "  警告：找不到 $name 对应的图片，跳过"
            continue
        fi

        # 决定放train还是val
        if [ "$idx" -lt "$val_count" ]; then
            split="val"
        else
            split="train"
        fi

        # 加上类别前缀避免comb和mouse文件重名冲突
        new_name="${category}_${name}"
        img_ext="${img_file##*.}"

        cp "$img_file" "$MERGED_DIR/images/$split/${new_name}.${img_ext}"

        if [ -f "$label_file" ]; then
            # 重写标签文件，把类别索引替换成new_class_id
            awk -v cid="$new_class_id" '{$1=cid; print}' "$label_file" > "$MERGED_DIR/labels/$split/${new_name}.txt"
        else
            # 没有标签文件说明这张图没有目标（负样本），创建空标注文件
            touch "$MERGED_DIR/labels/$split/${new_name}.txt"
        fi

        idx=$((idx + 1))
    done

    echo "  $category 处理完成"
    echo ""
}

# comb 保持类别索引 0，mouse 改成 1
process_category "comb" 0
process_category "mouse" 1

# 生成合并后的data.yaml
cat > "$MERGED_DIR/data.yaml" << EOF
path: $MERGED_DIR
train: images/train
val: images/val
nc: 2
names: [comb, mouse]
EOF

echo "===== 合并完成 ====="
echo ""
echo "最终统计："
echo "  train images: $(ls "$MERGED_DIR/images/train" | wc -l)"
echo "  train labels: $(ls "$MERGED_DIR/labels/train" | wc -l)"
echo "  val images:   $(ls "$MERGED_DIR/images/val" | wc -l)"
echo "  val labels:   $(ls "$MERGED_DIR/labels/val" | wc -l)"
echo ""
echo "data.yaml 已生成在: $MERGED_DIR/data.yaml"
cat "$MERGED_DIR/data.yaml"
