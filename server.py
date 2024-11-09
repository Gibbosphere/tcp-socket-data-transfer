# Networks Assignment 1
# Group 7 - GRDDAN017, THMJOR002, GBSKAN001
import os
import socket
import threading  # we will use threading to allow for multiple client connections to the server similtaneously
import hashlib


# CONSTANTS
HEADERSIZE = 8 # the first message we recieve will tell us the size of the entire message (it will be a length of 8 i.e max num characters we can send is 99 999 999 characters)
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())  # gives us the IP address of the server (we are using this device for this app)
ADDR = (SERVER, PORT) # the full address includes both the IP address and port#
#HERE = os.path.dirname(os.path.abspath(__file__)) # directory to find files on server

listOfFiles = [] # available files this server has stored



# FUNCTIONS
def start():
    checkDirectory()        # handle establishing path
    checkListOfFiles()
    server.listen(5) # our server must constantly be listening for any potential clients
    print(f"[LISTENING] server is listening on {SERVER}")
    fillListOfFilesArray()
    
    while True:
        conn, addr = server.accept() # waits infinitely for a new connection to the server. Then store addr (IP and port#) and a connection (an actual connection obect between client and server)
        thread = threading.Thread(target=handleClient, args=(conn,addr)) # Once we receive a connection, start this new connection between a client and the server in its own thread
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}") # this tells us number of clients connected (-1 because of main thread that's always listening for new connection)


def handleClient(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADERSIZE).decode('iso-8859-1') # first message received always tells us the size of the full incoming message

        if msg_length:
            msg_length = int(msg_length) 
            message = (conn.recv(msg_length).decode('iso-8859-1'))  # receiving the whole message now 
            if message != "<END>":
                # Extract header information
                checkSum = message[:message.find(" ")]
                message = message[message.find(" ")+1:] # cut off checksum
                actualMessage = message # use actual message for checksum validation
                method = message[:message.find(" ")]
                message = message[message.find(" ")+1:] # cut off method
                fileName = message[:message.find(" ")]
                message = message[message.find(" ")+1:] # cut off filename
                protection = message[:message.find("\n")]
                #print(f'method: {method}, file name: {fileName}, protection: {protection}, checksum: {checkSum}')

                # Handle client request
                if (validateCheckSum(checkSum, actualMessage)): # first check for corruption
                    if method == "download":
                        message = message[message.find("\n")+1:] # cut off protection and the newline character
                        if fileName == "ListOfFiles.txt":
                            messageBody = "successful\n" + listAvailabeFiles(message)
                        else:
                            if fileExists(fileName):
                                if getFileProtection(fileName) == "protected":
                                    key = message[message.find(" ")+1:message.find("\n")]
                                    if isValidKey(fileName, key):
                                        messageBody = "successful\n" + getMessageBody(fileName)
                                    else:
                                        messageBody = "unsuccessful\n" + "[DOWNLOAD UNSUCCESSFUL] - file does not exist or key is incorrect"  # if incorrect provided
                                else:
                                    messageBody = "successful\n" + getMessageBody(fileName)
                            else:
                                print("Not Exists")
                                messageBody = "unsuccessful\n" + "[DOWNLOAD UNSUCCESSFUL] - file does not exist or key is incorrect"  # if file does not exist

                    elif method == "upload":
                        key = ""
                        if not(fileExists(fileName)):       # if the file doesn't already exist
                            if protection == "protected":  # extract the given key for protected file
                                message = message[message.find("\n")+1:] # cut off protection and the newline character
                                key = " " + message[message.find(" ")+1:message.find("\n")] 
                            
                            message = message[message.find("\n")+3:-1] # cut off protection and the newline character
                            message = message[message.find("\n\n")+2:] # cut off full header, just left with message body
                            storeFile(fileName, protection, key, message)
                            messageBody = "successful\n" + "[UPLOAD SUCCESSFUL] - the file has been succesfully uploaded to the server"                
                        else:
                            messageBody = "unsuccessful\n" + "[UPLOAD UNSUCCESSFUL] - file with that name already exists" 
                else:
                    messageBody = "unsuccessful\n" + "[UPLOAD UNSUCCESSFUL] - the received message was found to be corrupted"
            else:   
                connected = False
                messageBody = "successful\n" + "[CONNECTION ENDED] - connection to the server has been successfully terminated"

            send(messageBody, conn) # send requested file/error message to client 
            
    conn.close()

# Validate receiving messages
def validateCheckSum(checkSum, receivedMessage):
    if (getCheckSum(receivedMessage) == checkSum):
        return True
    
    return False

