
from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import _thread, sys, time, threading, json, asyncio
import socket as s






# start of gui creation, oh boy



class MainWindow(QMainWindow):
    
    msgreceived = Signal(str)
    join = Signal(str)
    leave = Signal(str)
    resetSignal = Signal([])
    timeoutSignal = Signal(int)
    closeServer = Signal()
    connectbtn = Signal(str)

    def __init__(self): # when initialised
        super().__init__() # it was in the tutorial -_- canon event fr
        self.receivedMessage = {}
        self.setWindowTitle("Rizzcord for Nerds") # Sets window title
        self.setMinimumSize(1200,600)

        my_icon = QIcon()
        my_icon.addFile('images\\image.png')
        self.setWindowIcon(my_icon) # sets window icon
        self.initialiseWidgets()
        self.msgreceived.connect(self.receiveMessage)
        self.join.connect(self.addUser)
        self.leave.connect(self.removeUser)
        self.resetSignal.connect(self.resetUserList)
        self.timeoutSignal.connect(self.timeout)
        self.closeServer.connect(self.abandonConnection)
        self.connectbtn.connect(self.connectButton.setText)
        with open("profanity_list.txt", "r") as f:
            self.profanities = f.readline()
            self.profanities = self.profanities.split()
            print(self.profanities)
        self.profanitiestoggle = False
        self.messagesdisplay.append("Welcome to Rizzcord. \nOnce you have joined a server you may type /help to view the commands.")

    def initialiseWidgets(self): # new function just to seperate the creation and initialization of widgets
        
        mainlayoutnew = QHBoxLayout()
        mainlayout = QGridLayout() # main layout that is the root of everything
        infoColumnnew = QVBoxLayout() # created so that columns dont overlap
        messageColumnnew = QVBoxLayout() # created for same reason
        infoColumn = QGridLayout() # creates 2 main columns for the gui
        messageColumn = QGridLayout()

        # User List widget
        userListMain = QVBoxLayout()
        userListTitle = QLabel("Users:") # creates the title
        userListTitle.setStyleSheet("font-weight: bold; font-size: 16px;")
        userListMain.addWidget(userListTitle)
        self.userList = QTextEdit("")
        self.userList.setReadOnly(True)
        userListMain.addWidget(self.userList)
        infoColumnnew.addLayout(userListMain)

        # Server/User info

        # IP
        serverIPMain = QHBoxLayout()
        ipTitle = QLabel("Server IP: ")
        serverIPMain.addWidget(ipTitle)
        self.ipEntry = QLineEdit()
        serverIPMain.addWidget(self.ipEntry)
        self.ipEntry.setText("127.0.0.1")
        infoColumnnew.addLayout(serverIPMain)

        # Port (pretty much copy and paste of IP)

        serverPortMain = QHBoxLayout()
        portTitle = QLabel("Port: ")
        serverPortMain.addWidget(portTitle)
        self.portEntry = QLineEdit()
        self.portEntry.setMaxLength(5)
        self.portEntry.setValidator(QIntValidator(0,65535))
        serverPortMain.addWidget(self.portEntry)
        self.portEntry.setText("42069")
        infoColumnnew.addLayout(serverPortMain)

        # Username
        usernameMain = QHBoxLayout()
        usernameTitle = QLabel("Username: ")
        usernameMain.addWidget(usernameTitle)
        self.usernameEntry = QLineEdit()
        usernameMain.addWidget(self.usernameEntry)
        self.usernameEntry.setPlaceholderText("Enter a username (2-16 characters)")
        self.usernameEntry.setMaxLength(16)
        infoColumnnew.addLayout(usernameMain)

        # Colour, unfortunately can't be included
        '''
        coloursMain = QHBoxLayout()
        coloursTitle = QLabel("Colours: ")
        coloursMain.addWidget(coloursTitle)
        self.coloursOptions = QComboBox()
        self.coloursOptions.addItems(["Red", "Blue", "1", "2", "3"])
        coloursMain.addWidget(self.coloursOptions)
        infoColumnnew.addLayout(coloursMain)'''

        # Connect
        self.connected = False
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.serverConnection)
        infoColumnnew.addWidget(self.connectButton)

        # Sample button for testing purposes
        '''
        self.testButton = QPushButton("Test")
        self.testButton.clicked.connect(self.setText)
        '''
        

        # Messages area
        self.messagesdisplay = QTextEdit() #creates log text box
        self.messagesdisplay.setReadOnly(True) #makes it so you cant edit
        messageColumn.addWidget(self.messagesdisplay)
        
        # messageEntry
        messageEntryMain = QHBoxLayout()
        self.messageEntry = QLineEdit()
        self.messageEntry.setPlaceholderText('Enter Message')
        self.messageEntry.returnPressed.connect(self.sendMessage)
        self.messageEntry.setEnabled(False)
        messageEntryMain.addWidget(self.messageEntry)
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendMessage)
        self.sendButton.setEnabled(False)
        messageEntryMain.addWidget(self.sendButton)
        messageColumn.addLayout(messageEntryMain, 1, 0)



        # places the two main columns

        infoColumnnew.addLayout(infoColumn)
        messageColumnnew.addLayout(messageColumn)
        

        
        mainlayoutnew.addLayout(infoColumnnew, 1)
        mainlayoutnew.addLayout(messageColumnnew, 4)
        
        #mainlayout.addLayout(messageColumnnew, 0, 1, 0, 3) # Adds a  column for messages (sending and receiving) that spans 4 columns
        #mainlayout.addLayout(infoColumnnew, 0, 0, 0, 0) # Adds a column for info that spans 1 column 
        

        # finally places the mainlayout
        centralWidget = QWidget() # empty widget to put grid into, code breaks if this isnt done
        centralWidget.setLayout(mainlayoutnew)
        #centralWidget.setLayout(mainlayout)
        self.setCentralWidget(centralWidget)


    def receiveMessage(self, msg):
        if self.profanitiestoggle == True:
            for prof in self.profanities:
                proflength = len(prof)
                censor = ""
                for i in range(proflength):
                    censor += "*"
                msg = msg.casefold().replace(prof, censor)
            self.messagesdisplay.append(msg)
        else:
            self.messagesdisplay.append(msg)

    def serverConnection(self):
        print("test")
        # also change button purpose to be disconnect
        if self.connected == False:
            self.connected = True
            if len(self.usernameEntry.text()) <= 2 or len(self.usernameEntry.text()) >= 16:
                self.messagesdisplay.append("Username must be no greater than 12 characters and at least 2 characters long")
                self.connected = False
                return

            elif self.establishConnection() == "error":
                self.messagesdisplay.append("Server Not Found")
                self.connected = False
                return
            self.connectButton.setText("Disconnect")
            self.ipEntry.setEnabled(False)
            self.portEntry.setEnabled(False)
            self.usernameEntry.setEnabled(False)
            self.messageEntry.setEnabled(True)
            self.sendButton.setEnabled(True)
            
            
        else:
            self.connectButton.setText("Connect")
            self.ipEntry.setEnabled(True)
            self.portEntry.setEnabled(True)
            self.usernameEntry.setEnabled(True)
            self.messageEntry.setEnabled(False)
            self.sendButton.setEnabled(False)
            self.abandonConnection()
    
    
    def resetUserList(self):
        self.userList.setPlainText("")

    def sendMessage(self):
        message = self.messageEntry.text()

        if self.messageEntry.text() == "":
            return
        elif message[0] == "/":
            self.messageEntry.setText("")
            if message == "/help":
                self.messagesdisplay.append("Commands are:\n/help - Brings up this list\n/whisper or /w - privately message a user\n/clear - Clears the message log\n/profanity add/remove/toggle/view - Adds to or removes from the profanity or toggles it on or off\n/disconnect - If you can't manage to find the button yourself\nUse '/help <command>' to find further information on the command")
            elif message.split()[0].lower() == "/help":
                if message.split()[1].lower() in ["whisper", "w", "/whisper", "/w"]:
                    self.messagesdisplay.append("/Whisper or /w for short, allows you to privately message another user in the chatroom.\nCorrect syntax: /whisper <recipient> <message>")
                elif message.split()[1].lower() in ["clear", "/clear"]:
                    self.messagesdisplay.append("Inputting /clear will clear the messages display.")
                elif message.split()[1].lower() in ["/profanity", "profanity"]:
                    self.messagesdisplay.append("You may use /profanity to modify profanities that should be censored out during the session.\nCorrect syntax:\n/profanity add <word you want to the profanity list>\n/profanity remove <word you want to remove from the profanity list>\n/profanity toggle (either turns the profanity filter on or off)\n/profanity view (will show all filtered words)")

            elif message.split()[0] in ["/whisper", "/w"]:
                messagelist = message.split()
                if len(messagelist) < 3:  
                    self.messagesdisplay.append("No recipient or message was specified")
                    return
                if messagelist[1] not in self.userList.toPlainText().split("\n"): 
                    self.messagesdisplay.append("That user does not exist")
                    return
                print(messagelist)
                recipient = messagelist[1]
                messagelist.remove(messagelist[0])  
                messagelist.remove(messagelist[0])  
                print(messagelist)
                
                self.sock.send(json.dumps({
                    "type": "whisper",
                    "to": recipient,
                    "from": self.usernameEntry.text(),
                    "content": " ".join(messagelist) 
                }).encode())
                self.messagesdisplay.append(f"<i>You whisper to {recipient}: {" ".join(messagelist)}")
                '''messagelist = message.split()
                count = 0
                for i in messagelist:
                    count += 1
                if count == 1:
                    self.messagesdisplay.append("No recipient was specified")
                    return
                print(messagelist)
                recipient = messagelist[1]
                messagelist.remove(messagelist[0])
                messagelist.remove(messagelist[0])
                print(messagelist)
                messagelist = messagelist.remove(messagelist[0])
                
                self.sock.send(json.dumps({"type": "whisper", "to": recipient, "from": self.usernameEntry.text(), "content": " ".join(message)}).encode())
                self.messagesdisplay.append(f"<i>You whisper to {recipient}: {" ".join(message)}")'''
            elif message.split()[0] == "/clear":
                self.messagesdisplay.setText("")
                self.messagesdisplay.append("Messages cleared.")
            
            elif message.split()[0].lower() == "/profanity":
                if message.split()[1].lower() == "add":
                    self.profanities.append(message.split()[2].lower())
                    with open("profanity_list.txt", "w") as f:
                        f.write(" ".join(self.profanities))
                        print(self.profanities)
                        self.messagesdisplay.append("Item added to profanities list")
                elif message.split()[1].lower() == "remove":
                    try:
                        self.profanities.remove(message.split()[2].lower())
                        with open("profanity_list.txt", "w") as f:
                            f.write(" ".join(self.profanities))
                            print(self.profanities)
                            self.messagesdisplay.append("Item removed.")
                    except ValueError:
                        self.messagesdisplay.append("Item specified not in profanities.")
                elif message.split()[1].lower() == "toggle":
                    if self.profanitiestoggle == True:
                        self.profanitiestoggle = False
                        self.messagesdisplay.append("Profanity filter turned OFF")
                    else:
                        self.profanitiestoggle = True
                        self.messagesdisplay.append("Profanity filter turned ON")
                elif message.split()[1].lower() == "view":
                    self.messagesdisplay.append("Registered profanites are: " + ", ".join(self.profanities))
            else:
                self.messagesdisplay.append(f"'{message}' not found")

        else:
            print("sent")
            # This is where the message will be then sent as a dictionary
            self.sock.send(json.dumps({"type": "message", "username": self.usernameEntry.text(), "content": message, "colour": ""}).encode())
            #self.messagesdisplay.append(f"<{self.messageinfo['username']}> {self.messageinfo['content']}") # change this to be parts of the json stuff
            self.messageEntry.setText("")



    def closeEvent(self, event: QCloseEvent): # closeEvent() is automatically defined by PySide6 to run when the window is closed. In this case, the connection will be abandoned when the window is
        print("dead")
        self.abandonConnection()



    def establishConnection(self):
        self.ip = str(self.ipEntry.text()) or "127.0.0.1"
        self.port = int(self.portEntry.text()) or 42069
        self.username = self.usernameEntry.text() or "placeholder"
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM) # creates an instance of socket, SOCK_STREAM makes it tcp/ip
        try:
            self.sock.connect((self.ip, self.port))
            # self.sock.send(json.dumps({"type":"join", "username":self.username}).encode())  FOR WHEN IAN UPDATES THIS
            self.sock.send(self.username.encode())
        except WindowsError as e:
            print(e)
            return "error"
        
        
        self.recvThread = threading.Thread(target=self.receiveThread, args=(self.sock,)) 
        self.recvThread.start()

        self.callsign = str(self.usernameEntry.text())

    def addUser(self, user):
        print("User: ", user)
        if self.connected:
            users = self.userList.toPlainText().split("\n")
            if user not in users:
                self.userList.append(user)
                
                
                print(users)
    
    def removeUser(self, user):
        users = self.userList.toPlainText().split("\n")
        try:
            users.remove(user)
        except Exception as e:
            print(e)
        self.userList.setPlainText("")
        for i in users:
            self.userList.append(i)
        
       


    
    def receiveThread(self, sock):

        while self.connected:
            
            
            receivedMessagejson = None
            self.receivedMessage = {}
            try:
                receivedMessagejson = sock.recv(4096).decode()
                self.receivedMessage = json.loads(receivedMessagejson)
                print("Raw Input:", self.receivedMessage)
                #self.receivedMessage = self.receivedMessage.strip()
                
            except WindowsError:
                if self.connected:

                    self.msgreceived.emit("Server has closed")
            except Exception as e:
                print("Error")
                print(e)
                self.msgreceived.emit(f"Error in receivedThread: {e}")
                self.connectbtn.emit("Connect")
                time.sleep(0.5)
                sock.close()
                break
            
            try:
                if not isinstance(self.receivedMessage, dict) or "type" not in self.receivedMessage:
                    self.msgreceived.emit("Error receiving message from server")
                    print("Error Receiving:", self.receivedMessage)
                    continue
                
                elif self.connected == False: # This is a failsafe
                    self.receivedMessage = {}
                    self.connectbtn.emit("Connect")
                    #self.resetSignal.emit()
                    break

                elif self.receivedMessage.get("type") == "timeout":
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                    self.timeoutThread = threading.Thread(target=self.timeout, args=self.receivedMessage.get("time"),)
                    self.timeoutThread.start()

                elif self.receivedMessage.get("type") == "welcome":
                    self.msgreceived.emit(self.receivedMessage.get("content"))

                elif self.receivedMessage.get("type") == "join":
                    for user in self.receivedMessage.get("users"):
                        print("User:", user)
                        self.join.emit(user)
                
                    
                    
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                
                elif self.receivedMessage.get("type") == "kick":
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                    

                
                elif self.receivedMessage.get("type") == "leave":
                    self.leave.emit(self.receivedMessage.get("users")[0])
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                
                
                elif self.receivedMessage.get("type") == "message":
                    self.msgreceived.emit(f"<{self.receivedMessage.get('username')}> {self.receivedMessage.get('content')}")
                

                elif self.receivedMessage.get("type") == "whisper":
                    self.msgreceived.emit(f"<i>{self.receivedMessage.get('username')} whispers to you: {self.receivedMessage.get('content')}")
                    
            
            except Exception as e:
                print(e)
                try:
                    #self.messagesdisplay.append(self.receivedMessage)
                    print()
                except Exception as e:
                    print(e)
                    self.msgreceived.emit("Error receiving message.")
        print("Receive Thread ended")
        self.connected = False
    
    def timeout(self, minutes):
        self.messageEntry.setEnabled(False)
        self.sendButton.setEnabled(False)
        try:
            time.sleep(int(minutes)*60) # minutes are given by the server but time.sleep works in seconds so it needs to be multiplied by 60
        except:
            self.messagesdisplay.append("huh there was an error timing you out, funny that")
        self.messageEntry.setEnabled(True)
        self.sendButton.setEnabled(True)


    def abandonConnection(self):
        if self.connected:
            try:
                
                self.sock.shutdown(s.SHUT_RDWR)
                self.sock.close()
                self.messagesdisplay.append("<b>You have disconnected")
                self.connected = False
                self.resetUserList()
            except Exception as e:
                print(e)
                pass
        
        
        


if __name__ == "__main__": # checks if this file is being run
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # actually shows the window wow
    
    app.exec()

