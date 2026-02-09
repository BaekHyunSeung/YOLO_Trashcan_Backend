# server.py
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import uvicorn
import shutil
import os
import json

app = FastAPI()

# 저장 경로 설정
UPLOAD_DIR = "_received_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/detect/result")
async def receive_detection(
    file: UploadFile = File(...),      # 이미지 파일
    metadata: str = Form(...)          # JSON 문자열로 된 메타데이터
):
    try:
        # 1. JSON 메타데이터 파싱
        data = json.loads(metadata)
        camera_id = data.get("camera_id", "unknown")
        frame_id = data.get("frame_id", "unknown")
        detections = data.get("detections", [])

        print(f"[{camera_id}] Frame: {frame_id} 수신됨. 객체 수: {len(detections)}")

        # 2. 이미지 파일 저장 (옵션)
        file_location = f"{UPLOAD_DIR}/{frame_id}.jpg"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. 비즈니스 로직 처리 (DB 저장 등)
        # 예: print(detections)
        
        return {"status": "success", "frame_id": frame_id}

    except Exception as e:
        print(f"에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 0.0.0.0으로 열어서 외부 접속 허용, 포트 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
