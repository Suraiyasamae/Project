#include <Wire.h>  // ไลบรารีสำหรับการสื่อสารผ่าน I2C
#include <WiFi.h>  // ไลบรารีสำหรับการเชื่อมต่อ Wi-Fi
#include <WebServer.h>  // ไลบรารีสำหรับสร้างเว็บเซิร์ฟเวอร์
#include <Adafruit_MLX90640.h>  // ไลบรารีสำหรับการทำงานกับเซ็นเซอร์ MLX90640

// ข้อมูลการเชื่อมต่อ Wi-Fi
const char* ssid = "MedAI-146";  // ชื่อเครือข่าย Wi-Fi
const char* password = "ITD#R146";  // รหัสผ่าน Wi-Fi

// สร้างออบเจ็กต์ WebServer และ MLX90640
WebServer server(80);  // สร้างเซิร์ฟเวอร์ที่ทำงานบนพอร์ต 80 เพื่อให้ esp32 ทำหน้าที่เป็น server
Adafruit_MLX90640 mlx;  // ทำหน้าที่ในการสื่อสารกับเซ็นเซอร์และดึงข้อมูลอุณหภูมิจากเซ็นเซอร์มาใช้งาน

// ขนาดของภาพความร้อน
const int WIDTH = 32;  // ความกว้างของภาพ
const int HEIGHT = 24;  // ความสูงของภาพ
float frame[WIDTH * HEIGHT];  // อาร์เรย์สำหรับเก็บข้อมูลความร้อน

// ฟังก์ชันเพื่อเชื่อมต่อ Wi-Fi
void connectToWiFi() {
  WiFi.begin(ssid, password);  // เริ่มการเชื่อมต่อ Wi-Fi ด้วย SSID และรหัสผ่าน
  Serial.print("Connecting to WiFi");  // พิมพ์ข้อความระหว่างการเชื่อมต่อ
  unsigned long startTime = millis();  // บันทึกเวลาเริ่มต้นการเชื่อมต่อ
  while (WiFi.status() != WL_CONNECTED) {  // ตรวจสอบสถานะการเชื่อมต่อ
    delay(500);  // รอ 500 มิลลิวินาที
    Serial.print(".");  // พิมพ์จุดเพื่อแสดงความก้าวหน้า
    if (millis() - startTime > 20000) {  // หากเวลาผ่านไป 20 วินาที
      Serial.println("Failed to connect to WiFi");  // แจ้งความล้มเหลวในการเชื่อมต่อ
      return;  // ออกจากฟังก์ชัน
    }
  }
  Serial.println("Connected!");  // แจ้งว่าการเชื่อมต่อสำเร็จ
  Serial.print("IP Address: ");  // พิมพ์ที่อยู่ IP
  Serial.println(WiFi.localIP());  // แสดงที่อยู่ IP ของเครื่อง
}

// ฟังก์ชันเพื่อดึงข้อมูลความร้อนในรูปแบบ JSON
String getThermalData() {
  mlx.getFrame(frame);  // อ่านข้อมูลจากเซ็นเซอร์ MLX90640
  String data = "[";  // เริ่มต้นการสร้างสตริง JSON
  for (int i = 0; i < WIDTH * HEIGHT; i++) {  // วนลูปผ่านข้อมูลความร้อน
    data += String(frame[i]);  // แปลงข้อมูลเป็นสตริงและเพิ่มเข้าไปใน JSON
    if (i < WIDTH * HEIGHT - 1) {
      data += ",";  // เพิ่มคอมม่าระหว่างข้อมูล
    }
  }
  data += "]";  // จบ JSON array
  return data;  // คืนค่าข้อมูล JSON
}

void setup() {
  Serial.begin(115200);  // เริ่มต้นการสื่อสารทางอนุกรมที่บอเรดเรต 115200 bps (บิตต่อวินาที)
  
  // เชื่อมต่อ Wi-Fi
  connectToWiFi();  // เรียกใช้ฟังก์ชันเพื่อเชื่อมต่อ Wi-Fi

  // เริ่มต้น MLX90640 ตรวจสอบและตั้งค่าเซ็นเซอร์ MLX90640
  if (!mlx.begin()) {  // ตรวจสอบว่าเซ็นเซอร์เริ่มต้นได้สำเร็จหรือไม่
    Serial.println("Failed to find MLX90640 sensor");  // แจ้งความล้มเหลวในการค้นหาเซ็นเซอร์
    while (1);  // หยุดโปรแกรมหากเซ็นเซอร์ไม่ทำงาน
  }
  
  // กำหนดค่าเซ็นเซอร์ MLX90640 กำหนดโหมดและความละเอียดการทำงานของเซ็นเซอร์
  mlx.setMode(MLX90640_CHESS);  // ตั้งโหมดการอ่านค่าเป็น CHESS การจัดระเบียบข้อมูลที่เก็บมา
  mlx.setResolution(MLX90640_ADC_16BIT);  // ตั้งความละเอียดของ ADC เป็น 16-bit เพื่อให้ได้ข้อมูลที่มีความละเอียดสูง และการแสดงผลที่แม่นยำมากขึ้น


  // กำหนดค่าเว็บเซิร์ฟเวอร์
  server.on("/", HTTP_GET, []() {  // เมื่อมีการร้องขอ GET ที่พาธ "/"         
    String html = "<html><body><pre id='data'></pre><script>function updateData() {fetch('/thermal').then(response => response.json()).then(data => {document.getElementById('data').textContent = JSON.stringify(data, null, 2);});}function saveData() {fetch('/save');}setInterval(updateData, 500);</script></body></html>";
    server.send(200, "text/html", html);  // ส่งหน้า HTML กับไคลเอนต์
  });

  server.on("/thermal", HTTP_GET, []() {  // เมื่อมีการร้องขอ GET ที่พาธ "/thermal"
    String data = getThermalData();  // ดึงข้อมูลความร้อน
    server.send(200, "application/json", data);  // ส่งข้อมูล JSON ไปยังไคลเอนต์
  });

  server.on("/save", HTTP_GET, []() {  // เมื่อมีการร้องขอ GET ที่พาธ "/save"
    String data = getThermalData();  // ดึงข้อมูลความร้อน
    server.send(200, "application/json", data);  // ส่งข้อมูล JSON ไปยังไคลเอนต์
  });

  server.begin();  // เริ่มต้นการทำงานของเว็บเซิร์ฟเวอร์
}

void loop() {
  server.handleClient();  // จัดการคำขอของลูกค้า
}
