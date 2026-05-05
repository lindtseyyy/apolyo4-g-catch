import cv2
import numpy as np
import os

def run_ela(image_path, output_path, quality=90):
    print(f"Running Error Level Analysis on: {image_path}...")

    # 1. Load the target image
    original = cv2.imread(image_path)
    if original is None:
        print("Error: Could not read image. Check the file path.")
        return False

    # 2. Compress the image to a temporary file
    temp_filename = 'temp_compression.jpg'
    cv2.imwrite(temp_filename, original, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # 3. Load the compressed version back into memory
    compressed = cv2.imread(temp_filename)

    # 4. Mathematically subtract the compressed image from the original
    diff = cv2.absdiff(original, compressed)

    # 5. Convert the difference to grayscale
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    # 6. Enhance the image (multiply the brightness so artifacts glow)
    # The alpha value is a multiplier. 15 is usually a good starting point for JPEGs.
    enhanced_map = cv2.convertScaleAbs(gray_diff, alpha=8.0)

    # 7. Save the resulting map so we can look at it
    cv2.imwrite(output_path, enhanced_map)
    print(f"Success! ELA Map saved to: {output_path}")

    # Clean up the temporary file
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return True

if __name__ == "__main__":
    # The script looks for an image named 'test_receipt.jpg' in the same folder
    target_image = "fake1.jpg"
    output_image = "fake1result.jpg"

    if os.path.exists(target_image):
        run_ela(target_image, output_image)
    else:
        print(f"Waiting for test data: Please upload '{target_image}' to this folder.")
