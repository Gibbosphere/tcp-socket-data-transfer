# Kane Gibson GBSKAN001
# Group 7
import hashlib
import os
from pathlib import Path
import socket
import sys



# CONSTANTS
HEADERSIZE = 8 # this will be used as the size of the first message always received that contains the length of the message
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())  # gives us the IP address of the server (we are using this device for this app)
ADDR = (SERVER, PORT)
HERE = os.path.dirname(os.path.abspath(__file__)) # directory to find files on server

ListOfKeys = [] # keys for the protected files this client has


# FUNCTIONS
# returns header of message according to designed protocol
def getMessageHeader(method, fileName, protection):
    messageHeader = method + " " + fileName + " " + protection + "\n"

    if method == "download":
        # if you want a list of all the files, give every key you have for every protected file you have
        if fileName == "ListOfFiles.txt":
            for file in ListOfKeys:
                messageHeader += file[0] + " " + file[1] + "\n"

        # if you want to download one file, you just need to give that file's key
        elif getFileKey(fileName) is not None: # if you have a key for this file then add it to the header
            messageHeader += fileName + " " + getFileKey(fileName) + "\n"

    elif method == "upload":
        # if you are uploading a protected file, you need to supply a key
        if protection == "protected":
            messageHeader += fileName + " " + getFileKey(fileName) + "\n"

        # Just to be thorough about every command the client can send to server 
        elif protection == "open":
            pass

    messageHeader += "\n"
    return messageHeader

# returns contents of file as bytes, converted to a string
def getMessageBody(fileName):
    fileName = os.path.join(HERE, fileName)  # Search for file in correct directory
    myFile = open(fileName, "rb")
    messageBody = myFile.read()
    myFile.close()
    return str(messageBody)

# write file to client side
def storeFile(fileName, message):
    message = message.encode().decode('unicode_escape').encode("raw_unicode_escape")
    tfileName = fileName
    tfileName = os.path.join(HERE, tfileName)  # Search for file in correct directory
    myFile = open(tfileName, "wb")
    myFile.write(message)
    myFile.close()

# Checks if file exists, else it creates it
def checkListOfKeys():
    file_path = os.path.join(HERE,'ListOfKeys.txt')
    if not os.path.exists(file_path):
        f = open(file_path, 'wb')
        f.close()

# fills/refills the array of files stored on the server
def fillListOfKeysArray():
    fileName = os.path.join(HERE, 'ListOfKeys.txt')  # Search for file in correct directory
    myFile = open(fileName, 'r', encoding='utf-8')
    i = 0 
    for line in myFile:
        ListOfKeys.append(line.split(" "))
        ListOfKeys[i][len(ListOfKeys[i])-1] = ListOfKeys[i][len(ListOfKeys[i])-1][:-1]  # remove \n
        i += 1

# adds a new file and key that the client has
def updateListOfKeys(fileName, key):
    ListOfKeys.clear()
    files = os.path.join(HERE, 'ListOfKeys.txt')  # Search for file in correct directory
    myFile = open(files, 'a', encoding='utf-8')
    myFile.write(f'{fileName} {key}\n')
    myFile.close()
    fillListOfKeysArray()

# get the key for a given protected file. return none if file does not exist
def getFileKey(fileName):
    for file in ListOfKeys:
        if fileName == file[0]:
            return file[1]
    return None

# responsible for sending messages to the server
def send(message):
    message = message.encode('iso-8859-1') # encodes the actual string message data into bytes
    msgLength = len(message)  # this will give the number of characters in the string
    sendLength = str(msgLength).encode('iso-8859-1') # this will give the length of the message as bits. If msgLength is 24, send_length will be 00011000
    sendLength = b'0' * (HEADERSIZE - len(sendLength)) + sendLength # padding the send length so it will always be 7 characters long. e.g. 11000 will become 0011000

    client.send(sendLength)  # first message sent is the length of the full message incoming
    client.sendall(message)  # then send actual message (including header and body)

