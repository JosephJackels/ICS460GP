from socket import *
import sys, threading, queue


#Joseph Jackels, Punyapat Rabalert
#StarID: dn0012nk, ih2153wu
#
#
#
#This file is the client that can connect to the server in order to send/receive chat messages with other users
#It has 3 paramaters <hostname> <port> and <username> - the address of the server, the port to connect to it on, and the username to login as
#
#The main thread creates TWO sockets, a TCP socket and a UDP socket, both listen on the same port/host
#The TCP socket is used for sending operation commands to the server, and receiving responses necessary for carrying out those commands/operations
#The UDP socket is used only for receiving data messages from the server and saving them to be printed when appropriate
#
#The main thread checks via the server if the user is existing, new, or already active and handles each appropriately
#	-existing
#		prompt user for password, validate via the server
#	-new
#		prompt user for new password, validate that it is using safe characters, send to server for saving
#	-active
#		user is already logged in somewhere else, notify and end program
#
#After handling logging in, the main thread begins a thread for listening for data messages over the UDP socket
#
#The main thread then prompts the user for operations and executes them
#	-PM
#		prompts user for a public message to be sent to all other active users
#	-DM
#		gets a list of active users from the server and prompts the user for a user to send a message to and the message to be sent
#	-EX
#		logs the user out of the server
#
#Once the operation thread begins and data messages can be received, 
#	Whenever the main thread is waiting for input or for a response from the server, it starts threads to wait for the input/response instead
#	This allows for the queue of messages to be continuously checked and printed while waiting for the response/input to be received. The child thread then flags that it is ready
#	and the input/response is returned to the main thread

#data message receving thread
#receives data messages via the udpSocket
#adds them to the queue of messages to be printed out at the proper time
def message_recieving_thread(udpSocket):
	global messageQueue
	
	#listen for messages forever and save them to the messageQueue
	#this thread should only be run as a daemon so it will end when its parent does
	while True:
		message, address = udpSocket.recvfrom(4096)
		userFrom, address = udpSocket.recvfrom(4096)
		messageType, address = udpSocket.recvfrom(4096)
		messageQueue.put((message.decode(), userFrom.decode(), messageType.decode()))

#this function is to be used by a thread that waits for input and prompts it's parent that the input is ready
def input_listener_thread(prompt):
	global inputCommand
	global inputReadyFlag

	inputCommand = input(prompt)
	inputReadyFlag = True

#starts an input_listener_thread and waits for input to be received, continually check messageQueue for data messages to print
#if data messages are printed the prompt that is given for input is reprinted
#returns the string that was input
def get_input(prompt):
	global inputReadyFlag
	global inputCommand
	inputReadyFlag = False
	inputCommand = ""

	inputListenerThread = threading.Thread(target=input_listener_thread, args=(prompt,), daemon=True)
	inputListenerThread.start()
	
	while(not inputReadyFlag):
		print_messages(prompt)
	inputReadyFlag = False
	return inputCommand

#prints all the messages in the message queue
#reprints a given prompt. If no prompt is needed simply supply the function with an empty string
def print_messages(prompt):
	global messageQueue
	while not messageQueue.empty():
		messageTuple = messageQueue.get()
		print("\n*** New Message ***")
		print("Message type: " + messageTuple[2])
		print("From: " + messageTuple[1] + "\n")
		print(messageTuple[0] + "\n")
		print(prompt)

#starts a thread to listen for a socket response, to be used for getting operation responses over the tcp socket
#prints out messages from the queue while waiting for the response
#returns the string sent by the server
def get_response(socket, prompt):
	global responseReadyFlag
	global socketResponse
	responseReadyFlag = False
	socketResponse = ""

	socketResponseListener = threading.Thread(target=response_listener_thread, args=(serverSocket,), daemon=True)
	socketResponseListener.start()

	while(not responseReadyFlag):
		print_messages(prompt)
	responseReadyFlag = False
	return socketResponse

#receives a response from the server and saves it, flags the parent thread that the response is ready
def response_listener_thread(socket):
	global responseReadyFlag
	global socketResponse
	socketResponse = socket.recv(4096).decode()
	responseReadyFlag = True

#check amount of given arguements
if len(sys.argv) < 4:
	print("Start the client via $python3 chatclient.py hostname port username")
	sys.exit()

#save given arguements
hostname = sys.argv[1]
try:
	port = int(sys.argv[2])
except ValueError:
	print("Port must be given as an integer")
	sys.exit()
username = sys.argv[3]

#queue for storing/printing DM/PM messages received
messageQueue = queue.Queue()