# Calculate a checksum value to attach to header the the md5 hashing algorithm
def getCheckSum(body):
        bytes = body.encode('iso-8859-1')
        readable_hash = hashlib.md5(bytes).hexdigest()
        
        return readable_hash

# return the protection of a specific file in the list
def getFileProtection(fileName):
    for item in listOfFiles:
        if item[0] == fileName:
            return item[1]
    return None

# returns True if file exists on server
def fileExists(fileName):
    for item in listOfFiles:
        if item[0] == fileName:
            return True
    return False

# Returns true if key from user matches key for that file stored on server
def isValidKey(fileName, key):
    for item in listOfFiles:
        if item[0] == fileName:
            return key == item[2]
    return False

# fills/refills the array of files stored on the server
def fillListOfFilesArray():
    fileName = os.path.join(PATH, 'ListOfFiles.txt')  # Search for file in correct directory
    myFile = open(fileName, 'r', encoding='utf-8')
    i = 0 
    for line in myFile:
        listOfFiles.append(line.split(" "))
        listOfFiles[i][len(listOfFiles[i])-1] = listOfFiles[i][len(listOfFiles[i])-1][:-1]  # remove \n
        i += 1

# read the list of files stored on the server taking into account the keys the user has
def listAvailabeFiles(message):
    # Extract client's files and keys from message header
    clientKeys = {} 
    while message[0] != "\n": # while there are still more keys
        fileName = message[:message.find(" ")]
        key = message[message.find(" ")+1:message.find("\n")]
        clientKeys[fileName] = key
        message = message[message.find("\n")+1:]  # move to next file and key

    # Get List of all available files 
    list = "Available files on server:\n"
    fileName = os.path.join(PATH, 'ListOfFiles.txt')  # Search for file in correct directory
    myFile = open(fileName, 'r', encoding='utf-8') 
    for line in listOfFiles:
        fileName = line[0] 
        protection = line[1]
        if protection == "protected":
            key = line[2]
            if clientKeys.get(fileName) != None and clientKeys[fileName] == key:  # if client has correct key for protected file, add to list
                list += f'{fileName} ({protection})\n'  
        else:  # if file is open, it is visible to all
            list += f'{fileName} ({protection})\n'

    return list

# returns contents of file as bytes, converted to a string
def getMessageBody(fileName):
    fileName = os.path.join(PATH, fileName)  # Search for file in correct directory
    myFile = open(fileName, "rb")
    messageBody = myFile.read()
    myFile.close()
    return str(messageBody)

# write file to server side
def storeFile(fileName, protection, key, message):
    message = message.encode().decode('unicode_escape').encode("raw_unicode_escape")
    tfileName = fileName
    tfileName = os.path.join(PATH, tfileName)  # Search for file in correct directory
    myFile = open(tfileName, "wb")
    myFile.write(message)
    myFile.close()
    updateListOfFiles(fileName, protection, key)

# adds an added file to the ListOfFiles.txt and refills local array of files
def updateListOfFiles(fileName, protection, key):
    listOfFiles.clear()
    files = os.path.join(PATH, 'ListOfFiles.txt')  # Search for file in correct directory
    myFile = open(files, 'a', encoding='utf-8')
    myFile.write(f'{fileName} {protection}{key}\n')
    myFile.close()
    fillListOfFilesArray()

# returns the path we will be reading and writing to and from
def checkDirectory():
    folder_path = os.path.join(os.getcwd(),'serverStorage')   # create directory path
    if not os.path.exists(folder_path):     # if it doesn't exist, create it
        os.makedirs(folder_path)
    
    global PATH 
    PATH = folder_path 

# Checks if file exists, else it creates it
def checkListOfFiles():
    file_path = os.path.join(PATH,'ListOfFiles.txt')
    if not os.path.exists(file_path):
        f = open(file_path, 'wb')
        f.close()

# responsible for sending messages to the client
def send(message, connection):
    message = getCheckSum(message) + " " + message
    message = message.encode('iso-8859-1') # encodes the actual string message data into bytes
    msgLength = len(message)  # this will give the number of characters in the string
    sendLength = str(msgLength).encode('iso-8859-1') # this will give the length of the message as bits. If msgLength is 24, send_length will be 00011000
    sendLength = b'0' * (HEADERSIZE - len(sendLength)) + sendLength # padding the send length so it will always be 7 characters long. e.g. 11000 will become 0011000
    
    connection.send(sendLength)  # first message sent is the length of the full message incoming
    connection.sendall(message)  # then send requested file

# MAIN
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # AF_INET is used for IPV4 IP addresses. SOCK_STREAM corresponds to the TCP protocol
server.bind(ADDR) # anything that connects to this address will now hit our specified socket

print("[STARTING] server is starting...")
start()

# ALSO if a file already exists do not upload it