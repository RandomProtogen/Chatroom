import sys, datetime, logging, socket as s, select, json
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import qdarktheme

#todo
#password and disbale/enable ask to join server
#implement timeout fuction with nic
#whisper functions DONE MAYBE
#inactivity kick (we shall see)
#image transmit or file transmit function
#spam preventation CLIENT SIDE
#icons
#json msgs's recv DONE MAYBE
#coloured usernames
#custom ban, kick, timeout messages
#persistent messaging
#encryption

class ClientSignals(QObject):
    userjoined = Signal(str, str)  #callsign, ip
    usersleft = Signal(str)
    logmsgs = Signal(str)
    msgreceived = Signal(str)

class ServerApp(QMainWindow):
    def __init__(self):
        super().__init__() #ngl, no i dea what this does, i followed  the tutorial like a good soldier
        self.setWindowTitle("Server Status: Inactive") #sets title
        self.setMinimumSize(800, 450) #sets min size
        self.setGeometry(100, 100, 800, 400) #sets default launch size 

        self.ip = None
        self.port = None
        self.name = None

        #maps from socket to (callsign, ip)
        self.connections = {}  #format lime socket: (callsign, ip)
        #maps from callsign to socket
        self.callsigntosock = {}
        self.jointimemap = {}

        self.signals = ClientSignals() #starts the signals and connects them to functions
        self.signals.userjoined.connect(self.adduserrow)
        self.signals.usersleft.connect(self.removeuserrow)
        self.signals.logmsgs.connect(self.appendlog)
        self.signals.msgreceived.connect(self.distribute)

        self.elapsedtimer = QTimer() #strats a QTimer which has buily in timebased functions
        self.elapsedtimer.timeout.connect(self.updatetimer)
        self.elapsedtimer.start(1000) #like this which triggers every 1000ns

        self.initUI()

    def closeEvent(self, event: QCloseEvent):
        self.stopserver()

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
        #configlayout.addWidget(self.configlabel)
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
        self.threadcount = self.threadpool.maxThreadCount() #this just gets the max thread counts

        #logs that shit
        self.appendlog(f"Multithreading with maximum {self.threadcount} threads")

    def browseconfig(self):  #this just gets up the file browser
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(parent=self, caption="Select Config File", filter='JSON Files (*.json)', options=options)
        if filename:
            self.configinput.setText(filename)

    def startserver(self):
        try:
            self.stopbutton.setEnabled(True) #enables the stop server button
            self.startbutton.setEnabled(False) #disables a bunch of widgets so you cant mess with parmaeter
            self.configinput.setEnabled(False)
            self.configbutton.setEnabled(False)
            self.nameinput.setEnabled(False)
            self.portinput.setEnabled(False)

            self.setupLogging()
            #logging.info(f"Multithreading with maximum {self.threadcount} threads") 

            self.setWindowTitle("Server Status: Booting") #sets the window to boot
            if not self.configinput.text():
                self.name = self.nameinput.text() #gets the text inside the name entry
                if not self.name: #if its empty put the default name in
                    self.name = 'General Chat'
                    self.appendlog(f'No name was chosen. Starting as {self.name}')
                else:
                    self.appendlog(f'Starting server under the name {self.name}')
                self.nameinput.setEnabled(False) #disables name entry
            else:
                try:
                    with open(self.configinput.text(), 'r') as f:
                        jsraw = f.read()
                        jspars = json.loads(jsraw)
                        self.name = jspars['name']['name']
                        self.appendlog(f'Starting server under the name {self.name}')
                except Exception:
                    self.name = 'General Chat'
                    self.appendlog(f'No name was chosen. Starting as {self.name}')

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
            self.logdisplay.append(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] Server Binding at {self.ip}:{self.port}')
            
            if not self.configinput.text():
                self.usercap = 15
            else:
                try:
                    with open(self.configinput.text(), 'r') as f:
                        jsraw = f.read()
                        jspars = json.loads(jsraw)
                        self.usercap = int(jspars['usercap']['cap'])
                except Exception:
                    logging.error("Error reading config file, using default usercap")
                    self.usercap = 15
            self.server.listen(self.usercap) #listens for set amount of conns

            if self.port == 42069 and not self.portinput.text(): #just a custom message if its default port
                self.logdisplay.append(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] User cap set to {self.usercap}.')
                self.logdisplay.append(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] No port was chosen. Listening on port {self.port}')
            else:
                self.logdisplay.append(f'[{datetime.datetime.now().strftime("%H:%M:%S")}] User cap set to {self.usercap}. Listening on port {self.port}')
            logging.info(f'User cap set to {self.usercap}. Listening on port {self.port}')

            self.socketthr = QThread() #this is all to start the connection handlers
            self.socketworker = SocketSelectWorker(self.server, self.connections, self.callsigntosock, self.signals, self.configinput, self.usercap)
            self.socketworker.moveToThread(self.socketthr)
            self.socketthr.started.connect(self.socketworker.run)
            self.socketworker.finished.connect(self.socketthr.quit)
            self.socketworker.finished.connect(self.socketworker.deleteLater)
            self.socketthr.finished.connect(self.socketthr.deleteLater)
            self.socketthr.start() #starts thread
            self.appendlog('ConnectionHandler() succesfully started')
            logging.info('ConnectionHandler() succesfully started')

            self.setWindowTitle('Server Status: Active')
        except Exception as e: #error handling
            self.appendlog(f'Error: {e}')
            logging.error(e)
            self.stopserver()

    def stopserver(self):
        self.setWindowTitle("Server Status: Inactive")
        self.startbutton.setEnabled(True)
        self.stopbutton.setEnabled(False)
        self.portinput.setEnabled(True)
        self.nameinput.setEnabled(True)
        self.configinput.setEnabled(True)
        self.configbutton.setEnabled(True)

        if hasattr(self, 'server'):
            try:
                self.socketworker.running = False
            except Exception:
                pass
            try:
                #closes client connections
                for sock in list(self.connections.keys()):
                    try:
                        sock.send(json.dumps({"type": "message", "username": "SERVER", "content": "Server Closing..."}).encode())
                        self.disconnect(sock)
                    except Exception:
                        pass
                for user in self.connections:
                    try:
                        self.removeuserrow(user, action='kicked')
                    except Exception:
                        pass
                self.connections.clear()
                self.callsigntosock.clear()
                self.server.close()
                logging.info('Server socket closed.')
            except Exception as e:
                logging.error(f'Error closing server socket: {e}')

        self.appendlog('Server has been stopped.')

    def appendlog(self, message):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.logdisplay.append(f'[{timestamp}] {message}')

    def setupLogging(self):
        if not self.configinput.text():
            self.logname = "server"
        else:
            try:
                with open(self.configinput.text(), 'r') as f:
                    jsraw = f.read()
                    jspars = json.loads(jsraw)
                    self.logname = jspars.get("logfile", {}).get("file", "server")
            except Exception as e:
                logging.error("Error reading config file for log name, using default logname: %s", e)
                self.logname = 'server'
        logging.basicConfig(
            format="{levelname} {asctime} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO,
            filename=f'{self.logname}.log',
            filemode='a'
        )
        logging.info(f"Logging started at {self.logname}.log")
        self.appendlog(f"Logging started at {self.logname}.log")

    def adduserrow(self, callsign, ipaddr):
        rowspos = self.usertable.rowCount()
        self.usertable.insertRow(rowspos)
        self.usertable.setItem(rowspos, 0, QTableWidgetItem(callsign))
        self.usertable.setItem(rowspos, 1, QTableWidgetItem(ipaddr))
        self.usertable.setItem(rowspos, 2, QTableWidgetItem('0h 0m 0s'))
        self.jointimemap[callsign] = datetime.datetime.now()

        toolslayout = QHBoxLayout()
        toolslayout.setContentsMargins(0, 0, 0, 0)
        toolslayout.setSpacing(5)
        toolswidg = QWidget()
        kickbtn = QPushButton('K')
        banbtn = QPushButton('B')
        timeoutbtn = QPushButton('T')

        kickbtn.clicked.connect(lambda _, row=rowspos: self.kick(row))
        banbtn.clicked.connect(lambda _, row=rowspos: self.ban(row))
        timeoutbtn.clicked.connect(lambda _, row=rowspos: self.naughtycorner(row))

        toolslayout.addWidget(kickbtn)
        toolslayout.addWidget(banbtn)
        toolslayout.addWidget(timeoutbtn)
        toolswidg.setLayout(toolslayout)
        self.usertable.setCellWidget(rowspos, 3, toolswidg)

    def removeuserrow(self, callsign, action='left'):
        for row in range(self.usertable.rowCount()):
            item = self.usertable.item(row, 0)
            if item and item.text() == callsign:
                self.usertable.removeRow(row)
                break

        self.jointimemap.pop(callsign, None)

        if action == 'kicked': #implement custom ban message aswell
            self.signals.logmsgs.emit(f'{callsign} has been kicked from the server.')
            self.signals.msgreceived.emit(json.dumps({"type": "leave", "users": list(self.callsigntosock.keys()), "content": f"{callsign} has been kicked from the server."}))
        elif action == 'banned':
            self.signals.logmsgs.emit(f'{callsign} has been banned from the server.')
            self.signals.msgreceived.emit(json.dumps({"type": "leave", "users": list(self.callsigntosock.keys()),"content": f"{callsign} has been banned from the server."}))
        else:
            self.signals.logmsgs.emit(f'{callsign} has left the server.')
            self.signals.msgreceived.emit(json.dumps({"type": "leave", "users": list(self.callsigntosock.keys()), "content": f"{callsign} has left the server."}))

    def updatetimer(self):
        now = datetime.datetime.now()
        for row in range(self.usertable.rowCount()):
            callsignitem = self.usertable.item(row, 0)
            if not callsignitem:
                continue
            callsign = callsignitem.text()
            if callsign in self.jointimemap:
                jointime = self.jointimemap[callsign]
                elapsed = now - jointime
                h, remainder = divmod(int(elapsed.total_seconds()), 3600)
                m, s = divmod(remainder, 60)
                elapsedstr = f"{h}h {m}m {s}s"
                elapseditem = self.usertable.item(row, 2)
                if elapseditem:
                    elapseditem.setText(elapsedstr)

    def distribute(self, message):
        #send message to all clients
        for sock in list(self.connections.keys()):
            try:
                sock.send(message.encode())
            except Exception as e:
                logging.error(f'Error sending message to client: {e}')
                self.disconnect(sock)

    def disconnect(self, sock, reason=None):
        #safely disconnect and clean up a client socket
        if sock in self.connections:
            try:
                sock.close()
            except Exception:
                pass
            callsign, _ = self.connections.pop(sock)
            self.callsigntosock.pop(callsign, None)

            #emit usersleft and log message only if normal disconnect (no reason passed)
            if reason is None:
                self.signals.usersleft.emit(callsign)
                self.signals.logmsgs.emit(f'{callsign} has left the server.')
                logging.info(f'User {callsign} disconnected')
            else:
                #for 'kicked' or 'banned', do not emit usersleft signal again,
                #as removeuserrow already emitted distinct messages
                logging.info(f'User {callsign} disconnected due to {reason}')

        self.signals.logmsgs.emit(f'Connection with {callsign} closed.')
        try:
            if sock in self.buffers:
                del self.buffers[sock]
        except Exception:
            pass


    #admin tools placeholders
    def kick(self, row):
        callsignitem = self.usertable.item(row, 0)
        if callsignitem:
            callsign = callsignitem.text()
            reply = QMessageBox.question(self, 'Confirmation', f"Are you sure you want to kick {callsign}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.appendlog(f'{callsign} has been kicked')
                logging.info(f'{callsign} has been kicked')
                sock = self.callsigntosock.get(callsign)
                if sock:
                    try:
                        sock.send(json.dumps({"type": "message", "username": "SERVER", "content": "You have been kicked from the server."}).encode())
                    except Exception:
                        pass
                    self.removeuserrow(callsign, action='kicked')  #emit kick message
                    self.disconnect(sock, reason='kicked')  #disconnect with reason 'kicked'

    def ban(self, row):
        callsignitem = self.usertable.item(row, 0)
        if not callsignitem:
            return
        callsign = callsignitem.text()
        reply = QMessageBox.question(self, 'Confirmation', f"Are you sure you want to ban {callsign}?\nNOTE: Ban will only work if you have a config file", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            iptoban = self.usertable.item(row, 1).text()
            try:
                if not self.configinput.text():
                    self.appendlog(f'Unable to ban: Config file not present')
                    logging.info(f'Unable to ban: Config file not present')
                else:
                    with open(self.configinput.text(), 'r+') as f:
                        jsraw = f.read()
                        jspars = json.loads(jsraw)
                        if 'banlist' not in jspars:
                            jspars['banlist'] = {'banned': []}
                        if 'banned' not in jspars['banlist']:
                            jspars['banlist']['banned'] = []
                        if iptoban not in jspars['banlist']['banned']:
                            jspars['banlist']['banned'].append(iptoban)
                        f.seek(0)
                        json.dump(jspars, f, indent=4)
                        f.truncate()
                        self.appendlog(f'{callsign} has been banned')
                        logging.info(f'{callsign} has been banned')
            except Exception as e:
                logging.error(f"Failed to update banlist: {e}")
            sock = self.callsigntosock.get(callsign)
            if sock:
                try:
                    sock.send(json.dumps({"type": "message", "username": "SERVER", "content": f"You have been banned from {self.name}"}).encode())
                except Exception:
                    pass
                self.removeuserrow(callsign, action='banned')  #emit ban message
                self.disconnect(sock, reason='banned')

    def naughtycorner(self, row):
        callsignitem = self.usertable.item(row, 0)
        if not callsignitem:
            return
        callsign = callsignitem.text()
        timemins, ok = QInputDialog.getText(self, "Confirmation", f"How many minutes would you like to timeout {callsign}", text=f'5')
        if not ok or not timemins.strip():
            return
        sock = self.callsigntosock.get(callsign)
        if sock:
            try:
                timemsg = {"type": "timeout", "time": int(timemins), "msg": f"You got timed out for {int(timemins)}. Sucks to be you!"}
                sock.send(json.dumps(timemsg).encode())
            except Exception:
                pass
        self.appendlog(f'{callsign} timed out for {timemins} minutes')

class SocketSelectWorker(QObject):
    finished = Signal()
    def __init__(self, serversock, connections, callsigntosock, signals, config, usercap):
        super().__init__()
        self.serversock = serversock
        self.connections = connections #socket -> (callsign, ip)
        self.callsigntosock = callsigntosock
        self.signals = signals
        self.running = True
        self.configinput = config
        self.usercap = usercap
        self.serversock.setblocking(False)

        self.buffers = {}  #socket -> bytearray buffer of received but incomplete data

    def run(self):
        try:
            inputs = [self.serversock]
            while self.running:
                readable, _, exceptional = select.select(inputs, [], inputs, 1)
                for sck in readable:
                    if sck is self.serversock:
                        #accept new connection
                        try:
                            conn, addr = self.serversock.accept()
                            conn.setblocking(False)
                            ip = addr[0]

                            #load banlist fresh from config
                            bannedips = set()
                            if self.configinput and self.configinput.text():
                                try:
                                    with open(self.configinput.text(), 'r') as f:
                                        jsraw = f.read()
                                        jspars = json.loads(jsraw)
                                        bannedips = set(jspars.get('banlist', {}).get('banned', []))
                                except Exception as e:
                                    logging.error(f"Error reading banlist from config: {e}")

                            if ip in bannedips:
                                try:
                                    conn.send(json.dumps({"type": "message", "username": "SERVER", "content": "You are banned from this server."}).encode())
                                except Exception:
                                    pass
                                conn.close()
                                self.signals.logmsgs.emit(f'Banned IP {ip} attempted to connect and was rejected.')
                                logging.info(f'Banned IP {ip} attempted to connect and was rejected.')
                                continue

                            #check if user cap is reached
                            if len(self.connections) >= self.usercap:
                                try:
                                    conn.send(json.dumps({"type": "message", "username": "SERVER", "content": "User limit reached. Please try again later."}).encode())
                                except Exception:
                                    pass
                                conn.close()
                                self.signals.logmsgs.emit(f'Connection attempt from {ip} rejected due to user cap.')
                                logging.info(f'Connection attempt from {ip} rejected due to user cap.')
                                continue

                            inputs.append(conn)
                            self.buffers[conn] = bytearray()
                            self.signals.logmsgs.emit(f'{ip} has connected!')
                        except Exception as e:
                            logging.error(f"Accept failed: {e}")
                            continue #just spitballin
                    else:
                        try:
                            data = sck.recv(2048)
                            if data:
                                self.buffers[sck].extend(data)
                                #check if callsign known for this socket
                                if sck not in self.connections:
                                    #first message expected is callsign terminated by newline or all data available
                                    try:
                                        #decode buffer and strip spaces/newlines
                                        msg = self.buffers[sck].decode(errors='ignore').strip()
                                        if msg:
                                            callsign = msg
                                            ip = sck.getpeername()[0]
                                            self.connections[sck] = (callsign, ip)
                                            self.callsigntosock[callsign] = sck
                                            self.buffers[sck] = bytearray()  #clear buffer after callsign received
                                            self.signals.userjoined.emit(callsign, ip)
                                            self.signals.logmsgs.emit(f'{callsign} has joined!') #implement custom join messages
                                            self.signals.msgreceived.emit(json.dumps({"type": "join", "users": list(self.callsigntosock.keys()), "content": f"{callsign} has joined!"}))
                                            logging.info(f'{callsign} has joined!')
                                            if not self.configinput.text():
                                                welcomemsg = f"Welcome to our humble chatroom {callsign}!"
                                            else:
                                                try:
                                                    with open(self.configinput.text()) as f:
                                                        jsraw = f.read()
                                                        jspars = json.loads(jsraw)
                                                        welcomemsg = str(eval((jspars['welcome']['msg'])))
                                                except Exception: 
                                                    logging.error("Error reading config file, using default welcome message")
                                                    welcomemsg = f"Welcome to our humble chatroom {callsign}!"
                                                    
                                            sck.send(json.dumps({"type": "welcome", "content": str(welcomemsg), "users": list(self.callsigntosock.keys())}).encode())
                                    except Exception as ex:
                                        logging.error(f"Error reading callsign: {ex}")
                                        self.closesock(sck, inputs)
                                else:
                                    callsign, _ = self.connections[sck]
                                    try:
                                        #consider all data as message (strip trailing newlines)
                                        msgtext = self.buffers[sck].decode(errors='ignore').strip()
                                        msgtextjs = json.loads(msgtext)
                                        if msgtextjs == None or "":
                                            raise Exception('this is goddamn empty')
                                        if msgtext:
                                            if msgtextjs['type'] == "message":
                                                #msg = f'<{callsign}> {msgtext}'
                                                self.signals.logmsgs.emit(f'<{msgtextjs['username']}> {msgtextjs['content']}')
                                                self.signals.msgreceived.emit(msgtext)
                                                logging.info(f'Message from {msgtextjs["username"]}: {msgtextjs["content"]}')
                                                #clear buffer after processing message
                                                self.buffers[sck] = bytearray()
                                            elif msgtextjs['type'] == "whisper":
                                                self.signals.logmsgs.emit(f'<{msgtextjs['username']}> whispered to <{msgtextjs['to']}> {msgtextjs['content']}')
                                                logging.info(f'<{msgtextjs['username']}> whispered to <{msgtextjs['to']}> {msgtextjs['content']}')
                                                recepient = self.callsigntosock.get(str(msgtextjs["to"]))
                                                recepient.send(msgtext.encode())
                                                self.buffers[sck] = bytearray()
                                                #return 'ur mother'
                                    except Exception as e:
                                        logging.error(f"Error processing message from {callsign}: {e}")
                                        self.closesock(sck, inputs)
                            else:
                                #no data means client closed connection
                                self.closesock(sck, inputs)
                        except Exception as e:
                            logging.error(f"Error receiving data: {e}")
                            self.closesock(sck, inputs)

                for sck in exceptional:
                    self.closesock(sck, inputs)
        except Exception as e:
            logging.error(f'Select worker error: {e}')
        self.finished.emit()

    def closesock(self, sock, inputs):
        if sock in inputs:
            inputs.remove(sock)
        if sock in self.connections:
            callsign, _ = self.connections.pop(sock)
            self.callsigntosock.pop(callsign, None)
            self.signals.usersleft.emit(callsign)
            self.signals.logmsgs.emit(f'Connection with {callsign} closed.')
            logging.info(f'User {callsign} disconnected')
        if sock in self.buffers:
            del self.buffers[sock]
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #app.setStyleSheet(qdarktheme.load_stylesheet())
    window = ServerApp()
    window.show()
    sys.exit(app.exec())
