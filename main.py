import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ocr import process_image
from excel import save_record, get_next_sr_no

# ── Webcam support (optional) ──────────────────────────────────────────────
try:
    import cv2
    WEBCAM_AVAILABLE = True
except ImportError:
    WEBCAM_AVAILABLE = False

# ── Theme colors ───────────────────────────────────────────────────────────
BG        = "#1E1E2E"   # dark background
SURFACE   = "#2A2A3E"   # card / panel background
ACCENT    = "#7C6FF7"   # purple accent
ACCENT2   = "#A89CF7"   # lighter purple
TEXT      = "#E0E0F0"   # primary text
MUTED     = "#888899"   # secondary text
SUCCESS   = "#4CAF82"   # green for saved
ERROR     = "#F76F6F"   # red for errors
BORDER    = "#3A3A55"   # border color

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_LABEL  = ("Segoe UI", 10, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 9)
FONT_SMALL  = ("Segoe UI", 8)

FIELDS = ["NAME", "VILLAGE", "MOBILE.NO", "AADHAAR.NO", "AP.DATE", "CENTER"]


class OCRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OCR to Excel")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(720, 600)

        self.current_image_path = None
        self.field_vars = {f: tk.StringVar() for f in FIELDS}
        self.status_var = tk.StringVar(value="Load an image to begin.")
        self.sr_var = tk.StringVar(value=f"Next SR.NO: {get_next_sr_no()}")

        self._build_ui()
        self.geometry("820x680")

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=ACCENT, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="📋  OCR to Excel", font=FONT_TITLE,
                 bg=ACCENT, fg="white").pack(side="left", padx=20)
        tk.Label(header, textvariable=self.sr_var, font=FONT_BODY,
                 bg=ACCENT, fg=ACCENT2).pack(side="right", padx=20)

        # Main area
        main = tk.Frame(self, bg=BG, padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Left column: image preview + buttons
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._build_image_panel(left)
        self._build_buttons(left)

        # Right column: fields
        right = tk.Frame(main, bg=SURFACE, bd=0, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=True)
        self._build_fields_panel(right)

        # Status bar
        status_bar = tk.Frame(self, bg=SURFACE, pady=6,
                              highlightbackground=BORDER, highlightthickness=1)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, textvariable=self.status_var,
                 font=FONT_SMALL, bg=SURFACE, fg=MUTED).pack(padx=16)

    def _build_image_panel(self, parent):
        frame = tk.Frame(parent, bg=SURFACE, height=280,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, pady=(0, 10))
        frame.pack_propagate(False)

        self.image_label = tk.Label(frame, text="No image loaded\nLoad a photo of the form",
                                    bg=SURFACE, fg=MUTED, font=FONT_BODY,
                                    wraplength=300, justify="center")
        self.image_label.pack(expand=True)

    def _build_buttons(self, parent):
        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(fill="x")

        self._btn(btn_frame, "📂  Load Image", self._load_image, ACCENT).pack(
            side="left", fill="x", expand=True, padx=(0, 6))

        if WEBCAM_AVAILABLE:
            self._btn(btn_frame, "📷  Capture", self._capture_webcam, "#3A7BD5").pack(
                side="left", fill="x", expand=True)
        else:
            tk.Label(btn_frame, text="(Webcam: plug in later)", font=FONT_SMALL,
                     bg=BG, fg=MUTED).pack(side="left", padx=6)

    def _build_fields_panel(self, parent):
        tk.Label(parent, text="Extracted Fields", font=FONT_LABEL,
                 bg=SURFACE, fg=ACCENT2, pady=10).pack(fill="x", padx=16)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16)

        fields_area = tk.Frame(parent, bg=SURFACE, padx=16, pady=8)
        fields_area.pack(fill="both", expand=True)

        for field in FIELDS:
            row = tk.Frame(fields_area, bg=SURFACE, pady=4)
            row.pack(fill="x")

            tk.Label(row, text=field, font=FONT_LABEL, bg=SURFACE,
                     fg=TEXT, width=14, anchor="w").pack(side="left")

            entry = tk.Entry(row, textvariable=self.field_vars[field],
                             font=FONT_BODY, bg="#12121E", fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightbackground=BORDER, highlightthickness=1)
            entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(6, 0))

        # Action buttons
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        actions = tk.Frame(parent, bg=SURFACE, padx=16, pady=10)
        actions.pack(fill="x")

        self._btn(actions, "✅  Save to Excel", self._save_record, SUCCESS).pack(
            fill="x", pady=(0, 6))
        self._btn(actions, "🗑  Clear Fields", self._clear_fields, MUTED).pack(fill="x")

    def _btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg="white", font=FONT_BODY,
                         relief="flat", cursor="hand2",
                         activebackground=ACCENT2, activeforeground="white",
                         padx=10, pady=6, bd=0)

    # ── Actions ────────────────────────────────────────────────────────────

    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select form image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("All files", "*.*")]
        )
        if not path:
            return

        self.current_image_path = path
        self._show_image_preview(path)
        self._set_status("Running OCR... please wait.", MUTED)
        threading.Thread(target=self._run_ocr, args=(path,), daemon=True).start()

    def _run_ocr(self, path):
        try:
            fields, raw_text = process_image(path)
            self.after(0, lambda: self._populate_fields(fields))
            self.after(0, lambda: self._set_status("OCR complete. Review fields and save.", SUCCESS))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"OCR error: {e}", ERROR))

    def _show_image_preview(self, path):
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((320, 260))
            photo = ImageTk.PhotoImage(img)
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo  # keep reference
        except Exception:
            self.image_label.configure(text=f"Loaded:\n{os.path.basename(path)}")

    def _capture_webcam(self):
        if not WEBCAM_AVAILABLE:
            messagebox.showinfo("Webcam", "OpenCV not available.")
            return
        self._set_status("Opening webcam... press SPACE to capture, ESC to cancel.", MUTED)
        threading.Thread(target=self._webcam_capture_thread, daemon=True).start()

    def _webcam_capture_thread(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.after(0, lambda: self._set_status("Could not open webcam.", ERROR))
            return

        save_path = os.path.join(os.path.dirname(__file__), "output", "webcam_capture.jpg")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Webcam - SPACE to capture, ESC to cancel", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # SPACE
                cv2.imwrite(save_path, frame)
                break
            elif key == 27:  # ESC
                save_path = None
                break

        cap.release()
        cv2.destroyAllWindows()

        if save_path:
            self.current_image_path = save_path
            self.after(0, lambda: self._show_image_preview(save_path))
            self.after(0, lambda: threading.Thread(
                target=self._run_ocr, args=(save_path,), daemon=True).start())

    def _populate_fields(self, fields: dict):
        for key, var in self.field_vars.items():
            var.set(fields.get(key, ""))

    def _save_record(self):
        fields = {f: self.field_vars[f].get().strip() for f in FIELDS}

        # Basic validation
        if not fields["NAME"]:
            messagebox.showwarning("Missing Field", "NAME is required before saving.")
            return

        try:
            sr_no = save_record(fields)
            self._set_status(f"✅ Record saved as SR.NO {sr_no}.", SUCCESS)
            self.sr_var.set(f"Next SR.NO: {get_next_sr_no()}")
            self._clear_fields()
        except Exception as e:
            self._set_status(f"Save error: {e}", ERROR)

    def _clear_fields(self):
        for var in self.field_vars.values():
            var.set("")
        self.image_label.configure(image="", text="No image loaded\nLoad a photo of the form")
        self.image_label.image = None
        self.current_image_path = None
        self._set_status("Fields cleared. Ready for next entry.", MUTED)

    def _set_status(self, msg, color=MUTED):
        self.status_var.set(msg)


if __name__ == "__main__":
    app = OCRApp()
    app.mainloop()
