from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import cv2
import numpy as np
import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sort_contours(cnts, method="left-to-right"):
    if not cnts:
        return []
    reverse = False
    i = 0
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    cnts, boundingBoxes = zip(*sorted(zip(cnts, boundingBoxes),
                                      key=lambda b: b[1][i], reverse=reverse))
    return cnts

@app.route('/')
def home():
    return "OMR Checker Backend is running!"

@app.route('/check-answers', methods=['POST'])
def check_answers():
    correct_answers = request.form.get('correct_answers', '').upper()
    language = request.form.get('language', '')

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    file = request.files['image']

    img_path = os.path.join(UPLOAD_FOLDER, 'upload.png')
    file.save(img_path)

    image = cv2.imread(img_path)
    if image is None:
        return jsonify({'error': 'Failed to read uploaded image'}), 400

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    _, thresh = cv2.threshold(blurred, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    thresh_path = os.path.join(UPLOAD_FOLDER, f'debug_thresh_{timestamp}.png')
    cv2.imwrite(thresh_path, thresh)

    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)

    question_cnts = []
    for c in contours:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        # Bubble size range for SSC/HSC OMR bubbles (approx 6-8 mm in pixels)
        if 50 <= w <= 90 and 50 <= h <= 90 and 0.8 <= ar <= 1.2:
            question_cnts.append(c)

    if len(question_cnts) == 0:
        return jsonify({'error': 'No bubbles detected in image. Please check image quality and format.'}), 400

    question_cnts = sort_contours(question_cnts, method="top-to-bottom")

    bubbles_per_question = 4
    detected_answers = ""

    for (q, i) in enumerate(range(0, len(question_cnts), bubbles_per_question)):
        cnts = sort_contours(question_cnts[i:i + bubbles_per_question], method="left-to-right")
        bubbled = None

        for (j, c) in enumerate(cnts):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)

            total = cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask))

            # Ignore bubbles with very few pixels filled (noise)
            if total < 500:
                continue

            if bubbled is None or total > bubbled[0]:
                bubbled = (total, j)

        if bubbled is None:
            detected_answers += 'X' if language == 'eng' else '০'
            continue

        idx = bubbled[1]
        if language == "eng":
            detected_answers += "ABCD"[idx]
        else:
            detected_answers += "কখগঘ"[idx]

    print(f"Correct Answers: {correct_answers}")
    print(f"Detected Answers: {detected_answers}")

    total_questions = len(correct_answers)
    correct_count = sum(1 for ca, da in zip(correct_answers, detected_answers) if ca == da)
    incorrect_questions = [i + 1 for i, (ca, da) in enumerate(zip(correct_answers, detected_answers)) if ca != da]

    response = {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_questions": incorrect_questions,
        "detected_answers": detected_answers,
        "message": "OMR detection completed.",
        "debug_threshold_image": thresh_path
    }

    # Optional: remove uploaded image after processing
    # os.remove(img_path)

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

