import os
import sys
import random
import webbrowser
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import tempfile
import ctypes

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# HYNYA optimiZZZation
def apply_custom_filter_optimized(image_or_path, milk_mode=True, punt=50):
    if isinstance(image_or_path, str):
        image = Image.open(image_or_path).convert("RGBA")
    else:
        image = image_or_path.convert("RGBA")

    data = np.array(image)
    brightness = data[..., :3].mean(axis=2)
    output = data.copy()
    rand_mask = np.random.rand(*brightness.shape) < (punt / 100)

    if milk_mode:
        output[brightness <= 25] = [0, 0, 0, 255]
        output[(brightness >= 120) & (brightness < 200)] = [102, 0, 31, 255]
        output[brightness >= 230] = [137, 0, 146, 255]
        mask = (brightness > 25) & (brightness <= 70)
        output[mask & rand_mask] = [0, 0, 0, 255]
        output[mask & ~rand_mask] = [102, 0, 31, 255]
        mask = (brightness > 70) & (brightness < 120)
        output[mask & rand_mask] = [102, 0, 31, 255]
        output[mask & ~rand_mask] = [0, 0, 0, 255]
        mask = (brightness >= 200) & (brightness < 230)
        output[mask & rand_mask] = [137, 0, 146, 255]
        output[mask & ~rand_mask] = [102, 0, 31, 255]
    else:
        output[brightness <= 25] = [0, 0, 0, 255]
        output[(brightness >= 90) & (brightness < 150)] = [92, 36, 60, 255]
        output[brightness >= 200] = [203, 43, 43, 255]
        mask = (brightness > 25) & (brightness <= 70)
        output[mask & rand_mask] = [0, 0, 0, 255]
        output[mask & ~rand_mask] = [92, 36, 60, 255]
        mask = (brightness > 70) & (brightness < 90)
        output[mask & rand_mask] = [92, 36, 60, 255]
        output[mask & ~rand_mask] = [0, 0, 0, 255]
        mask = (brightness >= 150) & (brightness < 200)
        output[mask & rand_mask] = [203, 43, 43, 255]
        output[mask & ~rand_mask] = [92, 36, 60, 255]

    return Image.fromarray(output)

# ГУИ УИ
window = tk.Tk()
window.title("Milk Filter v1")
window.geometry("1100x700")

BG_MAIN = "#161618"
window.configure(bg=BG_MAIN)

try:
    # Чёрни полоса сверху (win 10/11)
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    value = ctypes.c_int(2)
    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
except:
    pass

try:
    # Иконка
    app_icon = tk.PhotoImage(file=resource_path("icon.png"))
    window.iconphoto(False, app_icon)
except:
    pass

# Цветовая палитра
BG_PANEL = "#1e1e20"
BG_SIDEBAR = "#0d0d0f"
TEXT_COLOR = "#e0e0e0"
ACCENT_GREEN = "#A63A40"
BTN_DARK = "#2a2a2d"

filename = None
original_image = None
filtered_image = None
is_video = False
video_temp_output = None

# Боковая панель (Sidebar)
sidebar = tk.Frame(window, bg=BG_SIDEBAR, width=170)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False)

# Лого
try:
    logo_img = tk.PhotoImage(file=resource_path("logo.png"))
    logo_img = logo_img.subsample(3, 3) 
    logo_label = tk.Label(sidebar, image=logo_img, bg=BG_SIDEBAR)
    logo_label.image = logo_img # Важно сохранить ссылку
    logo_label.pack(pady=(20, 10))
except:
    # Заглушка, если файла logo.png нет
    tk.Label(sidebar, text="[ ТУТ ЛОГО ]\nlogo.png", bg="#333", fg="white", width=12, height=3).pack(pady=(20, 10))

# Кнопки
def make_side_btn(text, cmd=None, is_action=False):
    hover_bg = ACCENT_GREEN if is_action else "#3a3a3d"
    btn = tk.Button(sidebar, text=text, bg=BG_SIDEBAR, fg=TEXT_COLOR, relief=tk.SOLID, 
                    borderwidth=1, activebackground=hover_bg, activeforeground="white", command=cmd)
    btn.pack(pady=5, padx=15, fill=tk.X)
    return btn


