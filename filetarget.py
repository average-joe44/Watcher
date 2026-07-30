import struct
import os

def recv_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return bytes(data)

def download_file(sock, namafile):
    bufsize = 65536
    size_data = recv_all(sock, 8)
    if not size_data:
        return
    
    filesize = struct.unpack("Q", size_data)[0]

    if filesize in (0, 1):
        return
    recv = 0
    with open(namafile, 'wb') as file:
        while recv < filesize:
                to_read = min(bufsize, filesize - recv)
                data = sock.recv(to_read)
                if not data:
                    break
                file.write(data)
                recv += len(data)

def upload_file(sock, namafile):
    bufsize = 65536
    if not os.path.exists(namafile):
        sock.sendall(struct.pack("Q", 0))
        return
    if os.path.isdir(namafile):
        sock.sendall(struct.pack("Q", 1))
        return
    
    filesize = os.path.getsize(namafile)
    sock.sendall(struct.pack("Q", filesize))

    with open(namafile, 'rb') as f:
        while True:
            data = f.read(bufsize)
            if not data:
                break
            sock.sendall(data)
