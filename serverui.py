import sys, datetime, logging, socket as s
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from _thread import *
import qdarktheme

class ServerApp(QMainWindow):
    def __init__(self):
        super().__init__() #no goddamn idea what this does, i just followed the tutorial
        self.setWindowTitle("Server Status: Inactive") #does what it says 1on the tin
        self.setMinimumSize(800, 400) #sets minimum size in px
        self.setGeometry(100, 100, 800, 400) #sets default launching size

        self.ip = None
        self.port = None
        self.name = None
        self.connections = []

        self.initUI() #iniatiates ui

    def initUI(self):
        mainlayout = QHBoxLayout() #gameplan is basically horixantal layout with two vertical colums

        settingslayout = QVBoxLayout()

        #dis te title for server settings
        settingstitle = QLabel("Server Settings")
        settingstitle.setStyleSheet("font-weight: bold; font-size: 16px;")
        settingslayout.addWidget(settingstitle)

        #this is da filtered port and server name entry
        namelayout = QHBoxLayout() #uses horizantal layout ot put label and entry next to each other, this particular one is for the server name entry
        self.namelabel = QLabel("Server Name:") #wow i wonder what this does
        self.nameinput = QLineEdit()
        self.nameinput.setPlaceholderText("Enter Server Name")
        namelayout.addWidget(self.namelabel) #adds the widgets to the layouts 
        namelayout.addWidget(self.nameinput)
        settingslayout.addLayout(namelayout) #adds teh layout ot the left column

        portlayout = QHBoxLayout() #literally a copy and paste of the srever button
        self.portlabel = QLabel("Port:")
        self.portinput = QLineEdit()
        self.portinput.setPlaceholderText("5 digits")
        self.portinput.setMaxLength(5) #except this, this limits amount of characters in entry
        self.portinput.setValidator(QIntValidator(0, 99999)) #only allows numbers
        portlayout.addWidget(self.portlabel)
        portlayout.addWidget(self.portinput)
        settingslayout.addLayout(portlayout)

        #this is the config file entry
        configlayout = QHBoxLayout() 
        self.configlabel = QLabel("Config File:")
        self.configinput = QLineEdit()
        self.configinput.setPlaceholderText('Leave this blank to run on default settings')
        self.configbutton = QPushButton("Browse")
        self.configbutton.clicked.connect(self.browseconfig) #connects the clicked button to file broser function
        configlayout.addWidget(self.configlabel) #puts that shit in the left column
        configlayout.addWidget(self.configinput)
        configlayout.addWidget(self.configbutton)
        settingslayout.addLayout(configlayout)

        buttonlayout = QHBoxLayout() #horizanta layout side by side start and stop button
        self.startbutton = QPushButton("Start Server")
        self.startbutton.clicked.connect(self.startserver)  
        self.stopbutton = QPushButton("Stop Server")
        self.stopbutton.clicked.connect(self.stopserver) 
        self.stopbutton.setEnabled(False)  
        buttonlayout.addWidget(self.startbutton)
        buttonlayout.addWidget(self.stopbutton)
        settingslayout.addLayout(buttonlayout)

        #admin tools table
        usertitle = QLabel("Admin Tools:")
        usertitle.setStyleSheet("font-weight: bold; font-size: 16px;") #sets some styling
        settingslayout.addWidget(usertitle)
        self.usertable = QTableWidget() #iniates table widget
        self.usertable.setColumnCount(4) #sets 4 columsa
        self.usertable.setHorizontalHeaderLabels(["User  ", "IP Address", "Elapsed Time", "Tools"]) #creates column headings
        settingslayout.addWidget(self.usertable)
        settingslayout.addWidget(usertitle)

        loglayout = QVBoxLayout()
        logtitle = QLabel("Logs")
        logtitle.setStyleSheet("font-weight: bold; font-size: 16px;")
        loglayout.addWidget(logtitle)

        self.logdisplay = QTextEdit() #creates log text box
        self.logdisplay.setReadOnly(True) #makes it so you cant edit
        loglayout.addWidget(self.logdisplay)

        mainlayout.addLayout(settingslayout)
        mainlayout.addLayout(loglayout)
        container = QWidget() #empty widget that shoves the columns in
        container.setLayout(mainlayout)
        self.setCentralWidget(container) #centres central widget aka the whole screen

        self.threadpool = QThreadPool()
        thread_count = self.threadpool.maxThreadCount()
        logging.info(f"Multithreading with maximum {thread_count} threads")
        self.logdisplay.append(f"Multithreading with maximum {thread_count} threads")

    def browseconfig(self): #opens the file dialog
        options = QFileDialog.Options()
        filename,  = QFileDialog.getOpenFileName(self, "Select Config File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if filename:
            self.configinput.setText(filename) #puts the file path in that one entry next to config file
    
    def startserver(self):
        try:
            self.startbutton.setEnabled(False) #switched pressabe button between stop and start 
            self.stopbutton.setEnabled(True)
            self.configinput.setEnabled(False)
            self.configbutton.setEnabled(False)

            self.setWindowTitle("Server Status: Booting") #changes window title
            self.name = self.nameinput.text() #gets the text from nameinput
            if not self.name: #instates default server name
                self.name = 'General Chat'
                self.logdisplay.append(f'[+] No name was chosen. Starting as {self.name}')
            else:
                self.logdisplay.append(f'[+] Starting {self.name}')
            self.nameinput.setEnabled(False)

            #this just starts logging
            logging.basicConfig(
                filename=f'{self.name}.log', filemode='a',
                format="{levelname} {asctime} - {message}", 
                style="{", datefmt="%Y-%m-%d %H:%M",
                level=logging.INFO
                )
            logging.info(f"Starting server")

            self.logdisplay.append(f'[+] Log has been started at {self.name}.log')

            self.port = self.portinput.text() #gets text from portinput
            if not self.port: #instates default port of 42069
                self.port = 42069
            else:
                self.port = int(self.port)
            self.portinput.setEnabled(False)

            self.server = s.socket(s.AF_INET, s.SOCK_STREAM) #initalises tcp/ip socket
            self.server.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #allows us to use ip conn more than once

            self.ip = s.gethostbyname(s.gethostname())
            self.server.bind((str(self.ip), int(self.port))) #bind server socket to this ip and this port
            logging.info(f'Server Binding at {self.ip}:{self.port}')
            self.logdisplay.append(f'[+] Server Binding at {self.ip}:{self.port}')

            self.usercap = 15 #sets how many connections can be accepted, figure out config file stuff later
            self.server.listen(self.usercap) #listens and accepts set amount of connections
            if self.port == 42069 and not self.portinput.text():
                self.logdisplay.append(f'[+] User cap set to {self.usercap}.')
                self.logdisplay.append(f'[+] No port was chosen. Listening on port {self.port}')
            else:
                self.logdisplay.append(f'[+] User cap set to {self.usercap}. Listening on port {self.port}')
            logging.info(f'[+] User cap set to {self.usercap}. Listening on port {self.port}')

            start_new_thread(self.connhandler, (self.server,))
            self.setWindowTitle('Server Status: Active')

        except Exception as e:
            self.logdisplay.append(f'[-] Error: {e}')
            self.logdisplay.append('[-] Aborting...')
            logging.error(f"Error: {e}")
            logging.critical('Aborting...')
            self.stopserver()  

    def stopserver(self):
        self.setWindowTitle("Server Status: Inactive")
        self.startbutton.setEnabled(True)
        self.stopbutton.setEnabled(False) 
        self.portinput.setEnabled(True)
        self.nameinput.setEnabled(True)
        self.configinput.setEnabled(True)
        self.configbutton.setEnabled(True)

        for conn in self.connections: #goes through all the connections and closes them
            try:
                conn.close()
                logging.info(f'Connection {conn} closed.')
            except Exception as e:
                logging.error(f'Error closing connection {conn}: {e}')

        self.connections.clear()#clears connections

        #closes the server socket if it still exists
        if hasattr(self, 'server'):
            try:
                self.server.close()
                logging.info('Server socket closed.')
            except Exception as e:
                logging.error(f'Error closing server socket: {e}')

        self.logdisplay.append('[+] Server has been stopped.')

    def connhandler(self, sock):
        while True:
            conn, addr = sock.accept()
            self.connections.append(conn)
            logging.info(f'{addr[0]} has connected!')
            self.logdisplay.append(f'[+] {addr[0]} has connected!')
            start_new_thread(self.clientthread, (conn, addr))

    def clientthread(self, conn, addr):
        callsign = conn.recv(2048).decode()
        self.logdisplay.append(f'{callsign} has joined!')
        conn.send("Welcome to our humble chatroom weary traveller!".encode()) #sends a welcome message, implement custom in config later
        while True:
            try:
                msgraw = conn.recv(2048).decode() #receives message up to 2048 bytes in length, should be able to set the cap of that in config
                msg = f'<{callsign}> {msgraw}' #formats the message, we can add json stuff later
                logging.info(msg) #logs the message
                self.logdisplay.append(msg)
                self.distribute(msg, conn) 
            except Exception and WindowsError as e:
                if (e.winerror == 10054 or 10038) or e == ConnectionResetError:  # Handle the specific error for forcibly closed connections
                    logging.info(f'Connection with {addr} forcibly closed.\n')
                    self.distribute(f'{callsign} has left :('.encode(), conn)
                    self.logdisplay.append(f'[-] Connection with {addr} forcibly closed.')
                else:
                    logging.error(f'Error: {e}\n')
                    self.logdisplay.append(f'[-] Error: {e}')
                    continue
            finally:
                self.remove(conn)
                conn.close()
                break

    def distribute(self, message, connection): 
        for clients in self.connections: 
            if clients != connection: #if the connection is not the same one that sent it it will send message
                try: 
                    clients.send(message.encode())
                except: 
                    clients.close()   
                    self.remove(clients) #if link is broken self.remove the client
    

if __name__ == "__main__":
    app = QApplication(sys.argv)  # creates empty window with commandline stuff
    #app.setStyleSheet(qdarktheme.load_stylesheet()) #chekc this shit out later, default is dark you or you can specify 'light'
    window = ServerApp()  # initializes above UI class
    window.show()  # makes it visible
    sys.exit(app.exec())  # executes the app
