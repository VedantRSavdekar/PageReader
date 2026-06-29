import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ocr import process_letter, process_aadhaar
from excel import save_record, get_next_sr_no, set_start_sr_no

try:
    import cv2
    WEBCAM_AVAILABLE = True
except ImportError:
    WEBCAM_AVAILABLE = False

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

# Validation rules: field -> required exact digit length (None = no check)
FIELD_LENGTHS = {
    "MOBILE.NO":   10,
    "AADHAAR.NO":  12,
}


class OCRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PageReader")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(860, 660)

        self.field_vars   = {f: tk.StringVar() for f in FIELDS}
        self.field_entries = {}  # store Entry widgets for border highlighting
        self.status_var   = tk.StringVar(value="Set starting SR.NO then load the printed letter.")
        self.sr_var       = tk.StringVar(value=f"Next SR.NO: {get_next_sr_no()}")
        self.start_sr_var = tk.StringVar(value="1")

        # Trace changes on MOBILE.NO and AADHAAR.NO for live validation
        self.field_vars["MOBILE.NO"].trace_add("write", lambda *_: self._validate_field("MOBILE.NO"))
        self.field_vars["AADHAAR.NO"].trace_add("write", lambda *_: self._validate_field("AADHAAR.NO"))

        self._build_ui()
        self.geometry("960x720")

    # ── UI ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  PageReader", font=FONT_TITLE,
                 bg=ACCENT, fg="white").pack(side="left", padx=20)
        tk.Label(hdr, textvariable=self.sr_var, font=FONT_BODY,
                 bg=ACCENT, fg=ACCENT2).pack(side="right", padx=20)

        # SR.NO config bar
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

        # Main
        main = tk.Frame(self, bg=BG, padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # Left: two image panels
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self._build_image_card(left, "📄  Step 1: Printed Letter",
                               "letter", ACCENT,
                               self._load_letter, "Load Letter")
        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=8)
        self._build_image_card(left, "🪪  Step 2: Aadhaar Card",
                               "aadhaar", BLUE,
                               self._load_aadhaar, "Load Aadhaar")

        # Right: fields panel
        right = tk.Frame(main, bg=SURFACE,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=True)
        self._build_fields_panel(right)

        # Status bar
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
            self._btn(btn_row, "📷", lambda k=key: self._capture_webcam(k),
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

            is_manual = False
            suffix = ""
            label_color = TEXT

            tk.Label(row, text=field + suffix, font=FONT_LABEL, bg=SURFACE,
                     fg=label_color, width=14, anchor="w").pack(side="left")

            entry = tk.Entry(row, textvariable=self.field_vars[field],
                             font=FONT_BODY, bg="#12121E", fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightbackground=BORDER, highlightthickness=1)
            entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(6, 0))
            self.field_entries[field] = entry

        tk.Label(area, text="✏️ = enter manually", font=FONT_SMALL,
                 bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(4, 0))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(8, 0))

        actions = tk.Frame(parent, bg=SURFACE, padx=16, pady=10)
        actions.pack(fill="x")
        self._btn(actions, "✅  Save to Excel", self._save_record, SUCCESS).pack(
            fill="x", pady=(0, 6))
        self._btn(actions, "🗑  Clear All", self._clear_fields, MUTED).pack(fill="x")

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
        """Check digit length. Highlight border red if invalid, green if valid."""
        required_len = FIELD_LENGTHS.get(field)
        if required_len is None:
            return True

        value = self.field_vars[field].get().strip()
        digits_only = "".join(filter(str.isdigit, value))
        entry = self.field_entries.get(field)
        if not entry:
            return True

        if value == "":
            # Empty — reset to neutral
            entry.configure(highlightbackground=BORDER)
            return True
        elif len(digits_only) == required_len:
            entry.configure(highlightbackground=SUCCESS)
            return True
        else:
            entry.configure(highlightbackground=ERROR)
            return False

    def _validate_all(self) -> bool:
        """Validate all fields with length rules. Returns True if all pass."""
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

    def _capture_webcam(self, key):
        if not WEBCAM_AVAILABLE:
            return
        self._set_status("Webcam open — SPACE to capture, ESC to cancel.", MUTED)
        threading.Thread(target=self._webcam_thread, args=(key,), daemon=True).start()

    def _webcam_thread(self, key):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.after(0, lambda: self._set_status("Could not open webcam.", ERROR))
            return
        save_path = os.path.join(os.path.dirname(__file__), "output", f"{key}_capture.jpg")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        captured = False
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow(f"Capture {key} — SPACE to snap, ESC to cancel", frame)
            k = cv2.waitKey(1) & 0xFF
            if k == 32:
                cv2.imwrite(save_path, frame)
                captured = True
                break
            elif k == 27:
                break
        cap.release()
        cv2.destroyAllWindows()
        if captured:
            self.after(0, lambda: self._show_preview(key, save_path))
            fn = self._run_letter_ocr if key == "letter" else self._run_aadhaar_ocr
            threading.Thread(target=fn, args=(save_path,), daemon=True).start()

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

    def _merge_fields(self, fields: dict):
        for key, value in fields.items():
            if value and key in self.field_vars:
                self.field_vars[key].set(value)

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
            self._set_status(f"✅ Saved as SR.NO {sr_no}. Ready for next entry.", SUCCESS)
            self.sr_var.set(f"Next SR.NO: {get_next_sr_no()}")
            self._clear_fields()
        except Exception as e:
            self._set_status(f"Save error: {e}", ERROR)

    def _clear_fields(self):
        for var in self.field_vars.values():
            var.set("")
        for entry in self.field_entries.values():
            entry.configure(highlightbackground=BORDER)
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
