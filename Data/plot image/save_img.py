import requests  # ใช้สำหรับส่ง HTTP requests
import csv  # ใช้สำหรับบันทึกและอ่านข้อมูลจากไฟล์ CSV
from datetime import datetime  # ใช้สำหรับจัดการข้อมูลเวลาปัจจุบัน
import pandas as pd  # ใช้ในการจัดการข้อมูลในรูปแบบตาราง (DataFrame)
import numpy as np  # ใช้สำหรับการคำนวณเชิงตัวเลขและการจัดการอาร์เรย์
import matplotlib.pyplot as plt  # ใช้สำหรับการพล็อตภาพ
import matplotlib.colors as mcolors  # ใช้ในการสร้าง colormap สำหรับการพล็อตภาพ

#///////////// ESP32 configuration //////////////////////////////////////////////////////////////////////////

ESP32_IP = "192.168.0.41"  # กำหนดที่อยู่ IP ของ ESP32
URL = f"http://{ESP32_IP}/save"  # URL ที่จะใช้ในการดึงข้อมูลจาก ESP32

# ///////////// CSV file name ///////////////////////////////////////////////////////////////////////////////////

CSV_FILE = "thermal_data.csv"  # ชื่อไฟล์ CSV ที่จะใช้บันทึกข้อมูล

#ดึงข้อมูล

def get_thermal_data():
    """ดึงข้อมูลความร้อนจาก ESP32 ผ่านการร้องขอ HTTP"""
    response = requests.get(URL)  # ส่งคำขอ HTTP GET ไปยัง ESP32
    if response.status_code == 200:  # ตรวจสอบว่าการตอบสนองสำเร็จหรือไม่
        return response.json()  # ส่งคืนข้อมูล JSON ถ้าสำเร็จ
    else:
        print(f"Error: {response.status_code}")  # แสดงข้อความข้อผิดพ  ลาดถ้าไม่สำเร็จ
        return None  # คืนค่า None ถ้าไม่สามารถดึงข้อมูลได้

def save_to_csv(data, filename=CSV_FILE):
    """บันทึกข้อมูลความร้อนไปยังไฟล์ CSV"""
    with open(filename, 'a', newline='') as file:  # เปิดไฟล์ CSV ในโหมดเพิ่มข้อมูล (append)
        writer = csv.writer(file)  # สร้าง writer object สำหรับเขียนข้อมูลลงไฟล์ CSV
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data)  # เขียนเวลาปัจจุบันและข้อมูลอุณหภูมิลงในไฟล์

#///////////// พล็อตเป็นภาพ //////////////////////////////////////////////////////////////////////////////////////

def temperature_to_color(t):
    """กำหนดสีตามช่วงอุณหภูมิ"""
    
    if t < 27.99:
        return (235/255, 131/255, 52/255)  # สีส้ม
    elif t < 28.51:
        return (235/255, 195/255, 52/255)  # สีเหลืองอ่อน
    elif t < 28.99:
        return (228/255, 235/255, 52/255)  # สีเขียวอ่อน
    elif t < 29.51:
        return (187/255, 235/255, 52/255)  # สีเขียวเข้ม
    elif t < 29.99:
        return (177/255, 235/255, 52/255)  # สีเขียวอ่อนมาก
    elif t < 30.51:
        return (52/255, 235/255, 110/255)  # สีเขียว
    elif t < 30.99:
        return (52/255, 235/255, 191/255)  # สีน้ำเงินเขียว
    elif t < 31.55:
        return (52/255, 235/255, 235/255)  # สีฟ้าอ่อน
    elif t < 31.99:
        return (83/255, 213/255, 83/255)  # สีเขียว
    elif t < 32.55:
        return (52/255, 177/255, 235/255)  # สีน้ำเงินอ่อน
    elif t < 32.99:
        return (52/255, 142/255, 235/255)  # สีน้ำเงิน
    elif t < 33.55:
        return (52/255, 112/255, 235/255)  # สีน้ำเงินเข้ม
    elif t < 34.00:
        return (52/255, 83/255, 235/255)  # สีน้ำเงินเข้มมาก
    elif t < 34.55:
        return (29/255, 63/255, 231/255)  # สีน้ำเงินเข้มที่สุด
    elif t < 34.99:
        return (0/255, 0/255, 255/255)  # สีน้ำเงิน
    elif t < 35.00:
        return (217/255, 39/255, 39/255)  # สีแดง
    else:
        return (2/255, 2/255, 196/255)  # สีน้ำเงินเข้มมาก

