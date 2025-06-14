# app/ocr_utils.py - EasyOCR Version (แก้ไขแล้ว)
import easyocr
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# สร้าง EasyOCR reader (รองรับภาษาไทยและอังกฤษ)
reader = easyocr.Reader(['th', 'en'], gpu=False)

def extract_text_from_image(image_path: str) -> str:
    """
    แยกข้อความจากรูปภาพด้วย EasyOCR
    
    Args:
        image_path (str): path ของไฟล์รูปภาพ
        
    Returns:
        str: ข้อความที่อ่านได้
    """
    try:
        logger.info(f"กำลังอ่านรูปภาพ: {image_path}")
        
        # อ่านข้อความจากรูป
        results = reader.readtext(image_path)
        
        # รวมข้อความทั้งหมด
        extracted_text = ""
        for (bbox, text, confidence) in results:
            # กรองข้อความที่มี confidence สูงกว่า 0.5
            if confidence > 0.5:
                extracted_text += text + "\n"
        
        logger.info(f"อ่านข้อความสำเร็จ: {len(extracted_text)} ตัวอักษร")
        return extracted_text.strip()
        
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise Exception(f"ไม่สามารถอ่านข้อความจากรูปได้: {str(e)}")


# รับข้อมูลจากสลิป (ต้องแก้ไข)
def parse_payment_slip(text: str) -> Dict[str, Any]:
    """
    แยกข้อมูลสลิปเงินจากข้อความ
    
    Args:
        text (str): ข้อความที่อ่านได้จากรูป
        
    Returns:
        Dict: ข้อมูลที่แยกได้
    """
    try:
        parsed_data = {
            "amount": None,
            "date": None,
            "time": None,
            "bank": None,
            "reference": None,
            "account_number": None,
            "recipient": None,
            "sender": None,
            "raw_text": text
        }
        
        # แยกจำนวนเงิน - ปรับปรุงให้จับได้ดีขึ้น
        amount_patterns = [r'(?:จำนวน|จำนวนเงิน|Amount)\s([\d,]+.\d{2})', r'([\d,]+.\d{2})\s(?:บาท|BAHT|THB)']
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data["amount"] = match.group(1).replace(',', '')
                break
                       
        # หาจำนวนเงินจากทุกบรรทัด
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in amount_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    amount_candidate = match.group(1).replace(',', '')
                    # ดึงเฉพาะตัวเลขทศนิยม (เช่น 1234.56)
                    decimal_match = re.search(r"\d+(?:\.\d+)?", amount_candidate)
                    if decimal_match:
                        amount_decimal = decimal_match.group()
                        try:
                            amount_num = float(amount_decimal)
                            if amount_num > 0:
                                parsed_data["amount"] = amount_decimal
                                break
                        except:
                            continue
            if parsed_data["amount"]:
                break
        
        # แยกวันที่ - ปรับปรุงให้จับภาษาไทยได้ดีขึ้น
        date_patterns = [
            r'(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+\d{4})',
            r'(\d{1,2}\s+(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                parsed_data["date"] = match.group(1)
                break
        
        # แยกเวลา
        time_patterns = [
            r'(\d{1,2}:\d{2}:\d{2})',
            r'(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                parsed_data["time"] = match.group(1)
                break
        
        # แยกชื่อธนาคาร - เพิ่ม SCB เป็นพิเศษ
        bank_keywords = {
            "กรุงเทพ": ["BBL", "BBLA", "BANGKOK BANK", "ธนาคารกรุงเทพ", "กรุงเทพ"],
            "กสิกรไทย": ["KBANK", "KASIKORNBANK", "KASI", "KPLUS", "K+", "MAKE", "MAKE by KBank", "ธนาคารกสิกรไทย", "กสิกรไทย", "กสิกร", "ร.กสิกรไทย", "ภ ส ก ร ไท ย"],
            "ไทยพาณิชย์": ["SCB", "SIAM COMMERCIAL BANK", "ธนาคารไทยพาณิชย์", "ไทยพาณิชย์"],
            "กรุงไทย": ["KTB", "KRUNGTHAI", "krungthai", "ธนาคารกรุงไทย", "กรุงไทย", "ก ร ง ไท ย"],
            "ทหารไทยธนชาต": ["TTB", "TMBTHANACHART BANK", "ธนาคารทหารไทยธนชาต", "ทีเอ็มบีธนชาต", "ทหารไทย", "ธนชาต", "TTMB"],
            "ออมสิน": ["GSB", "GOVERNMENT SAVINGS BANK", "MYMO", "ธนาคารออมสิน", "ออมสิน", "อ อ ม ส น"],
            "กรุงศรีอยุธยา": ["BAY", "KRUNGSRI", "BANK OF AYUDHYA", "ธนาคารกรุงศรีอยุธยา", "กรุงศรี"],
            "ธ.ก.ส.": ["BAAC", "ธกส", "ธ.ก.ส."],
            "ธนาคารอาคารสงเคราะห์": ["GHB", "GH BANK", "ธอส", "ธนาคารอาคารสงเคราะห์"],
            "CIMB THAI": ["CIMB", "ซีไอเอ็มบีไทย", "ซีไอเอ็มบี"],
            "UOB": ["UOB", "ยูโอบี"],
            "TISCO": ["TISCO", "ทิสโก้"],
            "KIATNAKIN PHATRA": ["KKP", "เกียรตินาคินภัทร"],
            "ICBC": ["ICBC", "ไอซีบีซี"]
        }
        
        text_lower = text.lower()
        for bank_name, keywords in bank_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    parsed_data["bank"] = bank_name
                    break
            if parsed_data["bank"]:
                break
        
        # รองรับสลิปกรุงไทย
        ktb_pattern = (
            r'(?:นาย|นาง|น\.ส\.|ด\.ช\.|ด\.ญ\.)\s*([^\n]+)\s*\n'
            r'(?:กรุงไทย|krungthai)\s*\n'
            r'xxx-x-[x\d]+-\d\s*\n'
            r'รหัสร้านค้า\s*\n'
            r'(\d+)\s*\n'
            r'(?:รหัสธุรกรรม|เลขที่อ้างอิง)\s*\n'
            r'[a-zA-Z0-9]+\s*\n'
            r'จำนวนเงิน\s*\n'
            r'(\d+(?:\.\d{2})?)\s*บาท'
        )
        match = re.search(ktb_pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            sender_name = match.group(1).strip()
            parsed_data["sender"] = sender_name
            parsed_data["amount"] = match.group(3)
            store_id = match.group(2)
            return parsed_data

        # รองรับสลิปกสิกรไทย - แก้ไขใหม่
        kbank_pattern = r'นาย\s+([^\n]+)\s*\nธ\.กสิกรไทย[\s\S]*?นาง\s+([^\n]+)\s*\nธ\.กสิกรไทย'
        match = re.search(kbank_pattern, text)
        if match:
            parsed_data["sender"] = f"นาย {match.group(1)}".strip()  # เพิ่ม "นาย" ในผู้โอน
            parsed_data["recipient"] = f"นาง {match.group(2)}".strip()
            return parsed_data

        # แยกผู้โอน - ปรับปรุงให้จับได้ดีขึ้น
        sender_patterns = [
            r'จาก\s*\n\s*(นาย\s+[^\n]+)',  # แก้ไขให้เก็บคำนำหน้า "นาย" ด้วย
            r'จาก\s*\n\s*(นาง\s+[^\n]+)', 
            r'จาก\s*\n\s*(นางสาว\s+[^\n]+)',
            r'จาก\s*\n\s*([^\n]+?)(?=\s*xxx|\s*x-|\n|$)',
            r'(นาย\s+[^\n]+?)(?=\s*xxx|\s*x-|\n|$)',  # แก้ไขให้เก็บคำนำหน้า "นาย" ด้วย
            r'(นาง\s+[^\n]+?)(?=\s*xxx|\s*x-|\n|$)',
            r'(นางสาว\s+[^\n]+?)(?=\s*xxx|\s*x-|\n|$)',
            r'ผู้โอน[:\s]*([^\n]+)',
            r'from[:\s]*([^\n]+)'
        ]
        
        for pattern in sender_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                sender = match.group(1).strip()
                # ทำความสะอาดชื่อ
                sender = re.sub(r'\s*xxx.*', '', sender).strip()
                sender = re.sub(r'\s*x-.*', '', sender).strip()
                if sender and len(sender) > 1:  # ตรวจสอบว่าไม่ใช่ข้อความว่าง
                    parsed_data["sender"] = sender  # ไม่ต้องเพิ่ม f"นาย {sender}" แล้ว
                    break

        # แยกผู้รับ - ปรับปรุงให้จับได้ดีขึ้น
        recipient_patterns = [
            r'ไปยัง\s*\n\s*บจก\.\s*\n\s*([^\n]+?)(?=\s*x-|\n|$)',
            r'ไปยัง\s*\n\s*([^\n]+?)(?=\s*x-|\n|$)',
            r'บจก\.\s*\n\s*([^\n]+?)(?=\s*x-|\n|$)',
            r'บจก\.\s*([^\n]+?)(?=\s*x-|\n|$)',
            r'ผู้รับ[:\s]*([^\n]+)',
            r'to[:\s]*([^\n]+)',
            r'นาย\s+([^\n]+?)(?=\s*xxx|\s*x-|\n|$)',
            r'นาง\s+([^\n]+?)(?=\s*xxx|\s*x-|\n|$)',
        ]
        
        for pattern in recipient_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                recipient = match.group(1).strip()
                # ทำความสะอาดชื่อ
                recipient = re.sub(r'\s*x-.*', '', recipient).strip()
                recipient = re.sub(r'\s*xxx.*', '', recipient).strip()
                if recipient and len(recipient) > 1:  # ตรวจสอบว่าไม่ใช่ข้อความว่าง
                    parsed_data["recipient"] = recipient
                    break
        
        # แยกหมายเลขอ้างอิง - ปรับปรุงให้จับได้ดีขึ้น
        ref_patterns = [
            r'รหัสอ้างอิง[:\s]*([A-Za-z0-9]+)',
            r'อ้างอิง[:\s]*([A-Za-z0-9]+)',
            r'เลขที่[:\s]*([A-Za-z0-9]+)',
            r'เลขที่รายการ[:\s]*([A-Za-z0-9]+)',
            r'หมายเลขอ้างอิง[:\s]*([A-Za-z0-9]+)',
            r'เลขที่อ้างอิง[:\s]*([A-Za-z0-9]+)',
            r'reference[:\s]*([A-Za-z0-9]+)',
            r'ref[:\s]*([A-Za-z0-9]+)'            
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data["reference"] = match.group(1)
                break
        
        # แยกเลขบัญชี
        account_patterns = [
            r'(xxx-xxx\d+-\d+)',
            r'(x-\d+)',
            r'บัญชี[:\s]*([0-9x-]+)',
            r'account[:\s]*([0-9x-]+)',
            r'a/c[:\s]*([0-9x-]+)'
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data["account_number"] = match.group(1)
                break
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing slip: {str(e)}")
        return {"raw_text": text, "error": str(e)}

# ปริ้นข้อความกลับ line (ต้องแก้ไข)
# def format_slip_summary(data) -> str:
    """
    จัดรูปแบบข้อมูลสลิปเงิน - รองรับทั้ง text และ parsed_data
    
    Args:
        data: ข้อความ (str) หรือข้อมูลที่แยกแล้ว (dict)
        
    Returns:
        str: ข้อความสรุปที่จัดรูปแบบแล้ว
    """
    try:
        # ตรวจสอบว่า input เป็น dict หรือ string
        if isinstance(data, dict):
            parsed_data = data
            text = data.get('raw_text', '')
        else:
            # ถ้าเป็น string ให้แยกข้อมูลก่อน
            text = data
            parsed_data = parse_payment_slip(text)
        
        summary = "📄 **สรุปข้อมูลสลิป**\n"
        
        # ผู้โอน
        if parsed_data.get("sender"):
            summary += f"👤 **ผู้โอน**: {parsed_data['sender']}\n"
        
        # ผู้รับ
        if parsed_data.get("recipient"):
            summary += f"👥 **ผู้รับ**: {parsed_data['recipient']}\n"
        
        # จำนวนเงิน แก้
        if parsed_data.get("amount"):
            amount = parsed_data["amount"]
            try:
                # แปลงเป็นตัวเลขแล้วจัดรูปแบบ
                amount_num = float(amount.replace(',', ''))
                summary += f"💰 **จำนวนเงิน**: {amount_num:,.2f} บาท\n"
            except:
                summary += f"💰 **จำนวนเงิน**: {amount} บาท\n"
        
                
        # เวลา
        if parsed_data.get("time"):
            summary += f"⏰ **เวลา**: {parsed_data['time']}\n"
        
        # ธนาคาร
        if parsed_data.get("bank"):
            summary += f"🏦 **ธนาคาร**: {parsed_data['bank']}\n"
        
        # หมายเลขอ้างอิง
        if parsed_data.get("reference"):
            summary += f"🔢 **หมายเลขอ้างอิง**: {parsed_data['reference']}\n"
        
        # วันที่ (ถ้ามี)
        if parsed_data.get("date"):
            summary += f"📅 **วันที่**: {parsed_data['date']}\n"
        
        # เลขบัญชี (ถ้ามี)
        if parsed_data.get("account_number"):
            summary += f"💳 **เลขบัญชี**: {parsed_data['account_number']}\n"
        
        # # # ข้อความเต็ม เอาออก
        # raw_text = parsed_data.get('raw_text', text if isinstance(data, str) else 'ไม่มีข้อมูล')
        # summary += f"📝 **ข้อความเต็ม**:\n```\n{raw_text}\n```\n"
        
       
        return summary
        
    except Exception as e:
        logger.error(f"Error formatting summary: {str(e)}")
        return f"❌ เกิดข้อผิดพลาดในการจัดรูปแบบ: {str(e)}"

def format_slip_summary(data) -> str:
    """
    จัดรูปแบบข้อมูลสลิปเงิน - รองรับทั้ง text และ parsed_data
    และบันทึกข้อมูลลงไฟล์ CSV ด้วย

    Args:
        data: ข้อความ (str) หรือข้อมูลที่แยกแล้ว (dict)
        
    Returns:
        str: ข้อความสรุปที่จัดรูปแบบแล้ว
    """
    import csv
    import os

    try:
        # ตรวจสอบว่า input เป็น dict หรือ string
        if isinstance(data, dict):
            parsed_data = data
            text = data.get('raw_text', '')
        else:
            # ถ้าเป็น string ให้แยกข้อมูลก่อน
            text = data
            parsed_data = parse_payment_slip(text)
        
        summary = "📄 **สรุปข้อมูลสลิป**\n"
        
        # ผู้โอน
        if parsed_data.get("sender"):
            summary += f"👤 **ผู้โอน**: {parsed_data['sender']}\n"
        # ผู้รับ
        if parsed_data.get("recipient"):
            summary += f"👥 **ผู้รับ**: {parsed_data['recipient']}\n"
        # จำนวนเงิน
        if parsed_data.get("amount"):
            amount = parsed_data["amount"]
            import re
            match = re.search(r"\d+(?:\.\d+)?", amount.replace(',', ''))
            if match:
                try:
                    amount_num = float(match.group())
                    summary += f"💰 **จำนวนเงิน**: {amount_num:,.2f} บาท\n"
                except:
                    summary += f"💰 **จำนวนเงิน**: {match.group()} บาท\n"
            else:
                summary += "💰 **จำนวนเงิน**: ไม่พบข้อมูล\n"
        # เวลา
        if parsed_data.get("time"):
            summary += f"⏰ **เวลา**: {parsed_data['time']}\n"
        # ธนาคาร
        if parsed_data.get("bank"):
            summary += f"🏦 **ธนาคาร**: {parsed_data['bank']}\n"
        # หมายเลขอ้างอิง
        if parsed_data.get("reference"):
            summary += f"🔢 **หมายเลขอ้างอิง**: {parsed_data['reference']}\n"
        # วันที่
        if parsed_data.get("date"):
            summary += f"📅 **วันที่**: {parsed_data['date']}\n"
        # เลขบัญชี
        if parsed_data.get("account_number"):
            summary += f"💳 **เลขบัญชี**: {parsed_data['account_number']}\n"
        summary += f"💳 **Download CSV file Here **: http://127.0.0.1:8000/static/slip_summary.csv\n"

        # --- เพิ่มส่วนบันทึก CSV ---
        csv_file = "slip_summary.csv"
        file_exists = os.path.isfile(csv_file)
        fieldnames = [
            "sender", "recipient", "amount", "time", "bank",
            "reference", "date", "account_number", "raw_text"
        ]
        with open("static/slip_summary.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "sender": parsed_data.get("sender", ""),
                "recipient": parsed_data.get("recipient", ""),
                "amount": parsed_data.get("amount", ""),
                "time": parsed_data.get("time", ""),
                "bank": parsed_data.get("bank", ""),
                "reference": parsed_data.get("reference", ""),
                "date": parsed_data.get("date", ""),
                "account_number": parsed_data.get("account_number", ""),
                "raw_text": parsed_data.get("raw_text", text if isinstance(data, str) else "")
            })
        # --- จบส่วนบันทึก CSV ---

        return summary
        
    except Exception as e:
        logger.error(f"Error formatting summary: {str(e)}")
        return f"❌ เกิดข้อผิดพลาดในการจัดรูปแบบ: {str(e)}"

# ไม่ต้องแก้อะไร
def extract_qr_code(image_path: str) -> Optional[str]:
    """
    แยก QR Code จากรูปภาพ (EasyOCR ไม่รองรับ QR Code โดยตรง)
    ใช้สำหรับอนาคต หรือเพิ่มเติมด้วย library อื่น
    
    Args:
        image_path (str): path ของไฟล์รูปภาพ
        
    Returns:
        Optional[str]: ข้อมูลใน QR Code หรือ None
    """
    try:
        # TODO: เพิ่มการอ่าน QR Code ด้วย pyzbar หรือ library อื่น
        logger.info("QR Code extraction ยังไม่รองรับ")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting QR code: {str(e)}")
        return None