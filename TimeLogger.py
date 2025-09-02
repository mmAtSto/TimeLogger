import tkinter as tk
import csv
from datetime import datetime

def start_logging():
    global running
    if not running:
        running = True

def stop_logging():
    global running
    if running:
        series_count = entry.get()
        if series_count:
            with open("log.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now().isoformat(), series_count])
            running = False
            entry.delete(0, tk.END)  # Eingabefeld leeren

# Einfaches GUI-Fenster
root = tk.Tk()
root.title("Logger")

running = False

tk.Label(root, text="Anzahl Serien:").pack()
entry = tk.Entry(root)
entry.pack()

start_btn = tk.Button(root, text="Start", command=start_logging)
start_btn.pack()

stop_btn = tk.Button(root, text="Stop", command=stop_logging)
stop_btn.pack()

root.mainloop()
