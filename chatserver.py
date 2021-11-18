from socket import *
import sys
import threading
import time
import os.path
#check that correct amount of paramaters are given
if len(sys.argv) < 2:
	print("please start server via $python3 chatserver.py port")
	sys.exit()
#set port variable
port = int(sys.argv[1])

#create tcp socket
serverSocket = socket(AF_INET, SOCK_STREAM)
#udpSocket = socket(AF_INET, SOCK_DGRAM)
#get hostname ex. 127.0.1.1
host = gethostbyname(gethostname())

connected = False
print("Attempting to bind host/port to sockets", end="", flush=True)
while not connected:
	#bind host/port to sockets
	try:
		connected = True
		serverSocket.bind((host, port))
		#udpSocket.bind((host, port))
	except OSError:
		connected = False
		print(".", end="", flush=True)
		time.sleep(3)

print("\nserver listening at", host, "on port", port)
serverSocket.listen(5)

maxConnections = 10

#list of dispatched threads for handling messages
connectionList = list() #[thread1, thread2, thread3...]

#list of currently active users, along with their assigned socket
activeUsers = list() #[(joe, joeTcpSocket), (bill, billSocket), (beth, bethSocket)...]

tempList = list() # for clearing /copying lists

#list of saved username/password pairs
credentialList = list() #[(joe, password), (bill, password1), (beth, password2)] READ IN FROM FILE (if available)

#mutexes (mutual exclusion locks) for accessing relevent lists without threading issues
userListMutex = threading.Lock()
credentialListMutex = threading.Lock()
fileMutex = threading.Lock()

#attempt to read in credentials from file credentials.txt
try:
	credentialFile = open('credentials.txt', 'r')
	lines = credentialFile.readlines()
	for line in lines:
		line = line.strip()#line = user pass
		credentialList.append((line.split()[0], line.split()[1]))#add (user, pass) to credential list
	credentialFile.close()
except IOError:
	#File not found, try to create file
	try:
		credentialFile = open('credentials.txt', 'w')
	except IOError:
		#can't create file, possible permissions error
		print("Error creating file. Are you allowed to?")

def send_op_message(socket, message):
	#sends an operation message over the supplied socket
	#operation messages will send "OP" then the message
	#handshaking to ensure each message is recieved

	socket.send("OP".encode())
	response = socket.recv(4096).decode()
	if(response != "OP"):
		print("Something went wrong sending operation code")
	else:
		socket.send(message.encode())
		response = socket.recv(4096).decode()
		if(response != "OK"):
			print("Something went wrong sending operation message")

def send_data_message(socket, message, userFrom, messageType):
	socket.send("DATA".encode())
	response = socket.recv(4096).decode()
	if(response != "DATA"):
		print("Error sending data")
	else:
		socket.send(message.encode())
		response = socket.recv(4096).decode()
		if(response == "OK"):
			socket.send(userFrom.encode())
			response = socket.recv(4096).decode()
			if(response == "OK"):
				socket.send(messageType.encode())
				response = socket.recv(4096).decode()
				if(response != "OK"):
					print("Error sending message")

