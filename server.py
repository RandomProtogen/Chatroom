import socket as s
from _thread import *
import os

name = 'placeholder'#input('Please input the name of the server: ')
log = open(f'{name}.log', 'a')

server = s.socket(s.AF_INET, s.SOCK_STREAM) #initalises tcp/ip socket
server.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #allows us to use ip conn more than once

ip = '127.0.0.1' #implement sys.argv later
port = 8081 #just using a random port for now

server.bind((ip, port)) #bind server socket to this ip and this port
log.write(f'[+] Server Binding at {ip}:{port}')
print(f'[+] Server Binding at {ip}:{port}')

usercap = 15 #sets how many connections can be accepted
server.listen(usercap) #listens and accepts set amount of connections
log.write(f'\n[+] User cap set to {usercap}\n[+] Listening on port {port}...')
print(f'\n[+] User cap set to {usercap}\n[+] Listening on port {port}...')

connections = [] #this will store the connections and their info

def clientthread(conn, addr):
    callsign = conn.recv(2048).decode()
    print(f'{callsign} has joined!')
    conn.send("Welcome to our humble chatroom weary traveller!".encode()) #sends a welcome message, implement custom in config later
    while True:
        try:
            msgraw = conn.recv(2048).decode() #receives message up to 2048 bytes in length, should be able to set the cap of that in config
            msg = f'<{callsign}> {msgraw}' #formats the message, we can add json stuff later
            log.write(msg) #logs the message
            print(msg)
            distribute(msg, conn) 
        except Exception and WindowsError as e:
            if (e.winerror == 10054 or 10038) or e == ConnectionResetError:  # Handle the specific error for forcibly closed connections
                log.write(f'[-] Connection with {addr} forcibly closed.\n')
                distribute(f'{callsign} has left :('.encode(), conn)
                print(f'[-] Connection with {addr} forcibly closed.')
            else:
                log.write(f'[-] Error: {e}\n')
                print(f'[-] Error: {e}')
                continue
        finally:
            remove(conn)
            conn.close()
            break

def distribute(message, connection): 
    for clients in connections: 
        if clients != connection: #if the connection is not the same one that sent it it will send message
            try: 
                clients.send(message.encode())
            except: 
                clients.close()   
                remove(clients) #if link is broken remove the client 

def remove(connection): 
    if connection in connections: 
        connections.remove(connection) 
        
try:
    while True:
        conn, addr = server.accept()
        connections.append(conn)
        log.write(f'[+] {addr[0]} has connected!')
        print(f'[+] {addr[0]} has connected!')
        start_new_thread(clientthread, (conn, addr))
except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    for conn in connections:
        conn.close()
    server.close()
    log.close()
    