#attempt to begin and bind tcpsocket and begin udp socket
try:
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.connect((hostname, port))
	udpSocket = socket(AF_INET, SOCK_DGRAM)
except ConnectionRefusedError:
	print("TCP Connection was refused at host:", hostname, "on port:", port)
	print("Did you use the order: hostname port requestedFile for the passed arguements?\nAre you using the correct host and port?")
	print("Did you properly supply an address ex 127.0.1.1 and a port ex 1000? Are they properly formatted?")
	sys.exit()

#send username to server
serverSocket.send(username.encode())
response = serverSocket.recv(4096).decode()

#handle authentication of existing user
if response == "existing":
	approved = False
	password = input("Existing user. Please enter password:\n")

	while not approved:
		serverSocket.send(password.encode())
		response = serverSocket.recv(4096).decode()
		if response == "refused":
			password = input("Incorrect password, please try again:\n")
		elif response == "final refuse":
			print("Password refused too many times. exiting program")
			serverSocket.close()
			sys.exit()
		else:
			approved = True

#handle creation of new user
elif response == "new":
	password = input("Welcome new user: " + username + " please enter a new password:\n")

	while " " in password:
		password = input("Password cannot contain \' \' character. Please re-enter a new password that does not contain a space:\n")

	serverSocket.send(password.encode())
	response = serverSocket.recv(4096).decode()
	print(response)

#username is already active
elif response == "inuse":
	print("That user is already actively logged in. Please restart the program as a different user")
	serverSocket.close()
	sys.exit()
else:
	print("server error?")
	serverSocket.close()
	sys.exit()

# send the address of the udp socket to the server
# dispatch a thread that handles recieving messages
# something like handle_messages(udp_socket)
udpSocket.sendto("udp begin".encode(), (hostname, port))

#wait for server to send over tcp socket that it has recieved the udp message.
response = serverSocket.recv(4096).decode()
if(response != "udp recieve"):
	print("Error receiving udp?")
	print(response)

#begin messageListening thread
messageListenerThread = threading.Thread(target=message_recieving_thread, args=(udpSocket,), daemon=True)
messageListenerThread.start()

responseReadyFlag = False
socketResponse = ""

inputReadyFlag = False
inputCommand = ""

#ready to send/receive operation messages with server
operating = True
while operating:
	#get command
	command = get_input("Please enter a command:\n\tPM - public message to all active users.\n\tDM - direct message to a  single user\n\tEX - exit program and logout of account\n")

	#handle sending a public message
	if command == "PM":
		serverSocket.send(command.encode())
		response = get_response(serverSocket, "")
		if response != "PM":
			print("Did not recognize PM request?")

		#ask for message
		message = get_input("Message:\n")
		serverSocket.send(message.encode())
		response = get_response(serverSocket, "")
		if response != "complete":
			print("message wasn't sent?")
		else:
			print("Message sent")

	#handle sending a direct message
	elif command == "DM":
		serverSocket.send(command.encode())
		response = get_response(serverSocket, "")
		if response != "DM":
			print("Server did not recieve DM request properly?")
			
		serverSocket.send("received".encode())
		
		gettingUser = True
		while gettingUser:

			print("Select a user to send a message to:")
			response = get_response(serverSocket, "")
			#receive list of active users
			while response != "END":
				print("\t" + response)
				serverSocket.send("received".encode())
				response = get_response(serverSocket, "")
			
			#prompt user to select recipient of DM
			sendTo = get_input("To:\n")
			serverSocket.send(sendTo.encode())
			response = get_response(serverSocket, "")
		
			#handle user Does Not Exist
			if(response == "DNE"):
				print("User does not exist.")
				serverSocket.send("received".encode())

			#user exists, prompt user for message to send
			elif(response == "message"):
				gettingUser = False
				#get message input, send it etc.
				message = get_input("\nEnter message:\n")
				serverSocket.send(message.encode())
				response = get_response(serverSocket, "")
				#message was not sent
				if(response != "complete"):
					print("Something went wrong")
				#message sent
				else:
					print("Message sent")
			else:
				print("Invalid response?")
	#log user out	
	elif command == "EX":
		#print and pending messages
		print_messages("")

		#log user out of server
		operating = False
		print("Sending logout command to server")
		serverSocket.send(command.encode())
		response = get_response(serverSocket, "")
		
		if response == "logout":
			print("successfully logged out. Closing client side socket and ending program.")
		else:
			print("Error logging out??? closing socket anyways")

		#close sockets and exit
		serverSocket.close()
		udpSocket.close()
		sys.exit()
	else:
		print("Unknown command.")