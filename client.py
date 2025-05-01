import socket
import threading
"""
to do:
make gui
when exit signal is called; cleanly closes connections
implement json for messages [date/time, username, username colour, message content]
sort of account creation (create username, colour)
colour for usernames
user list
/ commands (whispering, help, cls, possible admin commands)
connect to server
spam limit
client based profanity filtering
add image support (pls dear god no)
"""

# start of gui creation, oh boy
#class ClientApp(QMainWindow):



def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(2048).decode()
            if not msg:
                print("Connection closed by the server.")
                break
            print(msg)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def main():
    server_ip = input("Enter server IP address: ")#socket.gethostbyname(socket.gethostname())
    server_port = input("Enter port: ")
    
    try:
        server_port = int(server_port)
    except ValueError:
        print("Port must be an integer.")
        return

    callsign = input("Enter your username: ")
    if callsign == "":
        print("Please enter a username:")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Send the callsign to the server
    sock.send(callsign.encode())

    # Receive welcome message
    try:
        welcome = sock.recv(2048).decode()
        print(welcome)
    except Exception as e:
        print(f"Error receiving welcome message: {e}")
        sock.close()
        return

    # Start thread to listen for messages from server
    receive_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receive_thread.start()

    # Main loop to send messages
    try:
        while True:
            msg = input()
            if msg.lower() == "/quit":
                print("Disconnecting...")
                break
            if msg.strip() == "":
                continue
            sock.send(msg.encode())
    except KeyboardInterrupt:
        print("\nDisconnecting...")

    sock.close()

if __name__ == "__main__":
    main()