def plot_thermal_image(row_data, timestamp):
    """พล็อตภาพความร้อนจากข้อมูลดิบ"""
    row_data_numeric = pd.to_numeric(row_data[1:], errors='coerce')  # แปลงข้อมูลอุณหภูมิให้เป็นตัวเลข (ข้ามเวลาในคอลัมน์แรก)
    if row_data_numeric.isnull().any():  # ตรวจสอบว่ามีข้อมูลที่ไม่ใช่ตัวเลขหรือไม่
        print("Error: Non-numeric data found.")  # แสดงข้อความข้อผิดพลาดถ้าพบข้อมูลที่ไม่ใช่ตัวเลข
        return  # ออกจากฟังก์ชันถ้าพบข้อผิดพลาด

    thermal_data = np.array(row_data_numeric).reshape(24, 32)  # แปลงข้อมูลเป็นอาร์เรย์ขนาด 24x32

    cmap = mcolors.LinearSegmentedColormap.from_list(
        'custom_cmap',  # ชื่อของ colormap ที่สร้างขึ้นเอง
        [temperature_to_color(t) for t in np.linspace(27.99, 35.00, 256)],  # กำหนดสีตามช่วงอุณหภูมิ
        N=256  # จำนวนสีใน colormap
    )

    fig, ax = plt.subplots()  # สร้างรูปภาพและแกน (axis)
    im = ax.imshow(thermal_data, cmap=cmap, interpolation='nearest')  # พล็อตภาพความร้อน
    cbar = plt.colorbar(im)  # เพิ่มแถบสี (colorbar)
    cbar.set_label('Temperature (°C)')  # ตั้งชื่อแถบสี

    safe_timestamp = timestamp.replace(':', '-')  # แทนที่ ':' ด้วย '-' ในชื่อเวลา เพื่อให้สามารถใช้เป็นชื่อไฟล์ได้
    plt.title(f'Thermal Image at {timestamp}')  # ตั้งชื่อภาพด้วยเวลา
    plt.savefig(f"thermal_image_{safe_timestamp}.png")  # บันทึกภาพเป็นไฟล์ PNG
    plt.close()  # ปิดรูปภาพเพื่อป้องกันการใช้หน่วยความจำเกิน


# ดึงข้อมูลเพื่อ save ในไฟล์ CSV


def main():
    # Get and save data
    data = get_thermal_data()  # ดึงข้อมูลอุณหภูมิจาก ESP32
    if data:  # ถ้าดึงข้อมูลสำเร็จ
        save_to_csv(data)  # บันทึกข้อมูลลงในไฟล์ CSV
        print("Data saved to CSV")  # แสดงข้อความว่าบันทึกข้อมูลสำเร็จ
    else:
        print("Failed to get data")  # แสดงข้อความว่าดึงข้อมูลไม่สำเร็จ

    # Read and plot data
    csv_data = pd.read_csv(CSV_FILE, header=None)  # อ่านข้อมูลจากไฟล์ CSV โดยไม่มีส่วนหัว
    for index, row in csv_data.iterrows():  # วนลูปผ่านแต่ละแถวของข้อมูลใน CSV
        timestamp = row[0]  # ดึงเวลาที่บันทึกข้อมูล
        plot_thermal_image(row, timestamp)  # พล็อตภาพความร้อนสำหรับแถวนั้น ๆ

if __name__ == "__main__":
    main()  # เรียกใช้ฟังก์ชัน main() เมื่อรันโปรแกรมโดยตรง 