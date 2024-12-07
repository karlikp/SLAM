import sys
import os
import time
import board
import busio
from smbus2 import SMBus  
import threading
from function import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'module')))
from module import *

i2c = busio.I2C(board.SCL, board.SDA)
bus = SMBus(1)

bmp388 = Bmp388(i2c)
bmx160 = Bmx160(1)
vl6180x = Vl6180x(i2c)
vl53l1x = Vl53l1x(i2c)

lidar = Lidar_LM1()

last_mean_calculation_time = time.time()
lidar_is_dirty = False

def sensor_reading():
    global last_mean_calculation_time
    
    try:
        while True:
            current_time = time.time()

            bmp388.save_to_file()
            bmx160.save_to_file()

            vl6180x.collect_data()
            vl53l1x.collect_data()

           
            if current_time - last_mean_calculation_time >= 0.25:
            
                vl6180x.save_to_file()
                vl53l1x.save_to_file()

                last_mean_calculation_time = current_time
    except KeyboardInterrupt:
        print("Program interrupted")


def lidar_reading():

    lidar.check_init()
    lidar.check_dirty()
    lidar_is_dirty = lidar.get_is_dirty()
    lidar.parsing_data()

    
if __name__ == "__main__":
    
    sensor_thread = threading.Thread(target=sensor_reading)
    lidar_thread = threading.Thread(target=lidar_reading)
    MQTT_thread = threading.Thread(target=send_package)

    sensor_thread.start()
    lidar_thread.start()

    if lidar_is_dirty:
        exit()
    MQTT_thread.start()

    sensor_thread.join()