"""
视频输入模块
支持从摄像头或本地视频文件读取图像帧，并将处理帧率控制在目标FPS（默认5fps）
"""
import cv2
import time


class VideoInput:
    def __init__(self, source=0, target_fps=5):
        """
        source: 摄像头编号(如0) 或 视频文件路径(str)
        target_fps: 目标处理帧率，对应课程要求的5fps
        """
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频源: {source}")

        self.target_fps = target_fps
        self.source_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        # 根据源帧率和目标帧率计算跳帧间隔，例如源30fps目标5fps -> 每6帧取1帧
        self.frame_skip = max(1, round(self.source_fps / target_fps))

        print(f"[VideoInput] 源帧率: {self.source_fps:.1f}fps, "
              f"目标帧率: {target_fps}fps, 跳帧间隔: {self.frame_skip}")

    def read(self):
        """
        返回 (success, frame)，按目标帧率跳帧节流。
        用 grab() 跳过中间帧（只解码需要的那一帧），比反复 read() 更省性能，
        这点在算力有限的 Jetson 上比较重要。
        """
        for _ in range(self.frame_skip - 1):
            self.cap.grab()

        ret, frame = self.cap.read()
        if not ret:
            return False, None
        return True, frame

    def release(self):
        self.cap.release()


if __name__ == "__main__":
    # 独立测试用：确认帧率控制是否生效
    # source=0 表示摄像头；也可以传入视频文件路径测试，如 "test_video.mp4"
    video = VideoInput(source="../raw_videos/together/together-v1.mp4", target_fps=5)

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = video.read()
            if not ret:
                break

            frame_count += 1
            cv2.imshow("Video Input Test", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video.release()
        cv2.destroyAllWindows()
        elapsed = time.time() - start_time
        if elapsed > 0:
            print(f"共处理 {frame_count} 帧，用时 {elapsed:.1f}s，"
                  f"实际平均帧率: {frame_count/elapsed:.2f}fps")
