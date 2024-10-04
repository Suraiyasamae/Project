import requests  # ใช้สำหรับส่ง HTTP requests
import csv  # ใช้สำหรับบันทึกและอ่านข้อมูลจากไฟล์ CSV
from datetime import datetime  # ใช้สำหรับจัดการข้อมูลเวลาปัจจุบัน
import os  # ใช้ในการจัดการไฟล์และโฟลเดอร์
import time  # ใช้สำหรับการทำงานเกี่ยวกับเวลา

#///////////// ESP32 configuration //////////////////////////////////////////////////////////////////////////

ESP32_IP = "192.168.0.41"  # กำหนดที่อยู่ IP ของ ESP32
URL = f"http://{ESP32_IP}/save"  # URL ที่จะใช้ในการดึงข้อมูลจาก ESP32

#///////////// สร้างโฟลเดอร์ตามวันที่ปัจจุบัน //////////////////////////////////////////////////////////////////

def create_folder_for_today():
    """สร้างโฟลเดอร์สำหรับวันที่ปัจจุบัน"""
    today = datetime.now().strftime("%Y-%m-%d")  # ได้รูปแบบวันที่ปัจจุบันในรูป 'YYYY-MM-DD'
    if not os.path.exists(today):  # ถ้าโฟลเดอร์นี้ยังไม่มีอยู่
        os.makedirs(today)  # สร้างโฟลเดอร์ใหม่ตามชื่อวันที่
    return today

#///////////// การดึงข้อมูล /////////////////////////////////////////////////////////////////////////////

def get_thermal_data():
    """ดึงข้อมูลความร้อนจาก ESP32 ผ่านการร้องขอ HTTP"""
    response = requests.get(URL)  # ส่งคำขอ HTTP GET ไปยัง ESP32
    if response.status_code == 200:  # ตรวจสอบว่าการตอบสนองสำเร็จหรือไม่
        return response.json()  # ส่งคืนข้อมูล JSON ถ้าสำเร็จ
    else:
        print(f"Error: {response.status_code}")  # แสดงข้อความข้อผิดพลาดถ้าไม่สำเร็จ
        return None  # คืนค่า None ถ้าไม่สามารถดึงข้อมูลได้

#///////////// บันทึกข้อมูลไปยังไฟล์ CSV ///////////////////////////////////////////////////////////

def save_to_csv(data, filename):
    """บันทึกข้อมูลความร้อนไปยังไฟล์ CSV"""
    file_exists = os.path.isfile(filename)  # ตรวจสอบว่าไฟล์ CSV มีอยู่แล้วหรือไม่
    
    with open(filename, 'a', newline='') as file:  # เปิดไฟล์ CSV ในโหมดเพิ่มข้อมูล (append)
        writer = csv.writer(file)  # สร้าง writer object สำหรับเขียนข้อมูลลงไฟล์ CSV
        
        if not file_exists:  # ถ้าไฟล์ยังไม่มีอยู่ ให้เขียนหัวข้อคอลัมน์ก่อน
            headers = ["Time Stamp"] + list(range(0, len(data)))  # เพิ่มลำดับตัวเลขในแถวแรก
            writer.writerow(headers)  # เขียนแถวแรกเป็นลำดับตัวเลข
        
        # เขียนเวลาปัจจุบันในคอลัมน์แรก และข้อมูลอุณหภูมิในคอลัมน์ถัดไป
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data)

# ดึงข้อมูลและ save ในไฟล์ CSV

def main():
    # สร้างโฟลเดอร์ตามวันที่ปัจจุบัน
    folder_name = create_folder_for_today()  # สร้างโฟลเดอร์ตามวันที่ปัจจุบัน
    
    # กำหนดชื่อไฟล์ CSV ที่จะใช้บันทึกข้อมูล
    csv_file = os.path.join(folder_name, "thermal_data.csv")  # รวมโฟลเดอร์และชื่อไฟล์เข้าด้วยกัน
    
    start_time = time.time()  # บันทึกเวลาที่เริ่มต้น
    elapsed_time = 0  # ตัวแปรเก็บเวลาที่ใช้ไป
    while elapsed_time < 30:  # ทำซ้ำจนกว่าจะครบ 10 วินาที
        data = get_thermal_data()  # ดึงข้อมูลอุณหภูมิจาก ESP32
        if data:  # ถ้าดึงข้อมูลสำเร็จ
            save_to_csv(data, csv_file)  # บันทึกข้อมูลลงในไฟล์ CSV
            print(f"Data saved to {csv_file}")  # แสดงข้อความว่าบันทึกข้อมูลสำเร็จ
        else:
            print("Failed to get data")  # แสดงข้อความว่าดึงข้อมูลไม่สำเร็จ

        time.sleep(1)  # รอ 1 วินาทีก่อนที่จะดึงข้อมูลใหม่
        elapsed_time = time.time() - start_time  # อัปเดตเวลาที่ใช้ไป

if __name__ == "__main__":
    main()  # เรียกใช้ฟังก์ชัน main() เมื่อรันโปรแกรมโดยตรง
