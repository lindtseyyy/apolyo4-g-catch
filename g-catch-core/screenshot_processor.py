import cv2
import numpy as np
import os
import pytesseract
from PIL import Image
import re
from datetime import datetime

class ScreenshotProcessor:
    """
    Full screenshot processor that extracts amount fields and runs typography verification.
    Designed for GCash receipts and similar financial documents.
    """

    def __init__(self, tesseract_path=None):
        """
        Initialize the screenshot processor.

        Args:
            tesseract_path: Optional path to Tesseract OCR executable (Windows only)
        """
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path

        self.original_image = None
        self.processed_image = None
        self.detected_amounts = []
        self.verification_results = []

    def load_image(self, image_path):
        """Load and validate image file."""
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return False

        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            print("Error: Could not read image. Ensure it's a valid image format.")
            return False

        print(f"✓ Image loaded successfully: {image_path}")
        print(f"  Dimensions: {self.original_image.shape[1]}x{self.original_image.shape[0]} pixels")
        return True

    def preprocess_image(self):
        """Preprocess image for better OCR and region detection."""
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        self.processed_image = denoised
        print("✓ Image preprocessing complete")
        return denoised

    def find_amount_regions(self, image, keywords=['Amount', 'amount', 'AMOUNT', 'P', '₱']):
        """
        Detect potential amount field regions using OCR and keyword matching.

        Args:
            image: Preprocessed image
            keywords: Keywords to search for amount fields

        Returns:
            List of regions containing potential amounts
        """
        print("\n--- Searching for Amount Fields ---")

        # Use OCR to get bounding boxes
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        except Exception as e:
            print(f"OCR Error: {e}")
            print("Ensure Tesseract-OCR is installed and configured.")
            return []

        amount_regions = []
        detected_text = []

        # Find regions with keywords or numeric patterns
        for i, text in enumerate(data['text']):
            conf = int(data['conf'][i])

            # Skip low confidence detections
            if conf < 30:
                continue

            # Check for keywords or numeric patterns with peso sign
            if any(keyword in text for keyword in keywords) or re.search(r'[\d,\.]+', text):
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                if w > 20 and h > 15:  # Filter noise
                    detected_text.append({
                        'text': text,
                        'confidence': conf,
                        'region': (x, y, w, h)
                    })
                    print(f"  Found: '{text}' (confidence: {conf}%) at ({x}, {y})")

        self.detected_amounts = detected_text

        if not detected_text:
            print("  ⚠ No amount fields detected via OCR")
            return []

        return detected_text

    def extract_amount_field(self, region, expand_percentage=30):
        """
        Extract and crop the amount field region from the image.

        Args:
            region: Tuple (x, y, width, height) of the detected region
            expand_percentage: Percentage to expand region for better context

        Returns:
            Cropped image of the amount field
        """
        x, y, w, h = region

        # Expand region to capture full amount
        expansion_x = int(w * expand_percentage / 100)
        expansion_y = int(h * expand_percentage / 100)

        x1 = max(0, x - expansion_x)
        y1 = max(0, y - expansion_y)
        x2 = min(self.original_image.shape[1], x + w + expansion_x)
        y2 = min(self.original_image.shape[0], y + h + expansion_y)

        cropped = self.original_image[y1:y2, x1:x2]
        return cropped

    def extract_all_amounts(self, output_dir="extracted_amounts"):
        """
        Extract all detected amount fields and save them as separate images.

        Args:
            output_dir: Directory to save extracted amounts

        Returns:
            Dictionary mapping amount index to extracted image path
        """
        if not self.detected_amounts:
            print("\n⚠ No amounts to extract")
            return {}

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"\n--- Extracting Amount Fields ---")
        extracted_paths = {}

        for idx, amount_data in enumerate(self.detected_amounts):
            region = amount_data['region']
            text = amount_data['text']

            cropped = self.extract_amount_field(region, expand_percentage=30)

            # Save extracted amount
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"amount_{idx}_{timestamp}.jpg")
            cv2.imwrite(output_path, cropped)

            extracted_paths[idx] = output_path
            print(f"  ✓ Extracted amount {idx + 1}: '{text}' → {output_path}")

        return extracted_paths

    def check_typography(self, image_path, output_path=None):
        """
        Run typography & kerning forensics on an image.

        Args:
            image_path: Path to the image to verify
            output_path: Optional path to save verification result

        Returns:
            Dictionary with verification results
        """
        print(f"\n--- Running Typography & Kerning Forensics ---")
        print(f"Analyzing: {image_path}...")

        img = cv2.imread(image_path)
        if img is None:
            print("Error: Could not read image for typography analysis.")
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if h > 15 and w > 5:  # Filter noise
                bounding_boxes.append((x, y, w, h))

        # Sort from Left to Right
        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])

        if len(bounding_boxes) < 2:
            print("  ⚠ Insufficient character data for analysis")
            return {
                'verdict': 'INCONCLUSIVE',
                'reason': 'Insufficient character data',
                'flags': 0,
                'details': []
            }

        proof_img = img.copy()

        # --- METRIC 1: ASPECT RATIO (Font Thickness/Weight) ---
        print("\n  Font Aspect Ratios (Width/Height):")
        aspect_ratios = []
        for i, (x, y, w, h) in enumerate(bounding_boxes):
            ratio = round(w / h, 2)
            aspect_ratios.append(ratio)

            cv2.rectangle(proof_img, (x, y), (x + w, y + h), (255, 0, 0), 1)
            cv2.putText(proof_img, str(ratio), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            print(f"    Char {i+1}: Ratio {ratio}")

        # --- METRIC 2: KERNING (Horizontal Space Between Characters) ---
        print("\n  Kerning (Pixel Gaps):")
        gaps = []
        for i in range(len(bounding_boxes) - 1):
            current_char_end_x = bounding_boxes[i][0] + bounding_boxes[i][2]
            next_char_start_x = bounding_boxes[i+1][0]

            gap_pixels = next_char_start_x - current_char_end_x
            gaps.append(gap_pixels)

            mid_y = bounding_boxes[i][1] + int(bounding_boxes[i][3] / 2)
            cv2.line(proof_img, (current_char_end_x, mid_y), (next_char_start_x, mid_y), (0, 0, 255), 2)
            print(f"    Gap between Char {i+1} and {i+2}: {gap_pixels}px")

        # --- AUTOMATED VERDICT LOGIC ---
        print("\n  Forensic Analysis:")
        fraud_flags = 0
        reasons = []

        # Rule 1: The Peso Gap Check
        if len(gaps) > 0:
            peso_gap = gaps[0]
            if peso_gap > 3:
                fraud_flags += 1
                reasons.append(f"Suspiciously large gap after Peso sign ({peso_gap}px). Human spacebar use likely.")

        # Rule 2 & 3: Font Consistency & GCash Baseline
        if len(aspect_ratios) > 1:
            number_ratios = aspect_ratios[1:]

            ratio_variance = max(number_ratios) - min(number_ratios)
            if ratio_variance > 0.05:
                fraud_flags += 1
                reasons.append(f"Inconsistent font weights detected (Variance: {ratio_variance:.2f}). Mixed fonts used.")

            avg_ratio = sum(number_ratios) / len(number_ratios)
            if avg_ratio < 0.70 or avg_ratio > 0.85:
                fraud_flags += 1
                reasons.append(f"Font aspect ratio ({avg_ratio:.2f}) does not match GCash standard UI font.")

        # Output Verdict
        if fraud_flags > 0:
            verdict = "FORGED"
            color = (0, 0, 255)  # Red
            print(f"\n  🚨 VERDICT: FORGED")
        else:
            verdict = "AUTHENTIC"
            color = (0, 255, 0)  # Green
            print(f"\n  ✅ VERDICT: AUTHENTIC")

        for r in reasons:
            print(f"     - {r}")

        # Stamp the verdict onto the image
        cv2.putText(proof_img, f"VERDICT: {verdict}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(proof_img, f"Fraud Flags: {fraud_flags}", (5, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Save visual proof if output path provided
        if output_path:
            cv2.imwrite(output_path, proof_img)
            print(f"  ✓ Typography analysis saved to: {output_path}")

        result = {
            'verdict': verdict,
            'fraud_flags': fraud_flags,
            'reasons': reasons,
            'aspect_ratios': aspect_ratios,
            'gaps': gaps,
            'proof_image': proof_img
        }

        self.verification_results.append(result)
        return result

    def process_full_screenshot(self, image_path, output_dir="results"):
        """
        Complete pipeline: Load → Preprocess → Find amounts → Extract → Verify.

        Args:
            image_path: Path to screenshot/receipt image
            output_dir: Directory to save all results

        Returns:
            Dictionary with complete analysis results
        """
        print("\n" + "="*60)
        print("SCREENSHOT PROCESSING & TYPOGRAPHY VERIFICATION PIPELINE")
        print("="*60)

        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Step 1: Load
        if not self.load_image(image_path):
            return None

        # Step 2: Preprocess
        preprocessed = self.preprocess_image()

        # Step 3: Find amounts
        amounts = self.find_amount_regions(preprocessed)
        if not amounts:
            print("\n⚠ Pipeline halted: No amount fields detected")
            return None

        # Step 4: Extract amounts
        extracted_paths = self.extract_all_amounts(os.path.join(output_dir, "extracted_amounts"))

        # Step 5: Verify each extracted amount
        print(f"\n--- Typography Verification Results ---")
        verification_data = []

        for idx, extracted_path in extracted_paths.items():
            print(f"\n[Amount {idx + 1}] Processing: {extracted_path}")

            result_image_path = os.path.join(
                output_dir,
                f"verification_result_{idx}.jpg"
            )

            result = self.check_typography(extracted_path, result_image_path)

            if result:
                verification_data.append({
                    'amount_index': idx,
                    'original_text': self.detected_amounts[idx]['text'],
                    'extracted_image': extracted_path,
                    'result_image': result_image_path,
                    'verification': result
                })

        # Generate final report
        final_report = self.generate_report(verification_data, output_dir)

        return {
            'original_image': image_path,
            'detected_amounts': self.detected_amounts,
            'extracted_images': extracted_paths,
            'verification_results': verification_data,
            'final_report': final_report
        }

    def generate_report(self, verification_data, output_dir):
        """Generate a text report of all verifications."""
        report_path = os.path.join(output_dir, "VERIFICATION_REPORT.txt")

        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("TYPOGRAPHY VERIFICATION REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write(f"Total Amounts Detected: {len(verification_data)}\n\n")

            for data in verification_data:
                f.write("-" * 70 + "\n")
                f.write(f"Amount {data['amount_index'] + 1}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Detected Text: {data['original_text']}\n")
                f.write(f"Extracted Image: {data['extracted_image']}\n")
                f.write(f"Result Image: {data['result_image']}\n\n")

                verification = data['verification']
                f.write(f"Verdict: {verification['verdict']}\n")
                f.write(f"Fraud Flags: {verification['fraud_flags']}\n")
                f.write(f"Aspect Ratios: {verification['aspect_ratios']}\n")
                f.write(f"Kerning Gaps: {verification['gaps']}\n\n")

                if verification['reasons']:
                    f.write("Reasons:\n")
                    for reason in verification['reasons']:
                        f.write(f"  - {reason}\n")
                else:
                    f.write("No fraud indicators detected.\n")

                f.write("\n")

            # Summary
            forged_count = sum(1 for d in verification_data if d['verification']['verdict'] == 'FORGED')
            authentic_count = len(verification_data) - forged_count

            f.write("="*70 + "\n")
            f.write("SUMMARY\n")
            f.write("="*70 + "\n")
            f.write(f"Authentic: {authentic_count}\n")
            f.write(f"Forged: {forged_count}\n")
            f.write(f"Inconclusive: {len([d for d in verification_data if d['verification']['verdict'] == 'INCONCLUSIVE'])}\n")

        print(f"\n✓ Report saved to: {report_path}")
        return report_path


def main():
    """Example usage of the ScreenshotProcessor."""

    # Initialize processor
    processor = ScreenshotProcessor()

    # Process image
    image_path = "full_receipt.jpg"  # Change to your screenshot

    if os.path.exists(image_path):
        results = processor.process_full_screenshot(image_path, output_dir="results")

        if results:
            print("\n" + "="*60)
            print("PROCESSING COMPLETE")
            print("="*60)
            print(f"Results saved to: results/")
            print(f"Check VERIFICATION_REPORT.txt for detailed analysis")
    else:
        print(f"Error: Image '{image_path}' not found.")
        print("Usage:")
        print("  1. Place your screenshot in the same directory as this script")
        print("  2. Update 'image_path' variable with the filename")
        print("  3. Run: python screenshot_processor.py")


if __name__ == "__main__":
    main()