# what to do when message is received from server
def receive(method, fileName):
    msg_length = client.recv(HEADERSIZE).decode('iso-8859-1') # first message received always tells us the size of the full incoming message

    if msg_length:
        msg_length = int(msg_length) 
        message = client.recv(msg_length).decode('iso-8859-1')  # receiving the whole message now
        checkSum = message[:message.find(" ")] 
        message = message[message.find(" ")+1:]

        if validateCheckSum(checkSum, message):
            success = message[:message.find("\n")]

            if (method == "download") and (fileName != "ListOfFiles.txt") and (success == "successful"):
                message = message[message.find("\n")+3:-1]
                storeFile(fileName, message)
                print("[DOWNLOAD SUCCESSFUL] - file successfully received and saved")
            else:
                message = message[message.find("\n")+1:]
                print(message)
        else:
            print("[MESSAGE CORRUPT] - message received from server was found to be corrupted")

# end connection between server and client
def endConnection():
    send("<END>")
    receive(None, None)
    sys.exit()


# validate receiving messages
def validateCheckSum(checkSum, receivedMessage):
    if (getCheckSum(receivedMessage) == checkSum):
        return True
    
    return False

# calculate a checksum value to attach to header the the md5 hashing algorithm
def getCheckSum(message):
    bytes = message.encode('iso-8859-1')
    readable_hash = hashlib.md5(bytes).hexdigest()
        
    return readable_hash



# MAIN
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)
print("GIBSON'S FILE TRANSFERS")
checkListOfKeys()
fillListOfKeysArray()

connected = True
while connected:
    # Input command from the user to send to the server
    invalid = True
    invalid2 = True
    while invalid:
        method = input('Would you like to upload(u), download(d), list the available files for download (l), or add a key for a protected file (a)?  (type \'q\' to quit)\n')
        if (method.lower() == "u"):
            method = "upload"
            invalid = False
            fileName = input('Enter the name of the file to upload.  (type \'q\' to quit)\n')
            if (fileName == "q"):
                endConnection()
            if (' ' in fileName): # file names cannot have space characters
                invalid = True
                print('File names cannot include space characters')
                continue
            
            path = Path(os.path.join(HERE, fileName))
            if not (path.is_file()):
                invalid = True
                print('File does not exist')
                continue

            while invalid2:
                protection = input('Are you uploading a protected(p) or open(o) file?  (type \'q\' to quit)\n')
                if (protection.lower() == "p"):   # if you are uploading a protected file, you need to supply a key
                    protection = "protected"
                    invalid2 = False
                    key = input(f"Please enter a key for your protected file, {fileName}\n")
                    updateListOfKeys(fileName, key)  # if you upload this protected file, you will premanently have its key. So we will add it to our list of keys.
                elif (protection.lower() == 'o'):
                    protection = "open"
                    invalid2 = False
                elif (protection.lower() == "q"): 
                    endConnection()
                else:
                    print("Invalid command.")

        elif (method.lower() == "d"):
            method = "download"
            invalid = False
            fileName = input('Enter the name of the file to download.  (type \'q\' to quit)\n') 
            if (' ' in fileName):
                invalid = True
                print('File names cannot include space characters')
                continue
            if (fileName == "q"):
                endConnection()
            protection = "open" 

        elif (method.lower() == "l"):
            method = "download"
            invalid = False
            fileName = "ListOfFiles.txt"
            protection = "open"

        elif (method.lower() == "a"):
            invalid = False
            fileName = input('Enter the name of the file you have a key for.  (type \'q\' to quit)\n') 
            if (' ' in fileName):
                invalid = True
                print('File names cannot include space characters')
                continue
            key = input(f'Enter the key for the file {fileName}.  (type \'q\' to quit)\n') 
            updateListOfKeys(fileName, key)
            print("[INPUT SUCCESSFUL: key and file successfully added to list]")

        elif (method.lower() == "q"):
            endConnection()

        else:
            print("Invalid command.")

    if (method.lower() == "a"):
        continue


    # Building the message to send
    messageHeader = ""
    messageBody = ""

    if method != "download" and fileName != "ListOfFiles.txt":  # if you request a download, your message will have no body
        messageBody = getMessageBody(fileName) 
    messageHeader = getMessageHeader(method, fileName, protection)

    message = messageHeader + messageBody
    message = getCheckSum(message) + " " + message

    # Sending message
    send(message)
    # Receiving server response
    receive(method, fileName)

    

