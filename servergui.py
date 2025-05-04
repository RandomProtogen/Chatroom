import sys, datetime, logging, socket as s
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import qdarktheme

class ClientSignals(QObject): #signals class to communicate from worker threads to main ui thread because you have to do ui stuff in the ui class
    userjoined = Signal(str, str)  #this just defines signals to communicate with different classes and threads 
    usersleft = Signal(str)          
    logmsgs = Signal(str) #e.g this signal is just for communicating with the logdisplay ui in the ui thread
    msgreceived = Signal(str)  

class ClientWorker(QRunnable):
    def __init__(self, conn, addr, connections, users, signals): 
        super().__init__() #ngl, no idea what this does, i followed the tutorial like a good soldier
        self.users = users
        self.conn = conn #connection is carried over
        self.addr = addr #so is addr
        self.connections = connections #carries over connection array, signals, etc.
        self.signals = signals 
        self.callsign = None
        self.isactive = True

    def run(self): #this is the main client thread which recieves there username sends out a welcome msg
        try:
            self.callsign = self.conn.recv(2048).decode() #gets the first transmission which should be le username, figure out colour later
            if not self.callsign:
                self.conn.close()
                return
            #uses signal to notify ui thread of new user (puits new table)
            self.signals.userjoined.emit(self.callsign, self.addr[0])
            self.signals.logmsgs.emit(f'{self.callsign} has joined!')
            self.signals.msgreceived.emit(f'{self.callsign} has joined!')
            logging.info(f'{self.callsign} has joined!')
            try:
                self.conn.send("Welcome to our humble chatroom weary traveller!".encode())
            except Exception as e:
                self.signals.logmsgs.emit(f'Error sending welcome message: {e}')
                logging.error(f'Error sending welcome message: {e}')
                #gracefully ignores the error

            while self.isactive:
                try:
                    msgraw = self.conn.recv(2048).decode()
                    if not msgraw:  #client closed connection
                        break
                    msg = f'<{self.callsign}> {msgraw}'
                    self.signals.logmsgs.emit(msg)
                    self.signals.msgreceived.emit(msg)
                    logging.info(f'Message from {self.callsign}: {msgraw}')
                except Exception as e:
                    self.signals.logmsgs.emit(f'Error receiving message: {e}')
                    logging.error(f'Error receiving message: {e}')
                    break
        finally:
            self.removeconn()

    def removeconn(self):
        try:
            self.conn.close() #trys to close le connection
        except Exception as e:
            self.signals.logmsgs.emit(f'Error closing connection: {e}')
            logging.error(f'Error closing connection: {e}')
        
        #removes connection from connection list
        if self.conn in self.connections:
            self.connections.remove(self.conn)

        #notify ui to remove user (removes ui table row)
        if self.callsign:
            self.signals.usersleft.emit(self.callsign)
            self.signals.logmsgs.emit(f'Connection with {self.addr} closed.')
            logging.info(f'User {self.callsign} left')  #logs user leaving

