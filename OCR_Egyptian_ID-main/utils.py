from ultralytics import YOLO
import cv2
import re
import easyocr

# Initialize EasyOCR reader (once)
reader = easyocr.Reader(['ar'], gpu=False)

def preprocess_image(cropped_image):
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    return gray_image

def extract_text(image, bbox, lang='ara'):
    x1, y1, x2, y2 = bbox
    cropped_image = image[y1:y2, x1:x2]
    preprocessed_image = preprocess_image(cropped_image)
    results = reader.readtext(preprocessed_image, detail=0, paragraph=True)
    text = ' '.join(results)
    return text.strip()

def detect_national_id(cropped_image):
    model = YOLO('detect_id.pt')
    results = model(cropped_image)
    detected_info = []

    for result in results:
        for box in result.boxes:
            cls = int(box.cls)
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            detected_info.append((cls, x1))
            cv2.rectangle(cropped_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(cropped_image, str(cls), (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    detected_info.sort(key=lambda x: x[1])
    id_number = ''.join([str(cls) for cls, _ in detected_info])
    return id_number

def expand_bbox_height(bbox, scale=1.2, image_shape=None):
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    center_y = y1 + height // 2
    new_height = int(height * scale)
    new_y1 = max(center_y - new_height // 2, 0)
    new_y2 = min(center_y + new_height // 2, image_shape[0])
    return [x1, new_y1, x2, new_y2]

def decode_egyptian_id(id_number):
    governorates = {
        '01': 'Cairo', '02': 'Alexandria', '03': 'Port Said', '04': 'Suez',
        '11': 'Damietta', '12': 'Dakahlia', '13': 'Ash Sharqia', '14': 'Kaliobeya',
        '15': 'Kafr El - Sheikh', '16': 'Gharbia', '17': 'Monoufia', '18': 'El Beheira',
        '19': 'Ismailia', '21': 'Giza', '22': 'Beni Suef', '23': 'Fayoum', '24': 'El Menia',
        '25': 'Assiut', '26': 'Sohag', '27': 'Qena', '28': 'Aswan', '29': 'Luxor',
        '31': 'Red Sea', '32': 'New Valley', '33': 'Matrouh', '34': 'North Sinai',
        '35': 'South Sinai', '88': 'Foreign'
    }
    century_digit = int(id_number[0])
    year = int(id_number[1:3])
    month = int(id_number[3:5])
    day = int(id_number[5:7])
    governorate_code = id_number[7:9]
    gender_code = int(id_number[12:13])

    if century_digit == 2: full_year = 1900 + year
    elif century_digit == 3: full_year = 2000 + year
    else: raise ValueError("Invalid century digit")

    gender = "Male" if gender_code % 2 != 0 else "Female"
    governorate = governorates.get(governorate_code, "Unknown")
    birth_date = f"{full_year:04d}-{month:02d}-{day:02d}"
    return {'Birth Date': birth_date, 'Governorate': governorate, 'Gender': gender}

def process_image(cropped_image):
    model = YOLO('detect_odjects.pt')
    results = model(cropped_image)

    first_name = second_name = merged_name = nid = address = serial = ""

    for result in results:
        result.save("d2.jpg")
        for box in result.boxes:
            bbox = [int(c) for c in box.xyxy[0].tolist()]
            class_id = int(box.cls[0].item())
            class_name = result.names[class_id]

            if class_name == 'firstName':
                first_name = extract_text(cropped_image, bbox, 'ara')
            elif class_name == 'lastName':
                second_name = extract_text(cropped_image, bbox, 'ara')
            elif class_name == 'serial':
                serial = extract_text(cropped_image, bbox, 'eng')
            elif class_name == 'address':
                address = extract_text(cropped_image, bbox, 'ara')
            elif class_name == 'nid':
                expanded_bbox = expand_bbox_height(bbox, scale=1.5, image_shape=cropped_image.shape)
                cropped_nid = cropped_image[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]]
                nid = detect_national_id(cropped_nid)

    merged_name = f"{first_name} {second_name}"
    decoded_info = decode_egyptian_id(nid)
    return (first_name, second_name, merged_name, nid, address, decoded_info["Birth Date"], decoded_info["Governorate"], decoded_info["Gender"])

def detect_and_process_id_card(image_path):
    id_card_model = YOLO('detect_id_card.pt')
    id_card_results = id_card_model(image_path)
    image = cv2.imread(image_path)
    cropped_image = None

    for result in id_card_results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_image = image[y1:y2, x1:x2]
            break

    if cropped_image is None:
        return {"verified": False, "message": "Please capture a clear image of the Egyptian ID card"}

    try:
        data = process_image(cropped_image)
        return {"verified": True, "data": data}
    except:
        return {"verified": False, "message": "ID detected but data could not be read clearly"}
