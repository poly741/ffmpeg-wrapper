import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import os
import sys

# Try to use tkinterdnd2 for drag & drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    root = TkinterDnD.Tk()
    DND_AVAILABLE = True
except ImportError:
    root = tk.Tk()
    DND_AVAILABLE = False
    print("For drag & drop support, install: pip install tkinterdnd2")


# Now set up the GUI with this root
root.title("FFmpeg Utility")
root.geometry("700x500")  # Made slightly taller

# Set icon - fixed path handling
try:
    # Get the directory where the script is located
    if getattr(sys, 'frozen', False):
        # If running as exe
        script_dir = os.path.dirname(sys.executable)
    else:
        # If running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(script_dir, "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    else:
        print(f"Icon not found at: {icon_path}")
except Exception as e:
    print(f"Could not set icon: {e}")

# Dark mode colors
bg = "#1e1e1e"
fg = "#ffffff"
entry_bg = "#2d2d2d"
button_bg = "#3c3c3c"
list_bg = "#2d2d2d"
button_fg = "#ffffff"
selected_bg = "#404040"

root.configure(bg=bg)

# Functions
def add_files():
    files = filedialog.askopenfilenames(
        title="Select Video Files",
        filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.webm")]
    )
    for f in files:
        if f not in file_list.get(0, tk.END):
            file_list.insert(tk.END, f)
    update_status()

def remove_selected():
    selected = list(file_list.curselection())
    selected.reverse()
    for i in selected:
        file_list.delete(i)
    update_status()

def clear_all():
    file_list.delete(0, tk.END)
    update_status()

def update_status():
    count = file_list.size()
    status_label.config(text=f"Ready - {count} file(s) loaded")

def convert_all():
    files = file_list.get(0, tk.END)
    if not files:
        messagebox.showwarning("No files", "Add at least one file to convert.")
        return
    
    # Disable buttons during conversion
    convert_btn.config(state=tk.DISABLED)
    add_btn.config(state=tk.DISABLED)
    remove_btn.config(state=tk.DISABLED)
    clear_btn.config(state=tk.DISABLED)
    
    threading.Thread(target=run_conversion, args=(files,), daemon=True).start()

def run_conversion(files):
    successful = 0
    failed = 0
    
    root.after(0, lambda: progress_bar.configure(maximum=len(files), value=0))
    
    for idx, input_file in enumerate(files, 1):
        output_file = os.path.splitext(input_file)[0] + "_converted.mp4"
        command = ["ffmpeg", "-i", input_file, "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-y", output_file]

        # Update status safely using after()
        root.after(0, lambda f=input_file: status_label.config(text=f"Converting: {os.path.basename(f)}"))

        # Run ffmpeg
        try:
            # Check if ffmpeg is available
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            
            # Run the actual conversion
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                successful += 1
            else:
                failed += 1
                print(f"FFmpeg error for {input_file}: {result.stderr}")
                
        except subprocess.CalledProcessError:
            failed += 1
            root.after(0, lambda f=input_file: messagebox.showerror("Error", f"Failed to convert: {os.path.basename(f)}"))
        except FileNotFoundError:
            root.after(0, lambda: messagebox.showerror("Error", 
                        "FFmpeg not found!\n\nPlease install FFmpeg and add it to your PATH:\n"
                        "1. Download from: https://ffmpeg.org/download.html\n"
                        "2. Add to system PATH or place ffmpeg.exe in the same folder"))
            break

        # Update progress
        root.after(0, lambda i=idx: progress_bar.configure(value=i))

    # Re-enable buttons
    root.after(0, lambda: convert_btn.config(state=tk.NORMAL))
    root.after(0, lambda: add_btn.config(state=tk.NORMAL))
    root.after(0, lambda: remove_btn.config(state=tk.NORMAL))
    root.after(0, lambda: clear_btn.config(state=tk.NORMAL))
    
    if failed == 0:
        root.after(0, lambda: status_label.config(text=f"All done! Converted {successful} file(s)"))
        root.after(0, lambda: messagebox.showinfo("Finished", f"All {successful} videos converted successfully!"))
    else:
        root.after(0, lambda: status_label.config(text=f"Completed with {failed} failure(s)"))
        root.after(0, lambda: messagebox.showwarning("Finished", 
                    f"Converted: {successful}\nFailed: {failed}\n\nCheck console for details."))

