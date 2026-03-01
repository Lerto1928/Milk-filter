import os
import sys
import glob
import threading
import tempfile
import webbrowser
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import ctypes
import shutil

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# HYNYA optimiZZZation (Маски без изменений)
def apply_custom_filter_optimized(image_or_path, milk_mode=True, punt=50):
    is_numpy = isinstance(image_or_path, np.ndarray)
    
    if is_numpy:
        data = image_or_path
    elif isinstance(image_or_path, str):
        image = Image.open(image_or_path).convert("RGBA")
        data = np.array(image)
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

    if is_numpy:
        return output
    return Image.fromarray(output)

# глг первод деняг на мою карту
LANG = {
    "ru": {
        "about": "О нас", "donate": "Донат", "media_sel": "Выбор\nМедиа", "dir_sel": "Выбор\nПапки",
        "settings": "Настройки", "purple": "Фиолетовый", "eyebleed": "Вырвиглаз", "compress": "Сжать (фото)",
        "compress_lbl": "Сжатие:", "video": "видео", "photo": "фотки", "create": "+ Create", "tutor": "тутор",
        "source": "Исходный файл", "support": "если есть какие то проблемы пишите @eratusiaTT",
        "result": "Итог", "save": "Сохранить результат", "lang": "Язык:",
        "warn_nofile": "Дурашка, сначала файл выбери (кнопка слева)",
        "warn_nofilt": "фильтр налажи дурашка (кнопка + Create)",
        "processing": "Обработка...", "done_dir": "Папка обработана!", "dir_ready": "Папки выбраны. Жми Create!"
    },
    "en": {
        "about": "About", "donate": "Donate", "media_sel": "Select\nMedia", "dir_sel": "Select\nFolder",
        "settings": "Settings", "purple": "Purple", "eyebleed": "Eyebleed", "compress": "Compress (photo)",
        "compress_lbl": "Compression:", "video": "video", "photo": "photos", "create": "+ Create", "tutor": "tutorial",
        "source": "Source file", "support": "if you have any problems write to @eratusiaTT",
        "result": "Result", "save": "Save result", "lang": "Language:",
        "warn_nofile": "Silly, select a file first (button on the left)",
        "warn_nofilt": "Apply the filter first, silly (+ Create button)",
        "processing": "Processing...", "done_dir": "Folder processed!", "dir_ready": "Folders picked. Click Create!"
    }
}
current_lang = "ru"
widgets_to_translate = []

def register_translation(widget, key):
    widgets_to_translate.append((widget, key))
    widget.config(text=LANG[current_lang][key])

def change_language(*args):
    global current_lang
    current_lang = lang_var.get()
    for widget, key in widgets_to_translate:
        try:
            widget.config(text=LANG[current_lang][key])
        except: pass

# глобАльные переменные сердец
filename = None
original_image = None
filtered_image = None
is_video = False
video_temp_output = None
processing_mode = "single"
in_dir_path = None
out_dir_path = None

# --- ГУИ УИ ---
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

BG_PANEL = "#1e1e20"
BG_SIDEBAR = "#0d0d0f"
TEXT_COLOR = "#e0e0e0"
ACCENT_GREEN = "#A63A40"
BTN_DARK = "#2a2a2d"

# Боковая панель
sidebar = tk.Frame(window, bg=BG_SIDEBAR, width=170)
sidebar.pack(side=tk.LEFT, fill=tk.Y)
sidebar.pack_propagate(False)

try:
    logo_img = tk.PhotoImage(file=resource_path("logo.png")).subsample(4, 4) 
    logo_label = tk.Label(sidebar, image=logo_img, bg=BG_SIDEBAR)
    logo_label.image = logo_img
    logo_label.pack(pady=(20, 10))
except:
    tk.Label(sidebar, text="[ ТУТ ЛОГО ]\nlogo.png", bg="#333", fg="white", width=12, height=3).pack(pady=(20, 10))

def make_side_btn(key, cmd=None, is_action=False):
    hover_bg = ACCENT_GREEN if is_action else "#3a3a3d"
    btn = tk.Button(sidebar, bg=BG_SIDEBAR, fg=TEXT_COLOR, relief=tk.SOLID, 
                    borderwidth=1, activebackground=hover_bg, activeforeground="white", command=cmd)
    btn.pack(pady=5, padx=15, fill=tk.X)
    register_translation(btn, key)
    return btn

make_side_btn("about", is_action=True, cmd=lambda: webbrowser.open('https://t.me/eratusiaTT'))
make_side_btn("donate", is_action=True, cmd=lambda: webbrowser.open('https://www.donationalerts.com/r/eratusia'))

