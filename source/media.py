import cv2
import ffmpeg
import os
import glob

class Media:
    def __init__(self, config):
        self.config = config
        self.cap = None
        self.process = None
        self.fps = int(config.fps)
        self.width = int(config.width)
        self.height = int(config.height)
        self.output_path = config.output_path
        self.cleanup_hls_folder()
    
    # 세팅 값으로 카메라 열기
    def open_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
        self.cap.set(cv2.CAP_PROP_FPS, float(self.fps))
        if not self.cap.isOpened():
            raise RuntimeError("카메라 열기 실패")
        
    # 진혁이 테스트 비디오
    def open_video(self, video_path):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f"비디오 열기 실패: {video_path}")
        
    # 프레임 읽어와서 return
    def read_frame(self):
        if self.cap is None:
            raise RuntimeError("먼저 open_camera()를 호출하세요.")
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    # ffmpeg 서비스 키기 (비동기, 대기  상태)
    def start_streaming(self):
        stream = ffmpeg.input(
            'pipe:0',format='rawvideo',pix_fmt='bgr24',s=f'{self.width}x{self.height}', r=self.fps
            ).output(
                self.output_path,
                format='hls',
                vcodec='libx264',
                pix_fmt='yuv420p',
                preset='ultrafast',
                tune='zerolatency',
                r=2,  # frame rate
                x264opts=f'keyint={self.fps}:min-keyint={self.fps}:scenecut=0',
                an=None,
                hls_time=1,
                hls_list_size=5,
                hls_flags='delete_segments'
            ).global_args('-loglevel', 'error', '-nostats')
        self.process = ffmpeg.run_async(stream, pipe_stdin=True)

    # 대기 중인 ffmpeg에 쓰기
    def send_frame_to_ffmpeg(self, frame):
        if self.process and self.process.stdin:
            self.process.stdin.write(frame.tobytes())


# 정리 함수들 @@
    def stop_streaming(self):
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
            except Exception:
                self.process.wait()
                self.process = None
                            
    def release_camera(self):
        if self.cap:
            self.cap.release()

    def cleanup_hls_folder(self):
        if not os.path.exists("hls"):
            os.makedirs(self.output_path, exist_ok=True)
            return
        ts_files = glob.glob(os.path.join("hls", "*.ts"))
        
        m3u8_files = glob.glob(os.path.join("hls", "*.m3u8"))
        for f in ts_files + m3u8_files:
            try:
                os.remove(f)
            except Exception as e:
                print("[media.py] /hls 내부 파일 제거하다 에러남. media.py 살펴보세요.")
        print("[media.py] /hls 폴더 정리 완료")
