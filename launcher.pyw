import tkinter as tk
from tkinter import messagebox
from PIL import Image
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

def force_center_window(widget):
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32 # type: ignore
        HWND = user32.GetParent(widget.winfo_id())
        monitor = user32.MonitorFromWindow(HWND, 2)
        
        class RECT(ctypes.Structure):
            _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG), ("right", wintypes.LONG), ("bottom", wintypes.LONG)]
            
        class MONITORINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]
            
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
        
        screen_x, screen_y = mi.rcWork.left, mi.rcWork.top
        screen_w = mi.rcWork.right - mi.rcWork.left
        screen_h = mi.rcWork.bottom - mi.rcWork.top
        
        rect = RECT()
        user32.GetWindowRect(HWND, ctypes.byref(rect))
        win_w = rect.right - rect.left
        win_h = rect.bottom - rect.top
        
        x = screen_x + (screen_w - win_w) // 2
        y = screen_y + (screen_h - win_h) // 2
        user32.SetWindowPos(HWND, 0, x, y, 0, 0, 0x0001 | 0x0004)
    except Exception:
        pass

try:
    myappid = 'pmpc.datalogger.system.6'
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

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ── Minimalist Black & White Palette ────────────────────────────────────────
COLOR_BG         = "#000000"   # Pure black background
COLOR_SURFACE    = "#1e1e1e"   # Dark surface cards
COLOR_SURFACE_HI = "#1f1f1f"   # Elevated surface (hover / focus)
COLOR_BORDER     = "#444444"   # Subtle borders
COLOR_ACCENT     = "#ffffff"   # White accent
COLOR_SUCCESS    = "#22c55e"   # Running / OK
COLOR_ERROR      = "#ef4444"   # Stopped / Error
COLOR_WARNING    = "#f59e0b"   # Starting / Warning
COLOR_TEXT       = "#ffffff"   # Primary text — pure white
COLOR_TEXT_DIM   = "#888888"   # Secondary / muted text
COLOR_DISABLED   = "#1a1a1a"   # Disabled button background
COLOR_HEADER     = "#000000"   # Header bar — pure black
COLOR_LOG_BG     = "#121212"   # Log viewer background
COLOR_LOG_TEXT   = "#4ade80"   # Log text (green)

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PMPC Data Logger - System Launcher")
        
        window_width = 960
        window_height = 700
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.update_idletasks()
        self.root.after(50, lambda: force_center_window(self.root))
        self.root.after(200, lambda: force_center_window(self.root))
        self.root.resizable(False, False)
        self.root.configure(fg_color=COLOR_BG)
        

        
        try:
            import ctypes
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(base_dir, 'docs', 'assets', 'panasonic_logo.ico')
            self.ico_path = ico_path
            self.root.iconbitmap(ico_path)
            
            # Windows High-DPI Taskbar Fix: Bypass Tkinter's blurry aspect-ratio distortion
            try:
                windll = getattr(ctypes, 'windll', None)
                if windll:
                    HWND = windll.user32.GetParent(self.root.winfo_id())
                    # Load the crisp 64x64 layer directly from the ICO
                    hicon = windll.user32.LoadImageW(0, ico_path, 1, 64, 64, 0x00000010)
                    if hicon:
                        windll.user32.SendMessageW(HWND, 0x0080, 1, hicon) # ICON_BIG
                        windll.user32.SendMessageW(HWND, 0x0080, 0, hicon) # ICON_SMALL
            except Exception:
                pass
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
        # ── Premium Header ───────────────────────────────────────────────────
        header_frame = ctk.CTkFrame(self.root, fg_color=COLOR_HEADER, corner_radius=0, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        header_inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_inner.pack(expand=True)



        title_block = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_block.pack(expand=True)

        ctk.CTkLabel(
            title_block, text="PMPC Data Logger System",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLOR_TEXT
        ).pack(anchor="center")
        ctk.CTkLabel(
            title_block, text="System Launcher  ·  v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_DIM
        ).pack(anchor="center")

        # Accent line under header
        accent_line = ctk.CTkFrame(self.root, fg_color="#ffffff", corner_radius=0, height=2)
        accent_line.pack(fill=tk.X)

        # ── Main Content Container ───────────────────────────────────────────
        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        # ── Status Dashboard Cards ───────────────────────────────────────────
        status_row = ctk.CTkFrame(content, fg_color="transparent")
        status_row.pack(fill=tk.X, pady=(0, 18))

        # Web Server card
        web_card = ctk.CTkFrame(status_row, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        web_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        web_card_inner = ctk.CTkFrame(web_card, fg_color="transparent")
        web_card_inner.pack(expand=True, pady=14)

        web_info = ctk.CTkFrame(web_card_inner, fg_color="transparent")
        web_info.pack(expand=True)
        ctk.CTkLabel(web_info, text="Web Server", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=COLOR_TEXT_DIM).pack(anchor="center")
        
        self.lbl_web_status = ctk.CTkLabel(web_info, text="Stopped", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=COLOR_ERROR)
        self.lbl_web_status.pack(anchor="center", pady=(4, 0))
        self.web_dot = ctk.CTkLabel(web_card, text="●", font=ctk.CTkFont(size=14), text_color=COLOR_ERROR)
        self.web_dot.place(relx=1.0, rely=0.0, x=-20, y=20, anchor="center")

        # Weight Reader card
        weight_card = ctk.CTkFrame(status_row, fg_color=COLOR_SURFACE, corner_radius=12, border_width=1, border_color=COLOR_BORDER)
        weight_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        weight_card_inner = ctk.CTkFrame(weight_card, fg_color="transparent")
        weight_card_inner.pack(expand=True, pady=14)

        weight_info = ctk.CTkFrame(weight_card_inner, fg_color="transparent")
        weight_info.pack(expand=True)
        ctk.CTkLabel(weight_info, text="Weight Reader", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=COLOR_TEXT_DIM).pack(anchor="center")
        
        self.lbl_weight_status = ctk.CTkLabel(weight_info, text="Stopped", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=COLOR_ERROR)
        self.lbl_weight_status.pack(anchor="center", pady=(4, 0))
        self.weight_dot = ctk.CTkLabel(weight_card, text="●", font=ctk.CTkFont(size=14), text_color=COLOR_ERROR)
        self.weight_dot.place(relx=1.0, rely=0.0, x=-20, y=20, anchor="center")

        # ── Control Buttons ──────────────────────────────────────────────────
        control_frame = ctk.CTkFrame(content, fg_color="transparent")
        control_frame.pack(fill=tk.X, pady=(0, 18))

        btn_font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        btn_h = 40
        btn_r = 20  # pill-shaped corner radius

        # Load formal UI icons
        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(base_dir, 'docs', 'assets')
            
            icon_size = (18, 18)
            self.icon_start = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'play_black.png')), size=icon_size)
            self.icon_start_disabled = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'play.png')), size=icon_size)
            self.icon_stop = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'stop.png')), size=icon_size)
            self.icon_restart = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'restart.png')), size=icon_size)
            self.icon_browser = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'globe.png')), size=icon_size)
            self.icon_troubleshoot = ctk.CTkImage(light_image=Image.open(os.path.join(assets_dir, 'info.png')), size=icon_size)
        except Exception:
            self.icon_start = self.icon_start_disabled = self.icon_stop = self.icon_restart = self.icon_browser = self.icon_troubleshoot = None


        self.btn_start = ctk.CTkButton(
            control_frame, text=" Start System", font=btn_font,
            image=self.icon_start,
            fg_color="#ffffff", hover_color="#e5e5e5", text_color="#000000",
            width=160, height=btn_h, corner_radius=btn_r,
            command=self.start_system
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            control_frame, text=" Stop System", font=btn_font,
            image=self.icon_stop,
            fg_color=COLOR_DISABLED, hover_color="#dc2626",
            text_color=COLOR_TEXT_DIM,
            width=160, height=btn_h, corner_radius=btn_r,
            state=tk.DISABLED, command=self.stop_system
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_restart = ctk.CTkButton(
            control_frame, text=" Restart", font=btn_font,
            image=self.icon_restart,
            fg_color=COLOR_DISABLED, hover_color="#d97706",
            text_color=COLOR_TEXT_DIM,
            width=140, height=btn_h, corner_radius=btn_r,
            state=tk.DISABLED, command=self.restart_system
        )
        self.btn_restart.pack(side=tk.LEFT)

        self.btn_browser = ctk.CTkButton(
            control_frame, text=" Open Web App", font=btn_font,
            image=self.icon_browser,
            fg_color=COLOR_DISABLED, hover_color="#16a34a",
            text_color=COLOR_TEXT_DIM,
            width=170, height=btn_h, corner_radius=btn_r,
            state=tk.DISABLED, command=self.open_browser
        )
        self.btn_browser.pack(side=tk.RIGHT)

        self.btn_troubleshoot = ctk.CTkButton(
            control_frame, text=" Troubleshoot", font=btn_font,
            image=self.icon_troubleshoot,
            fg_color="#333333", hover_color="#444444",
            border_width=1, border_color="#555555",
            text_color="#ffffff",
            width=160, height=btn_h, corner_radius=btn_r,
            command=self.open_troubleshoot_dialog
        )
        self.btn_troubleshoot.pack(side=tk.RIGHT, padx=(0, 8))

        # ── Log Viewer ───────────────────────────────────────────────────────
        log_section = ctk.CTkFrame(content, fg_color="transparent")
        log_section.pack(fill=tk.BOTH, expand=True)

        log_header = ctk.CTkFrame(log_section, fg_color="transparent")
        log_header.pack(fill=tk.X, pady=(0, 8))
        ctk.CTkLabel(
            log_header, text="System Logs",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT
        ).pack(side=tk.LEFT)
        ctk.CTkFrame(log_header, fg_color=COLOR_BORDER, height=1).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0), pady=1)

        log_frame = ctk.CTkFrame(log_section, fg_color=COLOR_SURFACE, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_LOG_TEXT,
            fg_color=COLOR_LOG_BG,
            border_color=COLOR_BORDER,
            border_width=0,
            corner_radius=8
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        try:
            self.log_area._textbox.configure(padx=15, pady=10)
        except Exception:
            pass
        self.log_area.configure(state='disabled')

    def _update_status_dot(self, dot_widget, color):
        """Update a status indicator dot color."""
        try:
            dot_widget.configure(text_color=color)
        except Exception:
            pass

    def set_btn_state(self, btn, state, active_color):
        btn.configure(state=state)
        if state == tk.NORMAL:
            btn_text_color = "#000000" if active_color == "#ffffff" else COLOR_TEXT
            btn.configure(fg_color=active_color, text_color=btn_text_color)
            if hasattr(self, 'icon_start') and getattr(self, 'btn_start', None) == btn:
                btn.configure(image=self.icon_start)
        else:
            btn.configure(fg_color=COLOR_DISABLED, text_color=COLOR_TEXT_DIM)
            if hasattr(self, 'icon_start_disabled') and getattr(self, 'btn_start', None) == btn:
                btn.configure(image=self.icon_start_disabled)

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
            status_lbl.configure(text="CRASHED", text_color=COLOR_ERROR)
            # Update the matching dot
            if status_lbl == self.lbl_web_status:
                self._update_status_dot(self.web_dot, COLOR_ERROR)
            elif status_lbl == self.lbl_weight_status:
                self._update_status_dot(self.weight_dot, COLOR_ERROR)

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
        
        # 0. Force Start MySQL
        self.root.after(0, self.log, "Checking MySQL Service...")
        try:
            startupinfo = None
            if STARTUPINFO:
                startupinfo = STARTUPINFO()
                startupinfo.dwFlags |= 0x00000080
            
            # Check if MySQL is running
            query_proc = subprocess.run(["sc.exe", "query", "mysql80"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo)
            if "STATE" in query_proc.stdout and "RUNNING" not in query_proc.stdout:
                self.root.after(0, self.log, "MySQL is stopped. Attempting to force start (may prompt for Administrator)...")
                subprocess.run([
                    "powershell.exe", 
                    "-Command", 
                    "Start-Process cmd -ArgumentList '/c net start mysql80' -Verb RunAs -WindowStyle Hidden"
                ], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo)
                
                self.root.after(0, self.log, "Waiting for MySQL service to start (Please accept the Admin prompt if it appears)...")
                started = False
                for _ in range(30):  # Wait up to 30 seconds
                    chk = subprocess.run(["sc.exe", "query", "mysql80"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo)
                    if "STATE" in chk.stdout and "RUNNING" in chk.stdout:
                        started = True
                        break
                    time.sleep(1)
                
                if started:
                    self.root.after(0, self.log, "MySQL Service started successfully!")
                else:
                    self.root.after(0, self.log, "Warning: MySQL Service did not start within 30 seconds.")
            else:
                self.root.after(0, self.log, "MySQL Service is running.")
        except Exception as e:
            self.root.after(0, self.log, f"Could not force start MySQL: {e}")

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
        self.root.after(0, lambda: (self.lbl_web_status.configure(text="Starting...", text_color=COLOR_WARNING), self._update_status_dot(self.web_dot, COLOR_WARNING)))
        self.web_process = self.run_command([sys.executable, "wsgi.py"], "WEB", self.lbl_web_status)
        
        self.root.after(0, self.log, "Starting Weight Reader Service...")
        self.root.after(0, lambda: (self.lbl_weight_status.configure(text="Starting...", text_color=COLOR_WARNING), self._update_status_dot(self.weight_dot, COLOR_WARNING)))
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
                        self.root.after(0, lambda: (self.lbl_web_status.configure(text="Running", text_color=COLOR_SUCCESS), self._update_status_dot(self.web_dot, COLOR_SUCCESS)) if self.web_process and self.lbl_web_status.cget("text") != "CRASHED" else None)
                        self.root.after(0, lambda: self.set_btn_state(self.btn_browser, tk.NORMAL, COLOR_SUCCESS))
                        self.root.after(0, self.log, f"Web Server is ready and listening on port {port}.")
                except OSError:
                    pass

            if not weight_ready and self.weight_process:
                if time.time() - start_time >= 1.5:
                    if self.weight_process.poll() is None:
                        weight_ready = True
                        self.root.after(0, lambda: (self.lbl_weight_status.configure(text="Running", text_color=COLOR_SUCCESS), self._update_status_dot(self.weight_dot, COLOR_SUCCESS)) if self.weight_process and self.lbl_weight_status.cget("text") != "CRASHED" else None)
                    else:
                        break

            if (web_ready or not self.web_process) and (weight_ready or not self.weight_process):
                break
                
            time.sleep(0.5)
            
        if self.is_running:
            if not web_ready and self.web_process:
                self.root.after(0, lambda: (self.lbl_web_status.configure(text="FAILED", text_color=COLOR_ERROR), self._update_status_dot(self.web_dot, COLOR_ERROR)) if self.lbl_web_status.cget("text") != "CRASHED" else None)
                self.root.after(0, self.log, f"❌ Error: Web Server failed to start or respond on port {port}.")
            if not weight_ready and self.weight_process:
                self.root.after(0, lambda: (self.lbl_weight_status.configure(text="FAILED", text_color=COLOR_ERROR), self._update_status_dot(self.weight_dot, COLOR_ERROR)) if self.weight_process and self.lbl_weight_status.cget("text") != "CRASHED" else None)
                self.root.after(0, self.log, "❌ Error: Weight Reader failed to start.")

    def start_system(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.set_btn_state(self.btn_start, tk.DISABLED, "#ffffff")
        self.set_btn_state(self.btn_stop, tk.NORMAL, COLOR_ERROR)
        self.set_btn_state(self.btn_restart, tk.NORMAL, COLOR_WARNING)
        self.set_btn_state(self.btn_browser, tk.DISABLED, COLOR_SUCCESS)
        
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
            self.lbl_web_status.configure(text="Stopped", text_color=COLOR_ERROR)
            self._update_status_dot(self.web_dot, COLOR_ERROR)
            
        if self.weight_process:
            self.kill_process_tree(self.weight_process)
            self.weight_process = None
            self.lbl_weight_status.configure(text="Stopped", text_color=COLOR_ERROR)
            self._update_status_dot(self.weight_dot, COLOR_ERROR)
            
        self.is_running = False
        
        if not is_restarting:
            self.set_btn_state(self.btn_start, tk.NORMAL, "#ffffff")
            self.set_btn_state(self.btn_stop, tk.DISABLED, COLOR_ERROR)
            self.set_btn_state(self.btn_restart, tk.DISABLED, COLOR_WARNING)
            self.set_btn_state(self.btn_browser, tk.DISABLED, COLOR_SUCCESS)
            self.log("System stopped cleanly.")

    def restart_system(self):
        if not self.is_running:
            return
            
        self.set_btn_state(self.btn_start, tk.DISABLED, "#ffffff")
        self.set_btn_state(self.btn_stop, tk.DISABLED, COLOR_ERROR)
        self.set_btn_state(self.btn_restart, tk.DISABLED, COLOR_WARNING)
        self.set_btn_state(self.btn_browser, tk.DISABLED, COLOR_SUCCESS)
        
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
        
        self.set_btn_state(self.btn_browser, tk.DISABLED, COLOR_SUCCESS)
        self.root.after(1000, lambda: self.set_btn_state(self.btn_browser, tk.NORMAL, COLOR_SUCCESS) if self.is_running and self.web_process and self.web_process.poll() is None else None)
        
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
        if hasattr(self, 'ico_path'):
            dialog.after(200, lambda: dialog.iconbitmap(self.ico_path))
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
        dialog.configure(fg_color=COLOR_BG)
        
        hdr = ctk.CTkFrame(dialog, fg_color=COLOR_HEADER, corner_radius=0, height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="PMPC Data Logger — System is Running", font=ctk.CTkFont(family="Segoe UI", weight="bold", size=13), text_color=COLOR_TEXT).pack(pady=10)
        ctk.CTkFrame(dialog, fg_color="#ffffff", corner_radius=0, height=2).pack(fill=tk.X)
        
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        
        msg_lbl = ctk.CTkLabel(
            content_frame, 
            text="The web server and weight reader services are currently running.\nWhat would you like to do?", 
            justify=tk.LEFT,
            text_color=COLOR_TEXT_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        msg_lbl.pack(pady=(0, 24), anchor="w")
        
        self.dialog_choice = "cancel"
        
        def set_choice(choice):
            self.dialog_choice = choice
            dialog.destroy()
            
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_bg = ctk.CTkButton(btn_frame, text="Background", width=120, height=36, corner_radius=18, fg_color="#ffffff", hover_color="#e5e5e5", text_color="#000000", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=lambda: set_choice("background"))
        btn_bg.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_exit = ctk.CTkButton(btn_frame, text="Shutdown", width=120, height=36, corner_radius=18, fg_color=COLOR_ERROR, hover_color="#dc2626", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=lambda: set_choice("exit"))
        btn_exit.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", width=100, height=36, corner_radius=18, fg_color="#333333", hover_color="#444444", border_width=1, border_color="#555555", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=lambda: set_choice("cancel"))
        btn_cancel.pack(side=tk.RIGHT)
        
        self.root.wait_window(dialog)
        return self.dialog_choice

    def _build_troubleshoot_entries(self):
        """Return the structured troubleshoot data as a list of (category, entries) tuples."""
        return [
            ("SYSTEM STARTUP", [
                ("INFO", "Redis Cache Configuration",
                    "This is NOT an error — this is for your information only.\n\n"
                    "What this means:\n"
                    "The system can optionally use Redis (a fast memory cache) to speed up weight readings.\n"
                    "If Redis is not installed or not running, the system will automatically switch to using\n"
                    "a simple file on disk (current_weight.txt) to store scale readings instead.\n\n"
                    "Do I need to do anything?\n"
                    "  No. The system handles this automatically. Everything will work normally without Redis.\n"
                    "  You will see a message in the logs: '[INFO] Redis unavailable. Using file-based weight fallback system.'\n"
                    "  This is completely safe and expected on most workstations.",
                    "#ffffff"),
                ("ERR-LAUNCH", "Launcher Won't Open / Nothing Happens When Double-Clicking",
                    "What you see:\n"
                    "  You double-click 'PMPC Data Logger.bat' on the Desktop and nothing happens.\n"
                    "  No window appears, no error message, the screen stays the same.\n\n"
                    "Why this happens:\n"
                    "  Python is not installed on this computer, or it is installed but Windows\n"
                    "  cannot find it. The launcher needs Python to run.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Check if Python is installed.\n"
                    "     a. Click the Start button (Windows icon) at the bottom-left of the screen.\n"
                    "     b. Type 'cmd' and press Enter. A black command window will open.\n"
                    "     c. Type this exactly:  python --version\n"
                    "     d. Press Enter.\n"
                    "     e. If you see something like 'Python 3.11.5', Python IS installed. Go to Step 3.\n"
                    "     f. If you see 'is not recognized' or an error, Python is NOT installed. Go to Step 2.\n\n"
                    "  Step 2: Install Python (if Step 1 showed an error).\n"
                    "     a. Open a web browser and go to: https://www.python.org/downloads/\n"
                    "     b. Click the big yellow 'Download Python 3.x.x' button.\n"
                    "     c. Run the downloaded file.\n"
                    "     d. IMPORTANT: On the first screen, check the box that says 'Add Python to PATH'.\n"
                    "     e. Click 'Install Now' and wait for it to finish.\n"
                    "     f. Restart the computer.\n\n"
                    "  Step 3: Check if the launcher library is installed.\n"
                    "     a. Open the command window again (Start → type 'cmd' → Enter).\n"
                    "     b. Type this exactly:  pip install customtkinter\n"
                    "     c. Press Enter and wait for it to finish.\n"
                    "     d. Try double-clicking 'PMPC Data Logger.bat' again.",
                    None),
                ("ERR-INST", "Launcher Opens Then Immediately Closes / Another Instance Running",
                    "What you see:\n"
                    "  You double-click the launcher and the window opens for a split second, then closes.\n"
                    "  OR: The logs show 'Single-instance port bind failed'.\n\n"
                    "Why this happens:\n"
                    "  The launcher is already running in the background (you may have minimized it to the\n"
                    "  tray or clicked 'Background' when closing). Only one copy can run at a time.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Check if the launcher is already running.\n"
                    "     a. Look at the taskbar at the bottom of the screen.\n"
                    "     b. Look for the PMPC Data Logger icon. If you see it, click it to bring it back.\n\n"
                    "  Step 2: If you cannot find it, force-close the old launcher.\n"
                    "     a. Press Ctrl + Shift + Esc on the keyboard. This opens Task Manager.\n"
                    "     b. If Task Manager opens in 'simple' view, click 'More details' at the bottom.\n"
                    "     c. Look in the list for 'pythonw.exe' or 'Python' — there may be more than one.\n"
                    "     d. Click on each 'pythonw.exe' entry and click 'End Task' at the bottom-right.\n"
                    "     e. Close Task Manager.\n"
                    "     f. Double-click 'PMPC Data Logger.bat' again. It should now open normally.",
                    None),
            ]),
            ("DATABASE", [
                ("ERR-DB3306", "Database Connection Timeout",
                    "What you see:\n"
                    "  The Launcher log shows this message in RED:\n"
                    "  '[ERR-DB3306] Database Connection Timeout.'\n"
                    "  'Details: plcdata initialization exceeded 15s timeout.'\n"
                    "  The system stops and does not start the web server.\n\n"
                    "Why this happens:\n"
                    "  The MySQL database service on this computer is not running. The system\n"
                    "  tried to connect for 15 seconds and gave up.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Open the Windows Services panel.\n"
                    "     a. Press the Windows key + R on the keyboard at the same time.\n"
                    "        A small 'Run' dialog box will appear at the bottom-left.\n"
                    "     b. Type this exactly:  services.msc\n"
                    "     c. Press Enter. A window titled 'Services' will open showing a long list.\n\n"
                    "  Step 2: Find and start MySQL.\n"
                    "     a. Scroll down the list slowly. Look for a row that says 'MySQL80' or 'MySQL'.\n"
                    "     b. Look at the 'Status' column for that row:\n"
                    "        — If it says 'Running', MySQL is already on. Skip to Step 4.\n"
                    "        — If it is blank (empty), MySQL is stopped. Continue to Step 2c.\n"
                    "     c. Right-click on the MySQL row.\n"
                    "     d. Click 'Start' from the menu that appears.\n"
                    "     e. Wait a few seconds. The Status column should change to 'Running'.\n\n"
                    "  Step 3: Make MySQL start automatically when the computer turns on.\n"
                    "     a. Right-click on the MySQL row again.\n"
                    "     b. Click 'Properties'.\n"
                    "     c. Find the 'Startup type' dropdown and change it to 'Automatic'.\n"
                    "     d. Click 'OK'.\n\n"
                    "  Step 4: Check if a Firewall is blocking the connection.\n"
                    "     a. Click Start, type 'Windows Firewall' and open it.\n"
                    "     b. Click 'Allow an app or feature through Windows Firewall'.\n"
                    "     c. Look for 'MySQL' or 'mysqld' in the list. Make sure it is checked.\n"
                    "     d. If it is not in the list, click 'Allow another app' → Browse to\n"
                    "        C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\mysqld.exe → Add.\n\n"
                    "  Step 5: Verify the database port.\n"
                    "     a. Open the .env file in the project folder (use Notepad).\n"
                    "     b. Look for the line: DB_PORT=3306\n"
                    "     c. Make sure this number matches your MySQL installation.\n"
                    "        (The default MySQL port is 3306. Do not change this unless you\n"
                    "        specifically configured MySQL to use a different port.)\n\n"
                    "  Step 6: Try starting the PMPC system again.\n"
                    "     Click the '▶ Start System' button in the Launcher.",
                    None),
                ("ERR-DBCRED", "Database Authentication Failed (Access Denied)",
                    "What you see:\n"
                    "  The Launcher log shows an error like:\n"
                    "  'Error creating database: (1045, \"Access denied for user root@127.0.0.1\")'\n"
                    "  The system stops and does not start.\n\n"
                    "Why this happens:\n"
                    "  The database username or password saved in the .env file does not match\n"
                    "  the actual MySQL username and password on this computer.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Open the .env file.\n"
                    "     a. Open File Explorer (the yellow folder icon on the taskbar).\n"
                    "     b. Navigate to the project folder: Panasonic Web\n"
                    "     c. Find the file named '.env' (it may show as just 'env' if file extensions are hidden).\n"
                    "     d. Right-click the file → 'Open with' → 'Notepad'.\n\n"
                    "  Step 2: Check the database credentials.\n"
                    "     a. Look for these two lines:\n"
                    "        DB_USER=root\n"
                    "        DB_PASSWORD=db_MIndS2026\n"
                    "     b. Make sure the username and password here are EXACTLY the same as what\n"
                    "        you use to log into MySQL Workbench.\n\n"
                    "  Step 3: Test the credentials in MySQL Workbench.\n"
                    "     a. Open MySQL Workbench from the Start menu.\n"
                    "     b. Click your local connection (usually '127.0.0.1' or 'localhost').\n"
                    "     c. Enter the password from the .env file.\n"
                    "     d. If it connects successfully, the credentials are correct — the problem\n"
                    "        may be a copy/paste error. Re-type the password in the .env file carefully.\n"
                    "     e. If it says 'Access denied', your MySQL password is different. You need to\n"
                    "        update the DB_PASSWORD line in the .env file to match.\n\n"
                    "  Step 4: Save the .env file and restart the PMPC system.",
                    None),
                ("ERR-NODB", "Database 'plcdata' Does Not Exist / Could Not Be Created",
                    "What you see:\n"
                    "  The Launcher log shows an error mentioning 'Unknown database plcdata'\n"
                    "  or 'dont see the plcdata database'. The web server crashes immediately on startup.\n\n"
                    "Why this happens:\n"
                    "  MySQL is running, but the specific database named 'plcdata' has not been created\n"
                    "  yet, and the automatic creation script failed (possibly due to permissions).\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Open MySQL Workbench.\n"
                    "     a. Click Start, type 'MySQL Workbench' and open it.\n"
                    "     b. Click your local connection and log in with your password.\n\n"
                    "  Step 2: Create the database manually.\n"
                    "     a. In the query window (the big white text area), type this exactly:\n"
                    "        CREATE DATABASE plcdata;\n"
                    "     b. Click the lightning bolt icon (⚡) above the query window to run it.\n"
                    "     c. In the output panel at the bottom, look for a green checkmark indicating success.\n\n"
                    "  Step 3: Run the initial schema setup.\n"
                    "     a. In the Launcher, click the '▶ Start System' button.\n"
                    "     b. The system should now connect to the new 'plcdata' database and create\n"
                    "        all the necessary tables automatically.\n\n"
                    "  Step 4: If it still fails, check the .env file.\n"
                    "     a. Make sure DB_NAME=plcdata is set correctly in the .env file.",
                    None),
                ("ERR-DBMIGR", "Database Schema / Missing Column Error",
                    "What you see:\n"
                    "  The Launcher log shows an error like:\n"
                    "  'OperationalError: (1054, \"Unknown column xxx in field list\")'\n"
                    "  OR: 'ProgrammingError: (1146, \"Table plcdata.xxx doesn't exist\")'\n"
                    "  The web server crashes or pages show 500 errors.\n\n"
                    "Why this happens:\n"
                    "  The system code was updated (new version), but the database tables still\n"
                    "  have the old structure. New columns or tables need to be added.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Stop the PMPC system.\n"
                    "     Click the '■ Stop System' button in the Launcher.\n\n"
                    "  Step 2: Run the database update script.\n"
                    "     a. Click Start, type 'cmd', press Enter to open the command window.\n"
                    "     b. Type this command to go to the project folder:\n"
                    "        cd C:\\Users\\DELL\\Desktop\\Panasonic Project\\Panasonic Web\n"
                    "     c. Press Enter.\n"
                    "     d. Type this command to update the database:\n"
                    "        python tools/alter_db.py\n"
                    "     e. Press Enter and wait. You should see messages like 'Column added' or\n"
                    "        'Column already exists' (both are fine).\n\n"
                    "  Step 3: Start the PMPC system again.\n"
                    "     Click '▶ Start System' in the Launcher.\n\n"
                    "  If the error persists, contact the system developer with a screenshot of the error.",
                    None),
            ]),
            ("WEB SERVER", [
                ("ERR-WEB8080", "Web Server Failed to Start (Port 8080 In Use)",
                    "What you see:\n"
                    "  The Launcher shows 'Web Server:' status as 'FAILED' in red.\n"
                    "  The log shows: 'Error: Web Server failed to start or respond on port 8080.'\n"
                    "  Clicking 'Open Web App' does nothing or shows a blank page.\n\n"
                    "Why this happens:\n"
                    "  Another program on this computer is already using port 8080. Only one program\n"
                    "  can use a port at a time. Common culprits: a previous PMPC instance that didn't\n"
                    "  shut down, or another web application.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Find what is using port 8080.\n"
                    "     a. Click Start, type 'cmd', RIGHT-click 'Command Prompt', choose 'Run as administrator'.\n"
                    "     b. Type this exactly:  netstat -ano | findstr :8080\n"
                    "     c. Press Enter.\n"
                    "     d. You will see output like:\n"
                    "        TCP  0.0.0.0:8080  0.0.0.0:0  LISTENING  12345\n"
                    "        The number at the end (12345) is the Process ID (PID).\n\n"
                    "  Step 2: Close the program that is using port 8080.\n"
                    "     a. In the same command window, type:  taskkill /PID 12345 /F\n"
                    "        (Replace 12345 with the actual PID number from Step 1d.)\n"
                    "     b. Press Enter. You should see 'SUCCESS: The process ... has been terminated.'\n\n"
                    "  Step 3: Try starting the PMPC system again.\n"
                    "     Click '▶ Start System' in the Launcher.\n\n"
                    "  Alternative: If you cannot close the other program, you can change the PMPC port:\n"
                    "     a. Open the .env file in the project folder with Notepad.\n"
                    "     b. Find the line: SERVER_PORT=8080\n"
                    "     c. Change 8080 to another number, such as: SERVER_PORT=9090\n"
                    "     d. Save the file and restart the PMPC system.",
                    None),
                ("ERR-APP500", "Web Application Error (500 Internal Server Error)",
                    "What you see:\n"
                    "  The web browser shows a page that says '500 — Internal Server Error'.\n"
                    "  OR: Some buttons or pages on the web app stop working.\n"
                    "  The Launcher log may show red error messages with 'Traceback' or 'Error'.\n\n"
                    "Why this happens:\n"
                    "  The web application code encountered a bug — for example, a missing file,\n"
                    "  a typo in the code, or the database returned unexpected data.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Read the error message in the Launcher.\n"
                    "     a. Look at the 'System Logs' area in the Launcher window.\n"
                    "     b. Scroll UP until you find text in RED that mentions 'Traceback'.\n"
                    "     c. The LAST line of the Traceback is the most important — it tells you\n"
                    "        exactly what went wrong. For example:\n"
                    "        'KeyError: model_number'  means a value called 'model_number' was expected but missing.\n"
                    "        'FileNotFoundError'  means the system is trying to open a file that doesn't exist.\n"
                    "        'TypeError'  means the code received the wrong type of data.\n\n"
                    "  Step 2: Check the browser for more details.\n"
                    "     a. In the web browser, press F12 on the keyboard. The Developer Tools panel will open.\n"
                    "     b. Click the 'Console' tab at the top of this panel.\n"
                    "     c. Look for any red error messages. These give extra clues.\n"
                    "     d. You can also click the 'Network' tab, then try the action again.\n"
                    "        Failed requests appear in red — click one to see the error response.\n\n"
                    "  Step 3: Try restarting the system first.\n"
                    "     a. Click '↻ Restart' in the Launcher.\n"
                    "     b. Wait for the system to fully start.\n"
                    "     c. Try the action again in the browser.\n\n"
                    "  Step 4: If the error persists after restart.\n"
                    "     a. Take a screenshot of the full Launcher log (scroll to show the red error).\n"
                    "     b. Take a screenshot of the browser error (from Step 2).\n"
                    "     c. Send both screenshots to the system developer for assistance.",
                    None),
                ("ERR-SECRET", "SECRET_KEY Not Set (System Refuses to Start)",
                    "What you see:\n"
                    "  The Launcher log shows:\n"
                    "  'RuntimeError: SECRET_KEY environment variable is not set.'\n"
                    "  The web server does not start at all.\n\n"
                    "Why this happens:\n"
                    "  The .env file in the project folder is missing the SECRET_KEY line.\n"
                    "  This key is used to protect user login sessions and form security.\n"
                    "  Without it, the system refuses to start for safety.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Open the .env file.\n"
                    "     a. Open File Explorer and navigate to the project folder: Panasonic Web\n"
                    "     b. Find the file named '.env'.\n"
                    "     c. Right-click → 'Open with' → 'Notepad'.\n\n"
                    "  Step 2: Check if SECRET_KEY exists.\n"
                    "     a. Look for a line that starts with: SECRET_KEY=\n"
                    "     b. If the line exists and has a long string of letters and numbers after the =,\n"
                    "        the file is correct. The problem may be elsewhere — contact the developer.\n"
                    "     c. If the line is missing or blank, continue to Step 3.\n\n"
                    "  Step 3: Generate and add a new SECRET_KEY.\n"
                    "     a. Open Command Prompt (Start → type 'cmd' → Enter).\n"
                    "     b. Type this exactly:\n"
                    "        python -c \"import secrets; print(secrets.token_hex(32))\"\n"
                    "     c. Press Enter. A long string of random letters and numbers will appear.\n"
                    "        Example: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2\n"
                    "     d. Select and copy that entire string (right-click → Copy).\n"
                    "     e. Go back to the .env file in Notepad.\n"
                    "     f. Add a new line at the bottom: SECRET_KEY=paste_the_string_here\n"
                    "        (Replace 'paste_the_string_here' with the string you copied.)\n"
                    "     g. Save the file (Ctrl + S).\n\n"
                    "  Step 4: Restart the PMPC system.",
                    None),
            ]),
            ("HARDWARE / WEIGHING SCALE", [

                ("ERR-CONNECTION", "Network / Ethernet Communication Failure (Current System)",
                    "What you see:\n"
                    "  The Launcher log shows in red:\n"
                    "  '[ERR-CONNECTION] Hardware Communication Failure.'\n"
                    "  Followed by: 'Details: [WinError 10060] A connection attempt failed' or 'timed out'.\n"
                    "  The .env file has SERIAL_PORT set to a network address (e.g., tcp://192.168.0.11:8501).\n\n"
                    "Why this happens:\n"
                    "  The Keyence PLC is connected via Ethernet (network cable), not a serial cable.\n"
                    "  The PC cannot reach the PLC on the network.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Check the Ethernet cable.\n"
                    "     a. Find the network cable (Ethernet cable, usually a blue or gray cable)\n"
                    "        going from the PC to the PLC.\n"
                    "     b. Make sure both ends are firmly plugged in (you should hear/feel a click).\n"
                    "     c. Check for any damage to the cable.\n\n"
                    "  Step 2: Check if the PLC is powered on.\n"
                    "     a. Look at the Keyence PLC unit. It should have status lights that are lit.\n"
                    "     b. If all lights are off, the PLC is not receiving power. Check its power supply.\n\n"
                    "  Step 3: Ping the PLC to test the network connection.\n"
                    "     a. Open Command Prompt (Start → type 'cmd' → Enter).\n"
                    "     b. Type this exactly:  ping 192.168.0.11\n"
                    "     c. Press Enter.\n"
                    "     d. If you see 'Reply from 192.168.0.11: bytes=32 time<1ms' — the network is OK.\n"
                    "        The problem may be the PLC port or settings. Go to Step 5.\n"
                    "     e. If you see 'Request timed out' or 'Destination host unreachable' —\n"
                    "        the PC cannot reach the PLC on the network. Go to Step 4.\n\n"
                    "  Step 4: Check the PC's network settings (if ping failed).\n"
                    "     a. The PC must be on the same network as the PLC.\n"
                    "     b. Press Windows + R, type 'ncpa.cpl', press Enter.\n"
                    "     c. Find the Ethernet adapter connected to the PLC. Right-click → Properties.\n"
                    "     d. Select 'Internet Protocol Version 4 (TCP/IPv4)' → Properties.\n"
                    "     e. The PC IP must be set to the exact dedicated address for this server:\n"
                    "        PC IP Address: 192.168.0.20\n"
                    "        Subnet mask: 255.255.255.0\n"
                    "     f. Click OK, then try pinging again.\n\n"
                    "  Step 5: Verify the PLC settings in the .env file.\n"
                    "     a. Open the .env file with Notepad.\n"
                    "     b. Check these lines:\n"
                    "        SERIAL_PORT=tcp://192.168.0.11:8501  (should match the PLC's IP and port)\n"
                    "        PLC_WEIGHT_REGISTER=DM1004  (the DM register that holds the weight value)\n"
                    "        PLC_WEIGHT_FORMAT=float  (how the PLC sends the weight: 'float', 'string', or 's32')\n"
                    "     c. If any of these are wrong, correct them and save the file.\n\n"
                    "  Step 6: Restart the PMPC system.",
                    None),
                ("ERR-SCALE0", "Scale Always Shows 0.000 kg or Unstable / Jumping Weight",
                    "What you see:\n"
                    "  The weight display on the web app always shows 0.000 kg even when there\n"
                    "  is a unit on the scale. OR: The weight value is wildly jumping up and down\n"
                    "  (e.g., 0.000, 150.000, 3.200, 0.000) and never stabilizes.\n\n"
                    "Why this happens:\n"
                    "  The cable is connected and the Weight Reader is running, but the data it\n"
                    "  receives from the scale is incorrect. This could be caused by:\n"
                    "  — The scale needs recalibration.\n"
                    "  — The data format setting (PLC_WEIGHT_FORMAT) does not match the PLC output.\n"
                    "  — Electrical interference on the RS-232 line (unshielded cable near power lines).\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Check the physical scale indicator.\n"
                    "     a. Look at the scale indicator display (the physical device, not the computer).\n"
                    "     b. Place a known weight on the scale (e.g., a 10 kg calibration weight).\n"
                    "     c. Does the indicator display show the correct weight?\n"
                    "        — If YES: The scale is fine, the problem is the data format. Go to Step 2.\n"
                    "        — If NO: The scale needs calibration. Contact the scale maintenance team.\n\n"
                    "  Step 2: Check the data format setting (if using Keyence PLC).\n"
                    "     a. Open the .env file with Notepad.\n"
                    "     b. Find the line: PLC_WEIGHT_FORMAT=float\n"
                    "     c. This setting must match how the Keyence PLC stores the weight value:\n"
                    "        — 'float' → PLC stores weight as a 32-bit floating-point number in 2 DM registers.\n"
                    "        — 'string' → PLC stores weight as ASCII text characters across 10 DM registers.\n"
                    "        — 's32' → PLC stores weight as a signed 32-bit integer in 1 DM.D register.\n"
                    "     d. If you are not sure which format your PLC uses, check the PLC program in\n"
                    "        Keyence KV Studio or ask the PLC programmer.\n"
                    "     e. Change the value if needed, save the file, and restart the system.\n\n"
                    "  Step 3: Check for electrical interference (for RS-232 serial connections).\n"
                    "     a. Make sure the RS-232 cable is a SHIELDED cable.\n"
                    "     b. Keep the cable away from power lines, motors, and other electrical equipment.\n"
                    "     c. If the cable runs parallel to a power cable, separate them by at least 30 cm.\n\n"
                    "  Step 4: Check the weight register address.\n"
                    "     a. In the .env file, check: PLC_WEIGHT_REGISTER=DM1004\n"
                    "     b. This must be the exact DM register in the PLC that contains the weight value.\n"
                    "     c. Open the PLC program in KV Studio to verify the correct register.",
                    None),
            ]),
            ("WEB APPLICATION", [
                ("ERR-LOGIN", "Cannot Login / Account Locked Out",
                    "What you see:\n"
                    "  The login page shows a red message:\n"
                    "  'Too many failed attempts. Try again in Xm Xs.'\n"
                    "  You cannot log in even if you type the correct password.\n\n"
                    "Why this happens:\n"
                    "  For security, the system locks out any user who enters the wrong password\n"
                    "  5 times in a row. The lockout lasts for 5 minutes. This prevents unauthorized\n"
                    "  people from guessing passwords.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Option A: Wait for the lockout to expire.\n"
                    "     a. Wait the amount of time shown in the message (up to 5 minutes).\n"
                    "     b. After the time expires, try logging in again with the CORRECT password.\n"
                    "     c. Type your password carefully — another 5 wrong attempts will lock you out again.\n\n"
                    "  Option B: Restart the PMPC system to clear the lockout immediately.\n"
                    "     a. Go to the Launcher window.\n"
                    "     b. Click '↻ Restart'.\n"
                    "     c. Wait for the system to fully start (Web Server shows 'Running' in green).\n"
                    "     d. Try logging in again.\n"
                    "     Note: This clears ALL lockouts, so use this only if you are certain of your password.\n\n"
                    "  Option C: You forgot your password.\n"
                    "     a. Contact the Super Administrator of the PMPC system.\n"
                    "     b. Ask them to reset your password from the Admin panel → Account Management.\n"
                    "     c. After reset, your temporary password will be 'pmpc1234'.\n"
                    "     d. Log in with the temporary password and change it when prompted.",
                    None),
                ("ERR-CORS", "Weight Display Not Updating / WebSocket Connection Refused",
                    "What you see:\n"
                    "  The weight reading on the web app is stuck and does not update automatically.\n"
                    "  OR: The browser console (F12) shows red errors like:\n"
                    "  'Access-Control-Allow-Origin' or 'CORS policy' or 'WebSocket connection failed'.\n\n"
                    "Why this happens:\n"
                    "  You are accessing the web app from a different address than what is configured.\n"
                    "  For example, the system is configured for http://127.0.0.1:8080, but you are\n"
                    "  accessing it from http://192.168.1.100:8080 on another computer.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Find out what URL you are using.\n"
                    "     a. Look at the address bar in your web browser.\n"
                    "     b. Note the full address. For example: http://192.168.1.100:8080\n\n"
                    "  Step 2: Update the CORS setting to match.\n"
                    "     a. On the SERVER computer (where the Launcher is running), open the .env file.\n"
                    "     b. Find the line: CORS_ALLOWED_ORIGINS=http://127.0.0.1:8080\n"
                    "     c. Change it to match the address you noted in Step 1.\n"
                    "        For example: CORS_ALLOWED_ORIGINS=http://192.168.1.100:8080\n"
                    "     d. IMPORTANT: Do NOT add a trailing slash (/) at the end.\n"
                    "        Correct:   http://192.168.1.100:8080\n"
                    "        Wrong:     http://192.168.1.100:8080/\n"
                    "     e. Save the file.\n\n"
                    "  Step 3: Restart the PMPC system.\n"
                    "     a. In the Launcher, click '↻ Restart'.\n"
                    "     b. Wait for the system to fully start.\n"
                    "     c. Refresh the web page in your browser (press F5 or Ctrl+R).\n"
                    "     d. The weight display should now update automatically.",
                    None),
                ("ERR-BACKUP", "Database Backup Failed (mysqldump Not Found)",
                    "What you see:\n"
                    "  When running the backup script, the command window shows:\n"
                    "  'Error during backup: [WinError 2] The system cannot find the file specified'\n"
                    "  OR: 'mysqldump is not recognized as an internal or external command'.\n\n"
                    "Why this happens:\n"
                    "  The backup script uses a program called 'mysqldump.exe' to export the database.\n"
                    "  This program comes with MySQL, but Windows cannot find it because the MySQL\n"
                    "  folder is not in the system PATH.\n\n"
                    "How to fix it — follow these steps one by one:\n\n"
                    "  Step 1: Find where mysqldump is installed.\n"
                    "     a. Open File Explorer.\n"
                    "     b. Navigate to: C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin\\\n"
                    "     c. Look for a file named 'mysqldump.exe'.\n"
                    "     d. If you find it, note the full folder path (e.g., C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin).\n"
                    "     e. If the folder doesn't exist, look in:\n"
                    "        C:\\Program Files (x86)\\MySQL\\  or  C:\\MySQL\\  or similar.\n\n"
                    "  Step 2: Add MySQL to the system PATH.\n"
                    "     a. Right-click the Start button → click 'System'.\n"
                    "     b. On the right side, click 'Advanced system settings'.\n"
                    "     c. Click the 'Environment Variables' button at the bottom.\n"
                    "     d. In the BOTTOM section ('System variables'), find the row called 'Path'.\n"
                    "     e. Click on 'Path', then click 'Edit'.\n"
                    "     f. Click 'New' and paste the folder path from Step 1d\n"
                    "        (e.g., C:\\Program Files\\MySQL\\MySQL Server 8.0\\bin).\n"
                    "     g. Click 'OK' on all dialog boxes to save.\n\n"
                    "  Step 3: Test the backup.\n"
                    "     a. Close and re-open Command Prompt.\n"
                    "     b. Type: mysqldump --version\n"
                    "     c. If it shows a version number, the fix worked.\n"
                    "     d. Try running the backup script again:\n"
                    "        python tools/backup_db.py",
                    None),
            ]),
        ]

    def open_troubleshoot_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        if hasattr(self, 'ico_path'):
            dialog.after(200, lambda: dialog.iconbitmap(self.ico_path))
        dialog.withdraw()  # Hide immediately to prevent flickering
        dialog.title("PMPC System — Troubleshooting Guide")
        
        dialog_w = 820
        dialog_h = 720
        dialog.geometry(f"{dialog_w}x{dialog_h}")
        dialog.update_idletasks()
        dialog.after(50, lambda: force_center_window(dialog))
        dialog.after(200, lambda: force_center_window(dialog))
        dialog.resizable(False, False)
        


        dialog.transient(self.root)
        
        try:
            import os
            import ctypes
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(base_dir, 'docs', 'assets', 'panasonic_logo.ico')
            dialog.iconbitmap(ico_path)
            
            # Windows High-DPI Dialog Fix
            def set_dialog_icon():
                try:
                    dialog.iconbitmap(ico_path)
                    windll = getattr(ctypes, 'windll', None)
                    if windll:
                        HWND = windll.user32.GetParent(dialog.winfo_id())
                        hicon = windll.user32.LoadImageW(0, ico_path, 1, 64, 64, 0x00000010)
                        if hicon:
                            windll.user32.SendMessageW(HWND, 0x0080, 1, hicon)
                            windll.user32.SendMessageW(HWND, 0x0080, 0, hicon)
                except Exception:
                    pass
            
            dialog.after(250, set_dialog_icon)
        except Exception:
            pass

        dialog.configure(fg_color=COLOR_BG)

        # ── Header ───────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(dialog, fg_color=COLOR_HEADER, corner_radius=0, height=50)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Troubleshooting Guide", font=ctk.CTkFont(family="Segoe UI", weight="bold", size=16), text_color=COLOR_TEXT).pack(pady=12)
        ctk.CTkFrame(dialog, fg_color="#ffffff", corner_radius=0, height=2).pack(fill=tk.X)

        # ── Search Bar ───────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        search_frame.pack(fill=tk.X, padx=20, pady=(14, 6))

        search_var = tk.StringVar()
        
        search_box = ctk.CTkFrame(search_frame, fg_color="#333333", border_color="#555555", border_width=1, corner_radius=8, height=38)
        search_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_box.pack_propagate(False)

        try:
            from PIL import Image
            import os
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'assets', 'search_icon.png')
            search_img = ctk.CTkImage(light_image=Image.open(icon_path), size=(20, 20))
            ctk.CTkLabel(search_box, image=search_img, text="").pack(side=tk.LEFT, padx=(12, 4))
        except Exception:
            pass

        search_entry = ctk.CTkEntry(
            search_box, textvariable=search_var,
            placeholder_text="Search by Error Code (e.g., ERR-LAUNCH), Title, or Content...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent", border_width=0,
            text_color="#ffffff", placeholder_text_color="#bbbbbb"
        )
        search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        search_entry.bind("<Return>", lambda e: on_search())

        self.btn_search = ctk.CTkButton(
            search_frame, text="Search", width=100, height=38, corner_radius=8,
            fg_color="#333333", hover_color="#444444",
            border_width=1, border_color="#555555",
            text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", weight="bold")
        )
        self.btn_search.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_clear = ctk.CTkButton(
            search_frame, text="Clear", width=80, height=38, corner_radius=8,
            fg_color="transparent", hover_color="#333333",
            border_width=1, border_color="#555555",
            text_color="#cccccc", font=ctk.CTkFont(family="Segoe UI", weight="bold")
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(8, 0))

        # ── Scrollable Content ───────────────────────────────────────────────
        sf = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        sf.pack(fill=tk.BOTH, expand=True, padx=20, pady=(6, 10))

        # Build all entries
        entries_data = self._build_troubleshoot_entries()

        # Track all accordion items for search filtering
        all_items = []       # list of (code, title, body, header_frame, body_frame, category_frame, category_sep)
        category_widgets = []  # list of (category_label_frame, separator, entries_in_category)

        for cat_name, entries in entries_data:
            # Category separator
            cat_sep = ctk.CTkFrame(sf, fg_color=COLOR_BORDER, height=1)
            cat_sep.pack(fill=tk.X, pady=(16, 6))
            cat_label_frame = ctk.CTkFrame(sf, fg_color="transparent")
            cat_label_frame.pack(fill=tk.X)
            ctk.CTkLabel(cat_label_frame, text=cat_name, font=ctk.CTkFont(family="Segoe UI", weight="bold", size=13), text_color="#cccccc").pack(anchor="w", pady=(0, 4))

            cat_entry_items = []

            for code, title, body, code_color in entries:
                if code_color is None:
                    code_color = "#ffffff"  # default white

                # ── Accordion Item ──────────────────────────────────────────
                item_frame = ctk.CTkFrame(sf, fg_color="transparent")
                item_frame.pack(fill=tk.X, pady=(2, 0), padx=(0, 16))

                # Header row (clickable)
                header_btn = ctk.CTkFrame(item_frame, fg_color=COLOR_SURFACE, corner_radius=8, border_width=1, border_color=COLOR_BORDER, cursor="hand2")
                header_btn.pack(fill=tk.X)

                header_inner = ctk.CTkFrame(header_btn, fg_color="transparent")
                header_inner.pack(fill=tk.X, padx=12, pady=10)

                # Toggle arrow
                arrow_lbl = ctk.CTkLabel(header_inner, text="▶", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_DIM, width=16)
                arrow_lbl.pack(side=tk.LEFT, padx=(0, 8))

                # Error code badge
                code_badge = ctk.CTkFrame(header_inner, fg_color=code_color, corner_radius=4)
                code_badge.pack(side=tk.LEFT, padx=(0, 10))
                ctk.CTkLabel(code_badge, text=f" {code} ", font=ctk.CTkFont(family="Consolas", weight="bold", size=11), text_color="#000000" if code_color == "#ffffff" else "#ffffff").pack(padx=4, pady=1)

                # Title
                title_lbl = ctk.CTkLabel(header_inner, text=title, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=COLOR_TEXT, anchor="w")
                title_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # Body content (initially hidden)
                body_frame = ctk.CTkFrame(item_frame, fg_color=COLOR_SURFACE, corner_radius=0, border_width=0)
                # body_frame is NOT packed initially — collapsed by default

                body_inner = ctk.CTkFrame(body_frame, fg_color="transparent")
                body_inner.pack(fill=tk.X, padx=16, pady=(4, 14))
                
                # Calculate approximate height (approx 16 pixels per line for size 12 font)
                lines_list = body.split('\n')
                lines_count = len(lines_list) + sum(len(line) // 95 for line in lines_list)
                font_size = 12
                box_height = (lines_count * 16) + 16
                
                tb = ctk.CTkTextbox(body_inner, fg_color="transparent", text_color="#e2e8f0", font=ctk.CTkFont(family="Segoe UI", size=font_size), wrap="word", height=box_height)
                tb.pack(fill=tk.X, expand=True)
                tb.insert("1.0", body)
                try:
                    tb._textbox.tag_config("highlight", background="#fef08a", foreground="#000000")
                except Exception:
                    pass
                tb.configure(state="disabled")

                # Track expanded state
                is_expanded = {"value": False}

                def make_toggle(arrow=arrow_lbl, bframe=body_frame, expanded=is_expanded, hdr=header_btn):
                    def toggle(event=None):
                        if expanded["value"]:
                            bframe.pack_forget()
                            arrow.configure(text="▶")
                            hdr.configure(border_color=COLOR_BORDER)
                            expanded["value"] = False
                        else:
                            bframe.pack(fill=tk.X, after=hdr)
                            arrow.configure(text="▼")
                            hdr.configure(border_color="#707070")
                            expanded["value"] = True
                    return toggle

                toggle_fn = make_toggle()
                header_btn.bind("<Button-1>", toggle_fn)
                # Make all children of header also clickable
                for child in header_inner.winfo_children():
                    child.bind("<Button-1>", toggle_fn)
                    # And children of children (e.g., code badge label)
                    try:
                        for grandchild in child.winfo_children():
                            grandchild.bind("<Button-1>", toggle_fn)
                    except Exception:
                        pass

                all_items.append((code, title, body, item_frame, body_frame, is_expanded, arrow_lbl, header_btn, tb))
                cat_entry_items.append((code, title, body, item_frame))

            category_widgets.append((cat_label_frame, cat_sep, cat_entry_items))

        # ── No Results Frame ─────────────────────────────────────────────────
        no_results_frame = ctk.CTkFrame(sf, fg_color="transparent")
        lbl_no_results = ctk.CTkLabel(no_results_frame, text="", font=ctk.CTkFont(family="Segoe UI", weight="bold", size=14), text_color=COLOR_ERROR)
        lbl_no_results.pack(pady=(20, 5))
        lbl_suggestions = ctk.CTkLabel(no_results_frame, text="Suggestions:\n• Check your spelling.\n• Try searching for key terms like 'Network', 'Database', or 'Scale'.\n• Use the exact error code (e.g. ERR-CONNECTION).", justify=tk.CENTER, font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#cccccc")
        lbl_suggestions.pack(pady=(0, 20))
        

        # ── Footer Tip ───────────────────────────────────────────────────────
        footer_frame = ctk.CTkFrame(sf, fg_color=COLOR_SURFACE, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
        footer_frame.pack(fill=tk.X, pady=(20, 8), padx=2)
        ctk.CTkLabel(footer_frame, text="💡 General Tip", font=ctk.CTkFont(family="Segoe UI", weight="bold", size=12), text_color="#ffffff").pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(footer_frame, text=(
            "If none of the above solutions fix your problem, take a screenshot of the\n"
            "Launcher log (showing the error in red) and send it to info@mechatronicsindustrial.com.\n"
            "Include the exact time the error occurred and what you were doing when it happened."
        ), justify=tk.LEFT, text_color="#cccccc", wraplength=700, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(2, 10))

        # ── Search Filter Logic ──────────────────────────────────────────────
        def on_search(*args):
            query = search_var.get().lower().strip()

            # 1. Hide the footer and no-results frame
            footer_frame.pack_forget()
            no_results_frame.pack_forget()

            any_found = False

            # 2. Iterate through categories and items in correct visual order
            for cat_label_frame, cat_sep, cat_entries in category_widgets:
                cat_sep.pack_forget()
                cat_label_frame.pack_forget()
                
                # Check if this category has any matches
                has_visible = False
                for code, title, body, item_frame in cat_entries:
                    item_frame.pack_forget()  # Temporarily hide all items
                    searchable = f"{code} {title} {body}".lower()
                    if not query or query in searchable:
                        has_visible = True
                        any_found = True
                        
                # Pack category headers FIRST if visible
                if has_visible:
                    cat_sep.pack(fill=tk.X, pady=(16, 6))
                    cat_label_frame.pack(fill=tk.X)
                    
                    # Pack matching items SECOND (below their category header)
                    for code, title, body, item_frame in cat_entries:
                        searchable = f"{code} {title} {body}".lower()
                        if not query or query in searchable:
                            item_frame.pack(fill=tk.X, pady=(2, 0), padx=(0, 16))

            # 3. Handle search highlighting and collapse hidden items
            for code, title, body, item_frame, body_frame, is_expanded, arrow_lbl, header_btn, tb in all_items:
                searchable = f"{code} {title} {body}".lower()
                
                tb.configure(state="normal")
                try:
                    tb._textbox.tag_remove("highlight", "1.0", "end")
                    if query:
                        start_idx = "1.0"
                        while True:
                            pos = tb._textbox.search(query, start_idx, nocase=True, stopindex="end")
                            if not pos:
                                break
                            end_pos = f"{pos}+{len(query)}c"
                            tb._textbox.tag_add("highlight", pos, end_pos)
                            start_idx = end_pos
                except Exception:
                    pass
                tb.configure(state="disabled")
                
                if query and query not in searchable:
                    if is_expanded["value"]:
                        body_frame.pack_forget()
                        arrow_lbl.configure(text="▶")
                        header_btn.configure(border_color=COLOR_BORDER)
                        is_expanded["value"] = False
                elif query and query in searchable:
                    if not is_expanded["value"]:
                        body_frame.pack(fill=tk.X, after=header_btn)
                        arrow_lbl.configure(text="▼")
                        header_btn.configure(border_color="#707070")
                        is_expanded["value"] = True
                elif not query:
                    if is_expanded["value"]:
                        body_frame.pack_forget()
                        arrow_lbl.configure(text="▶")
                        header_btn.configure(border_color=COLOR_BORDER)
                        is_expanded["value"] = False
            
            # 4. If nothing was found, show the No Results message
            if not any_found and query:
                lbl_no_results.configure(text=f'No results found for "{query}"')
                no_results_frame.pack(fill=tk.X, pady=(20, 10))

            # 5. Repack the footer LAST so it is always at the absolute bottom
            footer_frame.pack(fill=tk.X, pady=(20, 8), padx=2)

        self.btn_search.configure(command=on_search)

        def on_clear():
            search_var.set("")
            on_search()
            search_entry.focus()
            
        self.btn_clear.configure(command=on_clear)

        # ── Close Button ─────────────────────────────────────────────────────
        btn_close = ctk.CTkButton(
            dialog, text="Close", width=140, height=38, corner_radius=19,
            fg_color="#333333", hover_color="#444444",
            border_width=1, border_color="#555555", anchor="center",
            text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", weight="bold"),
            command=dialog.destroy
        )
        btn_close.pack(pady=(4, 14))

        # Show window smoothly after it's fully built
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.grab_set()

    def show_background_info_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        if hasattr(self, 'ico_path'):
            dialog.after(200, lambda: dialog.iconbitmap(self.ico_path))
        dialog.title("System Running in Background")
        dialog.geometry("480x200")
        dialog.resizable(False, False)
        
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        dialog_w = 480
        dialog_h = 200
        
        x = main_x + (main_w - dialog_w) // 2
        x = max(0, x)
        y = main_y + (main_h - dialog_h) // 2
        y = max(0, y)
        
        dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")
        
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(fg_color=COLOR_BG)
        
        hdr = ctk.CTkFrame(dialog, fg_color=COLOR_HEADER, corner_radius=0, height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="PMPC Data Logger — Background Mode", font=ctk.CTkFont(family="Segoe UI", weight="bold", size=13), text_color=COLOR_TEXT).pack(pady=10)
        ctk.CTkFrame(dialog, fg_color="#ffffff", corner_radius=0, height=2).pack(fill=tk.X)
        
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        
        msg_lbl = ctk.CTkLabel(
            content_frame, 
            text="The PMPC Data Logger system is still running in the background.\n\nDouble-click 'Start PMPC System.vbs' at any time to bring this window back.", 
            justify=tk.LEFT,
            text_color=COLOR_TEXT_DIM,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        msg_lbl.pack(pady=(0, 20), anchor="w")
        
        self.bg_confirmed = False
        def confirm():
            self.bg_confirmed = True
            dialog.destroy()
            
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        
        btn_ok = ctk.CTkButton(content_frame, text="OK", width=100, height=32, corner_radius=16, fg_color="#333333", hover_color="#444444", text_color="#ffffff", border_width=1, border_color="#555555", font=ctk.CTkFont(family="Segoe UI", weight="bold"), command=confirm)
        btn_ok.pack(side=tk.RIGHT)
        
        self.root.wait_window(dialog)
        return self.bg_confirmed

    def on_closing(self):
        if self.is_running:
            choice = self.show_close_dialog()
            if choice == "background":
                if self.show_background_info_dialog():
                    self.log("[SYSTEM] Hiding launcher window. Services are active in the background.")
                    self.root.withdraw()
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
