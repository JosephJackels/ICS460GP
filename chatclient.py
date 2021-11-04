from socket import *
import sys

#recieve thread

#react thread

if len(sys.argv) < 4:
	print("Start the client via $python3 chatclient.py hostname port username")
	sys.exit()

hostname = sys.argv[1]
port = int(sys.argv[2])
username = sys.argv[3]

try:
	serverSocket = socket(AF_INET, SOCK_STREAM)
	serverSocket.connect((hostname, port))
except ConnectionRefusedError:
	print("Connection was refused at host:", hostname, "on port:", port)
	print("Did you use the order: hostname port requestedFile for the passed arguements?\nAre you using the correct host and port?")
	sys.exit()

# create a udp socket for recieving message etc.
udpSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.send(username.encode())
response = serverSocket.recv(4096).decode()

if response == "existing":
	approved = False
	password = input("Existing user. Please enter password.")
	while not approved:
		serverSocket.send(password.encode())
		response = serverSocket.recv(4096).decode()
		if response == "refused":
			password = input("Incorrect password, please try again")
		elif response == "final refuse":
			print("Password refused too many times. exiting program")
			serverSocket.close()
			sys.exit()
		else:
			approved = True
elif response == "new":
	password = input("Enter a password for: " + username)
	serverSocket.send(password.encode())
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
udpSocket.sendTo("udp begin".encode(), (hostname, port))

#wait for server to send over tcp socket that it has recieved the udp message.
while(response != "udp recieve") {
	response = serverSocket.recv(4096).decode()
}
#just recieved operation***
operating = True
while operating:

	command = input("Please enter a command:\n\tPM - public message to all active users.\n\tDM - direct message to a  single user\n\tEX - exit program and logout of account.")

	if command == "PM":
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		if response != "PM":
			print("Did not recognize PM request?")
			#exit this block? go to beginning of while?

		#ask for message
		message = input("Message: ")
		serverSocket.send(message.encode())
		response = serverSocket.recv(4096).decode()
		if response != "complete":
			print("message wasn't sent?")

	elif command == "DM":
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		if response != "DM":
			print("Server did not recieve DM request properly?")
			#exit or go to beginning of while loop?

		print("Select a user to send a message to:")
		response = serverSocket.recv(4096).decode()
		while response != "END":
			print("\t" + response)
			response = serverSocket.recv(4096).decode()
		sendTo = input("To: ")
		serverSocket.send(sendTo.encode())
		response = serverSocket.recv(4096).decode()
		if(response == "DNE"):
			#handle Does Not Exist
			print("User does not exist. Re-enter username:")
		elif(response == "message"):
			#get message input, send it etc.
			message = input("Enter message:")
			serverSocket.send(message.encode())
			response = serverSocket.recv(4096).decode()
			if(response != "complete"):
				print("Something went wrong")
		else:
			print("Invalid response?")
		
	elif command == "EX":
		operating = False
		print("Sending logout command to server")
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		
		if response == "logout":
			print("successfully logged out. CLosing client side socket and ending program.")
		else:
			print("Error logging out??? closing socket anyways")

		serverSocket.close()
		sys.exit()
	else:
		print("Unknown command.")

	# end of recieving command
	# print all pending messages from recieving thread?

def message_recieving_thread(udpSocket):
	#listen for PM/DM being sent to this socket
	#decide when to print?
	
	# maybe we should make a global queue that contains (message, address)
	# this thread can simply recieve messages and add to the queue
	# then the main thread above can decide when it is a "safe" time
	# to print any pending messages, e.x. after a command is processed it will print all messages?
	# we could even have a third 'printing' thread that handles printing for both the main operation thread and this thread 

	while(True):
		message, address = udpSocket.recvfrom(4096)
		userFrom, address = udpSocket.recvfrom(4096)
		#do something with message and username of sender.
		#either print it out now, or add to queue to print when able
