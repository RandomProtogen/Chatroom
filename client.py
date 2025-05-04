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

class ChatClient:
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.is_running = True

    def connect(self):
        try:
            self.client_socket.connect(self.server_address)
            print("Connected to the server.")
            self.username = input("Enter your username: ")
            self.client_socket.send(self.username.encode())
            print("Welcome to the chatroom!")
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.send_messages()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client_socket.close()

    def receive_messages(self):
        while self.is_running:
            try:
                message = self.client_socket.recv(2048).decode()
                if message:
                    print(message)
                else:
                    print("Disconnected from server.")
                    self.is_running = False
                    self.client_socket.close()
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.is_running = False
                self.client_socket.close()

    def send_messages(self):
        while self.is_running:
            message = input()
            if message.lower() == 'exit':
                self.is_running = False
                self.client_socket.close()
                print("Disconnected from the chat.")
                break
            self.client_socket.send(message.encode())

if __name__ == "__main__":
    host = socket.gethostbyname(socket.gethostname())
    port = int(input("Enter server port (default 42069): ") or 42069)
    
    client = ChatClient(host, port)
    client.connect()
