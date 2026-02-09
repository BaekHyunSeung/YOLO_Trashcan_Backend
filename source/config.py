import configparser as cp

class Config:
    def __init__(self):
        config = cp.ConfigParser()
        config.read("config/config.ini")
        """기본 세팅"""
        self.device_id=config["settings"]["device_id"]

        """Camera 세팅"""
        self.width=config["CAMERA"]["width"]
        self.height=config["CAMERA"]["height"]
        self.fps=config["CAMERA"]["fps"]

        """INPUT 세팅"""
        self.video_file_path=config["INPUT"]["video_file_path"]

        """YOLO 세팅"""
        self.output_path=config["FFMPEG"]["output_path"]
        self.model_path=config["YOLO"]["model_path"]
        self.classes_path=config["YOLO"]["class_file_path"]

        """Server 세팅"""
        self.ip=config["SERVER"]["ip"]
        self.port=config["SERVER"]["port"]
        self.uri=config["SERVER"]["uri"]
        self.is_send = config.getboolean("SERVER", "send")

        """Log Setting"""
        self.log_enable=config.getboolean("LOGGING", "enable")
        self.log_second=config.getint("LOGGING","second")
        self.is_test=config.getboolean("LOGGING", "test_video")

