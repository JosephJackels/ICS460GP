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

#just recieved operation***
operating = True
while operating:
	command = input("Please enter a command:\n\tPM - public message to all active users.\n\tDM - direct Mmessage toa  single user\n\tEX - exit program and logout of account.")

	if command == "PM":

	elif command == "DM":
		serverSocket.send(command.encode())
		response = serverSocket.recv(4096).decode()
		if response != "DM":
			print("Server did not recieve DM request properly?")
			serverSocket.close()
			sys.exit()
		print("Select a user to send a message to:")
		response = serverSocket.recv(4096).decode()
		while response != "END":
			print("\t" + response)
			response = serverSocket.recv(4096).decode()
		sendTo = input("To: ")
		serverSocket.send(sendTo.encode())
		response = serverSocket.recv()
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