#function used by client threads
def client_connection_thread(clientSocket):
	global userListMutex
	global credentialListMutex
	global fileMutex
	global credentialList
	global activeUsers

	#wait for username
	username = clientSocket.recv(4096).decode()
	
	#check if existing or new (store credentials in file)
	credentialListMutex.acquire()
	existingUser = False

	for userTuple in credentialList:
		if userTuple[0] == username:
			existingUser = True
			break
	
	credentialListMutex.release()

	#check if the user ios already logged in
	userListMutex.acquire()
	for userTuple in activeUsers:
		if userTuple[0] == username:
			#already loggged in!
			clientSocket.send("inuse".encode())
			clientSocket.close()
			userListMutex.release()
			return
	userListMutex.release()

	#handle login for existing user
	if(existingUser):
		#acknowledge client is existing
		clientSocket.send("existing".encode())
		accepted = False
		attemptCount = 0

		#allow user to attempt to login, 3 false passwords gives error and ends thread
		while(not accepted):
			#wait for password
			password = clientSocket.recv(4096).decode()
			
			credentialListMutex.acquire()
			#check password
			for userTuple in credentialList:
				if userTuple[0] == username:
					if userTuple[1] == password:
						accepted = True
					break
			credentialListMutex.release()

			if(not accepted):
				#refusal - reenter loop to ask for password
				#allowed 3 attempts
				attemptCount+=1
				if attemptCount >= 3:
					#tell client password was refused for third time, end thread
					clientSocket.send("final refuse".encode())
					clientSocket.close()
					return
				else:
					#tell client password is incorrect, allow to try again
					clientSocket.send("refused".encode())
			else:
				clientSocket.send("accepted".encode())
	else:
		#acknowledge client is new
		clientSocket.send("new".encode())
		
		#wait for password
		password = clientSocket.recv(4096).decode()
		
		#aqcknowledge new registration
		message = "News User: " + username + " Password: " + password
		clientSocket.send(message.encode())

		fileExists = os.path.isfile('credentials.txt')
		fileEmpty = (os.path.getsize('credentials.txt') == 0)#number of bytes?
		#register - add to file AND update credentialList
		fileMutex.acquire()
		file = open('credentials.txt', 'a')
		if fileExists and not fileEmpty:
			file.write("\n")
		file.write(username + " " + password)
		file.close()
		fileMutex.release()
		credentialList.append((username, password))
		#proceed to handling block

	#handling block
	#user is logged in / registered
	
	# recieve message from the udp socket
	# save somewhere in the active userList the udp address for sending messages to
	# USERlIST WILL HAVE TO BE CHANGED TO SOMETHING LIKE (username, tcpSocket, udpSocket)
	#messageType, address = udpSocket.recvfrom(4096)

	#append them to active user list
	userListMutex.acquire()
	activeUsers.append((username, clientSocket))
	userListMutex.release()
	running = True

	#tell client that it has recievd the udp address and is ready to recieve commands.
	#clientSocket.send("udp recieve".encode())
	
	while running:
		#prompt client for operation
		#clientSocket.send("operation".encode())
		
		#wait for command
		operation = clientSocket.recv(4096).decode()
		
		if operation == "PM":
			#PM - broadcast to all active () logged in and not yet exitted
			#send acknowledgement of PM request
			#prompt for message
			#clientSocket.send("PM".encode())
			send_op_message(clientSocket, "PM")
			#wait for message
			message = clientSocket.recv(4096).decode()

			#pmThread = threading.Thread(target=pm_message, args=(message, (username, clientSocket)))
			#pmThread.start()
			userListMutex.acquire()
			for userTuple in activeUsers:
				if userTuple[0] != username:
					#userTuple[1].send(message.encode())
					send_data_message(userTuple[1], message, username, "Public Message (PM)")
					#udpSocket.sendto(message.encode(), userTuple[2])
					#udpSocket.sendto(username.encode(), userTuple[2])
					#udpSocket.sendto("Public Message (PM)".encode(), userTuple[2])
			userListMutex.release()
			#clientSocket.send("complete".encode())
			send_op_message(clientSocket, "complete")
			#return to wait for command

		elif operation == "DM":
			#DM
				#acknowledge DM request
				#clientSocket.send("DM".encode())
				send_op_message(clientSocket, "DM")
				message = clientSocket.recv(4096).decode()
				if(message != "received"):
					print("Error handshaking?")
					print(message)
				
				gettingUser = True
				while gettingUser:
					userListMutex.acquire()
					for userTuple in activeUsers:
						#clientSocket.send(userTuple[0].encode())
						send_op_message(clientSocket, userTuple[0])
						message = clientSocket.recv(4096).decode()
						if(message != "received"):
							print("client did not receive username properly")
					userListMutex.release()

					#clientSocket.send("END".encode())
					send_op_message(clientSocket, "END")
					reciever = clientSocket.recv(4096).decode()

					found = False
				
					userListMutex.acquire()
					for userTuple in activeUsers:
						if userTuple[0] == reciever:
							found = True
							recieverSocket = userTuple[1]
							break
					userListMutex.release()

					if not found:
						#clientSocket.send("DNE".encode())
						send_op_message(clientSocket, "DNE")
						message = clientSocket.recv(4096).decode()
						if(message != "received"):
							print("Error receving DNE?")
					else:
						gettingUser = False
						#clientSocket.send("message".encode())
						send_op_message(clientSocket, "message")
						message = clientSocket.recv(4096).decode()
						#recieverSocket.send(message.encode())
						send_data_message(recieverSocket, message, username, "Direct Message (DM)")
						#udpSocket.sendto(message.encode(), recieverAddress)
						#udpSocket.sendto(username.encode(), recieverAddress)
						#udpSocket.sendto("Direct Message (DM)".encode(), recieverAddress)
						#clientSocket.send("complete".encode())
						send_op_message(clientSocket, "complete")
				#send client list of online users
				#wait for username AND message
				#check that user exists and is online
				#forward message to reciever's socket
				#senc client message sent confirmation or User Does Not Exist / User is NOt Online message
				#return to wait for command

		elif operation == "EX":
			running = False
			userListMutex.acquire()
			for userTuple in activeUsers:
				if userTuple[0] == username:
					activeUsers.remove(userTuple)
					break
			userListMutex.release()
			#clientSocket.send("logout".encode())
			send_op_message(clientSocket, "logout")
			clientSocket.close()
			#EX
				#close socket
				#update list of logged in threads
				#client closes it's own socket
				#allow this thread to end by exiting while loop and reaching end of the function

		else:
			#clientSocket.send("unknown".encode())
			send_op_message(clientSocket, "unkown")
			#unknown


print("Server ready to recieve connections")
while True:
	while(len(connectionList) > maxConnections):
			tempList.clear()
			for thread in connectionList:
				if thread.is_alive():
					tempList.append(thread)
			connectionList.clear()
			connectionList = tempList.copy()
	
	#wait for new connection
	newConnection, addr = serverSocket.accept()
		
	#create thread, add to list of threads, start new thread
	newThread = threading.Thread(target=client_connection_thread, args=(newConnection,))
		
	#cleanup any finished threads by removing from list
	tempList.clear()
	for thread in connectionList:
		if thread.is_alive():
			tempList.append(thread)
	connectionList.clear()
	connectionList = tempList.copy()

	#add newly created thread to list, then start it!
	connectionList.append(newThread)
	newThread.start()