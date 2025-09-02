import tkinter as tk
from tkinter import ttk
import csv
from datetime import datetime
from pathlib import Path
import sys

CSV_PATH = Path("log.csv")
DT_FMT = "%Y-%m-%d %H:%M:%S"  # Excel-freundlich


# ---------- CSV Utils ----------
def ensure_csv():
    if not CSV_PATH.exists():
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CSV_PATH.open("w", newline="") as f:
            pass  # kein Header

def read_rows():
    ensure_csv()
    with CSV_PATH.open("r", newline="") as f:
        return [row for row in csv.reader(f)]

def write_rows(rows):
    with CSV_PATH.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)

def append_row(row):
    with CSV_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        w.writerow(row)

def last_row_open_session(rows):
    """
    Offene Session = letzte Zeile hat start_time, aber leeres stop_time.
    Schema: [start_time, stop_time, series_count]
    """
    if not rows:
        return None
    last = rows[-1]
    if len(last) >= 2 and last[0] and (last[1] == "" or last[1] is None):
        return len(rows) - 1
    return None


# ---------- App ----------
class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=16)
        self.master = master
        self.running = False
        self.resume_bar = None  # Hinweisbalken bei offener Session

        # Theme (macOS Aqua ignoriert Farben -> 'clam')
        style = ttk.Style()
        if sys.platform == "darwin":
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        # Layout
        self.grid(sticky="nsew")
        self.master.title("Serien-Logger")
        self.master.minsize(460, 250)
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        container = ttk.Frame(self, padding=(12, 12, 12, 12))
        container.grid(sticky="nsew")
        container.columnconfigure(1, weight=1)

        # (optional) Resume-Bar Platzhalter – wird nur angezeigt, falls nötig
        self.resume_container = ttk.Frame(container)
        self.resume_container.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.resume_container.grid_remove()

        title = ttk.Label(container, text="Serien-Logger", font=("Arial", 16, "bold"))
        title.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(container, text="CSV-Datei:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.csv_var = tk.StringVar(value=str(CSV_PATH.resolve()))
        ttk.Entry(container, textvariable=self.csv_var, state="readonly").grid(
            row=2, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(0, 6)
        )

        ttk.Label(container, text="Anzahl Serien (Pflicht bei Stop):").grid(row=3, column=0, sticky="w")
        self.entry_series = ttk.Entry(container, width=12)
        self.entry_series.grid(row=3, column=1, sticky="w", padx=(8, 0))

        self.status_dot = ttk.Label(container, text="●", foreground="grey")
        self.status_dot.grid(row=3, column=2, sticky="e")

        btns = ttk.Frame(container, padding=(0, 8, 0, 0))
        btns.grid(row=4, column=0, columnspan=3, sticky="w")
        self.btn_start = ttk.Button(btns, text="Start", command=self.on_start, width=14)
        self.btn_stop = ttk.Button(btns, text="Stop", command=self.on_stop, width=14, state="disabled")
        self.btn_start.grid(row=0, column=0, padx=(0, 8))
        self.btn_stop.grid(row=0, column=1)

        self.msg_var = tk.StringVar(value="")
        self.msg_label = ttk.Label(container, textvariable=self.msg_var, foreground="#444", wraplength=420, justify="left")
        self.msg_label.grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.entry_series.bind("<Return>", lambda e: self.on_stop() if self.running else self.on_start())

        # CSV prüfen und ggf. Resume anbieten
        ensure_csv()
        self.check_resume_on_launch()

    # ---------- UI helpers ----------
    def set_message(self, text, kind="info"):
        colors = {"info": "#444", "ok": "#2fa14f", "warn": "#b58900", "error": "#c0392b"}
        self.msg_var.set(text)
        self.msg_label.configure(foreground=colors.get(kind, "#444"))

    def set_running_ui(self, running: bool):
        self.running = running
        if running:
            self.btn_start.state(["disabled"])
            self.btn_stop.state(["!disabled"])
            self.status_dot.configure(foreground="#2fa14f")
        else:
            self.btn_start.state(["!disabled"])
            self.btn_stop.state(["disabled"])
            self.status_dot.configure(foreground="grey")

    # ---------- Resume-Logik ----------
    def check_resume_on_launch(self):
        rows = read_rows()
        idx = last_row_open_session(rows)
        if idx is None:
            # Option (1) Automatisch fortsetzen? -> einfach hier einschalten:
            # self.set_running_ui(False)  # (Start aktiv lassen)
            return

        # Offene Session gefunden -> Wahl anbieten
        self.show_resume_bar(rows[idx][0])  # zeigt Startzeit an

        # Wenn du stattdessen **automatisch fortsetzen** willst (Option 1),
        # kommentiere die Zeile oben aus und nutze:
        # self.set_running_ui(True)
        # self.set_message(f"Offene Session seit {rows[idx][0]} – weiterführen.", kind="warn")

    def show_resume_bar(self, start_time_str: str):
        self.resume_container.grid()  # sichtbar machen
        for w in self.resume_container.winfo_children():
            w.destroy()

        bar = ttk.Frame(self.resume_container, padding=8)
        bar.grid(sticky="ew")
        bar.columnconfigure(0, weight=1)

        text = ttk.Label(
            bar,
            text=f"Es gibt eine offene Session seit {start_time_str}. Weiterführen oder neu starten?",
            foreground="#b58900",
        )
        text.grid(row=0, column=0, sticky="w")

        btns = ttk.Frame(bar)
        btns.grid(row=0, column=1, sticky="e", padx=(8, 0))
        ttk.Button(btns, text="Weiterführen", command=self.on_resume_continue).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btns, text="Neu starten", command=self.on_resume_restart).grid(row=0, column=1)

        # Bis zur Entscheidung: Start deaktivieren, Stop deaktiviert lassen
        self.btn_start.state(["disabled"])
        self.btn_stop.state(["disabled"])

    def hide_resume_bar(self):
        self.resume_container.grid_remove()

    def on_resume_continue(self):
        self.hide_resume_bar()
        self.set_running_ui(True)
        self.set_message("Offene Session wird weitergeführt. Stop zum Beenden drücken.", kind="ok")

    def on_resume_restart(self):
        rows = read_rows()
        idx = last_row_open_session(rows)
        if idx is not None:
            rows.pop(idx)     # hängende Zeile entfernen
            write_rows(rows)
        self.hide_resume_bar()
        self.set_running_ui(False)
        self.set_message("Hängende Session verworfen. Du kannst neu starten.", kind="info")

    # ---------- Start/Stop ----------
    def on_start(self):
        if self.running:
            return

        # Falls beim Start noch eine offene Session vorhanden ist (z. B. Entscheidung nicht getroffen),
        # wird sie verworfen und neu begonnen – so wie zuvor spezifiziert.
        rows = read_rows()
        idx = last_row_open_session(rows)
        if idx is not None:
            rows.pop(idx)
            write_rows(rows)

        start_time = datetime.now().strftime(DT_FMT)
        append_row([start_time, "", ""])
        self.set_running_ui(True)
        self.set_message(f"Gestartet: {start_time}", kind="ok")

    def on_stop(self):
        if not self.running:
            return

        series = self.entry_series.get().strip()
        if not series.isdigit():
            self.set_message("Bitte eine gültige ganze Zahl bei 'Anzahl Serien' eingeben!", kind="error")
            self.entry_series.focus_set()
            return

        rows = read_rows()
        if not rows:
            self.set_message("Keine laufende Session gefunden.", kind="error")
            self.set_running_ui(False)
            return

        last = rows[-1]
        stop_time = datetime.now().strftime(DT_FMT)
        if len(last) < 3:
            last += [""] * (3 - len(last))
        last[1] = stop_time
        last[2] = series
        rows[-1] = last
        write_rows(rows)

        self.entry_series.delete(0, tk.END)
        self.set_running_ui(False)
        self.set_message(f"Gestoppt: {stop_time} – Serien {series} gespeichert.", kind="ok")


def main():
    root = tk.Tk()
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
