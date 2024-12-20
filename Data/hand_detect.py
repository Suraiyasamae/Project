import threading
import keyboard
import requests
import csv
from datetime import datetime
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


# ESP32 configuration
ESP32_IP = "192.168.0.41"
URL = f"http://{ESP32_IP}/save"

def create_folders_for_today():
    """สร้างโฟลเดอร์สำหรับวันที่ปัจจุบัน, ข้อมูล CSV และรูปภาพ"""
    today = datetime.now().strftime("%Y-%m-%d")
    data_folder = os.path.join(today, "data")
    image_folder = os.path.join(today, "images")
    
    os.makedirs(data_folder, exist_ok=True)
    os.makedirs(image_folder, exist_ok=True)
    
    return today, data_folder, image_folder

def get_thermal_data():
    """ดึงข้อมูลความร้อนจาก ESP32 ผ่านการร้องขอ HTTP"""
    response = requests.get(URL)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

def save_to_csv(data, filename, label):
    """บันทึกข้อมูลความร้อนไปยังไฟล์ CSV"""
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            headers = ["Time Stamp"] + list(range(0, len(data))) + ["Label"]
            writer.writerow(headers)
        
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data + [label])

def temperature_to_color(t):
    """กำหนดสีตามช่วงอุณหภูมิ"""
    if t < 27.0:
        return (52/255, 112/255, 235/255)  # น้ำเงินเข้ม
    elif t < 27.5:
        return (52/255, 142/255, 235/255)  # น้ำเงินปานกลาง
    elif t < 28.0:
        return (52/255, 177/255, 235/255)  # ฟ้า
    elif t < 28.5:
        return (52/255, 235/255, 235/255)  # ฟ้าสว่าง
    elif t < 29.0:
        return (228/255, 235/255, 52/255)  # เหลืองอ่อน
    elif t < 29.5:
        return (235/255, 195/255, 52/255)  # เหลืองส้ม
    elif t < 30.0:
        return (235/255, 131/255, 52/255)  # ส้มอ่อน
    elif t < 30.5:
        return (235/255, 83/255, 52/255)   # ส้มเข้ม
    elif t < 31.0:
        return (217/255, 39/255, 39/255)   # แดงอ่อน
    else:
        return (196/255, 2/255, 2/255)     # แดงเข้ม



def plot_thermal_image(row_data, timestamp, image_folder):
    """พล็อตภาพความร้อนจากข้อมูลดิบและบันทึกในโฟลเดอร์ที่กำหนด"""
    try:
        row_data_numeric = np.array([float(x) for x in row_data[1:-1]])
    except ValueError:
        print("Error: Non-numeric data found.")
        return

    # Reshape data to 24x32 grid
    thermal_data = row_data_numeric.reshape(24, 32)

    # Define the color map
    cmap = plt.cm.coolwarm  # Using coolwarm for the temperature range

    fig, ax = plt.subplots()

    # Create the heatmap with numbers
    im = ax.imshow(thermal_data, cmap=cmap, interpolation='nearest')

    # Annotate each cell with the numeric value
    for i in range(24):
        for j in range(32):
            text = ax.text(j, i, f"{thermal_data[i, j]:.1f}",
                           ha="center", va="center", color="black", fontsize=3)
            

    # Add color bar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.set_label('Temperature (°C)')

    # Format the title and save the image
    safe_timestamp = timestamp.replace(':', '-').replace(' ', '_')
    plt.title(f'Heatmap of MLX90640, at Time: {safe_timestamp}', fontsize=10)
    
    image_filename = os.path.join(image_folder, f"thermal_image_{safe_timestamp}.png")
    plt.savefig(image_filename)
    plt.close()
    print(f"Image saved as {image_filename}")

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
    today_folder, data_folder, image_folder = create_folders_for_today()
    start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_file = os.path.join(data_folder, f"{start_time}.csv")
    run_image_folder = os.path.join(image_folder, start_time)
    os.makedirs(run_image_folder, exist_ok=True)

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
                
                plot_thermal_image([current_timestamp] + data + [label], 
                                 current_timestamp, 
                                 run_image_folder)

            time.sleep(0)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        stop_flag.set()
        key_thread.join(timeout=1)
        print(f"\nData collection complete.")
        print(f"CSV file saved in {data_folder}")
        print(f"Thermal images saved in {run_image_folder}")


if __name__ == "__main__":
    main() 
