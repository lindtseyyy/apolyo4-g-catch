import os
import re
from datetime import datetime

import cv2
import pytesseract

from gcatch.detectors.typography import analyze_typography


class ScreenshotProcessor:
    """Full screenshot processor for GCash receipts and similar documents.

    Uses OCR to locate amount fields, extracts them, and runs typography
    verification on each.
    """

    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
        self.original_image = None
        self.processed_image = None
        self.detected_amounts = []
        self.verification_results = []

    def load_image(self, image_path):
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return False
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            print("Error: Could not read image.")
            return False
        print(f"Image loaded successfully: {image_path}")
        print(f"  Dimensions: {self.original_image.shape[1]}x{self.original_image.shape[0]} pixels")
        return True

    def preprocess_image(self):
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        self.processed_image = denoised
        print("Image preprocessing complete")
        return denoised

    def find_amount_regions(self, image, keywords=None):
        if keywords is None:
            keywords = ['Amount', 'amount', 'AMOUNT', 'P', '₱']

        print("\n--- Searching for Amount Fields ---")

        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except Exception as e:
            print(f"OCR Error: {e}")
            print("Ensure Tesseract-OCR is installed and configured.")
            return []

        detected_text = []

        for i, text in enumerate(data['text']):
            conf = int(data['conf'][i])
            if conf < 30:
                continue

            if any(keyword in text for keyword in keywords) or re.search(r'[\d,\.]+', text):
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                if w > 20 and h > 15:
                    detected_text.append({
                        'text': text,
                        'confidence': conf,
                        'region': (x, y, w, h),
                    })
                    print(f"  Found: '{text}' (confidence: {conf}%) at ({x}, {y})")

        self.detected_amounts = detected_text

        if not detected_text:
            print("  No amount fields detected via OCR")
            return []

        return detected_text

    def extract_amount_field(self, region, expand_percentage=30):
        x, y, w, h = region
        expansion_x = int(w * expand_percentage / 100)
        expansion_y = int(h * expand_percentage / 100)

        x1 = max(0, x - expansion_x)
        y1 = max(0, y - expansion_y)
        x2 = min(self.original_image.shape[1], x + w + expansion_x)
        y2 = min(self.original_image.shape[0], y + h + expansion_y)

        return self.original_image[y1:y2, x1:x2]

    def extract_all_amounts(self, output_dir="extracted_amounts"):
        if not self.detected_amounts:
            print("\nNo amounts to extract")
            return {}

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"\n--- Extracting Amount Fields ---")
        extracted_paths = {}

        for idx, amount_data in enumerate(self.detected_amounts):
            region = amount_data['region']
            text = amount_data['text']
            cropped = self.extract_amount_field(region, expand_percentage=30)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"amount_{idx}_{timestamp}.jpg")
            cv2.imwrite(output_path, cropped)

            extracted_paths[idx] = output_path
            print(f"  Extracted amount {idx + 1}: '{text}' -> {output_path}")

        return extracted_paths

    def verify_amount(self, image_path, output_path=None):
        """Run typography forensics on an extracted amount image.

        Delegates to gcatch.detectors.typography.analyze_typography.
        """
        print(f"\n--- Running Typography & Kerning Forensics ---")
        print(f"Analyzing: {image_path}")

        result = analyze_typography(image_path, output_path)
        self.verification_results.append(result)
        return result

    def process_full_screenshot(self, image_path, output_dir="results"):
        """Complete pipeline: Load -> Preprocess -> Find amounts -> Extract -> Verify."""
        print("\n" + "=" * 60)
        print("SCREENSHOT PROCESSING & TYPOGRAPHY VERIFICATION PIPELINE")
        print("=" * 60)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not self.load_image(image_path):
            return None

        preprocessed = self.preprocess_image()
        amounts = self.find_amount_regions(preprocessed)
        if not amounts:
            print("\nPipeline halted: No amount fields detected")
            return None

        extracted_paths = self.extract_all_amounts(os.path.join(output_dir, "extracted_amounts"))

        print(f"\n--- Typography Verification Results ---")
        verification_data = []

        for idx, extracted_path in extracted_paths.items():
            print(f"\n[Amount {idx + 1}] Processing: {extracted_path}")
            result_image_path = os.path.join(output_dir, f"verification_result_{idx}.jpg")
            result = self.verify_amount(extracted_path, result_image_path)

            if result:
                verification_data.append({
                    'amount_index': idx,
                    'original_text': self.detected_amounts[idx]['text'],
                    'extracted_image': extracted_path,
                    'result_image': result_image_path,
                    'verification': result,
                })

        final_report = self.generate_report(verification_data, output_dir)

        return {
            'original_image': image_path,
            'detected_amounts': self.detected_amounts,
            'extracted_images': extracted_paths,
            'verification_results': verification_data,
            'final_report': final_report,
        }

    def generate_report(self, verification_data, output_dir):
        report_path = os.path.join(output_dir, "VERIFICATION_REPORT.txt")

        with open(report_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("TYPOGRAPHY VERIFICATION REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Amounts Detected: {len(verification_data)}\n\n")

            for data in verification_data:
                f.write("-" * 70 + "\n")
                f.write(f"Amount {data['amount_index'] + 1}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Detected Text: {data['original_text']}\n")
                f.write(f"Extracted Image: {data['extracted_image']}\n")
                f.write(f"Result Image: {data['result_image']}\n\n")

                v = data['verification']
                f.write(f"Verdict: {v['verdict']}\n")
                f.write(f"Fraud Flags: {v['fraud_flags']}\n")
                f.write(f"Kerning Gaps: {v['gap_analysis']}\n\n")

                if v['reasons']:
                    f.write("Reasons:\n")
                    for reason in v['reasons']:
                        f.write(f"  - {reason}\n")
                else:
                    f.write("No fraud indicators detected.\n")
                f.write("\n")

            forged_count = sum(1 for d in verification_data if d['verification']['verdict'] == 'FORGED')
            authentic_count = len(verification_data) - forged_count
            inconclusive = len([d for d in verification_data if d['verification']['verdict'] == 'INCONCLUSIVE'])

            f.write("=" * 70 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 70 + "\n")
            f.write(f"Authentic: {authentic_count}\n")
            f.write(f"Forged: {forged_count}\n")
            f.write(f"Inconclusive: {inconclusive}\n")

        print(f"\nReport saved to: {report_path}")
        return report_path
