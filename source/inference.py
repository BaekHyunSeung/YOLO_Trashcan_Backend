import cv2
import numpy as np
from hailo_platform import VDevice, HailoSchedulingAlgorithm
import json

class Inference:
    def __init__(self, config, timeout_ms=1000):
        # HEF 파일
        self.hef_path   = config.model_path
        self.timeout_ms = timeout_ms

        self.vdevice  = None
        self.model    = None
        self.cmodel   = None
        self.bindings = None

        self.H = self.W = self.C = None

        self.scale = 1.0
        self.dx = 0
        self.dy = 0

        self.in_buf = None
        self.out_buf = None

        # 라벨, 색
        with open(config.classes_path, 'r') as f:
            def_labels = f.read().splitlines()

        self.LABELS = []
        self.COLORS = {}
        for e in def_labels:
            class_name = e
            self.LABELS.append(class_name)
            self.COLORS[class_name] = (0, 0, 255)  # b g r(255)

        '''
        with open(config.classes_path) as f:
            class_config = json.load(f)
        self.LABELS = []
        self.COLORS = {}

        for e in class_config["classes"]:
            class_name = list(e.keys())[0]
            class_info = e[class_name]
            self.LABELS.append(class_name)
            if "color" in class_info:
                self.COLORS[class_name] = tuple(class_info["color"])
            else:
                self.COLORS[class_name] = (255, 255, 255)
        '''

    def setup_npu(self):
        params = VDevice.create_params()
        params.scheduling_algorithm = HailoSchedulingAlgorithm.ROUND_ROBIN
        self.vdevice = VDevice(params)
        self.model   = self.vdevice.create_infer_model(self.hef_path)

        in_shape = tuple(self.model.input().shape)
        self.H, self.W, self.C = in_shape

        self.cmodel   = self.model.configure()
        self.bindings = self.cmodel.create_bindings()

        self.in_buf  = np.empty((self.H, self.W, self.C), dtype=np.uint8)
        self.bindings.input().set_buffer(self.in_buf)

        out_shape    = tuple(self.model.output().shape)
        self.out_buf = np.empty(out_shape, dtype=np.float32)
        self.bindings.output().set_buffer(self.out_buf)

    def _letterbox(self, img, color=(114,114,114)):
        h0, w0 = img.shape[:2]
        self.scale = min(self.W / w0, self.H / h0)
        nw, nh = int(w0 * self.scale), int(h0 * self.scale)
        resized = cv2.resize(img, (nw, nh))
        self.dx = (self.W - nw) // 2
        self.dy = (self.H - nh) // 2
        top, bottom = self.dy, self.H - nh - self.dy
        left, right = self.dx, self.W - nw - self.dx
        padded = cv2.copyMakeBorder(resized, top, bottom, left, right,
                                    cv2.BORDER_CONSTANT, value=color)
        return padded

    def infer(self, frame):
        padded = self._letterbox(frame)
        cv2.cvtColor(padded, cv2.COLOR_BGR2RGB, dst=self.in_buf)
        job = self.cmodel.run_async([self.bindings])
        job.wait(self.timeout_ms)
        return self.bindings.output().get_buffer()

    def draw_boxes(self, frame, detections):
        h0, w0 = frame.shape[:2]

        for cls_idx, dets in enumerate(detections):
            label = self.LABELS[cls_idx]
            color = self.COLORS[label]

            for y1, x1, y2, x2, score in dets:
                x1_p = int(x1 * self.W)
                y1_p = int(y1 * self.H)
                x2_p = int(x2 * self.W)
                y2_p = int(y2 * self.H)

                x1_o = int((x1_p - self.dx) / self.scale)
                y1_o = int((y1_p - self.dy) / self.scale)
                x2_o = int((x2_p - self.dx) / self.scale)
                y2_o = int((y2_p - self.dy) / self.scale)

                cv2.rectangle(frame, (x1_o, y1_o), (x2_o, y2_o), color, 2)
                cv2.putText(frame, f"{label} {score:.2f}",
                            (x1_o, max(y1_o - 5, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2) # fontSize 05 to 1
        return frame

    def cleanup(self):
        del self.cmodel
        self.cmodel = None
        del self.vdevice
        self.vdevice = None
