#!/usr/bin/env python3
"""
自动预标注脚本
用训练好的种子辅助模型，对剩余未标注图片批量生成候选标注框（YOLO格式txt）
同时保存画好框的预览图，方便人工快速审核

用法：
    python3 auto_prelabel.py
"""

import os
from pathlib import Path
from ultralytics import YOLO

# ====== 配置区（按需修改）======
BASE_DIR = Path.home() / "robot-integration-project-1" / "E4_object_detection"
MODEL_PATH = BASE_DIR / "DataSet" / "runs" / "detect" / "runs" / "final_model" / "weights" / "best.pt"
SAMPLED_FRAMES_DIR = BASE_DIR / "sampled_frames"
OUTPUT_LABELS_DIR = BASE_DIR / "pre_labels"          # 存放预测的YOLO格式txt标注
OUTPUT_PREVIEW_DIR = BASE_DIR / "pre_labels_preview" # 存放画好框的预览图，方便肉眼快速检查

CATEGORIES = ["comb", "mouse"]
CONF_THRESHOLD = 0.2  # 置信度阈值，种子模型数据少，适当调低避免漏检太多
# ================================


def main():
    if not MODEL_PATH.exists():
        print(f"错误：找不到模型权重文件 {MODEL_PATH}")
        print("请确认种子模型已经训练完成，且路径正确")
        return

    print(f"加载模型: {MODEL_PATH}")
    model = YOLO(str(MODEL_PATH))

    OUTPUT_LABELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    total_processed = 0
    total_with_detections = 0
    total_no_detections = 0

    for category in CATEGORIES:
        input_dir = SAMPLED_FRAMES_DIR / category
        if not input_dir.exists():
            print(f"跳过 {category}（源文件夹不存在: {input_dir}）")
            continue

        label_out_dir = OUTPUT_LABELS_DIR / category
        preview_out_dir = OUTPUT_PREVIEW_DIR / category
        label_out_dir.mkdir(parents=True, exist_ok=True)
        preview_out_dir.mkdir(parents=True, exist_ok=True)

        image_files = sorted(list(input_dir.glob("new_*.jpg")) + list(input_dir.glob("new_*.jpeg")) + list(input_dir.glob("new_*.png")))

        if not image_files:
            print(f"{category}: 没有找到图片，跳过")
            continue

        print(f"\n===== 处理 {category} 类别（共 {len(image_files)} 张）=====")

        for img_path in image_files:
            results = model.predict(
                source=str(img_path),
                conf=CONF_THRESHOLD,
                verbose=False,
                save=False,
            )

            result = results[0]
            num_boxes = len(result.boxes)

            # 写YOLO格式标注文件（即使没检测到目标，也生成空文件，方便后续统一处理）
            label_path = label_out_dir / f"{img_path.stem}.txt"
            with open(label_path, "w") as f:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    x_center, y_center, w, h = box.xywhn[0].tolist()
                    f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")

            # 保存画好框的预览图，方便人工快速扫一眼判断质量
            preview_path = preview_out_dir / img_path.name
            annotated_img = result.plot()
            import cv2
            cv2.imwrite(str(preview_path), annotated_img)

            total_processed += 1
            if num_boxes > 0:
                total_with_detections += 1
            else:
                total_no_detections += 1

        print(f"  {category} 处理完成")

    print("\n===== 全部完成 =====")
    print(f"总计处理图片: {total_processed}")
    print(f"检测到目标的图片: {total_with_detections}")
    print(f"未检测到目标的图片: {total_no_detections}")
    print(f"\n标注文件保存在: {OUTPUT_LABELS_DIR}")
    print(f"预览图保存在: {OUTPUT_PREVIEW_DIR}")
    print("\n下一步：请打开预览图逐张检查，标注质量不佳的图片需要在标注工具中手动修正")


if __name__ == "__main__":
    main()
