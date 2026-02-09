import base64
import requests
import cv2
import json

class Sender:
    def __init__(self, config):
        self.device_id      = config.device_id
        # 0) confirm URL
        self.server_url     = f"http://{config.ip}:{config.port}{config.uri}"
        print (f"URL= {self.server_url}")
        #/auth/violations"

        # 1) 이벤트 지속 카운터 (프레임 단위)
        self.event_count    = 0
        # 2) 재전송 억제 시간 -2초
        self.suppress_frames = int(config.fps * 2)

    def process_frame(self, frame, detections, camera_id="CAM_0", frame_id="0_0"):
        """
        프레임과 검출 정보를 서버로 전송
        """
        try:
            # 1. 이미지 인코딩 (JPG 압축)
            # 압축률 90% 설정 (전송 속도를 위해 조정 가능)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            success, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            
            if not success:
                print("[Sender] 이미지 인코딩 실패")
                return

            # 2. 데이터 직렬화 (NumPy -> Python List/Float 변환)
            # detections 구조: list of [y1, x1, y2, x2, score] (Hailo 예시 기준)
            clean_detections = []
            
            # Hailo 결과 구조에 따라 파싱 (List of Lists 가정)
            # 예: [[cls_idx, [y1, x1, y2, x2, score], ...], ...] 구조일 경우 단순화 필요
            # 아래는 일반적인 [y1, x1, y2, x2, score] 리스트라고 가정하고 변환
            
            # (만약 inference.py에서 detections 형식이 [[bbox1], [bbox2]] 라면)
            # 여기서는 예시로 JSON 변환 가능한 형태로 만듭니다.
            for cls_idx, dets in enumerate(detections):
                # dets는 해당 클래스의 박스 리스트
                for detection in dets:
                    # detection: (y1, x1, y2, x2, score)
                    bbox = {
                        "class_id": int(cls_idx),
                        "bbox": [float(x) for x in detection[:4]], # 좌표
                        "score": float(detection[4])               # 신뢰도
                    }
                    clean_detections.append(bbox)

            # 3. 메타데이터 구성
            metadata = {
                "camera_id": self.device_id,
                "frame_id": frame_id,
                "detections": clean_detections,
                "timestamp":  "" # 필요시 시간 추가
            }

            # 4. 멀티파트 전송 (파일 + JSON)
            # 'file': (파일명, 바이트스트림, MIME타입)
            files = {
                'file': (f'{frame_id}.jpg', encoded_img.tobytes(), 'image/jpeg')
            }
            # 'metadata': JSON 문자열
            data = {
                'metadata': json.dumps(metadata)
            }

            # 5. POST 요청 전송
            # timeout 설정으로 네트워크 지연 시 스레드 멈춤 방지
            response = requests.post(self.server_url, files=files, data=data, timeout=2.0)

            if response.status_code != 200:
                print(f"[Sender] 전송 실패: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            print(f"[Sender] 서버 응답 시간 초과 ({self.server_url})")
        except Exception as e:
            print(f"[Sender] 에러 발생: {e}")

    def process_frame_(self, frame, detections):
        """
        detections: list of np.ndarray
        [ [y1,x1,y2,x2,score], ... ] 형태로 합친 뒤 개수 체크
        """
        total_dets = sum(len(d) for d in detections)

        # 1) 이벤트 발생(검출) 중
        if total_dets > 0:
            # 카운터가 0 이면 새로운 이벤트로 간주
            if self.event_count <= 0:
                self.send_event(frame, detections)
                # 카운터 리셋: suppress_frames 만큼 재전송 억제
                self.event_count = self.suppress_frames
        # 2) 이벤트 비발생(검출 없음) 중이라도 카운터가 올라가 있으면
        #    프레임마다 1씩 감소시켜 마침내 0이 되면 다음 이벤트를 허용
        elif self.event_count > 0:
            self.event_count -= 1

    def send_event(self, frame, detections):
        print ("**** sending event ")
        json_data = self.build_payload(frame, detections)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "hello_seopia"
        }
        try:
            resp = requests.post(self.url, json=json_data, headers=headers, timeout=1.0)
            print(f"[Sender] 이벤트 전송 완료 (status: {resp.status_code})")
        except Exception as e:
            print(f"[Sender] 이벤트 전송 실패: {e}")

    def build_payload_(self, frame, detections):
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        img_data = f"data:image/jpeg;base64,{img_base64}"

        # 검출된 사람 수, 헬멧 미착용 수 등 추가 가능
        total = sum(len(d) for d in detections)
        nohelmet = len(detections[0])

        return {
            "deviceId": self.device_id,
            "totalDetections": total,
            "noHelmetCount": nohelmet,
            "image": img_data
        }
