import webview
import sounddevice as sd
import numpy as np
import threading
import time
import json

class AudioEngine:
    def __init__(self):
        self.is_playing = False
        self.mode = "tone"  # "tone" | "sweep"
        self.frequency = 1000.0
        self.sweep_low = 100.0
        self.sweep_high = 10000.0
        self.sweep_duration = 4.0
        self._sweep_sample_pos = 0
        self.volume = 0.85
        self.last_db = -1.4
        self.sample_rate = 48000
        self.device_id = None
        self.stream = None
        self.phase = 0.0
        self.lock = threading.Lock()

    @staticmethod
    def _normalized_device(device_id):
        """Pywebview may pass JS strings; OutputStream expects int index or None (default)."""
        if device_id is None:
            return None
        if isinstance(device_id, int):
            return device_id
        s = str(device_id).strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return None

    def _effective_output_device(self):
        idx = self._normalized_device(self.device_id)
        if idx is None:
            return sd.default.device[1]
        return idx

    def _samplerate_for_device(self, output_index):
        try:
            info = sd.query_devices(output_index)
            sr = info.get('default_samplerate')
            if sr:
                return int(float(sr))
        except Exception:
            pass
        return self.sample_rate
    
    def callback(self, outdata, frames, time_info, status):
        if status:
            print(f"Status: {status}")

        with self.lock:
            mode = self.mode
            vol = self.volume
            sr = self.sample_rate
            freq = self.frequency
            f_low = self.sweep_low
            f_high = self.sweep_high
            sweep_T = self.sweep_duration

        if mode == "tone":
            phase_increment = 2 * np.pi * freq / sr
            phases = self.phase + np.arange(frames) * phase_increment
            self.phase = (phases[-1] + phase_increment) % (2 * np.pi)
            samples = np.sin(phases) * vol
        else:
            f0 = max(20.0, min(f_low, f_high))
            f1 = max(f0, min(20000.0, max(f_low, f_high)))
            T = max(0.05, float(sweep_T))

            with self.lock:
                n0 = self._sweep_sample_pos
                self._sweep_sample_pos = n0 + frames

            idx = np.arange(frames, dtype=np.float64) + n0
            t = (idx / sr) % T

            if f1 <= f0 * 1.000001:
                f_inst = np.full(frames, f0)
            else:
                # Logarithmic sweep: f = f0 * (f1/f0)^(t/T) => equal time per octave.
                f_inst = f0 * (f1 / f0) ** (t / T)

            dphi = 2 * np.pi * f_inst / sr
            phi_arr = self.phase + np.cumsum(dphi)
            samples = np.sin(phi_arr) * vol
            self.phase = float(phi_arr[-1] % (2 * np.pi))

        outdata[:, 0] = samples
        outdata[:, 1] = samples
    
    def db_to_gain(self, db):
        """将 dB 转换为线性增益"""
        return 10 ** (db / 20)
    
    def start(self, frequency, db):
        with self.lock:
            self.mode = "tone"
            self.frequency = frequency
            self.volume = self.db_to_gain(db)
            self.last_db = float(db)
            self.phase = 0.0
            self._sweep_sample_pos = 0

        if self.stream is not None:
            self.stop()
        
        try:
            out_idx = self._effective_output_device()
            sample_rate = self._samplerate_for_device(out_idx)

            with self.lock:
                self.sample_rate = sample_rate

            self.stream = sd.OutputStream(
                samplerate=sample_rate,
                channels=2,
                dtype=np.float32,
                device=out_idx,
                callback=self.callback,
                blocksize=2048,
            )
            self.stream.start()
            self.is_playing = True
            return True
        except Exception as e:
            print(f"启动音频失败: {e}")
            return False

    def start_sweep(self, f_low, f_high, db):
        with self.lock:
            self.mode = "sweep"
            self.sweep_low = float(f_low)
            self.sweep_high = float(f_high)
            self.volume = self.db_to_gain(db)
            self.last_db = float(db)
            self.phase = 0.0
            self._sweep_sample_pos = 0

        if self.stream is not None:
            self.stop()

        try:
            out_idx = self._effective_output_device()
            sample_rate = self._samplerate_for_device(out_idx)

            with self.lock:
                self.sample_rate = sample_rate

            self.stream = sd.OutputStream(
                samplerate=sample_rate,
                channels=2,
                dtype=np.float32,
                device=out_idx,
                callback=self.callback,
                blocksize=2048,
            )
            self.stream.start()
            self.is_playing = True
            return True
        except Exception as e:
            print(f"启动扫频失败: {e}")
            return False

    def stop(self):
        self.is_playing = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"停止音频失败: {e}")
            finally:
                self.stream = None
    
    def set_frequency(self, frequency):
        with self.lock:
            if self.mode != "tone":
                return
            self.frequency = frequency

    def set_sweep_range(self, f_low, f_high):
        with self.lock:
            if self.mode != "sweep":
                return
            self.sweep_low = float(f_low)
            self.sweep_high = float(f_high)
    
    def set_volume(self, db):
        """设置音量（dB值）"""
        with self.lock:
            self.volume = self.db_to_gain(db)
            self.last_db = float(db)
    
    def set_device(self, device_id):
        self.device_id = device_id if device_id else None
        if self.is_playing:
            db = self.last_db
            mode = self.mode
            self.stop()
            time.sleep(0.1)
            if mode == "sweep":
                f_lo = self.sweep_low
                f_hi = self.sweep_high
                self.start_sweep(f_lo, f_hi, db)
            else:
                self.start(self.frequency, db)
    
    def get_devices(self):
        """获取所有输出设备"""
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_output_channels'] > 0:
                name = device['name'].strip()
                if not name:
                    name = f"Device {i}"
                devices.append({
                    'id': str(i),
                    'name': name
                })
        return devices


class Api:
    def __init__(self):
        self.audio = AudioEngine()
    
    def start_tone(self, frequency, volume):
        """开始播放正弦波"""
        return self.audio.start(frequency, volume)

    def start_sweep(self, f_low, f_high, volume):
        """开始播放对数扫频（从 f_low 到 f_high，循环）"""
        return self.audio.start_sweep(f_low, f_high, volume)
    
    def stop_tone(self):
        """停止播放"""
        self.audio.stop()
    
    def set_frequency(self, frequency):
        """设置频率"""
        self.audio.set_frequency(frequency)

    def set_sweep_range(self, f_low, f_high):
        """声场模式：更新扫频起止频率"""
        self.audio.set_sweep_range(f_low, f_high)
    
    def set_volume(self, volume):
        """设置音量"""
        self.audio.set_volume(volume)
    
    def set_device(self, device_id):
        """设置输出设备"""
        self.audio.set_device(device_id)
    
    def get_devices(self):
        """获取设备列表"""
        return self.audio.get_devices()


def main():
    api = Api()
    
    # 创建窗口
    window = webview.create_window(
        'Sweet Signal Generator',
        'src/index.html',
        width=560,
        height=760,
        resizable=False,
        js_api=api
    )
    
    # 启动后更新设备列表
    def on_loaded():
        devices = api.get_devices()
        if window:
            window.evaluate_js("window.updateDeviceList(" + json.dumps(devices) + ")")
    
    webview.start(on_loaded, debug=False)


if __name__ == '__main__':
    main()
