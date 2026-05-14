import webview
import sounddevice as sd
import numpy as np
import threading
import time
import json

class AudioEngine:
    def __init__(self):
        self.is_playing = False
        self.frequency = 1000.0
        self.volume = 0.85
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
            freq = self.frequency
            vol = self.volume
        
        # 生成正弦波 - 使用连续相位
        phase_increment = 2 * np.pi * freq / self.sample_rate
        
        # 使用累积相位，避免频率变化时的相位跳变
        phases = self.phase + np.arange(frames) * phase_increment
        self.phase = (phases[-1] + phase_increment) % (2 * np.pi)
        
        samples = np.sin(phases) * vol
        
        # 立体声输出
        outdata[:, 0] = samples
        outdata[:, 1] = samples
    
    def db_to_gain(self, db):
        """将 dB 转换为线性增益"""
        return 10 ** (db / 20)
    
    def start(self, frequency, db):
        with self.lock:
            self.frequency = frequency
            self.volume = self.db_to_gain(db)
            self.phase = 0.0
        
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
            # 频率变化时，相位不需要调整！
            # 因为 phase += 2πf·dt，当 f 变化时，相位自然连续变化
            # 只要保持 phase 的连续性，就不会产生咔哒声或调制音色
            self.frequency = frequency
    
    def set_volume(self, db):
        """设置音量（dB值）"""
        with self.lock:
            self.volume = self.db_to_gain(db)
    
    def set_device(self, device_id):
        self.device_id = device_id if device_id else None
        # 如果正在播放，重启音频流以应用新设备
        if self.is_playing:
            freq = self.frequency
            db = 20 * np.log10(max(self.volume, 1e-12))
            self.stop()
            time.sleep(0.1)
            self.start(freq, db)
    
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
    
    def stop_tone(self):
        """停止播放"""
        self.audio.stop()
    
    def set_frequency(self, frequency):
        """设置频率"""
        self.audio.set_frequency(frequency)
    
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
        height=700,
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
