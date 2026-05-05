#modify nalang for frontend and backend, ung andito test gui kasi


import cv2
import pytesseract
from pytesseract import Output
import os
import time
import numpy as np
import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def process_receipt_logic(receipt_path, log_callback):
    log_callback(f"🔍 Reading Receipt: {receipt_path}...")

    output_dir = "analyzed_receipts"
    os.makedirs(output_dir, exist_ok=True)

    img_color = cv2.imread(receipt_path)
    if img_color is None:
        log_callback("❌ Error: Could not load the receipt image.")
        return None, None

    img_height, img_width, _ = img_color.shape


    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    d = pytesseract.image_to_data(img_gray, output_type=Output.DICT)
    n_boxes = len(d['text'])

    anchor_y, anchor_h, anchor_x = None, None, None
    anchor_index = None


    for i in range(n_boxes):
        if int(d['conf'][i]) > 60:
            text = d['text'][i].lower()
            if text == "total":
                if i + 1 < n_boxes and "amount" in d['text'][i + 1].lower():
                    anchor_y = d['top'][i]
                    anchor_h = d['height'][i]
                    anchor_x = d['left'][i + 1] + d['width'][i + 1]
                    anchor_index = i
                    break

    if anchor_y is not None:


        pad_v = 15
        crop_y_min = max(0, anchor_y - pad_v)
        crop_y_max = min(img_height, anchor_y + anchor_h + pad_v)


        full_row = img_color[crop_y_min:crop_y_max, 0:img_width]

        #--- STEP 4: FIND THE ₱ GLYPH VIA PIXEL COLUMN SCAN ---
        # The amount text is dark navy
        b_ch, g_ch, r_ch = cv2.split(full_row)
        dark_mask = (
            (r_ch.astype(np.int16) < 100) &
            (g_ch.astype(np.int16) < 100) &
            (b_ch.astype(np.int16) < 100)
        ).astype(np.uint8) * 255

        # Column ink density
        col_density = np.sum(dark_mask > 0, axis=0)

        # Only search the right of imagre
        search_start = int(img_width * 0.45)
        right_density = col_density[search_start:]

        # ink blobs
        ink_cols = np.where(right_density > 0)[0]

        amount_x_start = None
        if len(ink_cols) > 0:

            gap_threshold = 12
            blob_start = ink_cols[-1]
            for j in range(len(ink_cols) - 2, -1, -1):
                if ink_cols[j + 1] - ink_cols[j] > gap_threshold:

                    blob_start = ink_cols[j + 1]
                    break
                blob_start = ink_cols[j]
            amount_x_start = search_start + blob_start

        # Fallback
        if amount_x_start is None:
            amount_x_start = anchor_x + 10

        # cropping
        pad_h = 8
        crop_x_min = max(0, amount_x_start - pad_h)
        crop_x_max = img_width

        wide_crop = full_row[:, crop_x_min:crop_x_max]

        #  SHRINK WRAP
        b2, g2, r2 = cv2.split(wide_crop)
        thresh = (
            (r2.astype(np.int16) < 100) &
            (g2.astype(np.int16) < 100) &
            (b2.astype(np.int16) < 100)
        ).astype(np.uint8) * 255
        coords = cv2.findNonZero(thresh)

        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            pad = 8
            tight_y_min = max(0, y - pad)
            tight_y_max = min(wide_crop.shape[0], y + h + pad)
            tight_x_min = max(0, x - pad)
            tight_x_max = min(wide_crop.shape[1], x + w + pad)
            final_cropped_amount = wide_crop[tight_y_min:tight_y_max, tight_x_min:tight_x_max]
        else:
            final_cropped_amount = wide_crop

        # --- STEP 6: SAVE ASSETS ---
        transaction_id = int(time.time())

        full_ela_path  = os.path.join(output_dir, f"{transaction_id}_full_ela.png")
        crop_typo_path = os.path.join(output_dir, f"{transaction_id}_crop_typography.png")


        cv2.imwrite(full_ela_path, img_color)
        cv2.imwrite(crop_typo_path, final_cropped_amount)

        log_callback(f"✅ Success! OCR found 'Total Amount'.")
        log_callback(f"📁 Saved Pristine Full Image : {full_ela_path}")
        log_callback(f"📁 Saved Cropped Amount      : {crop_typo_path}")


        debug_img = img_color.copy()
        cv2.rectangle(
            debug_img,
            (d['left'][anchor_index], anchor_y),
            (anchor_x, anchor_y + anchor_h),
            (0, 200, 80), 2          # green anchor box — GUI only
        )
        # NO red crop-area

        return debug_img, final_cropped_amount

    else:
        log_callback("❌ Failed. OCR could not find 'Total Amount' on this receipt.")
        return None, None



# gui section

class ReceiptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GCash Forgery Detection — OCR Cropper")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        # Top Frame: Controls
        top_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        top_frame.pack(fill=tk.X)

        self.btn_upload = tk.Button(
            top_frame,
            text="Upload & Process Receipt",
            font=("Arial", 14, "bold"),
            bg="#007bff", fg="white",
            command=self.upload_image
        )
        self.btn_upload.pack(pady=10)

        #Image Display
        img_frame = tk.Frame(root, bg="#f0f0f0")
        img_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # Left Panel GUI debug view (has green anchor box, no red box)
        left_frame = tk.Frame(img_frame, bg="white", bd=2, relief=tk.GROOVE)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(
            left_frame,
            text="Debug View (Full Receipt)",
            font=("Arial", 12, "bold"), bg="white"
        ).pack(pady=5)
        self.lbl_debug_img = tk.Label(left_frame, bg="white")
        self.lbl_debug_img.pack(expand=True)

        # Right Panel — cropped amount only (no "Sent")
        right_frame = tk.Frame(img_frame, bg="white", bd=2, relief=tk.GROOVE)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        tk.Label(
            right_frame,
            text="Cropped Amount (Bill Output)",
            font=("Arial", 12, "bold"), bg="white"
        ).pack(pady=5)
        self.lbl_crop_img = tk.Label(right_frame, bg="white")
        self.lbl_crop_img.pack(expand=True)

        # Bottom Frame: Logs
        bottom_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        bottom_frame.pack(fill=tk.X, padx=10)
        tk.Label(
            bottom_frame,
            text="System Logs (Saved to 'analyzed_receipts' folder):",
            bg="#f0f0f0", font=("Arial", 10, "bold")
        ).pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(bottom_frame, height=8, font=("Courier", 10))
        self.log_box.pack(fill=tk.X)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.root.update()

    def resize_for_display(self, cv_img, max_width, max_height):
        h, w = cv_img.shape[:2]
        scaling_factor = min(max_width / w, max_height / h)
        new_w = int(w * scaling_factor)
        new_h = int(h * scaling_factor)
        resized = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rgb_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(image=Image.fromarray(rgb_img))

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")]
        )
        if not file_path:
            return

        self.log_box.delete(1.0, tk.END)
        self.lbl_debug_img.config(image='')
        self.lbl_crop_img.config(image='')

        debug_img, crop_img = process_receipt_logic(file_path, self.log)

        if debug_img is not None and crop_img is not None:
            self.tk_debug = self.resize_for_display(debug_img, 450, 450)
            self.lbl_debug_img.config(image=self.tk_debug)

            self.tk_crop = self.resize_for_display(crop_img, 400, 200)
            self.lbl_crop_img.config(image=self.tk_crop)


if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiptApp(root)
    root.mainloop()
