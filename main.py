import sys
import os
import json
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, colorchooser
from pathlib import Path
import tkinter.font as tkfont
import ctypes
from ctypes import wintypes

try:
	from PIL import Image, ImageTk
	_PIL_AVAILABLE = True
except Exception:
	_PIL_AVAILABLE = False

try:
	import keyboard
except Exception:
	keyboard = None


def resource_path(rel_path: str) -> str:
	# Return absolute path to a resource bundled with the app.
	# Uses Pathlib and supports PyInstaller's _MEIPASS extraction directory.
	base = get_app_base_dir()
	return str((base / rel_path).resolve())


# Application identity/version
APP_NAME = "RobloxWindowStacker"
APP_VERSION = "1.0.0"

def get_app_version() -> str:
	return APP_VERSION


def get_app_base_dir() -> Path:
	"""
	Return the base directory for bundled resources.
	- When frozen by PyInstaller, use sys._MEIPASS if available or the executable's folder.
	- When running from source, use the script's parent directory.
	"""
	try:
		if getattr(sys, 'frozen', False):
			meipass = getattr(sys, '_MEIPASS', None)
			if meipass:
				return Path(meipass)
			return Path(sys.executable).resolve().parent
	except Exception:
		pass
	return Path(__file__).resolve().parent


def warn_if_not_launched_by_launcher():
	"""Optionally warn the user if the app was not launched by the launcher.
	The launcher should set environment variable LAUNCHED_BY_LAUNCHER=1.
	"""
	try:
		if os.environ.get('LAUNCHED_BY_LAUNCHER') != '1':
			try:
				messagebox.showwarning(
					f"{APP_NAME} - Launcher recommended",
					"This executable may need to be launched via the official launcher to receive automatic updates.\n"
					"If you launched this directly, you can continue, but updates won't be applied automatically."
				)
			except Exception:
				# If messagebox fails (e.g., no GUI available), fallback to printing
				try:
					print(f"{APP_NAME}: not launched by launcher (LAUNCHED_BY_LAUNCHER!=1)")
				except Exception:
					pass
	except Exception:
		pass


def center_window(win, width: int, height: int):
	try:
		win.update_idletasks()
		sw = win.winfo_screenwidth()
		sh = win.winfo_screenheight()
		x = (sw // 2) - (width // 2)
		y = (sh // 2) - (height // 2)
		win.geometry(f'{width}x{height}+{x}+{y}')
	except Exception:
		win.geometry(f'{width}x{height}')


def _get_config_path():
	try:
		if sys.platform == 'win32':
			return os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'roblox_window_stacker_config.json')
	except Exception:
		pass
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'roblox_window_stacker_config.json')


def get_appdata_dir():
	if sys.platform == "win32":
		base = os.environ.get("LOCALAPPDATA")
		if not base:
			base = os.path.expanduser("~\\AppData\\Local")
		return os.path.join(base, "RobloxWindowStacker")
	return os.path.join(os.path.expanduser("~"), ".roblox_window_stacker")


def get_settings_path():
	return os.path.join(get_appdata_dir(), "Settings.json")


def ensure_settings_exist():
	"""
	Copies bundled Settings.json to AppData on first run
	"""
	appdata_dir = get_appdata_dir()
	dst = get_settings_path()

	if os.path.exists(dst):
		return

	try:
		os.makedirs(appdata_dir, exist_ok=True)

		src = resource_path("Settings.json")

		if os.path.exists(src):
			import shutil
			shutil.copy2(src, dst)
		else:
			with open(dst, "w", encoding="utf-8") as f:
				json.dump({}, f, indent=2)
	except Exception:
		pass


def load_config():
	path = _get_config_path()
	try:
		if os.path.exists(path):
			with open(path, 'r', encoding='utf-8') as f:
				return json.load(f)
	except Exception:
		pass
	return {}


def save_config(data: dict):
	path = _get_config_path()
	try:
		d = os.path.dirname(path)
		if d and not os.path.exists(d):
			os.makedirs(d, exist_ok=True)
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f)
	except Exception:
		pass


def load_settings():
	path = get_settings_path()
	try:
		if os.path.exists(path):
			with open(path, "r", encoding="utf-8") as f:
				return json.load(f)
	except Exception:
		pass
	return {}


def save_settings(data: dict):
	path = get_settings_path()
	try:
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2)
	except Exception:
		pass


def load_window_geometry_settings(name: str):
	try:
		s = load_settings()
		g = s.get(f'{name}_geometry')
		if isinstance(g, (list, tuple)) and len(g) == 4:
			return tuple(int(v) for v in g)
	except Exception:
		pass
	return None


def save_window_geometry_settings(name: str, w: int, h: int, x: int, y: int):
	try:
		s = load_settings()
		s[f'{name}_geometry'] = [int(w), int(h), int(x), int(y)]
		save_settings(s)
	except Exception:
		pass


def load_window_size():
	path = _get_config_path()
	try:
		if os.path.exists(path):
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			w = int(data.get('width', 0))
			h = int(data.get('height', 0))
			if w > 0 and h > 0:
				return (w, h)
	except Exception:
		pass
	return None


def load_window_geometry():
	path = _get_config_path()
	try:
		if os.path.exists(path):
			with open(path, 'r', encoding='utf-8') as f:
				data = json.load(f)
			w = int(data.get('width', 0))
			h = int(data.get('height', 0))
			x = int(data.get('x', 0))
			y = int(data.get('y', 0))
			if w > 0 and h > 0:
				return (w, h, x, y)
	except Exception:
		pass
	return None


def save_window_size(w, h):
	path = _get_config_path()
	try:
		data = {'width': int(w), 'height': int(h)}
		d = os.path.dirname(path)
		if d and not os.path.exists(d):
			os.makedirs(d, exist_ok=True)
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f)
	except Exception:
		pass


