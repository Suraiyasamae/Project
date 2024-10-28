import threading
import keyboard
import requests
import csv
from datetime import datetime
import os
import time

# ESP32 configuration
ESP32_IP = "192.168.0.24"
URL = f"http://{ESP32_IP}/save"

def create_folders_for_today():
    """สร้างโฟลเดอร์สำหรับวันที่ปัจจุบัน, ข้อมูล CSV"""
    today = datetime.now().strftime("%Y-%m-%d")
    data_folder = os.path.join(today, "data")
    
    os.makedirs(data_folder, exist_ok=True)
    
    return today, data_folder

# ----------ดึงข้อมูลจากเซนเซอร์-----------------------------------------------------

def get_thermal_data():
    """ดึงข้อมูลความร้อนจาก ESP32 ผ่านการร้องขอ HTTP"""
    response = requests.get(URL)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# -------------------------------------------------------------------------------

def save_to_csv(data, filename, label):
    """บันทึกข้อมูลความร้อนไปยังไฟล์ CSV"""
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            headers = ["Time Stamp"] + list(range(0, len(data))) + ["Label"]
            writer.writerow(headers)
        
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data + [label])

# สร้าง event flag สำหรับควบคุมการทำงาน
stop_flag = threading.Event()

def key_listener():
    """ฟังก์ชันสำหรับตรวจจับการกดปุ่ม"""
    while not stop_flag.is_set():
        if keyboard.is_pressed('q'):  # เปลี่ยนจาก space เป็น 'q'
            print("\nStop key pressed! Stopping data collection...")
            stop_flag.set()
            break
        time.sleep(0.1)

def main():
    today_folder, data_folder = create_folders_for_today()
    start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_file = os.path.join(data_folder, f"{start_time}.csv")

    print("Choose Label:")
    print("1 = left hand")
    print("2 = right hand")
    print("3 = both hands")
    print("4 = non-request")
    print("5 = test")
    print("Press 'q' to quit.")  # เปลี่ยนข้อความแจ้งเตือน

    # เริ่ม thread สำหรับตรวจจับการกดปุ่ม
    key_thread = threading.Thread(target=key_listener)
    key_thread.daemon = True  # ให้ thread จบการทำงานเมื่อโปรแกรมหลักจบ
    key_thread.start()

    choice = input("Enter label choice (or 'q' to quit): ")
    
    if choice == 'q':
        print("Exiting data collection...")
        return

    label = {
        '1': 'left hand',
        '2': 'right hand',
        '3': 'both hands',
        '4': 'non-request',
        '5': 'test'
    }.get(choice, 'non-request')

    print(f"Starting data collection with label: {label}")
    print("Press 'q' to stop collection")

    try:
        while not stop_flag.is_set():
            data = get_thermal_data()
            if data:
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                save_to_csv(data, csv_file, label)
                print(f"Data saved at {current_timestamp}", end='\r')
            time.sleep(0)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        stop_flag.set()
        key_thread.join(timeout=1)
        print(f"\nData collection complete.")
        print(f"CSV file saved in {data_folder}")
        print('-------------------------------------------------------------------')

if __name__ == "__main__":
    main()
