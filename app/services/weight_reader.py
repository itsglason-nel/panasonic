"""
PMPC Data Logger — Weight Reader Service
Daemon to read RS-232 data from Instru-Tech FI05-150K-4252C.
Stores the latest reading in Redis for the frontend to poll.
"""
import serial  # type: ignore
import time
import threading
import redis
import os
import re
import socket
import struct
from dotenv import load_dotenv

load_dotenv()


class WeightReader:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.redis_error_logged = False
        self.hardware_error_logged = False
        
        # We will use the same redis connection as Flask-Session if possible,
        # or a direct connection.
        self.redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST', '127.0.0.1'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True
        )
        
        self.port = os.environ.get('SERIAL_PORT', 'COM3')
        self.baudrate = int(os.environ.get('SERIAL_BAUDRATE', 9600))
        self.timeout = float(os.environ.get('SERIAL_TIMEOUT', 1.0))
        
    def init_app(self, app):
        self.app = app
        
    def start(self):
        if self.running:
            return
        self.running = True
        print(f"Initializing WeightReader on {self.port} at {self.baudrate} baud...")
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def set_weight(self, value):
        # 1. Try Redis
        try:
            self.redis_client.set('current_weight_kg', str(value))
            if self.redis_error_logged:
                print("WeightReader Redis Connection Restored.")
                self.redis_error_logged = False
        except Exception as e:
            # Fallback to file system
            try:
                import os
                temp_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'current_weight.txt')
                with open(temp_file, 'w') as f:
                    f.write(str(value))
            except Exception as file_e:
                pass
            
            if not self.redis_error_logged:
                print("[INFO] Redis unavailable. Using file-based weight fallback system.")
                self.redis_error_logged = True

    def _read_loop(self):
        is_tcp = self.port.startswith('tcp://')
        plc_register = os.environ.get('PLC_WEIGHT_REGISTER', 'DM1004')
        plc_format = os.environ.get('PLC_WEIGHT_FORMAT', 'float')
        
        while self.running:
            ser = None
            sock = None
            try:
                if is_tcp:
                    ip, port_str = self.port[6:].split(':')
                    port_num = int(port_str)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(self.timeout)
                    sock.connect((ip, port_num))
                    print(f"WeightReader successfully connected to PLC at {ip}:{port_num}.")
                else:
                    ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                    print(f"WeightReader successfully connected to {self.port}.")
                
                # Reset hardware error status on success
                self.hardware_error_logged = False
                
                # Active reading loop
                while self.running:
                    if is_tcp:
                        if sock is None:
                            break
                        # Keyence Upper Level Link Command
                        if plc_format == 'float':
                            cmd = f"RDS {plc_register} 2\r"
                        elif plc_format == 'string':
                            cmd = f"RDS {plc_register} 10\r"
                        else: # default to s32
                            cmd = f"RDS {plc_register}.D 1\r"
                            
                        sock.sendall(cmd.encode('ascii'))
                        
                        response = b""
                        while not response.endswith(b"\r\n") and not response.endswith(b"\r"):
                            chunk = sock.recv(1)
                            if not chunk:
                                break
                            response += chunk
                            
                        response_str = response.decode('ascii').strip()
                        
                        if self.hardware_error_logged:
                            print("WeightReader Hardware Connection Restored.")
                            self.hardware_error_logged = False
                            
                        if not response_str.startswith("E") and response_str != "":
                            if plc_format == 'float':
                                words = [int(x) for x in response_str.split()]
                                if len(words) >= 2:
                                    w0, w1 = words[0] & 0xFFFF, words[1] & 0xFFFF
                                    val_bytes = struct.pack('<HH', w0, w1)
                                    weight = struct.unpack('<f', val_bytes)[0]
                                    self.set_weight(round(weight, 3))
                            elif plc_format == 'string':
                                words = [int(x) for x in response_str.split()]
                                chars = []
                                for w in words:
                                    w = w & 0xFFFF
                                    chars.append(chr(w & 0xFF))
                                    chars.append(chr((w >> 8) & 0xFF))
                                string_val = "".join(chars).replace('\x00', '')
                                match = re.search(r'[-+]?\s*\d+\.\d+', string_val)
                                if match:
                                    weight = float(match.group(0).replace(' ', ''))
                                    self.set_weight(weight)
                            else:
                                self.set_weight(float(response_str))
                    else:
                        if ser is None:
                            break
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('ascii', errors='ignore').strip()
                            if self.hardware_error_logged:
                                print("WeightReader Hardware Connection Restored.")
                                self.hardware_error_logged = False
                            match = re.search(r'[-+]?\s*\d+\.\d+', line)
                            if match:
                                val_str = match.group(0).replace(' ', '')
                                weight = float(val_str)
                                self.set_weight(weight)
                                
                    time.sleep(0.5 if is_tcp else 0.1)
                    
            except Exception as e:
                self.set_weight('error')
                if not self.hardware_error_logged:
                    print("[ERR-CONNECTION] Hardware Communication Failure.")
                    print(f"Details: {e}")
                    print("Action Required: Please consult the '[?] Troubleshoot' guide in the Launcher.")
                    print("Note: Retrying connection in 5 seconds...")
                    self.hardware_error_logged = True
                
                # Cleanup connection handles before reconnecting
                if ser:
                    try:
                        ser.close()
                    except:
                        pass
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                        
                time.sleep(5.0)

# Global instance
weight_reader = WeightReader()

if __name__ == '__main__':
    try:
        weight_reader.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        weight_reader.stop()