def save_window_geometry(w, h, x, y):
	path = _get_config_path()
	try:
		data = {'width': int(w), 'height': int(h), 'x': int(x), 'y': int(y)}
		d = os.path.dirname(path)
		if d and not os.path.exists(d):
			os.makedirs(d, exist_ok=True)
		with open(path, 'w', encoding='utf-8') as f:
			json.dump(data, f)
	except Exception:
		pass


CURRENT_BG = None


def apply_bg_color(color):
	global CURRENT_BG
	if not color:
		return
	CURRENT_BG = color
	try:
		root.configure(bg=color)
	except Exception:
		pass

	# Respect a user-selected button color: if a button color is saved in settings,
	# do not overwrite button backgrounds when changing the overall bg color.
	try:
		s = load_settings()
		user_btn = s.get('button_bg')
	except Exception:
		user_btn = None

	def _apply(w):
		try:
			if isinstance(w, tk.Button):
				if user_btn:
					# user has chosen a button color previously; keep that color
					fg = 'white' if is_dark_hex(user_btn) else 'black'
					try:
						w.configure(bg=user_btn, activebackground=user_btn, fg=fg)
					except Exception:
						pass
				else:
					try:
						w.configure(bg='white', activebackground='white', fg='black')
					except Exception:
						pass
			else:
				try:
					w.configure(bg=color)
				except Exception:
					pass
		except Exception:
			pass
		try:
			children = w.winfo_children()
		except Exception:
			children = []
		for c in children:
			_apply(c)

	try:
		_apply(root)
	except Exception:
		pass


# Color utilities ---------------------------------------------------------
def hex_to_rgb(hexcol: str):
	try:
		h = hexcol.lstrip('#')
		if len(h) == 3:
			h = ''.join([c*2 for c in h])
		return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
	except Exception:
		return (255, 255, 255)


def is_dark_hex(hexcol: str, threshold: float = 128.0) -> bool:
	try:
		r, g, b = hex_to_rgb(hexcol)
		lum = 0.299 * r + 0.587 * g + 0.114 * b
		return lum < threshold
	except Exception:
		return False



def apply_button_color(color):
	if not color:
		return
	try:
		def _apply(w):
			try:
				if isinstance(w, tk.Button):
					fg = 'white' if is_dark_hex(color) else 'black'
					try:
						w.configure(bg=color, activebackground=color, fg=fg)
					except Exception:
						pass
			except Exception:
				pass
			try:
				children = w.winfo_children()
			except Exception:
				children = []
			for c in children:
				_apply(c)
		_apply(root)
	except Exception:
		pass


def mk_button(master, **kwargs):
	cmd = kwargs.pop('command', None)
	if 'bg' not in kwargs and 'background' not in kwargs:
		try:
			_s = load_settings()
			bcol = _s.get('button_bg', 'white')
		except Exception:
			bcol = 'white'
		kwargs['bg'] = bcol
		kwargs['activebackground'] = bcol
	b = tk.Button(master, **kwargs)
	if cmd:
		b.config(command=cmd)
	# set readable text color based on button background
	try:
		bg = b.cget('bg')
		fg = 'white' if is_dark_hex(bg) else 'black'
		b.configure(fg=fg)
	except Exception:
		pass
	return b


# --- Windows API helpers -------------------------------------------------


def move_roblox_windows_top_left():
	if sys.platform != 'win32':
		messagebox.showerror('Unsupported', 'This feature is only supported on Windows.')
		return

	user32 = ctypes.windll.user32
	kernel32 = ctypes.windll.kernel32

	HWND_TOP = 0
	SWP_NOSIZE = 0x0001
	SWP_NOZORDER = 0x0004
	SW_RESTORE = 9

	found = get_roblox_windows()

	if not found:
		messagebox.showinfo('No windows', 'No RobloxPlayerBeta.exe windows found.')
		return

	# Get selected monitor's work area
	settings = load_settings()
	monitor_index = settings.get('selected_monitor_index', -1)
	keep_in_bounds = settings.get('keep_in_bounds', False)
	
	monitor_work = get_monitor_work_area(monitor_index)
	if monitor_work:
		start_x, start_y = monitor_work[0], monitor_work[1]
	else:
		start_x, start_y = 0, 0

	for hwnd in found:
		try:
			user32.ShowWindow(hwnd, SW_RESTORE)
			x, y = start_x, start_y
			if keep_in_bounds:
				x, y = clamp_to_monitor(hwnd, x, y, monitor_work)
			user32.SetWindowPos(hwnd, HWND_TOP, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
		except Exception:
			pass


# --- Multi-Monitor Support -------------------------------------------------

def list_monitors():
	"""
	Enumerate all monitors on Windows using WinAPI.
	Returns list of dicts: {hMonitor, name, rcMonitor, rcWork, isPrimary}
	Names: "Primary", "Monitor #2", "Monitor #3", etc. (sorted by position)
	rcMonitor: (left, top, right, bottom) - full area
	rcWork: (left, top, right, bottom) - work area (excluding taskbar)
	"""
	raw_monitors = []
	user32 = ctypes.windll.user32

	class RECT(ctypes.Structure):
		_fields_ = [
			('left', wintypes.LONG),
			('top', wintypes.LONG),
			('right', wintypes.LONG),
			('bottom', wintypes.LONG)
		]

	class MONITORINFO(ctypes.Structure):
		_fields_ = [
			('cbSize', wintypes.DWORD),
			('rcMonitor', RECT),
			('rcWork', RECT),
			('dwFlags', wintypes.DWORD)
		]

	MONITORINFOF_PRIMARY = 1

	@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
	def enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
		try:
			mi = MONITORINFO()
			mi.cbSize = ctypes.sizeof(MONITORINFO)
			if user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi)):
				is_primary = bool(mi.dwFlags & MONITORINFOF_PRIMARY)
				raw_monitors.append({
					'hMonitor': hMonitor,
					'isPrimary': is_primary,
					'rcMonitor': (mi.rcMonitor.left, mi.rcMonitor.top, mi.rcMonitor.right, mi.rcMonitor.bottom),
					'rcWork': (mi.rcWork.left, mi.rcWork.top, mi.rcWork.right, mi.rcWork.bottom)
				})
		except Exception:
			pass
		return True

	try:
		user32.EnumDisplayMonitors(None, None, enum_proc, 0)
	except Exception:
		pass

	# Separate primary and non-primary monitors
	primary = None
	others = []
	for m in raw_monitors:
		if m['isPrimary']:
			primary = m
		else:
			others.append(m)

	# Sort non-primary by position: left-to-right, then top-to-bottom
	others.sort(key=lambda m: (m['rcMonitor'][0], m['rcMonitor'][1]))

	# Build final list with proper names
	monitors = []
	if primary:
		primary['name'] = "Primary"
		monitors.append(primary)

	for i, m in enumerate(others, start=2):
		m['name'] = f"Monitor #{i}"
		monitors.append(m)

	return monitors


