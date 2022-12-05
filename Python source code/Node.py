"""
Source code to execute on each node of the network

@author Thibault Pavée
"""

from socket import *
import threading
import time
import json

# --- Global Variables ---
isAppRunning = True
networkPort = 12000
listIPAddresses = []

"""
interprets the data received and returns the data serving as a response
"""
def dataInterpretation(rawData, addr):
    dataSplited = rawData.split(b'\n')
    #the data is treated differently depending on its header (firstConnection, etc.)
    #each use case should be covered here
    if (dataSplited[0] == b'firstConnection'):
        answer = '\n'.join(listIPAddresses)
        listIPAddresses.append(str(addr))
        print("A new node wishes to connect to the network")
        print("New node address: "+ str(addr))
        print("all the ip addresses of the networks are transmitted to the new node")
        return answer.encode()
    elif (dataSplited[0] == b'JsonStr'):
        jsonName = dataSplited[1].decode()
        del dataSplited[0]
        del dataSplited[0]
        answer = '\n'.join(i.decode() for i in dataSplited)
        # Writing to json
        with open('JSON_remote/' + jsonName , "w") as outfile:
            outfile.write(answer)
        return answer.encode()
    else:
        print("received data cannot be interpreted")
        return "error\n"

"""
Wait for connection and send the appropriate response
This thread must continue as long as the rest of the application continues running
"""
def receivingThread(validations):
    selfIPAddress = gethostbyname(gethostname())
    #Creating the socket and binding "like a server"
    receivingSocket = socket(AF_INET,SOCK_STREAM)
    receivingSocket.bind((selfIPAddress, networkPort))
    #Listening to clients one by one
    receivingSocket.listen(1)
    print('The data reception thread is ready to receive')
    #Inform the main Thread that the data reception thread is ready to receive by adding a validation
    validations.append(True)
    while isAppRunning:
        #Accepting the connection
        connectionSocket, addr = receivingSocket.accept()
        print("Connection accepted")
        #Receiving the data
        rawData = connectionSocket.recv(1500000)
        #Finding what to do with the data
        answer = dataInterpretation(rawData, addr[0])
        connectionSocket.send(answer)
        #Closing the connection
        connectionSocket.close()

def startReception():
    validations = []
    print("creation of the data reception thread...")
    #Creating the Thread
    rThread = threading.Thread(target=receivingThread, args=(validations,))
    #Starting the Thread
    rThread.start()

    #waiting for the initialization of the receiving Thread
    startingTime = time.time()
    waitingTime = time.time() - startingTime
    while(len(validations) == 0 and waitingTime <=5):
        waitingTime = time.time() - startingTime
    if (len(validations) >= 1):
        return False
    return True

"""
Send data and wait for the answer
This Thread can be kill if the answer does not come in time
"""
def sendingThread(destinationIP, data, answers):
    try:
        #Creating the socket
        requestSocket = socket(AF_INET, SOCK_STREAM)
        #Connecting to the node
        requestSocket.connect((destinationIP,networkPort))
        #Sending the request to the server
        requestSocket.send(data)
        #Waiting for the answer of the node
        answer = requestSocket.recv(1500000)
        #Adding the answer to the results list (pongs)
        answers.append(answer)
        #Closing the socket
        requestSocket.close()
    except Exception:
        #If the reception is interupt, nothing appends (it's on purpose)
        pass

"""
establish connection with the first node of the p2p network

@return boolean (true == error)
"""
def firstConnection():
    #Setting first connection details
    firstNodeIP = input('Input a node IP: ')
    #the user can type "self" to test a connection on himself
    if (firstNodeIP == 'self'):
        firstNodeIP = gethostbyname(gethostname())
    listIPAddresses.append(firstNodeIP)
    request = 'firstConnection\n'

    answers = []
    print("Sending the request...")
    #Creating the Thread
    sThread = threading.Thread(target=sendingThread, args=(firstNodeIP, request.encode(), answers))
    #Starting the Thread
    sThread.start()
    #Keeping the time when the Thread sending/receiving the ping was started.
    startingTime = time.time()

    rtt = time.time() - startingTime
    #As long as the thread has not received a answer or the time is not exceeded, we continue to wait
    while (len(answers) == 0 and rtt <= 5):
        rtt = time.time() - startingTime
    
    #If the thread has not received a answer (we cut it before), we display the error
    if (len(answers) <= 0):
        print("...Reply waiting time exceeded (>= 5s)")
        error = True
    else: #we interpret the answer
        print("the RTT is " + str(rtt))
        listNewAddresses = answers[0].decode().split('\n')
        listIPAddresses.extend(listNewAddresses)
        print("the list of all the addresses of the network has been recovered obtained:")
        print(str(listIPAddresses))
        error = False
    
    #We return if there was an error
    return error

"""
send a JSON string to a node of the network

@return boolean (true == error)
"""
def sendJsonStr(ipAddr, jsonName, jsonStr):
    request = 'JsonStr\n' + jsonName + '\n' + jsonStr
    answers = []
    print("Sending the request...")
    #Creating the Thread
    sThread = threading.Thread(target=sendingThread, args=(ipAddr, request.encode(), answers))
    #Starting the Thread
    sThread.start()
    #Keeping the time when the Thread sending/receiving the ping was started.
    startingTime = time.time()

    rtt = time.time() - startingTime
    #As long as the thread has not received a answer or the time is not exceeded, we continue to wait
    while (len(answers) == 0 and rtt <= 3):
        rtt = time.time() - startingTime
    
    #If the thread has not received a answer (we cut it before), we display the error
    if (len(answers) <= 0):
        print("...Reply waiting time exceeded (>= 3s)")
        error = True
    else: #we interpret the answer
        print("the RTT is " + str(rtt))
        if (answers[0].decode() == jsonStr):
            print("The JSON was sended successfully")
            error = False
        else:
            print("The JSON was not sended successfully")
            error = True
    
    #We return if there was an error
    return error

# --- Beginning of the "main" ---

error = startReception()
if (error == True):
        print("The creation of the process for receiving data is impossible")
        quit()

error = firstConnection()
if (error == True):
        print("The connection to the network was impossible. Try again.")
        quit()

####

# Opening a JSON file as example
file = open('JSON_local/wheel_rotation_ sensor_data.json')
#Reading the file
jsonStr = file.read()
# Closing file
file.close()
# returns JSON object as a dictionary
data = json.loads(jsonStr)

#test on self
ipAddr = gethostbyname(gethostname())
error = sendJsonStr(ipAddr, 'wheel_rotation_ sensor_data.json', jsonStr)