lbl_media_cat = tk.Label(sidebar, bg=BG_SIDEBAR, fg="gray", font=("Arial", 9))
lbl_media_cat.pack(anchor="w", padx=15, pady=(15, 0))
register_translation(lbl_media_cat, "media_sel") 
btn_sel_media = make_side_btn("media_sel", cmd=lambda: select_file(), is_action=True)
btn_sel_dir = make_side_btn("dir_sel", cmd=lambda: select_directory(), is_action=True)

lbl_settings = tk.Label(sidebar, bg=BG_SIDEBAR, fg="gray", font=("Arial", 9))
lbl_settings.pack(anchor="w", padx=15, pady=(20, 5))
register_translation(lbl_settings, "settings")

milk, eff, comp, slider_int = tk.IntVar(value=1), tk.IntVar(value=1), tk.IntVar(value=0), tk.IntVar(value=0)

def make_styled_check(key, var):
    chk = tk.Checkbutton(sidebar, variable=var, bg=BG_SIDEBAR, fg=TEXT_COLOR,
                         selectcolor=BG_MAIN, activebackground=BG_SIDEBAR, activeforeground=ACCENT_GREEN,
                         relief=tk.FLAT, bd=0, highlightthickness=0)
    chk.pack(anchor="w", padx=15, pady=2)
    register_translation(chk, key)

make_styled_check("purple", milk)
make_styled_check("eyebleed", eff)
make_styled_check("compress", comp)

lbl_comp = tk.Label(sidebar, bg=BG_SIDEBAR, fg="gray", font=("Arial", 8))
lbl_comp.pack(anchor="w", padx=15, pady=(10, 0))
register_translation(lbl_comp, "compress_lbl")

slider = tk.Scale(sidebar, variable=slider_int, from_=0, to=100, orient=tk.HORIZONTAL, 
                  bg=BG_SIDEBAR, fg=TEXT_COLOR, bd=0, highlightthickness=0, troughcolor=BG_MAIN, activebackground=ACCENT_GREEN)
slider.pack(fill=tk.X, padx=15)

# блок и правый хук языка
lang_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
lang_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=15)
lbl_lang = tk.Label(lang_frame, bg=BG_SIDEBAR, fg="gray", font=("Arial", 8))
lbl_lang.pack(anchor="w")
register_translation(lbl_lang, "lang")
lang_var = tk.StringVar(value="ru")
lang_menu = tk.OptionMenu(lang_frame, lang_var, "ru", "en", command=change_language)
lang_menu.config(bg=BG_SIDEBAR, fg=TEXT_COLOR, bd=1, highlightthickness=0, activebackground=BTN_DARK, relief=tk.SOLID)
lang_menu["menu"].config(bg=BG_SIDEBAR, fg=TEXT_COLOR)
lang_menu.pack(anchor="w", fill=tk.X)

# основная рабочая область
main_area = tk.Frame(window, bg=BG_MAIN)
main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

top_bar = tk.Frame(main_area, bg=BG_MAIN, height=60)
top_bar.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)

tk.Label(top_bar, text="Milk filter v1", bg=BG_MAIN, fg=TEXT_COLOR, font=("Courier", 14, "bold")).pack(side=tk.LEFT)

toggle_frame = tk.Frame(top_bar, bg=BTN_DARK, relief=tk.FLAT, bd=2)
toggle_frame.pack(side=tk.LEFT, padx=40)
lbl_vid_tog = tk.Label(toggle_frame, bg=BTN_DARK, fg="gray", font=("Arial", 10), padx=10, pady=5)
lbl_vid_tog.pack(side=tk.LEFT)
register_translation(lbl_vid_tog, "video")
lbl_pho_tog = tk.Label(toggle_frame, bg="#3a3a3d", fg=TEXT_COLOR, font=("Arial", 10), padx=10, pady=5)
lbl_pho_tog.pack(side=tk.LEFT)
register_translation(lbl_pho_tog, "photo")

btn_create = tk.Button(top_bar, bg="#C83F49", fg="white", font=("Arial", 10, "bold"), 
                       relief=tk.FLAT, padx=15, pady=5, activebackground="#A63A40", activeforeground="white", command=lambda: apply_filter())
btn_create.pack(side=tk.RIGHT)
register_translation(btn_create, "create")

btn_tutor = tk.Button(top_bar, bg=BTN_DARK, fg=TEXT_COLOR, relief=tk.FLAT, padx=15, pady=5,
                      activebackground="#3a3a3d", activeforeground="white", command=lambda: webbrowser.open('https://github.com/Lerto1928/Milk-filter?tab=readme-ov-file'))
btn_tutor.pack(side=tk.RIGHT, padx=10)
register_translation(btn_tutor, "tutor")

content_area = tk.Frame(main_area, bg=BG_MAIN)
content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
content_area.columnconfigure(0, weight=1, uniform="panels")
content_area.columnconfigure(1, weight=1, uniform="panels")
content_area.rowconfigure(0, weight=1)

left_panel = tk.Frame(content_area, bg=BG_PANEL, highlightbackground="#333", highlightthickness=1)
left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
lbl_src = tk.Label(left_panel, bg=BG_PANEL, fg="#C83F49", font=("Courier", 12))
lbl_src.pack(anchor="w", padx=15, pady=10)
register_translation(lbl_src, "source")
display_original = tk.Label(left_panel, bg=BG_PANEL)
display_original.pack(expand=True)
lbl_sup = tk.Label(left_panel, bg=BG_PANEL, fg="gray", font=("Courier", 9))
lbl_sup.pack(anchor="w", padx=15, pady=10)
register_translation(lbl_sup, "support")

right_panel = tk.Frame(content_area, bg=BG_PANEL, highlightbackground="#333", highlightthickness=1)
right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
lbl_res = tk.Label(right_panel, bg=BG_PANEL, fg=ACCENT_GREEN, font=("Courier", 12, "bold"))
lbl_res.pack(anchor="w", padx=15, pady=10)
register_translation(lbl_res, "result")
display_filtered = tk.Label(right_panel, bg=BG_PANEL)
display_filtered.pack(expand=True)

btn_save = tk.Button(right_panel, bg=BTN_DARK, fg=TEXT_COLOR, relief=tk.FLAT, pady=8, activebackground=ACCENT_GREEN, activeforeground="white", command=lambda: save_filtered())
btn_save.pack(fill=tk.X, padx=15, pady=15)
register_translation(btn_save, "save")

# --- ФУНКЦИОНАЛ ---
def show_image(img, widget):
    img_copy = img.copy()
    img_copy.thumbnail((400, 400), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(img_copy)
    widget.config(image=tk_img)
    widget.image = tk_img

def select_file():
    global filename, original_image, is_video, processing_mode
    processing_mode = "single"
    file = filedialog.askopenfilename(filetypes=[("Images/Videos", "*.png *.jpg *.jpeg *.bmp *.mp4 *.avi"), ("All files", "*.*")])
    if file:
        filename = file
        is_video = file.lower().endswith(('.mp4', '.avi'))
        lbl_src.config(text=LANG[current_lang]["source"])
        if is_video:
            lbl_vid_tog.config(bg="#3a3a3d", fg=TEXT_COLOR)
            lbl_pho_tog.config(bg=BTN_DARK, fg="gray")
            cap = cv2.VideoCapture(file)
            ret, frame = cap.read()
            cap.release()
            if ret:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
                original_image = img
                show_image(img, display_original)
        else:
            lbl_vid_tog.config(bg=BTN_DARK, fg="gray")
            lbl_pho_tog.config(bg="#3a3a3d", fg=TEXT_COLOR)
            original_image = Image.open(file).convert("RGBA")
            show_image(original_image, display_original)

def select_directory():
    global in_dir_path, out_dir_path, processing_mode
    in_dir = filedialog.askdirectory(title="Выберите папку с медиа")
    if not in_dir: return
    out_dir = filedialog.askdirectory(title="Выберите папку для сохранения (куда)")
    if not out_dir: return

    in_dir_path = in_dir
    out_dir_path = out_dir
    processing_mode = "directory"
    lbl_src.config(text=LANG[current_lang]["dir_ready"])
    
    # показывая что мы в режиме потока
    display_original.config(image='')
    display_filtered.config(image='')

# запуск фильтра
def apply_filter():
    global filtered_image, video_temp_output
    punt = 70 if eff.get() else 100
    milk_val = bool(milk.get())

    if processing_mode == "directory":
        if not in_dir_path or not out_dir_path:
            messagebox.showwarning("Warning", LANG[current_lang]["warn_nofile"])
            return
        btn_create.config(text=LANG[current_lang]["processing"], state=tk.DISABLED)
        threading.Thread(target=process_dir_thread, args=(in_dir_path, out_dir_path, milk_val, punt), daemon=True).start()
    
    elif processing_mode == "single":
        if not filename:
            messagebox.showwarning("Warning", LANG[current_lang]["warn_nofile"])
            return

        if not is_video:
            temp_path = filename
            if comp.get():
                compressed = Image.open(filename).convert("RGB")
                compressed.save("temp.jpg", quality=100-slider_int.get())
                temp_path = "temp.jpg"
            filtered_image = apply_custom_filter_optimized(temp_path, milk_mode=milk_val, punt=punt)
            show_image(filtered_image, display_filtered)
        else:
            btn_create.config(text=LANG[current_lang]["processing"], state=tk.DISABLED)
            threading.Thread(target=process_single_video_thread, args=(filename, milk_val, punt), daemon=True).start()

# потоки
def process_dir_thread(in_dir, out_dir, milk_mode, punt):
    exts = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.mp4', '*.avi')
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(in_dir, ext)))
        files.extend(glob.glob(os.path.join(in_dir, ext.upper())))

    for f in files:
        try:
            is_vid = f.lower().endswith(('.mp4', '.avi'))
            base_name = os.path.basename(f)
            
            #показываем исходник который в обработке
            if is_vid:
                cap = cv2.VideoCapture(f)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    src_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
                    window.after(0, lambda img=src_img: show_image(img, display_original))
            else:
                src_img = Image.open(f).convert("RGBA")
                window.after(0, lambda img=src_img: show_image(img, display_original))

            # обрабатываем
            if is_vid:
                out_name = os.path.splitext(base_name)[0] + ".mp4"
                out_path = os.path.join(out_dir, "processed_" + out_name)
                
                cap = cv2.VideoCapture(f)
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps == 0 or fps is None or np.isnan(fps): fps = 24.0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Устанавливаем кодек H.264
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
                
                first_frame_img = None
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # переводим в RGBA
                    rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    out_rgba = apply_custom_filter_optimized(rgba, milk_mode, punt)
                    # переводим обратно в BGR
                    out_bgr = cv2.cvtColor(out_rgba, cv2.COLOR_RGBA2BGR)
                    
                    out.write(out_bgr)
                    
                    if frame_count == 0:
                        first_frame_img = Image.fromarray(cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
                    frame_count += 1
                
                cap.release()
                out.release()
                
                # выводим итог
                if first_frame_img is not None:
                    window.after(0, lambda img=first_frame_img: show_image(img, display_filtered))

            else:
                out_path = os.path.join(out_dir, "processed_" + base_name)
                img_result = apply_custom_filter_optimized(f, milk_mode, punt)
                
                if base_name.lower().endswith(('.jpg', '.jpeg')):
                    img_result.convert("RGB").save(out_path, quality=90)
                else:
                    img_result.save(out_path)
                
                window.after(0, lambda img=img_result: show_image(img, display_filtered))
                
        except Exception as e:
            print(f"Error processing {f}: {e}")

    window.after(0, lambda: [
        btn_create.config(text=LANG[current_lang]["create"], state=tk.NORMAL),
        lbl_src.config(text=LANG[current_lang]["source"]),
        messagebox.showinfo("Success", LANG[current_lang]["done_dir"])
    ])

def process_single_video_thread(input_file, milk_mode, punt):
    global video_temp_output, filtered_image
    temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(temp_fd)
    
    try:
        cap = cv2.VideoCapture(input_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None or np.isnan(fps): fps = 24.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # ставим кодек H.264
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
        
        first_frame_img = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            out_rgba = apply_custom_filter_optimized(rgba, milk_mode=milk_mode, punt=punt)
            out_bgr = cv2.cvtColor(out_rgba, cv2.COLOR_RGBA2BGR)
            
            out.write(out_bgr)
            
            if frame_count == 0:
                first_frame_img = Image.fromarray(cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
            frame_count += 1
            
        cap.release()
        out.release()
        
        video_temp_output = temp_path
        
        if first_frame_img is not None:
            window.after(0, lambda: on_video_processed(first_frame_img))
        else:
            window.after(0, lambda: btn_create.config(text=LANG[current_lang]["create"], state=tk.NORMAL))
            
    except Exception as e:
        print("Video Processing Error:", e)
        window.after(0, lambda: btn_create.config(text=LANG[current_lang]["create"], state=tk.NORMAL))

def on_video_processed(preview_img):
    global filtered_image
    filtered_image = preview_img
    show_image(preview_img, display_filtered)
    btn_create.config(text=LANG[current_lang]["create"], state=tk.NORMAL)

def save_filtered():
    if not is_video and not filtered_image:
        messagebox.showwarning("Warning", LANG[current_lang]["warn_nofilt"])
        return

    filetypes = [("PNG", "*.png"), ("JPEG", "*.jpg")] if not is_video else [("MP4 Video", "*.mp4")]
    ext = ".png" if not is_video else ".mp4"

    file = filedialog.asksaveasfilename(defaultextension=ext, filetypes=filetypes)
    if file:
        if not is_video:
            if file.lower().endswith(('.jpg', '.jpeg')):
                q = 100 - slider_int.get() if comp.get() else 95
                filtered_image.convert("RGB").save(file, quality=q, optimize=True)
            else:
                filtered_image.save(file, optimize=True)
        else:
            if video_temp_output:
                shutil.copy2(video_temp_output, file)

window.mainloop()