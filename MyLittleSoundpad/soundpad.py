import os
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox

import sounddevice as sd
import soundfile as sf




SOUNDS_FOLDER = "sounds"

SUPPORTED_FORMATS = (
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
)


OUTPUT_DEVICE_NAME = "Hoparlör (Realtek(R) Audio)"




sound_files = []
audio_cache = {}




def find_output_device():

    devices = sd.query_devices()

    # Önce bizim belirlediğimiz cihazı ara
    for index, device in enumerate(devices):

        name = device["name"]

        if (
            OUTPUT_DEVICE_NAME.lower() in name.lower()
            and device["max_output_channels"] > 0
        ):
            return index


    try:
        default_device = sd.default.device

        if isinstance(default_device, (list, tuple)):
            output_device = default_device[1]
        else:
            output_device = default_device

        if output_device is not None and output_device >= 0:
            return output_device

    except Exception:
        pass

    return None




def load_audio(path):

    # Daha önce yüklenmişse tekrar dönüştürme
    if path in audio_cache:
        return audio_cache[path]

    try:

        extension = os.path.splitext(path)[1].lower()

      

        if extension == ".mp3":

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            )

            temp_path = temp_file.name

            temp_file.close()

            try:

                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-loglevel",
                        "error",
                        "-i",
                        path,
                        "-acodec",
                        "pcm_s16le",
                        temp_path
                    ],
                    check=True
                )

                data, samplerate = sf.read(
                    temp_path,
                    dtype="float32"
                )

            finally:

                if os.path.exists(temp_path):
                    os.remove(temp_path)



        else:

            data, samplerate = sf.read(
                path,
                dtype="float32"
            )

        audio = {
            "data": data,
            "samplerate": samplerate
        }

        audio_cache[path] = audio

        return audio

    except FileNotFoundError:

        messagebox.showerror(
            "FFmpeg bulunamadı",
            "FFmpeg bulunamadı.\n\n"
            "Terminalde şu komutu çalıştır:\n\n"
            "ffmpeg -version"
        )

        return None

    except Exception as error:

        messagebox.showerror(
            "Ses yüklenemedi",
            f"{os.path.basename(path)}\n\n"
            f"Hata:\n{error}"
        )

        return None



def play_sound(path):

    audio = load_audio(path)

    if audio is None:
        return

    try:

        # Önce mevcut sesi durdur
        sd.stop()

        device = find_output_device()

        if device is None:

            messagebox.showerror(
                "Ses cihazı bulunamadı",
                "Normal ses çıkış cihazı bulunamadı."
            )

            return

        sd.play(
            audio["data"],
            audio["samplerate"],
            device=device
        )

        status_var.set(
            "▶ " + os.path.basename(path)
        )

    except Exception as error:

        messagebox.showerror(
            "Ses oynatılamadı",
            str(error)
        )




def stop_sound():

    try:
        sd.stop()
        status_var.set("■ Durduruldu")

    except Exception as error:

        status_var.set(
            f"Hata: {error}"
        )




def refresh_sounds():

    global sound_files

    sound_files = []

    # Cache temizle
    audio_cache.clear()

 
    for widget in sound_frame.winfo_children():
        widget.destroy()


    if not os.path.exists(SOUNDS_FOLDER):

        os.makedirs(
            SOUNDS_FOLDER
        )


    files = []

    for filename in os.listdir(SOUNDS_FOLDER):

        if filename.lower().endswith(
            SUPPORTED_FORMATS
        ):
            files.append(filename)


    files.sort(
        key=lambda x: x.lower()
    )

    sound_files = files



    if not sound_files:

        empty_label = tk.Label(
            sound_frame,
            text=(
                "sounds klasöründe ses bulunamadı.\n\n"
                "MP3 dosyalarını buraya koy."
            ),
            bg="#151515",
            fg="#777777",
            font=("Segoe UI", 11),
            justify="center"
        )

        empty_label.pack(
            pady=50
        )

        status_var.set(
            "0 ses bulundu"
        )

        return



    for index, filename in enumerate(
        sound_files,
        start=1
    ):

        create_sound_row(
            index,
            filename
        )

    status_var.set(
        f"{len(sound_files)} ses bulundu"
    )

    sound_frame.update_idletasks()

    canvas.configure(
        scrollregion=canvas.bbox("all")
    )




