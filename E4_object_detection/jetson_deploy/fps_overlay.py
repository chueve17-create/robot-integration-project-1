"""
FPS 计算与叠加显示模块
用滑动窗口平均帧间隔来计算实时FPS，并叠加到画面右上角
"""
import cv2
import time
from collections import deque


class FPSCounter:
    def __init__(self, window_size=10):
        """
        window_size: 用最近N帧的时间间隔算平均FPS，而不是单帧瞬时值，
        避免因为单帧偶然卡顿导致FPS数字剧烈跳动，显示更稳定
        """
        self.timestamps = deque(maxlen=window_size)

    def tick(self):
        """
        每处理完一帧调用一次，记录当前时间戳并返回最新平均FPS
        """
        now = time.time()
        self.timestamps.append(now)

        if len(self.timestamps) < 2:
            return 0.0

        # 用队列里最早和最新时间戳之间的跨度，除以帧数，得到平均FPS
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed <= 0:
            return 0.0
        fps = (len(self.timestamps) - 1) / elapsed
        return fps


def draw_fps(frame, fps):
    """
    把FPS数字画在画面右上角
    frame: OpenCV图像 (numpy数组, BGR)
    fps: 当前帧率数值
    """
    h, w = frame.shape[:2]
    text = f"FPS: {fps:.1f}"

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2

    # 先算出文字尺寸，才能精确算出右上角的摆放位置
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    margin = 15
    x = w - text_w - margin
    y = margin + text_h

    # 文字底部加一个半透明深色底框，避免背景太亮时文字看不清
    overlay = frame.copy()
    cv2.rectangle(
        overlay,
        (x - 8, y - text_h - 8),
        (x + text_w + 8, y + baseline + 8),
        (0, 0, 0),
        -1
    )
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # 文字用绿色，在深色底框上比较清晰醒目
    cv2.putText(frame, text, (x, y), font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)

    return frame


if __name__ == "__main__":
    # 独立测试：用摄像头验证FPS计算和叠加效果
    cap = cv2.VideoCapture(0)
    fps_counter = FPSCounter(window_size=10)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            fps = fps_counter.tick()
            frame = draw_fps(frame, fps)

            cv2.imshow("FPS Overlay Test", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
