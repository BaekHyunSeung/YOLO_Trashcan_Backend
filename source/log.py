import time
from collections import defaultdict
import contextlib
class LoopProfiler:
    def __init__(self, config):
        self.enabled = config.log_enable
        self.target_frames = int(config.log_second) * int(config.fps) if self.enabled else 1
        
        self.acc_times = defaultdict(float)
        self.frame_count = 0
        self.loop_start_time = 0

    def start_frame(self):
        if not self.enabled: return
        self.loop_start_time = time.time()

    def end_frame(self):
        if not self.enabled: return
        total_duration = time.time() - self.loop_start_time
        self.acc_times['Total'] += total_duration
        self.frame_count += 1

        if self.frame_count >= self.target_frames:
            self._print_stats()
            self._reset_stats()
            
    @contextlib.contextmanager
    def measure(self, name):
        if not self.enabled:
            yield
            return

        start = time.time()
        yield 
        duration = time.time() - start
        self.acc_times[name] += duration

    def _print_stats(self):
        seconds_elapsed = self.frame_count / self.target_frames * (self.target_frames / 25)
        
        stats_str = f"[log.py] [Log every {self.frame_count} frames] "
        
        avg_total = self.acc_times['Total'] / self.frame_count
        current_fps = 1.0 / avg_total if avg_total > 0 else 0
        
        stats_str += f"Real FPS: {current_fps:.1f} | "

        for name, total_time in self.acc_times.items():
            avg_ms = (total_time / self.frame_count) * 1000
            stats_str += f"{name}: {avg_ms:.1f}ms | "
            
        print(stats_str)

    def _reset_stats(self):
        self.acc_times.clear()
        self.frame_count = 0