def get_monitor_work_area(monitor_index=-1):
	"""
	Get the work area (rcWork) of a monitor by index.
	monitor_index: -1 = primary (default), 1 = Monitor #2, 2 = Monitor #3, etc.
	Returns: (left, top, right, bottom) or None if not found
	"""
	try:
		monitors = list_monitors()
		if not monitors:
			return None

		if monitor_index == -1:
			# Find primary
			for m in monitors:
				if m['isPrimary']:
					return m['rcWork']
			# Fallback to first
			return monitors[0]['rcWork'] if monitors else None
		else:
			# monitor_index N corresponds to "Monitor #(N+1)"
			target_name = f"Monitor #{monitor_index + 1}"
			for m in monitors:
				if m['name'] == target_name:
					return m['rcWork']
	except Exception:
		pass
	return None


def get_window_size(hwnd):
	"""
	Get window width and height using GetWindowRect.
	Returns: (width, height) or (800, 600) as fallback
	"""
	try:
		user32 = ctypes.windll.user32
		rect = wintypes.RECT()
		if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
			win_width = rect.right - rect.left
			win_height = rect.bottom - rect.top
			if win_width > 0 and win_height > 0:
				return (win_width, win_height)
	except Exception:
		pass
	return (800, 600)


def get_roblox_windows(limit=None):
	"""
	Enumerate open RobloxPlayerBeta.exe windows, return sorted HWND list.
	If limit is an int > 0, return only the first `limit` HWNDs (sorted ascending).
	"""
	try:
		if sys.platform != 'win32':
			return []
		user32 = ctypes.windll.user32
		kernel32 = ctypes.windll.kernel32
		found = []

		@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
		def _enum_proc(hwnd, lParam):
			try:
				if not user32.IsWindowVisible(hwnd):
					return True
			except Exception:
				return True
			pid = wintypes.DWORD()
			user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
			pid_val = pid.value
			if not pid_val:
				return True
			PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
			hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid_val)
			exe_name = None
			if hProcess:
				try:
					buf = ctypes.create_unicode_buffer(260)
					size = wintypes.DWORD(260)
					if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
						exe_name = os.path.basename(buf.value)
				except Exception:
					exe_name = None
				try:
					kernel32.CloseHandle(hProcess)
				except Exception:
					pass
			if exe_name and exe_name.lower() == 'robloxplayerbeta.exe':
				found.append(hwnd)
			return True

		try:
			user32.EnumWindows(_enum_proc, 0)
		except Exception:
			pass

		# Sort HWNDs for deterministic order
		found.sort()
		if isinstance(limit, int) and limit > 0:
			return found[:limit]
		return found
	except Exception:
		return []


def clamp_to_monitor(hwnd, x, y, monitor_rcWork):
	"""
	Clamp window position (x, y) to stay within monitor work area.
	monitor_rcWork: (left, top, right, bottom)
	Returns: (x, y) clamped to monitor bounds
	"""
	try:
		if not monitor_rcWork:
			return (x, y)

		left, top, right, bottom = monitor_rcWork
		user32 = ctypes.windll.user32

		# Get window dimensions
		rect = wintypes.RECT()
		if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
			win_width = rect.right - rect.left
			win_height = rect.bottom - rect.top
		else:
			win_width = 800
			win_height = 600

		# Clamp x: window left edge >= monitor left, right edge <= monitor right
		x = max(x, left)
		x = min(x, right - win_width)

		# Clamp y: window top edge >= monitor top, bottom edge <= monitor bottom
		y = max(y, top)
		y = min(y, bottom - win_height)

		return (int(x), int(y))
	except Exception:
		return (x, y)


