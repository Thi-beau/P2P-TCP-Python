from socket import*
from datetime import datetime
import select
import time

# setting up the server to recive the image
serverName = 'localhost'
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)
print("Server is ready")
connectionSocket, addr = serverSocket.accept()


file = open("recivedImage.jpg", "wb") #creates the image, that will be writen to
image_chunk = connectionSocket.recv(2048) 

 
# loops the file writing until the image is completley transmitted

while image_chunk:
    connectionSocket.settimeout(5.0)
    file.write(image_chunk) # writes to the .jpg
    image_chunk = connectionSocket.recv(2048)
file.close() # closes the acces to the file, so that the writing is finalized