# Drag & Drop function
def drop(event):
    # Handle different event data formats
    data = event.data
    
    # Remove curly braces and split
    files = []
    current = ""
    in_braces = False
    
    for char in data:
        if char == '{':
            in_braces = True
            current = ""
        elif char == '}':
            in_braces = False
            if current:
                files.append(current)
        elif char == ' ' and not in_braces:
            if current:
                files.append(current)
                current = ""
        else:
            current += char
    
    if current:
        files.append(current)
    
    # Add valid files
    added = 0
    for f in files:
        f = f.strip()
        if os.path.isfile(f) and f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')):
            if f not in file_list.get(0, tk.END):
                file_list.insert(tk.END, f)
                added += 1
    
    if added > 0:
        update_status()

# Title
title = tk.Label(root, text="FFmpeg Video Converter", font=("Segoe UI", 18, "bold"), bg=bg, fg=fg)
title.pack(pady=(15, 5))

# Subtitle / info
if DND_AVAILABLE:
    info_text = "Drag & drop files here or use buttons below"
else:
    info_text = "Install 'pip install tkinterdnd2' for drag & drop support"
info_label = tk.Label(root, text=info_text, font=("Segoe UI", 9), bg=bg, fg="#888888")
info_label.pack(pady=(0, 10))

# File list box with frame
file_frame = tk.Frame(root, bg=bg)
file_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=15)

# Create listbox with scrollbar
listbox_frame = tk.Frame(file_frame, bg=bg)
listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

file_list = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, bg=list_bg, fg=fg, 
                       width=80, height=12, borderwidth=1, highlightthickness=1,
                       highlightbackground="#404040", selectbackground=selected_bg,
                       selectforeground=fg, font=("Segoe UI", 10))
file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Configure selection colors
file_list.configure(selectbackground=selected_bg, selectforeground=fg)

scrollbar = tk.Scrollbar(listbox_frame, command=file_list.yview, bg=button_bg, troughcolor=bg)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
file_list.config(yscrollcommand=scrollbar.set)

# Buttons frame
button_frame = tk.Frame(root, bg=bg)
button_frame.pack(pady=10)

# Style for buttons
button_style = {
    'bg': button_bg,
    'fg': button_fg,
    'padx': 20,
    'pady': 8,
    'borderwidth': 1,
    'relief': tk.FLAT,
    'font': ("Segoe UI", 10),
    'activebackground': "#505050",
    'activeforeground': fg
}

add_btn = tk.Button(button_frame, text="Add Files", command=add_files, **button_style)
add_btn.grid(row=0, column=0, padx=5)

remove_btn = tk.Button(button_frame, text="Remove Selected", command=remove_selected, **button_style)
remove_btn.grid(row=0, column=1, padx=5)

clear_btn = tk.Button(button_frame, text="Clear All", command=clear_all, **button_style)
clear_btn.grid(row=0, column=2, padx=5)

convert_btn = tk.Button(button_frame, text="Convert All", command=convert_all, 
                       bg="#2a6d2a", fg=fg, padx=20, pady=8, borderwidth=1,
                       relief=tk.FLAT, font=("Segoe UI", 10, "bold"),
                       activebackground="#3a8a3a", activeforeground=fg)
convert_btn.grid(row=0, column=3, padx=5)

# Progress bar and status
progress_frame = tk.Frame(root, bg=bg)
progress_frame.pack(pady=(10, 5), fill=tk.X, padx=15)

progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
progress_bar.pack(fill=tk.X, expand=True)

# Status bar at bottom
status_frame = tk.Frame(root, bg="#2d2d2d", height=25)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)
status_frame.pack_propagate(False)

status_label = tk.Label(status_frame, text="Ready - 0 file(s) loaded", 
                       bg="#2d2d2d", fg="#aaaaaa", anchor=tk.W, padx=10)
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Enable drag & drop if available
if DND_AVAILABLE:
    file_list.drop_target_register(DND_FILES)
    file_list.dnd_bind('<<Drop>>', drop)

# Start the app
if __name__ == "__main__":
    root.mainloop()