make_side_btn("О нас", is_action=True, cmd=lambda: o_nas())
make_side_btn("Донат", is_action=True, cmd=lambda: donat())
tk.Label(sidebar, text="Media", bg=BG_SIDEBAR, fg="gray", font=("Arial", 9)).pack(anchor="w", padx=15, pady=(15, 0))
make_side_btn("Выбор\nМедиа", cmd=lambda: select_file(), is_action=True)

# Блок красивых настроек
tk.Label(sidebar, text="Настройки", bg=BG_SIDEBAR, fg="gray", font=("Arial", 9)).pack(anchor="w", padx=15, pady=(20, 5))

milk = tk.IntVar(value=1)
eff = tk.IntVar(value=1)
comp = tk.IntVar(value=0)
slider_int = tk.IntVar(value=0)

# Стилизованные галочки
def make_styled_check(text, var):
    chk = tk.Checkbutton(sidebar, text=text, variable=var, bg=BG_SIDEBAR, fg=TEXT_COLOR,
                         selectcolor=BG_MAIN, activebackground=BG_SIDEBAR, activeforeground=ACCENT_GREEN,
                         relief=tk.FLAT, bd=0, highlightthickness=0)
    chk.pack(anchor="w", padx=15, pady=2)

make_styled_check("Фиолетовый", milk)
make_styled_check("Вырвиглаз", eff)
make_styled_check("Сжать (JPEG)", comp)

tk.Label(sidebar, text="Сжатие:", bg=BG_SIDEBAR, fg="gray", font=("Arial", 8)).pack(anchor="w", padx=15, pady=(10, 0))
slider = tk.Scale(sidebar, variable=slider_int, from_=0, to=100, orient=tk.HORIZONTAL, 
                  bg=BG_SIDEBAR, fg=TEXT_COLOR, bd=0, highlightthickness=0, troughcolor=BG_MAIN, activebackground=ACCENT_GREEN)
slider.pack(fill=tk.X, padx=15)

# Основная рабочая область
main_area = tk.Frame(window, bg=BG_MAIN)
main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Верхняя панель (Top Bar)
top_bar = tk.Frame(main_area, bg=BG_MAIN, height=60)
top_bar.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)

tk.Label(top_bar, text="Milk filter v1", bg=BG_MAIN, fg=TEXT_COLOR, font=("Courier", 14, "bold")).pack(side=tk.LEFT)

# Переключатель
toggle_frame = tk.Frame(top_bar, bg=BTN_DARK, relief=tk.FLAT, bd=2)
toggle_frame.pack(side=tk.LEFT, padx=40)
tk.Label(toggle_frame, text="видео", bg=BTN_DARK, fg="gray", font=("Arial", 10), padx=10, pady=5).pack(side=tk.LEFT)
tk.Label(toggle_frame, text="фотки", bg="#3a3a3d", fg=TEXT_COLOR, font=("Arial", 10), padx=10, pady=5).pack(side=tk.LEFT)

# Правые кнопки
btn_create = tk.Button(top_bar, text="+ Create", bg="#C83F49", fg="white", font=("Arial", 10, "bold"), 
                       relief=tk.FLAT, padx=15, pady=5, activebackground="#A63A40", activeforeground="white", command=lambda: apply_filter())
btn_create.pack(side=tk.RIGHT)

btn_tutor = tk.Button(top_bar, text="тутор", bg=BTN_DARK, fg=TEXT_COLOR, relief=tk.FLAT, padx=15, pady=5,
                      activebackground="#3a3a3d", activeforeground="white", command=lambda: tutor())
btn_tutor.pack(side=tk.RIGHT, padx=10)

# Делилка
content_area = tk.Frame(main_area, bg=BG_MAIN)
content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

# Сетка (москитная)
content_area.columnconfigure(0, weight=1, uniform="panels")
content_area.columnconfigure(1, weight=1, uniform="panels")
content_area.rowconfigure(0, weight=1)

# Лева хрень
left_panel = tk.Frame(content_area, bg=BG_PANEL, highlightbackground="#333", highlightthickness=1)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

tk.Label(left_panel, text="Исходный файл", bg=BG_PANEL, fg="#C83F49", font=("Courier", 12)).pack(anchor="w", padx=15, pady=10)
display_original = tk.Label(left_panel, bg=BG_PANEL)
display_original.pack(expand=True)

