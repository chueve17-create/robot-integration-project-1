"""
检测结果发布模块
将YOLO推理结果转换为标准ROS2消息 vision_msgs/Detection2DArray 并发布，
供下游节点(如机械臂抓取逻辑)订阅使用
"""
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from geometry_msgs.msg import Pose


def build_detection_array(yolo_result, class_names, header):
    """
    把YOLO单帧推理结果(yolo_result)转换成 Detection2DArray 消息

    yolo_result: ultralytics推理返回的results[0]，包含 .boxes (xyxy坐标、置信度、类别id)
    class_names: 类别id到名称的映射，如 {0: 'comb', 1: 'mouse'}
    header: std_msgs/Header，需要和原始图像消息保持相同的时间戳和frame_id，
            这样下游节点才能把检测框和正确的坐标系/时刻对应起来
    """
    detection_array = Detection2DArray()
    detection_array.header = header

    boxes = yolo_result.boxes
    if boxes is None or len(boxes) == 0:
        return detection_array  # 这一帧没有检测到目标，返回空数组

    for box in boxes:
        detection = Detection2D()
        detection.header = header

        # YOLO给出的是xyxy(左上角+右下角)坐标，Detection2D用的是中心点+宽高格式，需要换算
        xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        w = x2 - x1
        h = y2 - y1

        detection.bbox.center.position.x = cx
        detection.bbox.center.position.y = cy
        detection.bbox.size_x = w
        detection.bbox.size_y = h

        # 类别和置信度
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        hypothesis = ObjectHypothesisWithPose()
        hypothesis.hypothesis.class_id = class_names.get(class_id, str(class_id))
        hypothesis.hypothesis.score = confidence
        detection.results.append(hypothesis)

        detection_array.detections.append(detection)

    return detection_array
