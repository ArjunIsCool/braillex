import threading
import serial


class SerialWorker(threading.Thread):
    def __init__(self, port, baud, event_queue):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.q = event_queue
        self._stop = threading.Event()
        self.ser = None
        self._send_lock = threading.Lock()

    def send_command(self, cmd):
        if not self.ser or not self.ser.is_open:
            return False
        try:
            with self._send_lock:
                self.ser.write((cmd + "\n").encode("utf-8"))
            return True
        except Exception:
            return False

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.5)
            self.q.put(("connected", self.port))
        except Exception as e:
            self.q.put(("error", str(e)))
            return

        buf = ""
        while not self._stop.is_set():
            try:
                data = self.ser.read(64).decode("utf-8", errors="ignore")
                if data:
                    buf += data
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.q.put(("data", line))
            except serial.SerialException as e:
                self.q.put(("error", str(e)))
                break
            except Exception:
                pass

        if self.ser and self.ser.is_open:
            self.ser.close()
        self.q.put(("disconnected", self.port))

    def stop(self):
        self._stop.set()
