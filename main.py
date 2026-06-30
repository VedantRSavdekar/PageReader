import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ocr import process_letter, process_aadhaar
from excel import save_record, get_next_sr_no, set_start_sr_no
from villages import get_villages, add_village

try:
    import cv2
    WEBCAM_AVAILABLE = True
except ImportError:
    WEBCAM_AVAILABLE = False

try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

# ── Theme ──────────────────────────────────────────────────────────────────
BG      = "#1E1E2E"
SURFACE = "#2A2A3E"
ACCENT  = "#7C6FF7"
ACCENT2 = "#A89CF7"
TEXT    = "#E0E0F0"
MUTED   = "#888899"
SUCCESS = "#4CAF82"
ERROR   = "#F76F6F"
BORDER  = "#3A3A55"
BLUE    = "#3A7BD5"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_LABEL = ("Segoe UI", 10, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 8)

FIELDS = ["NAME", "VILLAGE", "MOBILE.NO", "AADHAAR.NO", "AP.DATE", "CENTER"]

FIELD_LENGTHS = {
    "MOBILE.NO":   10,
    "AADHAAR.NO":  12,
}

CENTER_OPTIONS = ["Dharangaon", "Jalgaon", "Yawal"]


class OCRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PageReader")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(880, 700)

        self.field_vars    = {f: tk.StringVar() for f in FIELDS}
        self.field_entries = {}
        self.field_locked  = {f: tk.BooleanVar(value=False) for f in FIELDS}
        self.status_var    = tk.StringVar(value="Set starting SR.NO then load the printed letter.")
        self.sr_var        = tk.StringVar(value=f"Next SR.NO: {get_next_sr_no()}")
        self.start_sr_var  = tk.StringVar(value="1")

        self.last_used_date = ""  # remembers the most recently saved AP.DATE

        self.field_vars["MOBILE.NO"].trace_add("write", lambda *_: self._validate_field("MOBILE.NO"))
        self.field_vars["AADHAAR.NO"].trace_add("write", lambda *_: self._validate_field("AADHAAR.NO"))

        self._build_ui()
        self.geometry("980x760")

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        hdr = tk.Frame(self, bg=ACCENT, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  PageReader", font=FONT_TITLE,
                 bg=ACCENT, fg="white").pack(side="left", padx=20)
        tk.Label(hdr, textvariable=self.sr_var, font=FONT_BODY,
                 bg=ACCENT, fg=ACCENT2).pack(side="right", padx=20)

        sr_bar = tk.Frame(self, bg=SURFACE, pady=8,
                          highlightbackground=BORDER, highlightthickness=1)
        sr_bar.pack(fill="x", padx=0)
        tk.Label(sr_bar, text="Starting SR.NO:", font=FONT_LABEL,
                 bg=SURFACE, fg=TEXT).pack(side="left", padx=(16, 6))
        sr_entry = tk.Entry(sr_bar, textvariable=self.start_sr_var,
                            font=FONT_BODY, bg="#12121E", fg=TEXT,
                            insertbackground=TEXT, relief="flat",
                            highlightbackground=BORDER, highlightthickness=1,
                            width=6)
        sr_entry.pack(side="left", ipady=4)
        self._btn(sr_bar, "Set", self._set_start_sr, ACCENT).pack(side="left", padx=8)
        tk.Label(sr_bar, text="(Set once before saving first record)",
                 font=FONT_SMALL, bg=SURFACE, fg=MUTED).pack(side="left")

        main = tk.Frame(self, bg=BG, padx=16, pady=12)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self._build_image_card(left, "📄  Step 1: Printed Letter",
                               "letter", ACCENT,
                               self._load_letter, "Load Letter")
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=8)
        self._build_image_card(left, "🪪  Step 2: Aadhaar Card",
                               "aadhaar", BLUE,
                               self._load_aadhaar, "Load Aadhaar")

        right = tk.Frame(main, bg=SURFACE,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=True)
        self._build_fields_panel(right)

        sb = tk.Frame(self, bg=SURFACE, pady=6,
                      highlightbackground=BORDER, highlightthickness=1)
        sb.pack(fill="x", side="bottom")
        tk.Label(sb, textvariable=self.status_var,
                 font=FONT_SMALL, bg=SURFACE, fg=MUTED).pack(padx=16)

    def _build_image_card(self, parent, title, key, color, cmd, btn_label):
        tk.Label(parent, text=title, font=FONT_LABEL,
                 bg=BG, fg=color).pack(anchor="w", pady=(0, 4))

        frame = tk.Frame(parent, bg=SURFACE, height=180,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True)
        frame.pack_propagate(False)

        lbl = tk.Label(frame, text="No image loaded", bg=SURFACE,
                       fg=MUTED, font=FONT_BODY)
        lbl.pack(expand=True)
        setattr(self, f"{key}_label", lbl)

        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))
        self._btn(btn_row, f"📂  {btn_label}", cmd, color).pack(
            side="left", fill="x", expand=True)

        if WEBCAM_AVAILABLE:
            self._btn(btn_row, "📷  Webcam", lambda k=key: self._capture_webcam(k),
                      "#555577").pack(side="left", padx=(6, 0))

    def _build_fields_panel(self, parent):
        tk.Label(parent, text="Extracted Fields", font=FONT_LABEL,
                 bg=SURFACE, fg=ACCENT2, pady=10).pack(fill="x", padx=16)
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16)

        area = tk.Frame(parent, bg=SURFACE, padx=16, pady=8)
        area.pack(fill="both", expand=True)

        for field in FIELDS:
            row = tk.Frame(area, bg=SURFACE, pady=4)
            row.pack(fill="x")

            tk.Label(row, text=field, font=FONT_LABEL, bg=SURFACE,
                     fg=TEXT, width=14, anchor="w").pack(side="left")

            if field == "CENTER":
                widget = ttk.Combobox(row, textvariable=self.field_vars[field],
                                      values=CENTER_OPTIONS, font=FONT_BODY,
                                      state="readonly")
                widget.pack(side="left", fill="x", expand=True, ipady=2, padx=(6, 0))
            elif field == "VILLAGE":
                widget = ttk.Combobox(row, textvariable=self.field_vars[field],
                                      values=get_villages(), font=FONT_BODY,
                                      state="normal")  # editable + selectable
                widget.pack(side="left", fill="x", expand=True, ipady=2, padx=(6, 0))
            elif field == "AP.DATE" and CALENDAR_AVAILABLE:
                widget = DateEntry(row, textvariable=self.field_vars[field],
                                   font=FONT_BODY, date_pattern="dd-mm-yyyy",
                                   background=ACCENT, foreground="white",
                                   borderwidth=1, width=12)
                widget.pack(side="left", ipady=2, padx=(6, 0))
            else:
                widget = tk.Entry(row, textvariable=self.field_vars[field],
                                  font=FONT_BODY, bg="#12121E", fg=TEXT,
                                  insertbackground=TEXT, relief="flat",
                                  highlightbackground=BORDER, highlightthickness=1)
                widget.pack(side="left", fill="x", expand=True, ipady=4, padx=(6, 0))

            self.field_entries[field] = widget

            lock_btn = tk.Checkbutton(row, variable=self.field_locked[field],
                                      onvalue=True, offvalue=False,
                                      bg=SURFACE, fg=ACCENT2,
                                      activebackground=SURFACE,
                                      selectcolor="#12121E",
                                      text="🔒", font=FONT_SMALL,
                                      command=lambda f=field: self._toggle_lock(f))
            lock_btn.pack(side="left", padx=(4, 0))

        tk.Label(area, text="🔒 = lock field (won't be overwritten on reload)",
                 font=FONT_SMALL, bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(4, 0))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        actions = tk.Frame(parent, bg=SURFACE, padx=16, pady=10)
        actions.pack(fill="x")
        self._btn(actions, "✅  Save to Excel", self._save_record, SUCCESS).pack(
            fill="x", pady=(0, 6))
        self._btn(actions, "🗑  Clear All", self._clear_fields, MUTED).pack(fill="x")

        # Set default AP.DATE to last used date, if any
        if self.last_used_date and CALENDAR_AVAILABLE:
            try:
                self.field_entries["AP.DATE"].set_date(self.last_used_date)
            except Exception:
                pass

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg="white", font=FONT_BODY,
                         relief="flat", cursor="hand2",
                         activebackground=ACCENT2, activeforeground="white",
                         padx=10, pady=6, bd=0)

    # ── SR.NO ──────────────────────────────────────────────────────────────

    def _set_start_sr(self):
        try:
            val = int(self.start_sr_var.get().strip())
            if val < 1:
                raise ValueError
            set_start_sr_no(val)
            self.sr_var.set(f"Next SR.NO: {get_next_sr_no()}")
            self._set_status(f"✅ Starting SR.NO set to {val}.", SUCCESS)
        except ValueError:
            self._set_status("Starting SR.NO must be a positive number.", ERROR)

    # ── Validation ─────────────────────────────────────────────────────────

    def _validate_field(self, field: str) -> bool:
        required_len = FIELD_LENGTHS.get(field)
        if required_len is None:
            return True

        value = self.field_vars[field].get().strip()
        digits_only = "".join(filter(str.isdigit, value))
        entry = self.field_entries.get(field)
        if not entry:
            return True

        try:
            if value == "":
                entry.configure(highlightbackground=BORDER)
                return True
            elif len(digits_only) == required_len:
                entry.configure(highlightbackground=SUCCESS)
                return True
            else:
                entry.configure(highlightbackground=ERROR)
                return False
        except tk.TclError:
            return True

    def _validate_all(self) -> bool:
        all_valid = True
        for field in FIELD_LENGTHS:
            if not self._validate_field(field):
                all_valid = False
        return all_valid

    # ── Actions ────────────────────────────────────────────────────────────

    def _load_letter(self):
        path = filedialog.askopenfilename(
            title="Select printed letter image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if not path:
            return
        self._show_preview("letter", path)
        self._set_status("Reading letter... please wait.", MUTED)
        threading.Thread(target=self._run_letter_ocr, args=(path,), daemon=True).start()

    def _run_letter_ocr(self, path):
        try:
            fields, _ = process_letter(path)
            self.after(0, lambda: self._merge_fields(fields))
            self.after(0, lambda: self._set_status(
                "✅ Letter read! Now load the Aadhaar card.", SUCCESS))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Letter OCR error: {e}", ERROR))

    def _load_aadhaar(self):
        path = filedialog.askopenfilename(
            title="Select Aadhaar card image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if not path:
            return
        self._show_preview("aadhaar", path)
        self._set_status("Reading Aadhaar card... please wait.", MUTED)
        threading.Thread(target=self._run_aadhaar_ocr, args=(path,), daemon=True).start()

    def _run_aadhaar_ocr(self, path):
        try:
            fields, _ = process_aadhaar(path)
            self.after(0, lambda: self._merge_fields(fields))
            self.after(0, lambda: self._set_status(
                "✅ Aadhaar read! Review fields and save.", SUCCESS))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Aadhaar OCR error: {e}", ERROR))

    # ── Webcam (button-based capture, no keyboard needed) ───────────────────

    def _capture_webcam(self, key):
        if not WEBCAM_AVAILABLE:
            return
        win = tk.Toplevel(self)
        win.title(f"Capture {key.title()}")
        win.configure(bg=BG)

        video_label = tk.Label(win, bg=BG)
        video_label.pack(padx=10, pady=10)

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=(0, 10))

        state = {"running": True, "frame": None}

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self._set_status("Could not open webcam.", ERROR)
            win.destroy()
            return

        def update_frame():
            if not state["running"]:
                return
            ret, frame = cap.read()
            if ret:
                state["frame"] = frame
                from PIL import Image, ImageTk
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail((480, 360))
                photo = ImageTk.PhotoImage(img)
                video_label.configure(image=photo)
                video_label.image = photo
            win.after(30, update_frame)

        def do_capture():
            if state["frame"] is not None:
                save_path = os.path.join(os.path.dirname(__file__), "output", f"{key}_capture.jpg")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                cv2.imwrite(save_path, state["frame"])
                close_and_process(save_path)

        def close_and_process(save_path=None):
            state["running"] = False
            cap.release()
            win.destroy()
            if save_path:
                self._show_preview(key, save_path)
                fn = self._run_letter_ocr if key == "letter" else self._run_aadhaar_ocr
                threading.Thread(target=fn, args=(save_path,), daemon=True).start()

        self._btn(btn_row, "📸  Capture", do_capture, SUCCESS).pack(side="left", padx=6)
        self._btn(btn_row, "✖  Cancel", lambda: close_and_process(None), ERROR).pack(side="left", padx=6)

        win.protocol("WM_DELETE_WINDOW", lambda: close_and_process(None))
        update_frame()

    def _show_preview(self, key, path):
        lbl = getattr(self, f"{key}_label")
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((300, 160))
            photo = ImageTk.PhotoImage(img)
            lbl.configure(image=photo, text="")
            lbl.image = photo
        except Exception:
            lbl.configure(text=os.path.basename(path))

    def _toggle_lock(self, field):
        locked = self.field_locked[field].get()
        widget = self.field_entries.get(field)
        if widget:
            try:
                if locked:
                    widget.configure(state="disabled")
                    self._set_status(f"🔒 {field} locked.", MUTED)
                else:
                    state = "readonly" if field == "CENTER" else "normal"
                    widget.configure(state=state)
                    self._set_status(f"🔓 {field} unlocked.", MUTED)
            except tk.TclError:
                pass

    def _merge_fields(self, fields: dict):
        for key, value in fields.items():
            if value and key in self.field_vars and not self.field_locked[key].get():
                self.field_vars[key].set(value)
        # If a new village came in via OCR, refresh the dropdown list live
        if fields.get("VILLAGE"):
            self._refresh_village_list()

    def _refresh_village_list(self):
        widget = self.field_entries.get("VILLAGE")
        if widget is not None:
            try:
                widget.configure(values=get_villages())
            except tk.TclError:
                pass

    def _save_record(self):
        fields = {f: self.field_vars[f].get().strip() for f in FIELDS}

        if not fields["NAME"]:
            messagebox.showwarning("Missing Field", "NAME is required before saving.")
            return

        if not self._validate_all():
            self._set_status("⚠️ Fix highlighted fields before saving.", ERROR)
            return

        try:
            sr_no = save_record(fields)
            self.last_used_date = fields["AP.DATE"]  # remember for next entry
            if fields["VILLAGE"]:
                add_village(fields["VILLAGE"])
                self._refresh_village_list()
            self._set_status(f"✅ Saved as SR.NO {sr_no}. Ready for next entry.", SUCCESS)
            self.sr_var.set(f"Next SR.NO: {get_next_sr_no()}")
            self._clear_fields()
        except Exception as e:
            self._set_status(f"Save error: {e}", ERROR)

    def _clear_fields(self):
        for field, var in self.field_vars.items():
            if field == "AP.DATE" and self.last_used_date:
                var.set(self.last_used_date)
            else:
                var.set("")
        for field, widget in self.field_entries.items():
            try:
                if field == "CENTER":
                    widget.configure(state="readonly", highlightbackground=BORDER)
                elif field == "VILLAGE":
                    widget.configure(state="normal")
                else:
                    widget.configure(state="normal")
                    if hasattr(widget, "configure"):
                        try:
                            widget.configure(highlightbackground=BORDER)
                        except tk.TclError:
                            pass
            except tk.TclError:
                pass
        for var in self.field_locked.values():
            var.set(False)
        for key in ("letter", "aadhaar"):
            lbl = getattr(self, f"{key}_label")
            lbl.configure(image="", text="No image loaded")
            lbl.image = None
        self._set_status("Cleared. Load the printed letter.", MUTED)

    def _set_status(self, msg, color=MUTED):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = OCRApp()
    app.mainloop()