tk.Label(left_panel, text="если есть какие то проблемы пишите @eratusiaTT", bg=BG_PANEL, fg="gray", font=("Courier", 9)).pack(anchor="w", padx=15, pady=10)

# Права хрень
right_panel = tk.Frame(content_area, bg=BG_PANEL, highlightbackground="#333", highlightthickness=1)
right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

tk.Label(right_panel, text="Итог", bg=BG_PANEL, fg=ACCENT_GREEN, font=("Courier", 12, "bold")).pack(anchor="w", padx=15, pady=10)
display_filtered = tk.Label(right_panel, bg=BG_PANEL)
display_filtered.pack(expand=True)

btn_save = tk.Button(right_panel, text="Сохранить результат", bg=BTN_DARK, fg=TEXT_COLOR, 
                     relief=tk.FLAT, pady=8, activebackground=ACCENT_GREEN, activeforeground="white", command=lambda: save_filtered())
btn_save.pack(fill=tk.X, padx=15, pady=15)

# --- ФУНКЦИОНАЛ ---
def o_nas():
    webbrowser.open('https://t.me/eratusiaTT')
    
def donat():
    webbrowser.open('https://www.donationalerts.com/r/eratusia')
    
def tutor():
    webbrowser.open('https://github.com/Lerto1928/Milk-filter?tab=readme-ov-file')
    
def show_image(img, widget):
    resized = img.resize((400, 400), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(resized)
    widget.config(image=tk_img)
    widget.image = tk_img

def select_file():
    global filename, original_image, is_video
    file = filedialog.askopenfilename(filetypes=[
        ("Images and Videos", "*.png *.jpg *.jpeg *.bmp *.mp4 *.avi"),
        ("All files", "*.*")
    ])
    if file:
        filename = file
        is_video = file.lower().endswith(('.mp4', '.avi'))
        if is_video:
            toggle_frame.winfo_children()[0].config(bg="#3a3a3d", fg=TEXT_COLOR)
            toggle_frame.winfo_children()[1].config(bg=BTN_DARK, fg="gray")
        else:
            toggle_frame.winfo_children()[0].config(bg=BTN_DARK, fg="gray")
            toggle_frame.winfo_children()[1].config(bg="#3a3a3d", fg=TEXT_COLOR)

        if not is_video:
            original_image = Image.open(file).convert("RGBA")
            show_image(original_image, display_original)
        else:
            cap = cv2.VideoCapture(file)
            ret, frame = cap.read()
            cap.release()
            if ret:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
                original_image = img
                show_image(img, display_original)

def apply_filter():
    global filtered_image, video_temp_output
    if not filename:
        messagebox.showwarning("нет фотачки", "Дурашка, сначала файл выбери (кнопка слева)")
        return

    punt = 70 if eff.get() else 100
    temp_path = filename

    if not is_video:
        if comp.get():
            compressed = Image.open(filename).convert("RGB")
            compressed.save("temp.jpg", quality=100-slider_int.get())
            temp_path = "temp.jpg"
        filtered_image = apply_custom_filter_optimized(temp_path, milk_mode=bool(milk.get()), punt=punt)
        show_image(filtered_image, display_filtered)
    else:
        cap = cv2.VideoCapture(filename)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(temp_fd)
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
            img = apply_custom_filter_optimized(img, milk_mode=bool(milk.get()), punt=punt)
            out_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)
            out.write(out_frame)

        cap.release()
        out.release()
        video_temp_output = temp_path
        messagebox.showinfo("Ура", "Видео полили молочком! Теперь жми Сохранить Итог.")

def save_filtered():
    if not is_video and not filtered_image:
        messagebox.showwarning("Нет фильтра", "фильтр налажи дурашка (кнопка + Create)")
        return

    filetypes = [("PNG", "*.png"), ("JPEG", "*.jpg")] if not is_video else [("MP4 Video", "*.mp4")]
    ext = ".png" if not is_video else ".mp4"

    file = filedialog.asksaveasfilename(defaultextension=ext, filetypes=filetypes)
    if file:
        if not is_video:
            filtered_image.save(file)
        else:
            if video_temp_output:
                os.replace(video_temp_output, file)
                messagebox.showinfo("Готово", "Видео сохранено!")

window.mainloop()