def stack_next_roblox(win):
	if sys.platform != 'win32':
		messagebox.showerror('Unsupported', 'This feature is only supported on Windows.')
		return

	user32 = ctypes.windll.user32
	kernel32 = ctypes.windll.kernel32

	found = get_roblox_windows()

	if not found or len(found) < 2:
		messagebox.showinfo('No windows', 'Need at least two Roblox windows to stack.')
		return

	anchor = found[0]
	others = found[1:]
	if not others:
		messagebox.showinfo('No targets', 'No other Roblox windows found to stack.')
		return

	# Get selected monitor's work area
	settings = load_settings()
	monitor_index = settings.get('selected_monitor_index', -1)
	keep_in_bounds = settings.get('keep_in_bounds', False)
	
	monitor_work = get_monitor_work_area(monitor_index)
	if monitor_work:
		monitor_left = monitor_work[0]
	else:
		monitor_left = 0

	idx = getattr(win, '_stack_next_index', 0) % len(others)
	target = others[idx]

	last_pos = getattr(win, '_last_moved_pos', None)
	if last_pos is None:
		try:
			rect = wintypes.RECT()
			user32.GetWindowRect(anchor, ctypes.byref(rect))
			last_x, last_y = rect.left, rect.top
		except Exception:
			last_x, last_y = monitor_left, (monitor_work[1] if monitor_work else 0)
	else:
		last_x, last_y = last_pos

	new_x = int(last_x + 24)
	new_y = int(last_y + 24)

	HWND_TOP = 0
	SWP_NOSIZE = 0x0001
	SWP_NOZORDER = 0x0004
	SW_RESTORE = 9
	try:
		user32.ShowWindow(target, SW_RESTORE)
		if keep_in_bounds:
			new_x, new_y = clamp_to_monitor(target, new_x, new_y, monitor_work)
		user32.SetWindowPos(target, HWND_TOP, new_x, new_y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
	except Exception:
		pass

	try:
		if not hasattr(win, '_moved_order'):
			win._moved_order = []
		win._moved_order.append((new_x, new_y))
		win._last_moved_pos = (new_x, new_y)
		win._stack_next_index = (idx + 1) % len(others)
	except Exception:
		pass


def open_stacker():
	win = tk.Toplevel(root)
	win.title("Stacker")
	_g = load_window_geometry_settings('stacker')
	if _g:
		try:
			_w, _h, _x, _y = _g
			# Enforce minimum size of 450x260
			_w = max(_w, 450)
			_h = max(_h, 260)
			win.geometry(f'{_w}x{_h}+{_x}+{_y}')
		except Exception:
			win.geometry("450x260")
	else:
		win.geometry("450x260")
	if CURRENT_BG:
		try:
			win.configure(bg=CURRENT_BG)
		except Exception:
			pass
	# removed label to keep only the controls as requested

	win._moved_order = []
	win._last_moved_pos = None
	win._stack_next_index = 0

	# Monitor selection controls
	monitor_frame = tk.Frame(win)
	if CURRENT_BG:
		try:
			monitor_frame.configure(bg=CURRENT_BG)
		except Exception:
			pass
	monitor_frame.pack(pady=4)

	lbl_monitor = tk.Label(monitor_frame, text="Monitor:", font=("Arial", 10, "bold"))
	if CURRENT_BG:
		try:
			lbl_monitor.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				lbl_monitor.configure(fg="white")
			else:
				lbl_monitor.configure(fg="black")
		except Exception:
			pass
	lbl_monitor.pack(side=tk.LEFT, padx=(4, 2))

	monitors = list_monitors()
	monitor_names = [m['name'] for m in monitors]  # ["Primary", "Monitor #2", "Monitor #3", ...]

	settings = load_settings()
	saved_idx = settings.get('selected_monitor_index', -1)
	
	# Map saved_idx back to display name
	if saved_idx == -1:
		selected_name = "Primary"
	else:
		# saved_idx N corresponds to "Monitor #(N+1)"
		target_name = f"Monitor #{saved_idx + 1}"
		selected_name = target_name if target_name in monitor_names else "Primary"

	monitor_var = tk.StringVar(value=selected_name)

	def _on_monitor_changed(*args):
		try:
			sel = monitor_var.get()
			s = load_settings()
			
			if sel == "Primary":
				s['selected_monitor_index'] = -1
			else:
				# Extract number from "Monitor #X": save X-1
				parts = sel.split('#')
				if len(parts) == 2:
					try:
						monitor_num = int(parts[1])
						s['selected_monitor_index'] = monitor_num - 1
					except Exception:
						s['selected_monitor_index'] = -1
				else:
					s['selected_monitor_index'] = -1
			
			save_settings(s)
		except Exception:
			pass

	monitor_var.trace('w', _on_monitor_changed)

	monitor_combo = tk.OptionMenu(monitor_frame, monitor_var, *monitor_names)
	if CURRENT_BG:
		try:
			monitor_combo.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				monitor_combo.configure(fg="white")
			else:
				monitor_combo.configure(fg="black")
		except Exception:
			pass
	monitor_combo.pack(side=tk.LEFT, padx=2)

	bounds_var = tk.BooleanVar(value=settings.get('keep_in_bounds', False))

	def _on_bounds_changed(*args):
		try:
			s = load_settings()
			s['keep_in_bounds'] = bounds_var.get()
			save_settings(s)
		except Exception:
			pass

	bounds_var.trace('w', _on_bounds_changed)

	chk_bounds = tk.Checkbutton(monitor_frame, text="Keep in bounds", variable=bounds_var, font=("Arial", 10, "bold"))
	if CURRENT_BG:
		try:
			chk_bounds.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				chk_bounds.configure(fg="white")
			else:
				chk_bounds.configure(fg="black")
		except Exception:
			pass
	chk_bounds.pack(side=tk.LEFT, padx=2)

	# (Move Count removed)

	# Load placement controls (corner and stair spacing)
	load_frame = tk.Frame(win)
	if CURRENT_BG:
		try:
			load_frame.configure(bg=CURRENT_BG)
		except Exception:
			pass
	load_frame.pack(pady=4)

	lbl_corner = tk.Label(load_frame, text="Load corner:", font=("Arial", 10, "bold"))
	if CURRENT_BG:
		try:
			lbl_corner.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				lbl_corner.configure(fg="white")
			else:
				lbl_corner.configure(fg="black")
		except Exception:
			pass
	lbl_corner.pack(side=tk.LEFT, padx=(4, 2))

	settings_load = load_settings()
	corner_mode = settings_load.get('load_start_corner', 'top_left')
	corner_var = tk.StringVar(value="Top Left" if corner_mode == 'top_left' else "Top Right")

	def _on_corner_changed(*args):
		try:
			s = load_settings()
			if corner_var.get() == "Top Left":
				s['load_start_corner'] = 'top_left'
			else:
				s['load_start_corner'] = 'top_right'
			save_settings(s)
		except Exception:
			pass

	corner_var.trace('w', _on_corner_changed)

	corner_menu = tk.OptionMenu(load_frame, corner_var, "Top Left", "Top Right")
	if CURRENT_BG:
		try:
			corner_menu.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				corner_menu.configure(fg="white")
			else:
				corner_menu.configure(fg="black")
		except Exception:
			pass
	corner_menu.pack(side=tk.LEFT, padx=2)

	# Stair spacing controls
	lbl_dx = tk.Label(load_frame, text="dX:", font=("Arial", 9, "bold"))
	if CURRENT_BG:
		try:
			lbl_dx.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				lbl_dx.configure(fg="white")
			else:
				lbl_dx.configure(fg="black")
		except Exception:
			pass
	lbl_dx.pack(side=tk.LEFT, padx=(8, 2))

	dx_val = settings_load.get('load_stair_dx', 24)
	dx_var = tk.StringVar(value=str(dx_val))

	def _on_dx_changed(*args):
		try:
			s = load_settings()
			try:
				val = int(dx_var.get())
			except Exception:
				val = 24
			s['load_stair_dx'] = val
			save_settings(s)
		except Exception:
			pass

	dx_var.trace('w', _on_dx_changed)

	dx_entry = tk.Entry(load_frame, textvariable=dx_var, width=3, font=("Arial", 9))
	dx_entry.pack(side=tk.LEFT, padx=(0, 8))

	lbl_dy = tk.Label(load_frame, text="dY:", font=("Arial", 9, "bold"))
	if CURRENT_BG:
		try:
			lbl_dy.configure(bg=CURRENT_BG)
			if is_dark_hex(CURRENT_BG):
				lbl_dy.configure(fg="white")
			else:
				lbl_dy.configure(fg="black")
		except Exception:
			pass
	lbl_dy.pack(side=tk.LEFT, padx=(0, 2))

	dy_val = settings_load.get('load_stair_dy', 24)
	dy_var = tk.StringVar(value=str(dy_val))

	def _on_dy_changed(*args):
		try:
			s = load_settings()
			try:
				val = int(dy_var.get())
			except Exception:
				val = 24
			s['load_stair_dy'] = val
			save_settings(s)
		except Exception:
			pass

	dy_var.trace('w', _on_dy_changed)

	dy_entry = tk.Entry(load_frame, textvariable=dy_var, width=3, font=("Arial", 9))
	dy_entry.pack(side=tk.LEFT, padx=0)

	def _load_saved_windows():
		try:
			s = load_settings()
			mapping = s.get('roblox_windows', {})
			if not mapping:
				messagebox.showinfo('No saved', 'No saved windows found in Settings.json')
				return
			user32 = ctypes.windll.user32
			kernel32 = ctypes.windll.kernel32
			found = []

			# Use system helper to enumerate Roblox windows
			found = get_roblox_windows()
			items = sorted(mapping.items(), key=lambda kv: int(kv[0].lstrip('#')) if kv[0].lstrip('#').isdigit() else 0)
			count = min(len(items), len(found))
			if count == 0:
				messagebox.showinfo('No windows', 'No open Roblox windows to move')
				return
			HWND_TOP = 0
			SWP_NOSIZE = 0x0001
			SWP_NOZORDER = 0x0004
			SW_RESTORE = 9
			
			# Get selected monitor's work area
			monitor_index = s.get('selected_monitor_index', -1)
			keep_in_bounds = s.get('keep_in_bounds', False)
			monitor_work = get_monitor_work_area(monitor_index)
			
			# Get placement mode and stair spacing
			corner_mode = s.get('load_start_corner', 'top_left')
			dx = s.get('load_stair_dx', 24)
			dy = s.get('load_stair_dy', 24)
			
			if not monitor_work:
				monitor_left, monitor_top, monitor_right, monitor_bottom = 0, 0, 1920, 1080
			else:
				monitor_left, monitor_top, monitor_right, monitor_bottom = monitor_work
			
			if corner_mode == 'top_right':
				# For top-right, get first window's width to offset properly
				try:
					first_hwnd = found[0]
					win_w, win_h = get_window_size(first_hwnd)
					base_x = monitor_right - win_w
					base_y = monitor_top
				except Exception:
					base_x = monitor_right - 800
					base_y = monitor_top
			else:
				# top_left mode (default)
				base_x = monitor_left
				base_y = monitor_top
			
			for i in range(count):
				label, coord = items[i]
				try:
					if corner_mode == 'top_right':
						# Down-left stairway: start at top-right, move left and down
						x = base_x - i * dx
					else:
						# Down-right stairway: start at top-left, move right and down
						x = base_x + i * dx
					y = base_y + i * dy
					hwnd = found[i]
					user32.ShowWindow(hwnd, SW_RESTORE)
					if keep_in_bounds:
						x, y = clamp_to_monitor(hwnd, x, y, monitor_work)
					user32.SetWindowPos(hwnd, HWND_TOP, int(x), int(y), 0, 0, SWP_NOSIZE | SWP_NOZORDER)
				except Exception:
					pass
		except Exception:
			pass

	btn_load = mk_button(win, text='Load Saved Windows', width=20, command=_load_saved_windows, cursor='hand2')
	btn_load.pack(pady=(4, 6))

	def _top_left_and_record():
		move_roblox_windows_top_left()
		try:
			user32 = ctypes.windll.user32
			kernel32 = ctypes.windll.kernel32
			found = []

			@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
			def _enum_proc(hwnd, lParam):
				try:
					if not user32.IsWindowVisible(hwnd):
						return True
				except Exception:
					return True
				pid = wintypes.DWORD()
				user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
				pid_val = pid.value
				if not pid_val:
					return True
				PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
				hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid_val)
				exe_name = None
				if hProcess:
					try:
						buf = ctypes.create_unicode_buffer(260)
						size = wintypes.DWORD(260)
						if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
							exe_name = os.path.basename(buf.value)
					except Exception:
						exe_name = None
					try:
						kernel32.CloseHandle(hProcess)
					except Exception:
						pass
				if exe_name and exe_name.lower() == 'robloxplayerbeta.exe':
					found.append(hwnd)
				return True

			user32.EnumWindows(_enum_proc, 0)
			if found:
				try:
					rect = wintypes.RECT()
					user32.GetWindowRect(found[0], ctypes.byref(rect))
					x, y = rect.left, rect.top
					win._moved_order.append((x, y))
					win._last_moved_pos = (x, y)
				except Exception:
					pass
		except Exception:
			pass

	btn_top_left = mk_button(win, text='Top Left', width=20, command=_top_left_and_record, cursor='hand2')
	btn_top_left.pack(pady=8)

	btn_next = mk_button(win, text='Next', width=20, command=lambda: stack_next_roblox(win), cursor='hand2')
	btn_next.pack(pady=6)

	def _on_done():
		try:
			mapping = {}
			order = getattr(win, '_moved_order', [])
			for i, (x, y) in enumerate(order, start=1):
				mapping[f"#{i}"] = [int(x), int(y)]
			try:
				s = load_settings()
				s['roblox_windows'] = mapping
				save_settings(s)
			except Exception:
				pass
		except Exception:
			pass
		try:
			win.destroy()
		except Exception:
			pass

	btn_done = mk_button(win, text='Done', width=20, command=_on_done, cursor='hand2')
	btn_done.pack(pady=(4, 8))

	def _on_close_stacker():
		try:
			w = win.winfo_width()
			h = win.winfo_height()
			x = win.winfo_x()
			y = win.winfo_y()
			save_window_geometry_settings('stacker', w, h, x, y)
		except Exception:
			pass
		try:
			win.destroy()
		except Exception:
			pass

	try:
		win.protocol('WM_DELETE_WINDOW', _on_close_stacker)
	except Exception:
		pass


def open_tinytask():
	import shutil

	def find_tinytask():
		p = shutil.which('tinytask.exe') or shutil.which('TinyTask.exe')
		if p:
			return p
		cur = os.path.join(os.getcwd(), 'tinytask.exe')
		if os.path.exists(cur):
			return cur
		cur2 = os.path.join(os.getcwd(), 'TinyTask.exe')
		if os.path.exists(cur2):
			return cur2
		candidates = []
		pf = os.environ.get('ProgramFiles')
		pfx = os.environ.get('ProgramFiles(x86)')
		local = os.path.expanduser('~\\AppData\\Local')
		downloads = os.path.expanduser('~\\Downloads')
		for base in (pf, pfx, local, downloads):
			if not base:
				continue
			candidates.extend([
				os.path.join(base, 'TinyTask.exe'),
				os.path.join(base, 'tinytask.exe'),
				os.path.join(base, 'TinyTask', 'TinyTask.exe'),
				os.path.join(base, 'TinyTask', 'tinytask.exe'),
			])
		for c in candidates:
			try:
				if c and os.path.exists(c):
					return c
			except Exception:
				continue
		return None

	path = find_tinytask()
	if path:
		try:
			os.startfile(path)
		except Exception:
			try:
				import subprocess
				subprocess.Popen([path])
			except Exception:
				webbrowser.open('https://tinytask.net/download.html', new=2)
	else:
		webbrowser.open('https://tinytask.net/download.html', new=2)
 


DISCORD_URL = 'https://discord.gg/KhGrvNpGjb'


def open_discord_link(event=None):
	try:
		webbrowser.open(DISCORD_URL, new=2)
	except Exception:
		pass


def open_terms_of_service():
	win = tk.Toplevel(root)
	win.title('Terms of Service')
	win.geometry('650x550')
	if CURRENT_BG:
		try:
			win.configure(bg=CURRENT_BG)
		except Exception:
			pass

	text_frame = tk.Frame(win)
	if CURRENT_BG:
		try:
			text_frame.configure(bg=CURRENT_BG)
		except Exception:
			pass
	text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

	scrollbar = tk.Scrollbar(text_frame)
	scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Arial", 9))
	text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	scrollbar.config(command=text_widget.yview)

	tos_text = """Terms of Service (Roblox Window Stacker)

Effective Date: December 31, 2025
Software: Roblox Window Stacker ("Software")
Developer: Gamblian ("we", "us", "our")

By downloading, installing, or using Roblox Window Stacker, you agree to these Terms.

1) What the Software Does

Roblox Window Stacker is a Windows desktop tool that helps move and arrange open RobloxPlayerBeta.exe windows on your screen and can open links (e.g., Discord, info pages). The Software is not affiliated with or endorsed by Roblox Corporation.

2) License / Permission to Use

We give you a personal, non-exclusive, revocable license to use the Software for lawful purposes, as long as you follow these Terms.

3) Rules for Use

You agree that you will not:

- use the Software to cheat, exploit, or break Roblox or any other service's rules,
- use the Software for illegal activity,
- modify, reverse engineer, decompile, or redistribute the Software unless we explicitly allow it in writing,
- claim the Software is yours or remove credits/branding.

4) Third-Party Services and Links

The Software may open third-party websites (such as Discord or TinyTask download pages). We don't control those services and aren't responsible for their content, safety, or policies. Use them at your own risk.

5) Data and Settings

The Software may store local settings files on your computer (for example window positions, button colors, and other preferences). These settings are stored locally on your device.

We do not promise the settings will always be saved correctly, and settings may be reset or lost due to updates, device changes, or errors.

6) No Warranty

The Software is provided "AS IS" and "AS AVAILABLE."
We make no warranties of any kind, including implied warranties of merchantability, fitness for a particular purpose, or non-infringement.

7) Limitation of Liability

To the maximum extent allowed by law, Gamblian is not liable for any damages or losses arising from your use of the Software, including (but not limited to) lost data, lost profits, account issues, system problems, or game/service bans.

You are responsible for how you use the Software and for complying with Roblox's rules and any applicable laws.

8) Updates and Changes

We may update, change, or discontinue the Software at any time. We may also update these Terms. If you continue using the Software after changes, that means you accept the updated Terms.

9) Termination

We may terminate or suspend your permission to use the Software if you violate these Terms. You may stop using the Software at any time by uninstalling it.

10) Contact

If you have questions about these Terms, contact us through the official Roblox Window Stacker community/links provided in the Software (such as the Discord link)."""

	text_widget.insert(tk.END, tos_text)
	text_widget.config(state=tk.DISABLED)

	try:
		_g = load_window_geometry_settings('tos')
		if _g:
			_w, _h, _x, _y = _g
			win.geometry(f'{_w}x{_h}+{_x}+{_y}')
	except Exception:
		pass

	def _on_close_tos():
		try:
			w = win.winfo_width()
			h = win.winfo_height()
			x = win.winfo_x()
			y = win.winfo_y()
			save_window_geometry_settings('tos', w, h, x, y)
		except Exception:
			pass
		try:
			win.destroy()
		except Exception:
			pass

	try:
		win.protocol('WM_DELETE_WINDOW', _on_close_tos)
	except Exception:
		pass


DONATE_URL = 'https://discord.com/channels/1444204543880462448/1453245947248119868'


def open_donate_link(event=None):
	try:
		webbrowser.open(DONATE_URL, new=2)
	except Exception:
		pass


CREDITS_URL = 'https://discord.com/channels/1444204543880462448/1453968340417646706'


def open_credits_link(event=None):
	try:
		webbrowser.open(CREDITS_URL, new=2)
	except Exception:
		pass


INFO_URL = 'https://discord.com/channels/1444204543880462448/1453969039314391041'


def open_information_link(event=None):
	try:
		webbrowser.open(INFO_URL, new=2)
	except Exception:
		pass


def draw_discord_icon(canvas, size=36):
	canvas.create_oval(2, 2, size-2, size-2, fill='#5865F2', outline='')
	left_x = size * 0.33
	right_x = size * 0.67
	eye_y = size * 0.42
	r = max(2, int(size * 0.08))
	canvas.create_oval(left_x-r, eye_y-r, left_x+r, eye_y+r, fill='white', outline='')
	canvas.create_oval(right_x-r, eye_y-r, right_x+r, eye_y+r, fill='white', outline='')


def draw_gear_icon(canvas, size=36):
	canvas.create_oval(2, 2, size-2, size-2, fill='#DDDDDD', outline='')
	canvas.create_oval(size*0.28, size*0.28, size*0.72, size*0.72, fill='#FFFFFF', outline='')
	t = max(2, int(size * 0.08))
	canvas.create_rectangle((size/2)-t, 0, (size/2)+t, size*0.18, fill='#BBBBBB', outline='')
	canvas.create_rectangle((size/2)-t, size*0.82, (size/2)+t, size, fill='#BBBBBB', outline='')
	canvas.create_rectangle(0, (size/2)-t, size*0.18, (size/2)+t, fill='#BBBBBB', outline='')
	canvas.create_rectangle(size*0.82, (size/2)-t, size, (size/2)+t, fill='#BBBBBB', outline='')


def build_main_ui(root):
	root.title('Roblox Window Stacker')
	g = load_window_geometry()
	if g:
		try:
			w, h, x, y = g
			root.geometry(f'{w}x{h}+{x}+{y}')
		except Exception:
			center_window(root, 420, 160)
	else:
		center_window(root, 420, 160)

	frm = tk.Frame(root, bg=root.cget('bg'))
	frm.pack(padx=12, pady=12, fill='both', expand=True)

	# top bar with Discord (left) and Settings (right) on the same horizontal axis
	top_bar = tk.Frame(frm, bg=frm.cget('bg'))
	top_bar.pack(fill='x', side='top')

	discord_btn = mk_button(top_bar, text='Discord', width=10, command=open_discord_link, cursor='hand2')
	discord_btn.pack(side='left', padx=6, pady=(0, 8))

	gear_btn = mk_button(top_bar, text='Settings', width=10, command=open_settings, cursor='hand2')
	gear_btn.pack(side='right', padx=6, pady=(0, 8))

	lbl = tk.Label(frm, text='Roblox Window Stacker', font=('Segoe UI', 14, 'bold'), bg=frm.cget('bg'))
	lbl.pack(pady=(0, 8))

	btn_frame = tk.Frame(frm, bg=frm.cget('bg'))
	btn_frame.pack()

	btn_stacker = mk_button(btn_frame, text='Stacker (F1)', width=16, command=open_stacker, cursor='hand2')
	btn_stacker.grid(row=0, column=0, padx=6, pady=4)

	btn_tinytask = mk_button(btn_frame, text='TinyTask (F2)', width=16, command=open_tinytask, cursor='hand2')
	btn_tinytask.grid(row=0, column=1, padx=6, pady=4)

	btn_exit = mk_button(btn_frame, text='Exit (F3)', width=16, command=root.quit, cursor='hand2')
	btn_exit.grid(row=0, column=2, padx=6, pady=4)

	btn_donate = mk_button(btn_frame, text='Donate', width=16, command=lambda: webbrowser.open(DONATE_URL, new=2), cursor='hand2')
	btn_donate.grid(row=1, column=0, padx=6, pady=4)

	btn_tos = mk_button(btn_frame, text='Terms of Service', width=16, command=open_terms_of_service, cursor='hand2')
	btn_tos.grid(row=1, column=1, padx=6, pady=4)

	btn_credits = mk_button(btn_frame, text='Credits', width=16, command=lambda: webbrowser.open(CREDITS_URL, new=2), cursor='hand2')
	btn_credits.grid(row=1, column=2, padx=6, pady=4)

	def _open_settings():
		open_settings()

	# (Settings button moved into `frm` at top-right)