class ServerApp(QMainWindow): #this is the ui class thread
    def __init__(self):
        super().__init__() #ngl, i dont know what this does, i ama good soldier and follow tutorials
        self.setWindowTitle("Server Status: Inactive") #sets the window title
        self.setMinimumSize(800, 425) #sets the min size of 800, 400px
        self.setGeometry(100, 100, 800, 400) #this is the starting size

        self.ip = None #just defines some variables that will be used later
        self.port = None
        self.name = None
        self.connections = []

        #signals used for thread friendly ui updates
        self.signals = ClientSignals()
        self.signals.userjoined.connect(self.adduserrow)
        self.signals.usersleft.connect(self.removeuserrow)
        self.signals.logmsgs.connect(self.appendlog)
        self.signals.msgreceived.connect(self.distribute)

        self.initUI() #this as it says, iniatiates ui

    def initUI(self):
        mainlayout = QHBoxLayout() #this is horizantal container for the two vertical columns

        settingslayout = QVBoxLayout() #this is the left column container that contains settings and admib tools

        settingstitle = QLabel("Server Settings") #bold title, will reuse
        settingstitle.setStyleSheet("font-weight: bold; font-size: 16px;") #just a little styling pizazz
        settingslayout.addWidget(settingstitle)

        namelayout = QHBoxLayout() #horizantal continer so the label and entry are next to each other
        self.namelabel = QLabel("Server Name:") #label
        self.nameinput = QLineEdit() #entry
        self.nameinput.setPlaceholderText("Enter Server Name") #some default placeholder text
        namelayout.addWidget(self.namelabel)
        namelayout.addWidget(self.nameinput)
        settingslayout.addLayout(namelayout)

        portlayout = QHBoxLayout() #literally the exact same thing as above entry and label
        self.portlabel = QLabel("Port:")
        self.portinput = QLineEdit()
        self.portinput.setPlaceholderText("Leave blank to run on 42069")
        self.portinput.setMaxLength(5) #except this, this limits characters to five
        self.portinput.setValidator(QIntValidator(0, 99999)) #makes it so you can only put in digits
        portlayout.addWidget(self.portlabel)
        portlayout.addWidget(self.portinput)
        settingslayout.addLayout(portlayout)

        configlayout = QHBoxLayout() #more parallel butotns labels and entrys
        self.configlabel = QLabel("Config File:")
        self.configinput = QLineEdit()
        self.configinput.setPlaceholderText('Leave this blank to run on default settings')
        self.configbutton = QPushButton("Browse")
        self.configbutton.clicked.connect(self.browseconfig) #connects up to the filebrowser function, we can revampy this later
        configlayout.addWidget(self.configlabel)
        configlayout.addWidget(self.configlabel)
        configlayout.addWidget(self.configinput)
        configlayout.addWidget(self.configbutton)
        settingslayout.addLayout(configlayout)

        buttonlayout = QHBoxLayout() #hopefully you canunderstand how this works now, this is like the 5th time ive done this
        self.startbutton = QPushButton("Start Server")
        self.startbutton.clicked.connect(self.startserver)
        self.stopbutton = QPushButton("Stop Server")
        self.stopbutton.clicked.connect(self.stopserver)
        self.stopbutton.setEnabled(False) #starts this as disabled
        buttonlayout.addWidget(self.startbutton)
        buttonlayout.addWidget(self.stopbutton)
        settingslayout.addLayout(buttonlayout)

        usertitle = QLabel("Admin Tools:")
        usertitle.setStyleSheet("font-weight: bold; font-size: 16px;")
        settingslayout.addWidget(usertitle)

        self.usertable = QTableWidget()
        self.usertable.setColumnCount(4) #does what it says on the tin
        self.usertable.setHorizontalHeaderLabels(["User", "IP Address", "Elapsed Time", "Tools"])
        self.usertable.horizontalHeader().setStretchLastSection(True)
        settingslayout.addWidget(self.usertable)

        loglayout = QVBoxLayout()
        logtitle = QLabel("Logs")
        logtitle.setStyleSheet("font-weight: bold; font-size: 16px;")
        loglayout.addWidget(logtitle)

        self.logdisplay = QTextEdit() #basically massive texg box
        self.logdisplay.setReadOnly(True) #makes it so we cant screw with it
        loglayout.addWidget(self.logdisplay)

        #puts the columns in the horizantal container
        mainlayout.addLayout(settingslayout)
        mainlayout.addLayout(loglayout)
        container = QWidget() #this is the empty window we stuff the horizantal container that has the columns in it
        container.setLayout(mainlayout)
        self.setCentralWidget(container) #focuses the screen

        self.threadpool = QThreadPool() #this is where is starts to get fun, multithreading baby
        threadcount = self.threadpool.maxThreadCount() #this just gets the max thread counts
        logging.basicConfig( #logging has started
            format="{levelname} {asctime} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO,
            filename='server.log', #i want to fix this later, i want it to be the name of the server 
            filemode='a'
        )
        logging.info(f"Multithreading with maximum {threadcount} threads") #logs that shit
        self.appendlog(f"Multithreading with maximum {threadcount} threads")

    def browseconfig(self): #this just gets up the file browser
        options = QFileDialog.Options()
        filename,  = QFileDialog.getOpenFileName(self, "Select Config File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if filename:
            self.configinput.setText(filename) #shoves the file path in the entry

    def startserver(self): #this is the spinup protocol, fancy i know
        try:
            self.startbutton.setEnabled(False) #this just diables a lot of the entrys so you cant mess with it whilre its running
            self.stopbutton.setEnabled(True)
            self.configinput.setEnabled(False)
            self.configbutton.setEnabled(False)

            self.setWindowTitle("Server Status: Booting") #sets the window to boot
            self.name = self.nameinput.text() #gets the text inside the name entry
            if not self.name: #if its empty put the default name in
                self.name = 'General Chat'
                self.appendlog(f'No name was chosen. Starting as {self.name}')
            else:
                self.appendlog(f'Starting {self.name}')
            self.nameinput.setEnabled(False) #disables name entry

            self.port = self.portinput.text() #gets le port entry val
            if not self.port: #if its empty then it becomes dfault
                self.port = 42069
            else:
                self.port = int(self.port) #if its a custom port makes sure to convert it to integer
            self.portinput.setEnabled(False) #disables the port input

            self.server = s.socket(s.AF_INET, s.SOCK_STREAM) #starts the tcp socket
            self.server.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #basically just lets use reuse the same ip and port

            self.ip = s.gethostbyname(s.gethostname()) #gets the public/private ip from your computer name
            self.server.bind((str(self.ip), int(self.port))) #binds the port and socket
            logging.info(f'Server Binding at {self.ip}:{self.port}') #logs it
            self.logdisplay.append(f'[{datetime.datetime.now().strftime('%H:%M:%S')}] Server Binding at {self.ip}:{self.port}')
            
            self.usercap = 15 #set the usercapm figure out the config file later
            self.server.listen(self.usercap) #listens for set amount of conns

            if self.port == 42069 and not self.portinput.text(): #just a custom message if its default port
                self.logdisplay.append(f'[{datetime.datetime.now().strftime('%H:%M:%S')}] User cap set to {self.usercap}.')
                self.logdisplay.append(f'[{datetime.datetime.now().strftime('%H:%M:%S')}] No port was chosen. Listening on port {self.port}')
            else:
                self.logdisplay.append(f'[{datetime.datetime.now().strftime('%H:%M:%S')}] User cap set to {self.usercap}. Listening on port {self.port}')
            logging.info(f'User cap set to {self.usercap}. Listening on port {self.port}')

            handlerworker = ConnectionHandlerWorker(self.server, self.threadpool, self.connections, self.usertable, self.signals) #starts up client thread
            self.threadpool.start(handlerworker) #pushds the thread

            self.setWindowTitle('Server Status: Active') #sets window title and server status to active
        except Exception as e: #error stuff
            self.appendlog(f'Error: {e}') #logs it
            logging.error(f"Error: {e}") 
            self.stopserver() #stops the server

    def stopserver(self): #you could potentially call this a spindown protocal, fancy eh
        self.setWindowTitle("Server Status: Inactive") #sets the server status to inactive
        self.startbutton.setEnabled(True) #reenables the entrys and diables the stop button
        self.stopbutton.setEnabled(False)
        self.portinput.setEnabled(True)
        self.nameinput.setEnabled(True)
        self.configinput.setEnabled(True)
        self.configbutton.setEnabled(True)

        for conn in self.connections: #gets all the connections and closes each one
            try:
                conn.close()
                logging.info(f'Connection {conn} closed.')
            except Exception as e: #just in case of an error
                logging.error(f'Error closing connection {conn}: {e}')

        self.connections.clear() #clears the connection list

        if hasattr(self, 'server'): #if its the server socket does some special sauce
            try:
                self.server.close()
                logging.info('Server socket closed.')
            except Exception as e: #more error handling
                logging.error(f'Error closing server socket: {e}') 

        self.appendlog('Server has been stopped.') #just more log

    def appendlog(self, message): #appends log baby
        timestamp = datetime.datetime.now().strftime('%H:%M:%S') #custom formatting logs to include timestamps
        self.logdisplay.append(f'[{timestamp}] {message}')

    def adduserrow(self, callsign, ipaddr):
        #adds user to the usertable safely on the main thread
        rowspos = self.usertable.rowCount() #this stuff is just getting the table and setting values
        self.usertable.insertRow(rowspos)
        self.usertable.setItem(rowspos, 0, QTableWidgetItem(callsign))
        self.usertable.setItem(rowspos, 1, QTableWidgetItem(ipaddr))
        self.usertable.setItem(rowspos, 2, QTableWidgetItem('0h 0m 0s'))

        toolslayout = QHBoxLayout() #horizantal layout for side to side buttons
        toolslayout.setContentsMargins(0, 0, 0, 0) #disables margins
        toolslayout.setSpacing(5) #sets paddings

        toolswidg = QWidget() #empty container to shove in the cell
        kickbtn = QPushButton('K') #defines buttons
        #kickico = QIcon('assets/kick.ico') #sets the icon
        #kickbtn.setIcon(kickico) #shoves the icon in the button
        banbtn = QPushButton('B')
        #banico = QIcon('assets/ban.ico')
        #banbtn.setIcon(banico)
        timeoutbtn = QPushButton('T')
        #timeoutico = QIcon('assets/timeout.ico')
        #timeoutbtn.setIcon(timeoutico)
 
        kickbtn.clicked.connect(lambda: self.kick(rowspos)) #connects up the buttons to functions
        banbtn.clicked.connect(lambda: self.ban(rowspos))
        timeoutbtn.clicked.connect(lambda: self.naughtycorner(rowspos))

        toolslayout.addWidget(kickbtn) #adds widgets to container
        toolslayout.addWidget(banbtn)
        toolslayout.addWidget(timeoutbtn)
        toolswidg.setLayout(toolslayout) #sets layouts

        self.usertable.setCellWidget(rowspos, 3, toolswidg) #shoves that lyout in a cell

    def removeuserrow(self, callsign): #function to remove user row
        for row in range(self.usertable.rowCount()): # sorts through the rows
            item = self.usertable.item(row, 0) #gets the callsign in cell one (or programmer brain zero) val
            if item and item.text() == callsign: #if the callsign is equal to the one we looking for it removes the row
                self.usertable.removeRow(row)
                break
        self.signals.logmsgs.emit(f'{self.callsign} has left!')
        self.signals.msgreceived.emit(f'{self.callsign} has left!')

    def distribute(self, message):
        #send message to all connections except the sender
        for client in self.connections:
            try:
                client.send(message.encode())
            except Exception as e:
                logging.error(f'Error sending message to client: {e}')
                client.close()
                if client in self.connections:
                    self.connections.remove(client)

    #placeholder methods for admin tools
    def kick(self, row):
        callsignitem = self.usertable.item(row, 0)
        reply = QMessageBox.question(self, 'Confirmation', f"Are you sure you want to ban {callsignitem.text()}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if callsignitem:
            callsign = callsignitem.text()
            if reply == QMessageBox.Yes:
                self.appendlog(f'{callsign} has been kicked')
                logging.info(f'{callsign} has been kicked')
                self.disconnect(callsign) #find connection and close it

    def ban(self, row):
        usernameitem = self.usertable.item(row, 0)
        if usernameitem:
            username = usernameitem.text()
            self.appendlog(f'[ADMIN] Ban requested for user: {username}')
            #put logic in later

    def naughtycorner(self, row):
        usernameitem = self.usertable.item(row, 0)
        if usernameitem:
            username = usernameitem.text()
            self.appendlog(f'[ADMIN] Timeout requested for user: {username}')
            #put logic in later

    def disconnect(self, username):
        #disconnects user by callsign
        disconnect = None
        for conn in self.connections:
            #to find corresponding callsign, we would need a map callsign->conn, simplify for now
            #since no such map, skipping detailed implementation
            #ass a workaround, send a kick message or close all connections? 
            #in real app you should keep {callsign: conn} mapping.
            #here just close all connections as demo
            pass
        #this method should be extended to map callsigns to connections properly

class ConnectionHandlerWorker(QRunnable):
    def __init__(self, serversock, threadpool, connections, userstable, signals):
        super().__init__()
        self.serversock = serversock
        self.threadpool = threadpool
        self.connections = connections
        self.userstable = userstable
        self.signals = signals

    def run(self):
        while True:
            try:
                conn, addr = self.serversock.accept()
                self.connections.append(conn)
                self.signals.logmsgs.emit(f'{addr[0]} has connected!')
                #start clientworker with signals for ui updating
                worker = ClientWorker(conn, addr, self.connections, self.userstable, self.signals)
                self.threadpool.start(worker)
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")
                break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #app.setStyleSheet(qdarktheme.load_stylesheet())
    window = ServerApp()
    window.show()
    sys.exit(app.exec())
