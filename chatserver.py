from socket import *
import sys
import threading
import time
import os.path

#Joseph Jackels, Punyapat Rabalert
#StarID: dn0012nk, ih2153wu
#
#
#This file is the server, it receives connections from clients, handles logging them in/creating new users
#And handling recieved operation requests and the sending of data messages.
#
#It has one parameter <port> - the port number to start the server on. must be given as an integer
#
#-main thread
#	First, the input parameter is validated, sockets are bound, and the credentials are read and saved to a list.

#	Then, main thread handles receiving new connections and keeps track of them in a list of threads that it periodically checks and updates to remove threads that are no longer running
#	It will only allow new connections if the current amount of live connections is less then a given threshold (currently 10)
#	When a new connection is accepted a thread is created, added to the list, and dispatched to handle client logging in, hndling operations, sending messages etc.
#
#-client thread
#	The client thread handles checking if a user exists or not and if it is already active. 
#	If a client exists and is not active the login process is handled by requesting a password and validating it.
#	If a user is new a new password is requested and saved to the credentials file
#	A successfully logged in/created user is added to the list of active users, along with some information about it's socket/address. then the operation loop begins
#	The operation loop prompts the client for an operation to perform and handles the operation, along with prompting for any other necessary information and sending appropriate responses
#
#
#
#The server program has many lists for tracking things:
#	connectionList - a list of currently active connection threads
#	activeUsers - a list of currently active users
#	credentialList - a list of username/password pairs that is retrieved from the file credentials.txt
#
#In order to allow threads to safely read and write to these same lists, the program contains a mutex lock for each list(except for connectionList because ONLY the main thread will access it)
#	userListMutex - for accessing the activeUsers list
#	credentialListMutex - for accessing the credentilList list
#	fileMutex - for accessing the file credentials.txt

#check that correct amount of paramaters are given
if len(sys.argv) < 2:
	print("please start server via $python3 chatserver.py port")
	sys.exit()
#set port variable
try:
	port = int(sys.argv[1])
except ValueError:
	print("Port must be given as an integer")
	sys.exit()

#create tcp socket
serverSocket = socket(AF_INET, SOCK_STREAM)
udpSocket = socket(AF_INET, SOCK_DGRAM)

#get hostname ex. 127.0.1.1
host = gethostbyname(gethostname())

#attempts to bind sockets to host/port, waiting until able
connected = False
print("Attempting to bind host/port to sockets", end="", flush=True)
while not connected:
	#bind host/port to sockets
	try:
		connected = True
		serverSocket.bind((host, port))
		udpSocket.bind((host, port))
	except OSError:
		connected = False
		print(".", end="", flush=True)
		time.sleep(3)

print("\nserver listening at", host, "on port", port)
serverSocket.listen(5)

#max client connections at one time
maxConnections = 10

#list of dispatched threads for handling messages
connectionList = list() #[thread1, thread2, thread3...]

#list of currently active users, along with their assigned socket and address for sending udp messages
activeUsers = list() #[(joe, joeTcpSocket, joeUdpAddress), (bill, billSocket, billUdpAddress), (beth, bethSocket, bethUdpAddress)...]

tempList = list() # for clearing /copying lists

#list of saved username/password pairs
credentialList = list() #[(joe, password), (bill, passwordBill), (beth, passwordBeth)] READ IN FROM FILE

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
	#File not found, try to create file?
	try:
		credentialFile = open('credentials.txt', 'w')
	except IOError:
		#can't create file, possible permissions error
		print("Error creating file. Are you allowed to?")

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
	# save in the active userList the udp address for sending messages to
	messageType, address = udpSocket.recvfrom(4096)

	#append them to active user list
	userListMutex.acquire()
	activeUsers.append((username, clientSocket, address))
	userListMutex.release()
	running = True

	#tell client that it has recievd the udp address and is ready to recieve commands.
	clientSocket.send("udp recieve".encode())
	
	while running:
		#wait for command
		operation = clientSocket.recv(4096).decode()
		
		if operation == "PM":
			#PM - broadcast to all active () logged in and not yet exitted
			#send acknowledgement of PM request
			clientSocket.send("PM".encode())
			#wait for message
			message = clientSocket.recv(4096).decode()

			#check active user list for any users that aren't the sender, and send them the message
			userListMutex.acquire()
			for userTuple in activeUsers:
				if userTuple[0] != username:
					udpSocket.sendto(message.encode(), userTuple[2])
					udpSocket.sendto(username.encode(), userTuple[2])
					udpSocket.sendto("Public Message (PM)".encode(), userTuple[2])
			userListMutex.release()

			#notify user that message was sent
			clientSocket.send("complete".encode())
			#return to wait for command

		elif operation == "DM":
				#acknowledge DM request
				clientSocket.send("DM".encode())
				message = clientSocket.recv(4096).decode()
				if(message != "received"):
					print("Error handshaking?")
					print(message)

				#send user a list of all active users
				gettingUser = True
				while gettingUser:
					userListMutex.acquire()
					for userTuple in activeUsers:
						clientSocket.send(userTuple[0].encode())
						message = clientSocket.recv(4096).decode()
						if(message != "received"):
							print("client did not receive username properly")
					userListMutex.release()

					clientSocket.send("END".encode())

					#get recipent from client
					reciever = clientSocket.recv(4096).decode()

					#search list of active users for recipent
					found = False
					userListMutex.acquire()
					for userTuple in activeUsers:
						if userTuple[0] == reciever:
							found = True
							recieverAddress = userTuple[2]
							break
					userListMutex.release()

					#notify user that recipent does not exist or is not logged in
					if not found:
						clientSocket.send("DNE".encode())
						message = clientSocket.recv(4096).decode()
						if(message != "received"):
							print("Error receving DNE?")
					#send message to recipent
					else:
						gettingUser = False
						clientSocket.send("message".encode())
						message = clientSocket.recv(4096).decode()
						udpSocket.sendto(message.encode(), recieverAddress)
						udpSocket.sendto(username.encode(), recieverAddress)
						udpSocket.sendto("Direct Message (DM)".encode(), recieverAddress)
						clientSocket.send("complete".encode())
				#return to wait for command

		elif operation == "EX":
			running = False
			#update list of logged in threads
			userListMutex.acquire()
			for userTuple in activeUsers:
				if userTuple[0] == username:
					activeUsers.remove(userTuple)
					break
			userListMutex.release()
			#notify client that it was logged out, then close socket
			clientSocket.send("logout".encode())
			clientSocket.close()
			#allow this thread to end by exiting while loop and reaching end of the function

		else:
			clientSocket.send("unknown".encode())
			#unknown


#main thread for handling receiving new connections
print("Server ready to recieve connections")
while True:
	#blocks if there are more than the max collections allowed
	while(len(connectionList) >= maxConnections):
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