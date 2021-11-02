from socket import *
import sys
import threading

#check that correct amount of paramaters are given
if len(sys.argv) < 2:
	print("please start server via $python3 chatserver.py port")
	sys.exit()
#set port variable
port = (int) sys.argv[1]

#create tcp socket
serverSocket = socket(AF_INET, SOCK_STREAM)

#get hostname ex. 127.0.1.1
host = gethostbyname(gethostname())

#bind host/port to socket
serverSocket.bind((host,port))
print("server listening at", host, "on port", port)
serverSocket.listen(5)

maxConnections = 10

#list of dispatched threads for handling messages
connectionList = list() #[thread1, thread2, thread3...]

#list of currently active users, along with their assigned socket
activeUsers = list() #[(joe, joeSocket), (bill, billSocket), (beth, bethSocket)...]

tempList = list() # for clearing /copying lists

#list of saved username/password pairs
credentialList = list() #[(joe, password), (bill, password1), (beth, password2)] READ IN FROM FILE

#mutexes (mutual exclusion locks) for accessing relevent lists without threading issues
userListMutex = threading.Lock()
credentialListMutex = threading.Lock()
fileMutex = threading.Lock()

#attempt to read in credentials from file credentials.txt
try:
	credentialFile = open('credentials.txt', 'r')
	lines = credentialFile.readLines()
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
		#acknowledge client is new
		clientSocket.send("new".encode())
		
		#wait for password
		password = clientSocket.recv(4096).decode()
		
		#aqcknowledge new registration
		message = "News User: " + username + " Password: " + password
		clientSocket.send(message.encode())
		
		#register - add to file AND update credentialList
		fileMutex.acquire()
		file = open('credential.txt', a)
		file.write("\n")
		file.write(username + " " + password)
		file.close()
		fileMutex.release()
		credentialList.append((username, password))
		#proceed to handling block

	#handling block
	#user is logged in / registered
	
	#append them to active user list
	userListMutex.acquire()
	activeUsers.append((username, clientSocket))
	userListMutex.release()
	running = True
	
	while running:
		#prompt client for operation
		clientSocket.send("operation".encode())
		
		#wait for command
		operation = clientSocket.recv(4096).decode()
		
		if operation == "PM":
			#PM - broadcast to all active () logged in and not yet exitted
			#send acknowledgement of PM request
			#prompt for message
			clientSocket.send("PM".encode())
			#wait for message
			message = clientSocket.recv(4096).decode()

			#pmThread = threading.Thread(target=pm_message, args=(message, (username, clientSocket)))
			#pmThread.start()
			userListMutex.acquire()
			for userTuple in activeUsers:
				if userTuple[0] != username:
					userTuple[1].send(message.encode())
			userListMutex.release()
			clientSocket.send("complete".encode())
			#return to wait for command

		elif operation == "DM":
			#DM
				#acknowledge DM request
				clientSocket.send("DM".encode())
				userListMutex.acquire()
				for userTuple in activeUsers:
					clientSocket.send(userTuple[0].encode())
				userListMutex.release()

				clientSocket.send("END")
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
					clientSocket.send("DNE".encode())
				else:
					clientSocket.send("message".encode())
					message = clientSocket.recv(4096).decode()
					recieverSocket.send(message.encode())
					clientSocket.send("complete".encode())
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
			clientSocket.send("logout".encode())
			clientSocket.close()
			#EX
				#close socket
				#update list of logged in threads
				#client closes it's own socket

		else:
			clientSocket.send("unknown".encode())
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
	newConnection, addr = mainSocket.accept()
		
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