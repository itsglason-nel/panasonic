import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import subprocess
import threading
import os
import sys
import webbrowser
import time
import socket
import datetime
import ctypes

try:
    myappid = 'pmpc.datalogger.system.1'
    windll = getattr(ctypes, 'windll', None)
    if windll:
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Windows specific flag to hide the command prompt window
CREATE_NO_WINDOW = 0x08000000
SINGLE_INSTANCE_PORT = 28467

# Get STARTUPINFO dynamically to prevent static analysis errors on non-Windows environments
STARTUPINFO = getattr(subprocess, 'STARTUPINFO', None)

ctk.set_appearance_mode("Light")  
ctk.set_default_color_theme("blue") 

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PMPC Data Logger - System Launcher")
        
        window_width = 900
        window_height = 650
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(base_dir, 'docs', 'assets', 'panasonic_logo.ico')
            self.root.iconbitmap(ico_path)
        except Exception:
            pass
        
        self.web_process = None
        self.weight_process = None
        self.is_running = False
        
        self.create_widgets()
        
        # Ensure processes are killed on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup single-instance wakeup listener
        self.server_socket = None
        self.start_wakeup_listener()

    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self.root, fg_color="#000000", corner_radius=0, height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(header_frame, text="PMPC Data Logger System", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color="white")
        title_label.pack(pady=20)

        # Controls
        control_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        control_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.btn_start = ctk.CTkButton(control_frame, text="▶ Start System", font=ctk.CTkFont(weight="bold"), fg_color="#3182ce", command=self.start_system)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = ctk.CTkButton(control_frame, text="■ Stop System", font=ctk.CTkFont(weight="bold"), fg_color="#a0aec0", hover_color="#c53030", state=tk.DISABLED, command=self.stop_system)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        self.btn_restart = ctk.CTkButton(control_frame, text="↻ Restart", font=ctk.CTkFont(weight="bold"), fg_color="#a0aec0", hover_color="#c05621", state=tk.DISABLED, command=self.restart_system)
        self.btn_restart.pack(side=tk.LEFT, padx=5)

        self.btn_browser = ctk.CTkButton(control_frame, text="🌐 Open Web App", font=ctk.CTkFont(weight="bold"), fg_color="#a0aec0", hover_color="#2f855a", state=tk.DISABLED, command=self.open_browser)
        self.btn_browser.pack(side=tk.RIGHT, padx=5)

        self.btn_troubleshoot = ctk.CTkButton(control_frame, text="[?] Troubleshoot", font=ctk.CTkFont(weight="bold"), fg_color="#475569", hover_color="#334155", command=self.open_troubleshoot_dialog)
        self.btn_troubleshoot.pack(side=tk.RIGHT, padx=5)

        # Status
        status_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ctk.CTkLabel(status_frame, text="Web Server:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.lbl_web_status = ctk.CTkLabel(status_frame, text="Stopped", font=ctk.CTkFont(weight="bold"), text_color="#e53e3e")
        self.lbl_web_status.grid(row=0, column=1, sticky="w", padx=10)
        
        ctk.CTkLabel(status_frame, text="Weight Reader:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, sticky="w", padx=(30, 0))
        self.lbl_weight_status = ctk.CTkLabel(status_frame, text="Stopped", font=ctk.CTkFont(weight="bold"), text_color="#e53e3e")
        self.lbl_weight_status.grid(row=0, column=3, sticky="w", padx=10)

        # Logs
        log_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(log_frame, text="System Logs:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.log_area = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=12), text_color="#00ff00", fg_color="#1e1e1e", border_color="#d1d5db", border_width=2)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')

    def set_btn_state(self, btn, state, active_color):
        btn.configure(state=state)
        btn.configure(fg_color=active_color if state == tk.NORMAL else "#a0aec0")

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_area.configure(state='normal')
        
        full_msg = f"{timestamp} {message}\n"
        msg_lower = message.lower()
        is_error = "error" in msg_lower or "warning" in msg_lower or "[err" in msg_lower or "failed" in msg_lower
        
        # Configure the tag once if not already
        try:
            self.log_area.tag_config("error", foreground="#ff4444")
        except Exception:
            pass
            
        if is_error:
            self.log_area.insert(tk.END, full_msg, "error")
        else:
            self.log_area.insert(tk.END, full_msg)
            
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

    def read_stream(self, process, prefix, status_lbl):
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            self.root.after(0, self.log, f"[{prefix}] {line.strip()}")
            
        if self.is_running:
            process.wait()
            exit_code = process.poll()
            self.root.after(0, self.handle_process_crash, prefix, status_lbl, exit_code)

    def handle_process_crash(self, prefix, status_lbl, exit_code):
        if self.is_running:
            self.log(f"[{prefix}] ⚠️ Process unexpectedly stopped (Exit Code: {exit_code})")
            status_lbl.configure(text="CRASHED", text_color="#e53e3e")

    def run_command(self, command, prefix, status_lbl):
        try:
            env = os.environ.copy()
            env["FLASK_CONFIG"] = "production"
            env["PYTHONUNBUFFERED"] = "1"
            
            startupinfo = None
            if STARTUPINFO:
                startupinfo = STARTUPINFO()
                startupinfo.dwFlags |= 0x00000080
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
                startupinfo=startupinfo,
                env=env
            )
            
            threading.Thread(target=self.read_stream, args=(process, prefix, status_lbl), daemon=True).start()
            return process
        except Exception as e:
            self.root.after(0, self.log, f"[{prefix}] Error: {str(e)}")
            return None

    def _startup_sequence(self):
        self.root.after(0, self.log, "--- Starting PMPC Data Logger System ---")
        
        # 1. Initialize Database
        self.root.after(0, self.log, "Initializing Database (Timeout: 15s)...")
        db_proc = None
        try:
            startupinfo = None
            if STARTUPINFO:
                startupinfo = STARTUPINFO()
                startupinfo.dwFlags |= 0x00000080
            
            db_proc = subprocess.Popen([sys.executable, "tools/init_database.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo)
            db_out, _ = db_proc.communicate(timeout=15)
            self.root.after(0, self.log, db_out.strip())
        except subprocess.TimeoutExpired:
            if db_proc:
                self.kill_process_tree(db_proc)
            self.root.after(0, self.log, "[ERR-DB3306] Database Connection Timeout.")
            self.root.after(0, self.log, "Details: 'plcdata' initialization exceeded 15s timeout.")
            self.root.after(0, self.log, "Action Required: Please consult the '[?] Troubleshoot' guide in the Launcher.")
            self.root.after(0, self.stop_system)
            return
        except Exception as e:
            self.root.after(0, self.log, f"Database Init Error: {e}")
            self.root.after(0, self.stop_system)
            return
            
        if not self.is_running:
            return
        
        # 2. Initialize WSL Redis (Disabled, using file fallback)

        self.root.after(0, self.log, "Starting Web Server...")
        self.root.after(0, lambda: self.lbl_web_status.configure(text="Starting...", text_color="#dd6b20"))
        self.web_process = self.run_command([sys.executable, "wsgi.py"], "WEB", self.lbl_web_status)
        
        self.root.after(0, self.log, "Starting Weight Reader Service...")
        self.root.after(0, lambda: self.lbl_weight_status.configure(text="Starting...", text_color="#dd6b20"))
        self.weight_process = self.run_command([sys.executable, "app/services/weight_reader.py"], "SCALE", self.lbl_weight_status)

        port = 8080
        try:
            from config import config_map
            config_name = os.environ.get('FLASK_CONFIG', 'production')
            config = config_map.get(config_name, config_map['default'])
            port = getattr(config, 'SERVER_PORT', 8080)
        except Exception:
            pass

        start_time = time.time()
        timeout = 30
        web_ready = False
        weight_ready = False
        
        while time.time() - start_time < timeout and self.is_running:
            if not web_ready and self.web_process:
                if self.web_process.poll() is not None:
                    break
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.5) as s:
                        web_ready = True
                        self.root.after(0, lambda: self.lbl_web_status.configure(text="Running", text_color="#38a169") if self.web_process and self.lbl_web_status.cget("text") != "CRASHED" else None)
                        self.root.after(0, lambda: self.set_btn_state(self.btn_browser, tk.NORMAL, "#38a169"))
                        self.root.after(0, self.log, f"Web Server is ready and listening on port {port}.")
                except OSError:
                    pass

            if not weight_ready and self.weight_process:
                if time.time() - start_time >= 1.5:
                    if self.weight_process.poll() is None:
                        weight_ready = True
                        self.root.after(0, lambda: self.lbl_weight_status.configure(text="Running", text_color="#38a169") if self.weight_process and self.lbl_weight_status.cget("text") != "CRASHED" else None)
                    else:
                        break

            if (web_ready or not self.web_process) and (weight_ready or not self.weight_process):
                break
                
            time.sleep(0.5)
            
        if self.is_running:
            if not web_ready and self.web_process:
                self.root.after(0, lambda: self.lbl_web_status.configure(text="FAILED", text_color="#e53e3e") if self.lbl_web_status.cget("text") != "CRASHED" else None)
                self.root.after(0, self.log, f"❌ Error: Web Server failed to start or respond on port {port}.")
            if not weight_ready and self.weight_process:
                self.root.after(0, lambda: self.lbl_weight_status.configure(text="FAILED", text_color="#e53e3e") if self.weight_process and self.lbl_weight_status.cget("text") != "CRASHED" else None)
                self.root.after(0, self.log, "❌ Error: Weight Reader failed to start.")

    def start_system(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.set_btn_state(self.btn_start, tk.DISABLED, "#3182ce")
        self.set_btn_state(self.btn_stop, tk.NORMAL, "#e53e3e")
        self.set_btn_state(self.btn_restart, tk.NORMAL, "#dd6b20")
        self.set_btn_state(self.btn_browser, tk.DISABLED, "#38a169")
        
        self.log_area.configure(state='normal')
        # self.log_area.delete(1.0, tk.END) # Keep logs for debugging
        self.log_area.configure(state='disabled')
        
        threading.Thread(target=self._startup_sequence, daemon=True).start()

    def kill_process_tree(self, process):
        if process:
            try:
                startupinfo = None
                if STARTUPINFO:
                    startupinfo = STARTUPINFO()
                    startupinfo.dwFlags |= 0x00000080
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                               creationflags=CREATE_NO_WINDOW,
                               startupinfo=startupinfo)
            except Exception:
                pass

    def stop_system(self, is_restarting=False):
        if not self.is_running:
            return
            
        self.log("--- Stopping System ---")
        
        if self.web_process:
            self.kill_process_tree(self.web_process)
            self.web_process = None
            self.lbl_web_status.configure(text="Stopped", text_color="#e53e3e")
            
        if self.weight_process:
            self.kill_process_tree(self.weight_process)
            self.weight_process = None
            self.lbl_weight_status.configure(text="Stopped", text_color="#e53e3e")
            
        self.is_running = False
        
        if not is_restarting:
            self.set_btn_state(self.btn_start, tk.NORMAL, "#3182ce")
            self.set_btn_state(self.btn_stop, tk.DISABLED, "#e53e3e")
            self.set_btn_state(self.btn_restart, tk.DISABLED, "#dd6b20")
            self.set_btn_state(self.btn_browser, tk.DISABLED, "#38a169")
            self.log("System stopped cleanly.")

    def restart_system(self):
        if not self.is_running:
            return
            
        self.set_btn_state(self.btn_start, tk.DISABLED, "#3182ce")
        self.set_btn_state(self.btn_stop, tk.DISABLED, "#e53e3e")
        self.set_btn_state(self.btn_restart, tk.DISABLED, "#dd6b20")
        self.set_btn_state(self.btn_browser, tk.DISABLED, "#38a169")
        
        self.log("--- Initiating Restart ---")
        self.stop_system(is_restarting=True)
        
        def delayed_start():
            time.sleep(1.5)
            self.root.after(0, self.start_system)
            
        threading.Thread(target=delayed_start, daemon=True).start()

    def open_browser(self):
        port = 8080
        host = 'localhost'
        try:
            from config import config_map
            config_name = os.environ.get('FLASK_CONFIG', 'production')
            config = config_map.get(config_name, config_map['default'])
            port = getattr(config, 'SERVER_PORT', 8080)
            cfg_host = getattr(config, 'SERVER_HOST', 'localhost')
            if cfg_host == '0.0.0.0':
                host = 'localhost'
            else:
                host = cfg_host
        except Exception:
            pass

        url = f"http://{host}:{port}"
        
        self.set_btn_state(self.btn_browser, tk.DISABLED, "#38a169")
        self.root.after(1000, lambda: self.set_btn_state(self.btn_browser, tk.NORMAL, "#38a169") if self.is_running and self.web_process and self.web_process.poll() is None else None)
        
        threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()

    def start_wakeup_listener(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
            self.server_socket.listen(5)
            threading.Thread(target=self._wakeup_listener_loop, daemon=True).start()
        except OSError as e:
            self.log(f"[SYSTEM] Warning: Single-instance port bind failed: {e}")

    def _wakeup_listener_loop(self):
        while True:
            try:
                if not self.server_socket:
                    break
                conn, addr = self.server_socket.accept()
                data = conn.recv(1024)
                if data == b"RESTORE":
                    self.root.after(0, self.restore_window)
                conn.close()
            except Exception:
                break

    def restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.log("[SYSTEM] Window restored by external trigger.")

    def cleanup(self):
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

    def show_close_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("System Active")
        dialog.geometry("420x220")
        dialog.resizable(False, False)
        
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        dialog_w = 420
        dialog_h = 220
        
        x = main_x + (main_w - dialog_w) // 2
        x = max(0, x)
        y = main_y + (main_h - dialog_h) // 2
        y = max(0, y)
        
        dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        hdr = ctk.CTkFrame(dialog, fg_color="#000000", corner_radius=0, height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="PMPC Data Logger — System is Running", font=ctk.CTkFont(weight="bold"), text_color="white").pack(pady=8)
        
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        msg_lbl = ctk.CTkLabel(
            content_frame, 
            text="The web server and weight reader services are currently running.\nWhat would you like to do?", 
            justify=tk.LEFT
        )
        msg_lbl.pack(pady=(0, 20), anchor="w")
        
        self.dialog_choice = "cancel"
        
        def set_choice(choice):
            self.dialog_choice = choice
            dialog.destroy()
            
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_bg = ctk.CTkButton(btn_frame, text="Background", width=100, command=lambda: set_choice("background"))
        btn_bg.pack(side=tk.LEFT, padx=5)
        
        btn_exit = ctk.CTkButton(btn_frame, text="Shutdown", width=100, fg_color="#e53e3e", hover_color="#c53030", command=lambda: set_choice("exit"))
        btn_exit.pack(side=tk.LEFT, padx=5)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", width=80, fg_color="#cbd5e1", text_color="black", hover_color="#94a3b8", command=lambda: set_choice("cancel"))
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        self.root.wait_window(dialog)
        return self.dialog_choice

    def open_troubleshoot_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("System Troubleshooting Guide")
        dialog.geometry("650x550")
        dialog.resizable(False, False)
        
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        dialog_w = 650
        dialog_h = 550
        x = max(0, main_x + (main_w - dialog_w) // 2)
        y = max(0, main_y + (main_h - dialog_h) // 2)
        dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        hdr = ctk.CTkFrame(dialog, fg_color="#000000", corner_radius=0, height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Troubleshooting Guide", font=ctk.CTkFont(weight="bold"), text_color="white").pack(pady=8)

        # Content Frame
        scrollable_frame = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 1. Redis Note
        ctk.CTkLabel(scrollable_frame, text="[INFO] Redis Cache Configuration", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", pady=(10, 5))
        redis_text = (
            "Note: The system optionally uses WSL Redis for high-speed caching.\n"
            "If Redis is not installed or the service is stopped, the application will automatically "
            "and safely fallback to using a local file-based cache for the scale readings. "
            "No action is required and the system will run normally."
        )
        ctk.CTkLabel(scrollable_frame, text=redis_text, justify=tk.LEFT, text_color="#334155", wraplength=580).pack(anchor="w")

        # 2. Hardware Error
        ctk.CTkLabel(scrollable_frame, text="[ERR-RS232] Hardware Communication Failure", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", pady=(20, 5))
        hw_text = (
            "Cause: The RS-232 serial connection to the Instru-Tech FI05 weighing scale is lost.\n"
            "The physical connection has been interrupted or the COM port has changed.\n\n"
            "Steps to Resolve:\n"
            "  1. Verify the physical RS-232 to USB adapter is securely plugged into the PC.\n"
            "  2. Ensure the scale indicator is powered ON and displaying a weight.\n"
            "  3. Press Win + X and open 'Device Manager'.\n"
            "  4. Expand 'Ports (COM & LPT)' and ensure the USB-to-Serial cable is assigned to COM3.\n"
            "  5. Right-click the COM3 port -> Properties -> Port Settings. Confirm it is 9600 baud.\n"
            "  6. If the COM port changed to something else (e.g., COM4), update the 'SERIAL_PORT' variable in your .env file."
        )
        ctk.CTkLabel(scrollable_frame, text=hw_text, justify=tk.LEFT, text_color="#334155", wraplength=580).pack(anchor="w")

        # 3. DB Error
        ctk.CTkLabel(scrollable_frame, text="[ERR-DB3306] Database Connection Timeout", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", pady=(20, 5))
        db_text = (
            "Cause: The MySQL database ('plcdata') failed to respond within 15 seconds.\n"
            "The database service is either stopped, blocked by a firewall, or using the wrong port.\n\n"
            "Steps to Resolve:\n"
            "  1. Press Win + R, type 'services.msc', and press Enter.\n"
            "  2. Scroll down to find your MySQL service (usually 'MySQL80' or simply 'MySQL').\n"
            "  3. Right-click and select 'Start'. Ensure Startup Type is 'Automatic'.\n"
            "  4. Open MySQL Workbench and connect to your local instance (127.0.0.1:3306).\n"
            "  5. Verify the 'plcdata' schema exists and is accessible.\n"
            "  6. Verify your system .env credentials (DB_USER, DB_PASSWORD) match your Workbench setup."
        )
        ctk.CTkLabel(scrollable_frame, text=db_text, justify=tk.LEFT, text_color="#334155", wraplength=580).pack(anchor="w")

        # 4. App Error
        ctk.CTkLabel(scrollable_frame, text="[ERR-APP500] Web Application / Logic Error", font=ctk.CTkFont(weight="bold", size=14)).pack(anchor="w", pady=(20, 5))
        app_text = (
            "Cause: The Flask web server encountered an unexpected logic bug, syntax error, or unhandled exception.\n\n"
            "Steps to Resolve:\n"
            "  1. Open the Launcher terminal window and scroll up to locate the Python 'Traceback'.\n"
            "  2. Take a screenshot of the Traceback or look for the final error (e.g., KeyError, TypeError).\n"
            "  3. Note the specific .py file and line number mentioned in the trace to identify the broken code.\n"
            "  4. If you see '500 Internal Server Error' in the browser, press F12, open the Network tab, and check the failed API response.\n"
            "  5. Revert any recent code changes to the affected file."
        )
        ctk.CTkLabel(scrollable_frame, text=app_text, justify=tk.LEFT, text_color="#334155", wraplength=580).pack(anchor="w", pady=(0, 10))

        # Close Button
        btn_close = ctk.CTkButton(dialog, text="Close Guide", width=120, fg_color="#cbd5e1", text_color="black", hover_color="#94a3b8", command=dialog.destroy)
        btn_close.pack(pady=(0, 20))

    def on_closing(self):
        if self.is_running:
            choice = self.show_close_dialog()
            if choice == "background":
                self.root.withdraw()
                self.log("[SYSTEM] Hiding launcher window. Services are active in the background.")
                messagebox.showinfo(
                    "System Running in Background",
                    "The PMPC Data Logger system is still running in the background.\n\nDouble-click 'Start SFIS.bat' at any time to bring this window back."
                )
            elif choice == "exit":
                self.stop_system()
                self.cleanup()
                self.root.destroy()
        else:
            self.cleanup()
            self.root.destroy()

def check_single_instance():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(('127.0.0.1', SINGLE_INSTANCE_PORT))
        s.sendall(b"RESTORE")
        s.close()
        sys.exit(0)
    except socket.error:
        pass

if __name__ == "__main__":
    check_single_instance()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    root = ctk.CTk()
    app = LauncherApp(root)
    root.mainloop()
