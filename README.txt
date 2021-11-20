ICS 460-50: Network and Security

Group Project (Project 3):Chat Program

Contributor(s) Names: Joseph Jackels, Punyapat Rabalert

StarID: dn0012nk, ih2153wu



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
						-check validity of entered user (check done by server)
					-prompt user for message to be sent
					-send to server to be sent to entered target user
					-notify user message has been sent
				-EX
					-print any currently pending messages
					-send logout command to server to remove client from list of active users, close server's side of client socket
					-close client side socket
					-end program
		-threads
			-the client creates threads when needed while waiting for input from the user or while waiting for a response from the server while comminucating about the operations
			-the threads are dispatched from the methods get_input and get_response
				-get_input
					takes in a query string to prompt the user for input. The prompt will be re-printed if any data-messages are received and printed while waiting for the user to enter an input
				-get_response
					 waits for a response from the server, then returns the response, printing any data messages that are recieved while waiting
			-the threads naturally 'die' when reaching the end of the function and new threads are created the next time that a response/input is needed			

	chatserver.py:
		-the server file
		-@parameters port
		-begins the server to listen at machines hostname on supplied port
		
		-main thread
			-loads in any credentials from file 'credentials.txt' 
			-handles new connections, creates a new thread for every accepted connection

		-connection thread
			-gets username of requested connection, checks if suer exists or is new
				-exists
					-tell client that user exists
					-prompt user for password
					-validate password
						-invalid
							-tell user password is invalid, allow to try again.
							-limits user to three attempts before ending connection
						-valid
							-accept user 
							-add to list of active users
							-get address of clients UDP socket and save for sending data messages
				-new
					-tell client that user is new
					-prompt for password creation
					-add username/password to credentials.txt
					-get address of UDP socket
					-add to list of active users
			
			-prompt client for an operation
				-PM
					-handle getting message and sending to all currently logged in users (but NOT the sender)
				-DM
					-handle communicating list of active users to client, 
					-receiving username of user to send message to
					-validating username
					-receving message to be sent
					-forwarding the message
				-EX
					-remove user from list of active users
					-close sockets
					-allow thread to exit loop and end/die

	credentials.txt:
		- if it does not exist, when a new user is created the file will be created
		- file for storing username/password pairs to be read by the server
		- newly created users will have their credentials appended to the file by the server

Running the program:
	chatserver.py:
		-Run the commandline: python3 chatserver.py <port>
			-port, the argument specified by the server creator such as "command prompt>$python3 chatserver.py 1300"
		-The server displays the ready and running status to receive message(s) and the server's host for connection.
	chatclient.py:
		-python3 chatclient.py <host> <port> <username>
			-host , the IP address of the server required to establish connection
			-port, the port of the server required to establish connection
			-username, the username of the chat program
Example Output:
    -Server Connection Output: prompt>$python3 chatserver.py 10000
       Attempting to bind host/port to sockets
       server listening at 10.0.0.114 on port 10000
       Server ready to recieve connections
    
    -New User Logging in Output: prompt>$python3 chatclient.py 10.0.0.224 10000 renew
       Welcome new user: renew please enter a new password:
       re
       News User: renew Password: re
       Please enter a command:
              PM - public message to all active users.
              DM - direct message to a  single user
              EX - exit program and logout of account
    
    -Existing User Logging in: prompt>$python3 chatclient.py 10.0.0.224 10000 bob
      Existing user. Please enter password:
      password
      Please enter a command:
            PM - public message to all active users.
            DM - direct message to a  single user
            EX - exit program and logout of account
    
    -Public Message(PM):
      Client 1(renew):
        PM
        Message:
        Hello guys
        Message sent
        Please enter a command:
              PM - public message to all active users.
              DM - direct message to a  single user
              EX - exit program and logout of account
      
      //output for all Active User(s) besides the sender:
        *** New Message ***
        Message type: Public Message (PM)
        From: renew

        Hello guys

        Please enter a command:
              PM - public message to all active users.
              DM - direct message to a  single user
              EX - exit program and logout of account
    
    -Direct Message(DM):
      Client 1(renew):
         DM
         Select a user to send a message to:
                  bob
                  joe
                  renew
         To:
	 joe
	 Enter message:
         Hello joe
         Message sent
         Please enter a command:
                PM - public message to all active users.
                DM - direct message to a  single user
                EX - exit program and logout of account
      Client 2(joe):
         *** New Message ***
         Message type: Direct Message (DM)
         From: renew

         Hello joe

         Please enter a command:
                PM - public message to all active users.
                DM - direct message to a  single user
                EX - exit program and logout of account
     
     -Exit(EX):
        EX
        Sending logout command to server
        successfully logged out. Closing client side socket and ending program.

Citations:
	https://docs.python.org/3/howto/sockets.html
	https://realpython.com/python-sockets/
	https://www.geeksforgeeks.org/socket-programming-python/
	https://pymotw.com/2/socket/tcp.html