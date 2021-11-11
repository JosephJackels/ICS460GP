from socket import *
import sys, threading, queue

#recieve thread
def message_recieving_thread(udpSocket):
	global messageQueue
	#listen for PM/DM being sent to this socket
	#decide when to print?
	
	# maybe we should make a global queue that contains (message, address)
	# this thread can simply recieve messages and add to the queue
	# then the main thread above can decide when it is a "safe" time
	# to print any pending messages, e.x. after a command is processed it will print all messages?
	# we could even have a third 'printing' thread that handles printing for both the main operation thread and this thread 

	while True:
		message, address = udpSocket.recvfrom(4096)
		userFrom, address = udpSocket.recvfrom(4096)
		messageType, address = udpSocket.recvfrom(4096)
		messageQueue.put((message.decode(), userFrom.decode(), messageType.decode()))
		#do something with message and username of sender.
		#either print it out now, or add to queue to print when able

def input_listener_thread():
	global inputCommand
	global inputReadyFlag

	inputCommand = input("Please enter a command:\n\tPM - public message to all active users.\n\tDM - direct message to a  single user\n\tEX - exit program and logout of account\n")
	inputReadyFlag = True

def print_messages(waitingForCommand):
	global messageQueue
	while not messageQueue.empty():
		messageTuple = messageQueue.get()
		print("\n*** New Message ***")
		print("Message type: " + messageTuple[2])
		print("From: " + messageTuple[1] + "\n")
		print(messageTuple[0] + "\n")
		if waitingForCommand:
			print("Please enter a command:\n\tPM - public message to all active users.\n\tDM - direct message to a  single user\n\tEX - exit program and logout of account\n")

if len(sys.argv) < 4:
	print("Start the client via $python3 chatclient.py hostname port username")
	sys.exit()

hostname = sys.argv[1]
port = int(sys.argv[2])
username = sys.argv[3]

#queue for storing/printing DM/PM messages received
messageQueue = queue.Queue()

try:
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.connect((hostname, port))
except ConnectionRefusedError:
	print("TCP Connection was refused at host:", hostname, "on port:", port)
	print("Did you use the order: hostname port requestedFile for the passed arguements?\nAre you using the correct host and port?")
	sys.exit()

# create a udp socket for recieving message etc.
udpSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.send(username.encode())
response = serverSocket.recv(4096).decode()

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
elif response == "new":
	password = input("Welcome new user: " + username + " please enter a new password:\n")

	while " " in password:
		password = input("Password cannot contain \' \' character. Please re-enter a new password that does not contain a space:\n")

	serverSocket.send(password.encode())
	response = serverSocket.recv(4096).decode()
	print(response)

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

stopEvent = threading.Event()
#begin messageListening thread
messageListenerThread = threading.Thread(target=message_recieving_thread, args=(udpSocket,), daemon=True)
messageListenerThread.start()

#just recieved operation***
operating = True
while operating:

	inputReadyFlag = False
	inputCommand = ""
	inputListenerThread = threading.Thread(target=input_listener_thread, daemon=True)
	inputListenerThread.start()

	while(not inputReadyFlag):
		print_messages(True)

	command = inputCommand

	if command == "PM":
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		if response != "PM":
			print("Did not recognize PM request?")

		#ask for message
		message = input("Message:\n")
		serverSocket.send(message.encode())
		response = serverSocket.recv(4096).decode()
		if response != "complete":
			print("message wasn't sent?")

	elif command == "DM":
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		if response != "DM":
			print("Server did not recieve DM request properly?")
			
		serverSocket.send("received".encode())
		
		gettingUser = True
		while gettingUser:

			print("Select a user to send a message to:")
			response = serverSocket.recv(4096).decode()
		
			while response != "END":
				print("\t" + response)
				serverSocket.send("received".encode())
				response = serverSocket.recv(4096).decode()
		
			sendTo = input("To:\n")
			serverSocket.send(sendTo.encode())
			response = serverSocket.recv(4096).decode()
		
			if(response == "DNE"):
				#handle Does Not Exist
				print("User does not exist.")
				serverSocket.send("received".encode())

			elif(response == "message"):
				gettingUser = False
				#get message input, send it etc.
				message = input("\nEnter message:\n")
				serverSocket.send(message.encode())
				response = serverSocket.recv(4096).decode()
				if(response != "complete"):
					print("Something went wrong")
				else:
					print("Message sent")
			else:
				print("Invalid response?")
		
	elif command == "EX":
		
		print_messages(False)

		operating = False
		print("Sending logout command to server")
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		
		if response == "logout":
			print("successfully logged out. Closing client side socket and ending program.")
		else:
			print("Error logging out??? closing socket anyways")

		serverSocket.close()
		udpSocket.close()
		sys.exit()
	else:
		print("Unknown command.")