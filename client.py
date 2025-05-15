from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import _thread, sys, time, threading, json, asyncio
import socket as s


# start of gui creation, oh boy

class MainWindow(QMainWindow):
    # These are signals
    # These will have a signal received when a signal is emitted to them in another string
    # Protects the strings
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
        self.setWindowTitle("The Bench") # Sets window title
        self.setMinimumSize(1200,600)

        # my_icon = QIcon() 
        # my_icon.addFile('images\\image.png')
        # self.setWindowIcon(my_icon) # sets window icon
        self.initialiseWidgets()
        self.msgreceived.connect(self.receiveMessage) # Each of the following .connect()s to a function when the signal is called
        self.join.connect(self.addUser) 
        self.leave.connect(self.removeUser)
        self.resetSignal.connect(self.resetUserList)
        self.timeoutSignal.connect(self.timeout)
        self.closeServer.connect(self.abandonConnection)
        self.connectbtn.connect(self.connectButton.setText)
        with open("profanity_list.txt", "r") as f: # creates a list from the profanity list txt
            self.profanities = f.readline()
            self.profanities = self.profanities.split()
            #print(self.profanities)
        self.profanitiestoggle = False # automatically sets the profanity filter to off.
        self.messagesdisplay.append("Welcome to the Bench. \nOnce you have joined a server you may type /help to view the commands.")

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
        self.messagesdisplay = QTextEdit() #creates long text box
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


    def receiveMessage(self, msg): # Creates a receive message function, mainly to check if the profanity filter is True.
        if self.profanitiestoggle == True:
            for prof in self.profanities: # cycles through each profanity in the list
                proflength = len(prof) # Gets the length to detirmine how long the censor should be
                censor = ""
                for i in range(proflength):
                    censor += "*"
                msg = msg.casefold().replace(prof, censor) # Disregards the case of the string and checks and replaces if the censored word is in the message received
            self.messagesdisplay.append(msg) # appends the censored message to the message display
        else:
            self.messagesdisplay.append(msg)

    def serverConnection(self):
        # print("test")
        # also change button purpose to be disconnect
        if self.connected == False:
            self.connected = True
            if len(self.usernameEntry.text()) <= 2 or len(self.usernameEntry.text()) >= 16: # Checks if username length is within the valid range
                self.messagesdisplay.append("Username must be no greater than 12 characters and at least 2 characters long")
                self.connected = False
                return

            elif self.establishConnection() == "error": # Calls the function and checks if it returns an error.
                self.messagesdisplay.append("Server Not Found")
                self.connected = False
                return
            self.connectButton.setText("Disconnect") # Enables and disables various GUI elements. Disables server info area and enables messaging area
            self.ipEntry.setEnabled(False)
            self.portEntry.setEnabled(False)
            self.usernameEntry.setEnabled(False)
            self.messageEntry.setEnabled(True)
            self.sendButton.setEnabled(True)
            
            
        else:
            self.connectButton.setText("Connect") # Enables and disables various GUI elements. Enables server info area and disables messaging area
            self.ipEntry.setEnabled(True)
            self.portEntry.setEnabled(True)
            self.usernameEntry.setEnabled(True)
            self.messageEntry.setEnabled(False)
            self.sendButton.setEnabled(False)
            self.abandonConnection()

    
    def resetUserList(self): # resets the user list (on disconnect)
        self.userList.setPlainText("")

    def sendMessage(self):
        message = self.messageEntry.text() # gets the message in the message entry

        if self.messageEntry.text() == "": # checks if the entry is empty
            return
        elif message[0] == "/": # checks if it is a slash command
            self.messageEntry.setText("") # Sets message entry text to nothing
            if message == "/help": # checks for slash help and if it has a sub command
                self.messagesdisplay.append("Commands are:\n/help - Brings up this list\n/whisper or /w - privately message a user\n/clear - Clears the message log\n/profanity add/remove/toggle/view - Adds to or removes from the profanity or toggles it on or off\n/disconnect - If you can't manage to find the button yourself\nUse '/help <command>' to find further information on the command")
            elif message.split()[0].lower() == "/help":
                if message.split()[1].lower() in ["whisper", "w", "/whisper", "/w"]:
                    self.messagesdisplay.append("/Whisper or /w for short, allows you to privately message another user in the chatroom.\nCorrect syntax: /whisper <recipient> <message>")
                elif message.split()[1].lower() in ["clear", "/clear"]:
                    self.messagesdisplay.append("Inputting /clear will clear the messages display.")
                elif message.split()[1].lower() in ["/profanity", "profanity"]:
                    self.messagesdisplay.append("You may use /profanity to modify profanities that should be censored out during the session.\nCorrect syntax:\n/profanity add <word you want to the profanity list>\n/profanity remove <word you want to remove from the profanity list>\n/profanity toggle (either turns the profanity filter on or off)\n/profanity view (will show all filtered words)")

            elif message.split()[0] in ["/whisper", "/w"]: # whispers privately to another user, uses type "whisper" to differentiate it to the server.
                messagelist = message.split()
                if len(messagelist) < 3:  
                    self.messagesdisplay.append("No recipient or message was specified")
                    return
                if messagelist[1] not in self.userList.toPlainText().split("\n"): # If the recipient of the whisper isn't in the user list then the send fails
                    self.messagesdisplay.append("That user does not exist")
                    return
                # print(messagelist)
                recipient = messagelist[1]
                messagelist.remove(messagelist[0])  
                messagelist.remove(messagelist[0])  
                # print(messagelist)
                self.sock.send(json.dumps({
                    "type": "whisper",
                    "to": recipient,
                    "from": self.usernameEntry.text(),
                    "content": " ".join(messagelist) 
                }).encode())
                self.messagesdisplay.append(f"<i>You whisper to {recipient}: {" ".join(messagelist)}") # Appends to message area what you are whispering and who you are whispering to
            
            elif message.split()[0] == "/clear": # clears all messages in the message display
                self.messagesdisplay.setText("")
                self.messagesdisplay.append("Messages cleared.")
            
            elif message.split()[0].lower() == "/profanity": # if /profanity is used
                if message.split()[1].lower() == "add": # if profanity is added
                    self.profanities.append(message.split()[2].lower()) # adds the profanity to the local list
                    with open("profanity_list.txt", "w") as f:
                        f.write(" ".join(self.profanities)) # writes the new profanity list to the txt
                        # print(self.profanities)
                        self.messagesdisplay.append("Item added to profanities list")
                
                elif message.split()[1].lower() == "remove": # if a profanity is removed
                    try:
                        self.profanities.remove(message.split()[2].lower()) # removes the profanity from the local file list.
                        with open("profanity_list.txt", "w") as f:
                            f.write(" ".join(self.profanities)) # writes new profanity list to the txt
                            # print(self.profanities)
                            self.messagesdisplay.append("Item removed.")
                    except ValueError:
                        self.messagesdisplay.append("Item specified not in profanities.") # if the item is not in profanities.
                
                elif message.split()[1].lower() == "toggle": # turns the profanity filter on or off. self.profanities toggle affects the sending message function
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
            # print("sent")
            # This is where the message will be then sent as a dictionary
            self.sock.send(json.dumps({"type": "message", "username": self.usernameEntry.text(), "content": message, "colour": ""}).encode())
            #self.messagesdisplay.append(f"<{self.messageinfo['username']}> {self.messageinfo['content']}") # change this to be parts of the json stuff
            self.messageEntry.setText("")



    def closeEvent(self, event: QCloseEvent): # closeEvent() is automatically defined by PySide6 to run when the window is closed. In this case, the connection will be abandoned when the window is closed
        # print("dead")
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
            # print(e)
            return "error"
        
        
        self.recvThread = threading.Thread(target=self.receiveThread, args=(self.sock,)) # creates the thread for receiving messages
        self.recvThread.start() # starts the thread for receiving messages

        self.callsign = str(self.usernameEntry.text()) # Sends the username to the server

    def addUser(self, user): # adds a user to the userlist
        # print("User: ", user)
        if self.connected:
            users = self.userList.toPlainText().split("\n")
            if user not in users:
                self.userList.append(user) 
                
                
                #print(users)
    
    def removeUser(self, user): # removes a specific user but this isn't use anymore
        users = self.userList.toPlainText().split("\n")
        try:
            users.remove(user)
        except Exception as e:
            #print(e)
        self.userList.setPlainText("")
        for i in users:
            self.userList.append(i)
        
       


    
    def receiveThread(self, sock): # This is a function that will be run in another thread that will receive messages

        while self.connected: # while the user is connected
            
            
            receivedMessagejson = None
            self.receivedMessage = {} # creates empty variables so the program doesn't check an undefined variable
            try:
                receivedMessagejson = sock.recv(4096).decode() # decodes the message from server
                self.receivedMessage = json.loads(receivedMessagejson) # transfers json to dictionary
                # #print("Raw Input:", self.receivedMessage) # for testing pruposes
                #self.receivedMessage = self.receivedMessage.strip() # not necessary
                
            except WindowsError: # server is closed if a windows error is received
                if self.connected: # if connected

                    self.msgreceived.emit("Server has closed") 
            except Exception as e:
                # #print("Error") # testing purposes
                # #print(e)
                #self.msgreceived.emit(f"Error in receivedThread: {e}") # <-- this is just for debugging
                self.connectbtn.emit("Connect") 
                time.sleep(0.5)
                sock.close() # disconnects with an unknown error
                break
            
            try:
                if not isinstance(self.receivedMessage, dict) or "type" not in self.receivedMessage: # Checks if received message is a dictionary and has the 'type' header
                    self.msgreceived.emit("Error receiving message from server")
                    #print("Error Receiving:", self.receivedMessage)
                    continue
                
                elif self.connected == False: # In case an unexpected disconnect occurs
                    self.receivedMessage = {}
                    self.connectbtn.emit("Connect")
                    #self.resetSignal.emit()
                    break
                # timeouts unfortunately couldn't be implemented
                
                #elif self.receivedMessage.get("type") == "timeout":
                    #self.msgreceived.emit(self.receivedMessage.get("content"))
                    #self.timeoutThread = threading.Thread(target=self.timeout, args=self.receivedMessage.get("time"),)
                    #self.timeoutThread.start()
                
                elif self.receivedMessage.get("type") == "welcome": # in the case of the welcome type
                    self.msgreceived.emit(self.receivedMessage.get("content"))

                elif self.receivedMessage.get("type") == "join": # When somebody joins
                    for user in self.receivedMessage.get("users"):
                        #print("User:", user)
                        self.join.emit(user)
                
                    
                    
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                
                elif self.receivedMessage.get("type") == "kick": # when the user is kicked
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                    

                
                elif self.receivedMessage.get("type") == "leave": # when another user leaves
                    self.resetSignal.emit() # resets signals
                    for i in self.receivedMessage.get("users"): # then loops for each item in list of users to append to the userlist.
                        self.join.emit(i)
                    
                    self.msgreceived.emit(self.receivedMessage.get("content"))
                
                
                elif self.receivedMessage.get("type") == "message": # if a message is received
                    self.msgreceived.emit(f"<{self.receivedMessage.get('username')}> {self.receivedMessage.get('content')}")
                

                elif self.receivedMessage.get("type") == "whisper": # if a whisper is received
                    self.msgreceived.emit(f"<i>{self.receivedMessage.get('username')} whispers to you: {self.receivedMessage.get('content')}")
                    
            
            except Exception as e: # if an error occurs
                # #print(e)
                try:
                    #self.messagesdisplay.append(self.receivedMessage)
                    #print()
                except Exception as e:
                    #print(e)
                    self.msgreceived.emit("Error receiving message.")
        # #print("Receive Thread ended")
        self.connected = False
    # couldn't be implemented
    '''
    def timeout(self, minutes):
        self.messageEntry.setEnabled(False)
        self.sendButton.setEnabled(False)
        try:
            time.sleep(int(minutes)*60) # minutes are given by the server but time.sleep works in seconds so it needs to be multiplied by 60
        except:
            self.messagesdisplay.append("huh there was an error timing you out, funny that")
        self.messageEntry.setEnabled(True)
        self.sendButton.setEnabled(True)
        '''

    def abandonConnection(self):
        if self.connected: # Makes sure the user is connceted
            try:
                
                self.sock.shutdown(s.SHUT_RDWR) #  Closes the connection of the socket
                self.sock.close()
                self.messagesdisplay.append("<b>You have disconnected") # appends that the user has been disconnected
                self.connected = False # Changes the state of the use to be disconnected.
                self.resetUserList() # Resets the user list
            except Exception as e: 
                #print(e)
                pass
        
        
        


if __name__ == "__main__": # checks if this file is being run
    app = QApplication(sys.argv) # sys.argv allows console inputs
    window = MainWindow()
    window.show() # actually shows the window wow
    
    app.exec() # executes the app
