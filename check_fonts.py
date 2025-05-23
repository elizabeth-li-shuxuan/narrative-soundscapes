import tkinter as tk
import tkinter.font as tkfont

root = tk.Tk()
for f in sorted(tkfont.families()):
    print(f)
root.destroy()