def create_sound_row(
    index,
    filename
):

    row = tk.Frame(
        sound_frame,
        bg="#202020",
        height=50
    )

    row.pack(
        fill="x",
        padx=10,
        pady=4
    )

    row.pack_propagate(False)



    number_label = tk.Label(
        row,
        text=f"{index:02}",
        width=4,
        bg="#202020",
        fg="#888888",
        font=(
            "Segoe UI",
            10,
            "bold"
        )
    )

    number_label.pack(
        side="left"
    )

  

    name_label = tk.Label(
        row,
        text=filename,
        bg="#202020",
        fg="white",
        anchor="w",
        font=(
            "Segoe UI",
            10
        )
    )

    name_label.pack(
        side="left",
        fill="x",
        expand=True
    )


    play_button = tk.Button(
        row,
        text="▶",
        command=lambda f=filename: play_sound(
            os.path.join(
                SOUNDS_FOLDER,
                f
            )
        ),
        bg="#303030",
        fg="white",
        activebackground="#454545",
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        width=5,
        cursor="hand2"
    )

    play_button.pack(
        side="right",
        padx=5
    )




def key_pressed(event):

    key = event.keysym


    if key == "Escape":

        stop_sound()

        return


    if key == "F5":

        refresh_sounds()

        return


    if key == "0":

        stop_sound()
        root.destroy()

        return

 

    if key in (
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9"
    ):

        number = int(key)

        if number <= len(sound_files):

            filename = sound_files[
                number - 1
            ]

            path = os.path.join(
                SOUNDS_FOLDER,
                filename
            )

            play_sound(path)




root = tk.Tk()

root.title(
    "My Soundpad"
)

root.geometry(
    "650x650"
)

root.minsize(
    500,
    400
)

root.configure(
    bg="#101010"
)




title_label = tk.Label(
    root,
    text="MY SOUNDPAD",
    bg="#101010",
    fg="white",
    font=(
        "Segoe UI",
        22,
        "bold"
    )
)

title_label.pack(
    pady=(20, 5)
)




subtitle_label = tk.Label(
    root,
    text=(
        "1-9 Çal   •   ESC Durdur   •   "
        "F5 Yenile   •   0 Çıkış"
    ),
    bg="#101010",
    fg="#888888",
    font=(
        "Segoe UI",
        10
    )
)

subtitle_label.pack(
    pady=(0, 15)
)




container = tk.Frame(
    root,
    bg="#151515"
)

container.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)




canvas = tk.Canvas(
    container,
    bg="#151515",
    highlightthickness=0
)

canvas.pack(
    side="left",
    fill="both",
    expand=True
)




scrollbar = ttk.Scrollbar(
    container,
    orient="vertical",
    command=canvas.yview
)

scrollbar.pack(
    side="right",
    fill="y"
)

canvas.configure(
    yscrollcommand=scrollbar.set
)




sound_frame = tk.Frame(
    canvas,
    bg="#151515"
)

canvas_window = canvas.create_window(
    (0, 0),
    window=sound_frame,
    anchor="nw"
)




def update_scroll_region(event=None):

    canvas.configure(
        scrollregion=canvas.bbox("all")
    )


sound_frame.bind(
    "<Configure>",
    update_scroll_region
)



def resize_sound_frame(event):

    canvas.itemconfig(
        canvas_window,
        width=event.width
    )


canvas.bind(
    "<Configure>",
    resize_sound_frame
)




bottom_frame = tk.Frame(
    root,
    bg="#101010"
)

bottom_frame.pack(
    fill="x",
    padx=15,
    pady=15
)




status_var = tk.StringVar(
    value="Hazır"
)

status_label = tk.Label(
    bottom_frame,
    textvariable=status_var,
    bg="#101010",
    fg="#aaaaaa",
    anchor="w",
    font=(
        "Segoe UI",
        9
    )
)

status_label.pack(
    side="left",
    fill="x",
    expand=True
)




refresh_button = tk.Button(
    bottom_frame,
    text="⟳ Yenile",
    command=refresh_sounds,
    bg="#303030",
    fg="white",
    activebackground="#454545",
    activeforeground="white",
    relief="flat",
    borderwidth=0,
    padx=15,
    pady=7,
    cursor="hand2"
)

refresh_button.pack(
    side="right",
    padx=5
)




stop_button = tk.Button(
    bottom_frame,
    text="■ Durdur",
    command=stop_sound,
    bg="#303030",
    fg="white",
    activebackground="#454545",
    activeforeground="white",
    relief="flat",
    borderwidth=0,
    padx=15,
    pady=7,
    cursor="hand2"
)

stop_button.pack(
    side="right",
    padx=5
)



root.bind(
    "<Key>",
    key_pressed
)




refresh_sounds()

root.mainloop()