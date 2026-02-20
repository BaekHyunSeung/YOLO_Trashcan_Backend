from inference import Inference
from config import Config
from media import Media
from sender import Sender
from log import LoopProfiler
import json


def main():
    print("[main.py] 설정 로딩 중..")
    config = Config()   # 설정 클래스
    inference = Inference(config)   # 모델 이용 클래스
    inference.setup_npu()   
    media = Media(config)   # 이미지 관련 클래스
    sender = Sender(config) # 서버 전송 클래스
    log = LoopProfiler(config)  # 로그 클래스

    if config.is_test:
        media.open_video(config.video_file_path)
        print("[main.py] 테스트 비디오 시작")
    else:
        media.open_camera()
        print("[main.py] 스트리밍 시작")

    # 비동기 ffmepg 
    media.start_streaming()

    frame_id = 0
    try:
        while True:
            log.start_frame()

            # 프레임 읽기
            with log.measure("Read"):
                frame = media.read_frame()
            if frame is None: break
            
            # YOLO 추론
            with log.measure("Infer"):
                detections = inference.infer(frame)
            # 이벤트 발생시 서버 전송
            # config.is_send and sender.process_frame(frame, detections)
            # [ADD] device_id, frame_id
            config.is_send and sender.process_frame(frame, detections, 
                        config.device_id, frame_id)

            # 바운딩 박스
            with log.measure("Draw"):
                frame = inference.draw_boxes(frame, detections)

            # 프레임 HLS 전송
            with log.measure("Send"):
                media.send_frame_to_ffmpeg(frame)

            log.end_frame()
            frame_id = frame_id + 1

    except KeyboardInterrupt:
        print("\n키보드 강제 종료 요청")

    finally:
        media.release_camera()
        media.stop_streaming()
        inference.cleanup()
        print("자원 정리 완료")

if __name__ == "__main__":
    main()
