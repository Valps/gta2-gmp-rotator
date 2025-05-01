import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import showinfo
from pathlib import Path

import rotate_gmp
import rotate_miss2
import flip_gmp
import flip_miss2

ROTATION_ANGLES_DICT = {
    #'0° clockwise' : 0,
    '90° clockwise' : 90,
    '180° clockwise' : 180,
    '270° clockwise' : 270
}

FLIP_X = 1
FLIP_Y = 2

FLIP_DICT = {
    'Flip X coordinates' : FLIP_X,
    'Flip Y coordinates' : FLIP_Y
}

def set_field(field : tk.Entry, text : str):
    field.delete(first=0, last="end")
    field.insert(index=0,string=text)

window = tk.Tk()

window.title("Map Rotator/Flipper v1.0.0")
window.rowconfigure(0, weight=1)
window.columnconfigure(0, weight=1)

if Path("rotate.png").exists():
    window.wm_iconphoto(False, tk.PhotoImage(file='rotate.png'))

ROTATE = 0
FLIP = 1
perform_type = tk.IntVar(value=ROTATE)  # 0 = rotate, 1 = flip

# GMP row

gmp_label = tk.Label(text="GMP: ")
gmp_label.grid(row=0, column=0, sticky="E")

gmp_field = tk.Entry(width=50)
gmp_field.grid(row=0, column=1, columnspan=2)

def get_gmp_folder():
    gmp_folder = askopenfilename(title="Select a GMP file", filetypes=[("GTA2 map", ".gmp")])
    if gmp_folder:
        gmp_path = Path(gmp_folder)
        assert gmp_path.exists()

        print(gmp_path)

        gmp_field.delete(first=0, last="end")
        out_field.delete(first=0, last="end")

        gmp_field.insert(index=0,string=str(gmp_path))
        out_field.insert(index=0,string=str(gmp_path.parent))


def get_out_folder():
    out_folder = askdirectory(title="Select a output folder")
    if out_folder:
        out_path = Path(out_folder)
        assert out_path.exists()

        print(out_path)
        out_field.delete(first=0, last="end")
        out_field.insert(index=0,string=str(out_path))

def get_miss_folder():
    miss2_folder = askopenfilename(title="Select a MIS file", filetypes=[("GTA2 source script", ".mis")])
    if miss2_folder:
        miss2_path = Path(miss2_folder)
        assert miss2_path.exists()

        print(miss2_path)
        set_field(miss2_field, text=str(miss2_path))
        #gmp_field.delete(first=0, last="end")
        #out_field.delete(first=0, last="end")

        #gmp_field.insert(index=0,string=str(gmp_path))
        #out_field.insert(index=0,string=str(gmp_path.parent))

gmp_folder_button = tk.Button(text="Search", command=get_gmp_folder)
gmp_folder_button.grid(row=0, column=3)

# Output row

out_label = tk.Label(text="Output: ")
out_label.grid(row=1, column=0, sticky="E")

out_field = tk.Entry(width=50)
out_field.grid(row=1, column=1, columnspan=2)

out_folder_button = tk.Button(text="Search", command=get_out_folder)
out_folder_button.grid(row=1, column=3)

# Miss row

miss2_label = tk.Label(text="Script: ")
miss2_label.grid(row=2, column=0, sticky="E")

miss2_field = tk.Entry(width=50)
miss2_field.grid(row=2, column=1, columnspan=2)
miss2_field.insert(index=0, string="(optional)")

miss2_folder_button = tk.Button(text="Search", command=get_miss_folder)
miss2_folder_button.grid(row=2, column=3)

# rotation list

out_label = tk.Label(text="Angle: ")
out_label.grid(row=3, column=0, sticky="E")

rot_box = ttk.Combobox(window, values=list(ROTATION_ANGLES_DICT.keys()), state="readonly")
rot_box.grid(row=3, column=1, sticky="WE", columnspan=2)

# 'rotate map' button

# TODO: rotate script checkbox

