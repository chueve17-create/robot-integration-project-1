"""
ROS2 目标检测节点
订阅相机图像话题(sensor_msgs/Image)，用训练好的YOLOv8模型逐帧推理，
右上角叠加实时FPS，并将检测结果以 vision_msgs/Detection2DArray 发布
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import time
from fps_overlay import FPSCounter, draw_fps
from result_publisher import build_detection_array

# 类别id到名称的映射，需要和 data.yaml 里的 names 顺序保持一致
CLASS_NAMES = {0: "comb", 1: "mouse"}

# 模型路径：训练好的best.pt，Jetson部署时换成设备上的实际路径
MODEL_PATH = "best.pt"
# 相机驱动发布的图像话题名，需要和实际摄像头驱动节点核对一致
IMAGE_TOPIC = "/camera/image_raw"
# 置信度阈值：过滤低置信度误检(参考E4测试阶段发现的键盘误检问题)
CONF_THRESHOLD = 0.5
# 目标处理帧率：不管摄像头驱动实际发布多快，节点内部主动限速，稳定在这个值附近
TARGET_FPS = 5
MIN_FRAME_INTERVAL = 1.0 / TARGET_FPS


class DetectionNode(Node):
    def __init__(self):
        super().__init__('yolo_detection_node')

        # 加载模型，只在节点启动时加载一次，避免每帧重复加载拖慢速度
        self.get_logger().info(f"正在加载模型: {MODEL_PATH}")
        self.model = YOLO(MODEL_PATH)
        self.get_logger().info("模型加载完成")

        # cv_bridge 用于 ROS Image消息 <-> OpenCV图像(numpy数组) 的相互转换
        self.bridge = CvBridge()

        # FPS计数器，window_size=10表示用最近10帧算平均帧率，避免数字跳动
        self.fps_counter = FPSCounter(window_size=10)

        # 记录上一次实际处理(推理)的时间戳，用于主动限速判断
        self.last_process_time = 0.0

        # 订阅相机图像话题，每收到一帧就触发 image_callback
        self.subscription = self.create_subscription(
            Image,
            IMAGE_TOPIC,
            self.image_callback,
            10  # QoS队列深度
        )
        self.get_logger().info(f"已订阅话题: {IMAGE_TOPIC}")

        # 发布检测结果，供下游节点(如机械臂抓取逻辑)订阅
        self.detection_pub = self.create_publisher(
            Detection2DArray,
            '/detections',
            10
        )

    def image_callback(self, msg: Image):
        """
        每收到一帧图像执行一次：
        0. 主动限速：距上次处理不足1/TARGET_FPS秒，直接丢弃这一帧
        1. ROS Image消息 -> OpenCV图像
        2. YOLO推理
        3. FPS计算与右上角叠加
        4. 发布检测结果(Detection2DArray)
        """
        # 主动限速：不管摄像头驱动实际发布多快(比如30fps)，这里强制把真正做推理的频率卡在 TARGET_FPS 左右，多余的帧直接丢弃不处理
        now = time.time()
        if now - self.last_process_time < MIN_FRAME_INTERVAL:
            return
        self.last_process_time = now

        try:
            # ROS图像消息通常是bgr8编码，转成OpenCV常用的BGR格式
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"图像转换失败: {e}")
            return

        # YOLO推理，verbose=False避免每帧刷屏打印
        results = self.model(frame, conf=CONF_THRESHOLD, verbose=False)

        # results[0] 包含这一帧的所有检测框(boxes)、类别、置信度
        detections = results[0]

        # 画出检测框
        annotated_frame = detections.plot()

        # 计算当前FPS并叠加到画面右上角
        fps = self.fps_counter.tick()
        annotated_frame = draw_fps(annotated_frame, fps)

        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(1)

        # 把检测结果转换成Detection2DArray并发布，header沿用原始图像消息的时间戳和frame_id
        # 保证下游节点能把检测框和正确的坐标系/时刻对应起来
        detection_array = build_detection_array(detections, CLASS_NAMES, msg.header)
        self.detection_pub.publish(detection_array)


def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
