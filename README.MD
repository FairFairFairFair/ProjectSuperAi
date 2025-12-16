# ใช้ python version 3.10.11 นะครับ 3.12 กาก
# กรณืใช้เสร็จแล้ว ปิดทุกอย่างด้วยไม่งั้นจะรันไม่ได้
# ปิดของ line webhook
# ปิด ports vs code
# ctrl+c python main.py ด้วย

# วิธี Run Project

# สร้าง virtual env
python -m venv venv

# เปิดใช้ venv
venv\Scripts\activate

# ติดตั้ง library ตามลำดับเลยครับ
pip install -r requirements.txt

pip install "Pillow<10.0.0"

pip install gspread google-auth

# น้ำ key api จาก Line Developers มาใส่ในไฟล์ .env

key ของ LINE_CHANNEL_ACCESS_TOKEN

key ของ LINE_CHANNEL_SECRET

# Run main.py ใน terminal
python main.py

# เปิด ports 8000 ใน vs code ข้างๆกับ terminal

# ปรับเป็น public แล้วก็อป url มาแล้วใส่ใน line developers
อันที่ก็อปมา
https://shlm2sdr-8000.asse.devtunnels.ms/

# ใส่ในหมวด Messaging API ตรง Webhook URL
อันที่เอาไปใส่

https://shlm2sdr-8000.asse.devtunnels.ms/webhook

กด verify ใน line developers ด้วย

# ของ google sheets
เอา api มาจาก google cloud service

enable ของ google drive api กับ google sheets api ด้วยนะ

# ได้ไฟล์ json แล้ว
 วาง path เดียวกันกับ main.py เปลี่ยนชื่อไฟล์เป็น credentials.json

# แก้ชื่อให้ตรงกับ sheets ที่ต้องการเพิ่มข้อมูลด้วย
อยุ่ในไฟล์ ocr_utils.py

spreadsheet = gc.open("ชื่อ ไฟล์ Google Sheets")