def init_rotate_gmp():
    gmp_path = Path(gmp_field.get())
    out_path = Path(out_field.get())
    miss_path = Path(miss2_field.get())

    # Rotation stuff

    if perform_type.get() == ROTATE:
        
        rotation_angle = ROTATION_ANGLES_DICT.get(rot_box.get(), -2)
        if rotation_angle == -2:
            showinfo("Error!", "Select an angle to rotate.")
            return

        if gmp_field.get(): # if this field is not null

            if not gmp_path.exists():
                showinfo("Error!", "GMP path doesn't exist!")
                return
            elif not out_path.exists():
                showinfo("Error!", "Output path doesn't exist!")
                return
            
            chunk_infos = rotate_gmp.detect_headers_and_get_chunks(gmp_path)

            if chunk_infos == -1:
                showinfo("Error!", "File selected is not a GMP file!")
                return

            return_value = rotate_gmp.rotate_gmp(gmp_path, chunk_infos, rotation_angle, out_path)

            if return_value == 0:
                showinfo("Success!", """GMP rotated successfully!\n\nOBS: you need to open it in "uncompressed" mode on DMA editor and compress it to take effect in GTA2.""")
            elif return_value == -2:
                showinfo("Error!", """This GMP rotator only support uncompressed maps.\n\nOBS: to uncompress a map you need to open it on DMA editor and just click to save it.""")
            else:
                showinfo("Error!", "Some error ocurred during map rotation.")

        if "(optional)" not in str(miss_path) and miss_path.exists() and miss2_field.get():
            if not str(miss_path).endswith(".mis"):
                showinfo("Error!", f"The file {miss_path} isn't a miss2 script file.")
            else:
                return_value = rotate_miss2.main_rotate_miss(miss_path, rotation_angle)
                if return_value == 0:
                    showinfo("Success!", """Script coordinates rotated successfully!""")
                else:
                    showinfo("Error!", "Some error ocurred during script rotation.")

    # Flip stuff

    elif perform_type.get() == FLIP:
        
        flip_type = FLIP_DICT.get(rot_box.get(), -2)
        if flip_type == -2:
            showinfo("Error!", "Select a flip type.")
            return

        if gmp_field.get():

            if not gmp_path.exists():
                showinfo("Error!", "GMP path doesn't exist!")
                return
            elif not out_path.exists():
                showinfo("Error!", "Output path doesn't exist!")
                return

            chunk_infos = flip_gmp.detect_headers_and_get_chunks(gmp_path)

            if chunk_infos == -1:
                showinfo("Error!", "File selected is not a GMP file!")
                return
            
            return_value = flip_gmp.flip_gmp(gmp_path, chunk_infos, flip_type, out_path)

            if return_value == 0:
                showinfo("Success!", """GMP flipped successfully!\n\nOBS: you need to open it in "uncompressed" mode on DMA editor and compress it to take effect in GTA2.""")
            elif return_value == -2:
                showinfo("Error!", """This GMP flipper only support uncompressed maps.\n\nOBS: to uncompress a map you need to open it on DMA editor and just click to save it.""")
            else:
                showinfo("Error!", "Some error ocurred during map flipping.")

        if "(optional)" not in str(miss_path) and miss_path.exists() and miss2_field.get():
            if not str(miss_path).endswith(".mis"):
                showinfo("Error!", f"The file {miss_path} isn't a miss2 script file.")
            else:
                return_value = flip_miss2.main_flip_miss(miss_path, flip_type)
                if return_value == 0:
                    showinfo("Success!", """Script coordinates flipped successfully!""")
                else:
                    showinfo("Error!", "Some error ocurred during script flipping.")

        

def swap_params():
    if perform_type.get() == ROTATE:
        rot_box["values"] = list(ROTATION_ANGLES_DICT.keys())
        rot_box.set("")
        rotate_button["text"] = "Rotate map"
        out_label["text"] = "Angle: "

    elif perform_type.get() == FLIP:
        rot_box["values"] = list(FLIP_DICT.keys())
        rot_box.set("")
        rotate_button["text"] = "Flip map"
        out_label["text"] = "Type: "

rotate_radio_button = tk.Radiobutton(text="Rotate", variable=perform_type, value=ROTATE, command=swap_params)
rotate_radio_button.grid(row=4, column=1)

flip_radio_button = tk.Radiobutton(text="Flip", variable=perform_type, value=FLIP, command=swap_params)
flip_radio_button.grid(row=4, column=2)

rotate_button = tk.Button(text="Rotate map", command=init_rotate_gmp)
rotate_button.grid(row=5, column=1, columnspan=2)



window.mainloop()
