ICS 460-50: Network and Security

Group Project (Project 3):Chat Program

Contributor(s) Names: Joseph Jackels, Punyapat Rabalert

StarID: dn0012nk, 



Files present:

	chatclient.py:
		-the client file
		-@parameters hostname port username
		-takes the host and port and create tcp connection with the server
		-queries the server on whether user already exists
		
		-if the user exists
			-get password from client
			-attempt to login to server
		
		-else create new password and send to server for saving

		-create udp socket on same port for listening for data messages
		-send address to server to be saved

		-command loop
			-input loop
				- wait for input
				- while input has not been received
					-check message queue for any message to be printed, and print them
				- input recieved, signal thread to process input command
			- process input command
				-PM
					-prompt user for message
					-send to server to be sent to all other users
					-notify user message is sent
				-DM
					-send user list of active users to send message to
					-prompt user for user to send message to
						-check validity of entered user
					-prompt user for message to be sent
					-send to server to be sent to entered target user
					-notify user message has been sent
				-EX
					-print any currently pending messages
					-send logout command to server to remove client from active users, close server's side of client socket
					-close client side socket
					-end program

	chatserver.py:
		-the server file
		-@parameters port
		-begins the server to listen at machines hostname on supplied port
	credentials.txt:
		- if it does not exist, when a new user is created the file will be created
		- file for storing username/password pairs to be read by the server
		- newly created users will have their credentials appended to the file by the server

Running the program:

Example Output:

Citations: