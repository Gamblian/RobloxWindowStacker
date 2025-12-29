import sys
import os
import json
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, colorchooser
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
	base_path = getattr(sys, '_MEIPASS', None) or os.path.dirname(os.path.abspath(__file__))
	return os.path.join(base_path, rel_path)


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

	if not found:
		messagebox.showinfo('No windows', 'No RobloxPlayerBeta.exe windows found.')
		return

	for hwnd in found:
		try:
			user32.ShowWindow(hwnd, SW_RESTORE)
			user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
		except Exception:
			pass


def stack_next_roblox(win):
	if sys.platform != 'win32':
		messagebox.showerror('Unsupported', 'This feature is only supported on Windows.')
		return

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

	if not found or len(found) < 2:
		messagebox.showinfo('No windows', 'Need at least two Roblox windows to stack.')
		return

	anchor = found[0]
	others = found[1:]
	if not others:
		messagebox.showinfo('No targets', 'No other Roblox windows found to stack.')
		return

	idx = getattr(win, '_stack_next_index', 0) % len(others)
	target = others[idx]

	last_pos = getattr(win, '_last_moved_pos', None)
	if last_pos is None:
		try:
			rect = wintypes.RECT()
			user32.GetWindowRect(anchor, ctypes.byref(rect))
			last_x, last_y = rect.left, rect.top
		except Exception:
			last_x, last_y = 0, 0
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
			win.geometry(f'{_w}x{_h}+{_x}+{_y}')
		except Exception:
			win.geometry("320x200")
	else:
		win.geometry("320x200")
	if CURRENT_BG:
		try:
			win.configure(bg=CURRENT_BG)
		except Exception:
			pass
	# removed label to keep only the controls as requested

	win._moved_order = []
	win._last_moved_pos = None
	win._stack_next_index = 0

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
			items = sorted(mapping.items(), key=lambda kv: int(kv[0].lstrip('#')) if kv[0].lstrip('#').isdigit() else 0)
			count = min(len(items), len(found))
			if count == 0:
				messagebox.showinfo('No windows', 'No open Roblox windows to move')
				return
			HWND_TOP = 0
			SWP_NOSIZE = 0x0001
			SWP_NOZORDER = 0x0004
			SW_RESTORE = 9
			for i in range(count):
				label, coord = items[i]
				try:
					x, y = coord
					hwnd = found[i]
					user32.ShowWindow(hwnd, SW_RESTORE)
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

	btn_donate = mk_button(btn_frame, text='Donate', width=16, command=lambda: webbrowser.open(DONATE_URL, new=2), cursor='hand2')
	btn_donate.grid(row=1, column=0, padx=6, pady=4)

	btn_info = mk_button(btn_frame, text='Information', width=16, command=lambda: webbrowser.open(INFO_URL, new=2), cursor='hand2')
	btn_info.grid(row=1, column=1, padx=6, pady=4)

	btn_credits = mk_button(btn_frame, text='Credits', width=16, command=lambda: webbrowser.open(CREDITS_URL, new=2), cursor='hand2')
	btn_credits.grid(row=2, column=0, padx=6, pady=4)

	btn_exit = mk_button(btn_frame, text='Exit (F3)', width=16, command=root.quit, cursor='hand2')
	btn_exit.grid(row=2, column=1, padx=6, pady=4)

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