def open_settings():
	win = tk.Toplevel(root)
	win.title('Settings')
	_g = load_window_geometry_settings('settings')
	if _g:
		try:
			_w, _h, _x, _y = _g
			win.geometry(f'{_w}x{_h}+{_x}+{_y}')
		except Exception:
			win.geometry('360x220')
	else:
		win.geometry('360x220')

	s = load_settings()
	cur_bg = s.get('bg', '#FFFFFF')
	cur_btn = s.get('button_bg', 'white')
	# set settings window background to saved bg
	try:
		win.configure(bg=cur_bg)
	except Exception:
		pass

	def choose_bg():
		c = colorchooser.askcolor(title='Choose background color', initialcolor=cur_bg)
		if c and c[1]:
			try:
				s = load_settings()
				s['bg'] = c[1]
				save_settings(s)
				apply_bg_color(c[1])
			except Exception:
				pass

	def choose_button():
		c = colorchooser.askcolor(title='Choose button color', initialcolor=cur_btn)
		if c and c[1]:
			try:
				s = load_settings()
				s['button_bg'] = c[1]
				save_settings(s)
				apply_button_color(c[1])
			except Exception:
				pass

	lbl1 = tk.Label(win, text='Background color:', bg=win.cget('bg'))
	lbl1.pack(pady=(12, 4))
	btn_bg = mk_button(win, text='Choose Background', command=choose_bg, width=20, cursor='hand2')
	btn_bg.pack()

	lbl2 = tk.Label(win, text='Button color:', bg=win.cget('bg'))
	lbl2.pack(pady=(12, 4))
	btn_btn = mk_button(win, text='Choose Button Color', command=choose_button, width=20, cursor='hand2')
	btn_btn.pack()

	def _on_close():
		try:
			w = win.winfo_width()
			h = win.winfo_height()
			x = win.winfo_x()
			y = win.winfo_y()
			save_window_geometry_settings('settings', w, h, x, y)
		except Exception:
			pass
		try:
			win.destroy()
		except Exception:
			pass

	try:
		win.protocol('WM_DELETE_WINDOW', _on_close)
	except Exception:
		pass


def setup_hotkeys():
	if keyboard:
		def _f1():
			try:
				root.after(0, open_stacker)
			except Exception:
				pass

		def _f2():
			try:
				root.after(0, open_tinytask)
			except Exception:
				pass

		def _f3():
			try:
				root.after(0, root.quit)
			except Exception:
				pass

		try:
			keyboard.add_hotkey('f1', _f1)
			keyboard.add_hotkey('f2', _f2)
			keyboard.add_hotkey('f3', _f3)
		except Exception:
			pass


if __name__ == '__main__':
	ensure_settings_exist()   # ← IMPORTANT
	root = tk.Tk()

	# Print/app version for support and debugging
	try:
		print(f"{APP_NAME} version {get_app_version()}")
	except Exception:
		pass

	# Optional: warn user if not launched via the official launcher
	try:
		warn_if_not_launched_by_launcher()
	except Exception:
		pass

	# Make default Tk fonts bold so all text appears bold by default
	try:
		_default_font_names = [
			'TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont',
			'TkCaptionFont', 'TkSmallCaptionFont', 'TkIconFont', 'TkTooltipFont'
		]
		for _name in _default_font_names:
			try:
				f = tkfont.nametofont(_name)
				f.configure(weight='bold')
			except Exception:
				pass
	except Exception:
		pass

	settings = load_settings()
	bg = settings.get('bg')
	btn_bg = settings.get('button_bg')
	if bg:
		try:
			root.configure(bg=bg)
			CURRENT_BG = bg
		except Exception:
			pass
	build_main_ui(root)
	# apply background across widgets so saved bg persists visually
	if bg:
		try:
			apply_bg_color(bg)
		except Exception:
			pass
	if btn_bg:
		apply_button_color(btn_bg)

	g = load_window_geometry()
	if g:
		try:
			w, h, x, y = g
			root.geometry(f'{w}x{h}+{x}+{y}')
		except Exception:
			pass

	try:
		root.bind('<F1>', lambda e: open_stacker())
		root.bind('<F2>', lambda e: open_tinytask())
		root.bind('<F3>', lambda e: root.quit())
	except Exception:
		pass

	try:
		if keyboard:
			t = threading.Thread(target=setup_hotkeys, daemon=True)
			t.start()
	except Exception:
		pass

	try:
		root.mainloop()
	finally:
		try:
			w = root.winfo_width()
			h = root.winfo_height()
			x = root.winfo_x()
			y = root.winfo_y()
			save_window_geometry(w, h, x, y)
		except Exception:
			pass


