import os
import sys
import socket
import signal

# Parameters for server configuration and file paths
HOST_ADDRESS = socket.gethostbyname(socket.gethostname())
HOST_PORT = 11550
USERS_FILE_PATH = './users.txt'
DIRECTORY_PATH = './files'
SEQ_COUNTER = 0

def load_user_list():
    """
    Reads the users.txt file and loads the valid users into a list.
    """

    with open(USERS_FILE_PATH, 'r') as file:
        user_list = [line.strip() for line in file.readlines()]
    return user_list


def list_command():
    """
    Handles the LIST command from the client to list the files in the server's directory.
    """

    try:
        available_files = os.listdir(DIRECTORY_PATH)
        if not available_files:
            return f"{SEQ_COUNTER} NOK"
        files_str = ','.join(available_files)
        return f"{SEQ_COUNTER} ARQS {len(available_files)} {files_str}"

    except Exception as error:
        print(f"Error listing files: {error}")
        return f"{SEQ_COUNTER} NOK"


def cump_command(username, user_list):
    """
    Handles the CUMP command from the client to verify a user's existence.
    """

    if username in user_list:
        return f"{SEQ_COUNTER} OK"
    else:
        return f"{SEQ_COUNTER} NOK"


def pega_command(file_name):
    """
    Handles the PEGA command from the client to retrieve a specific file.
    """

    file_path = os.path.join(DIRECTORY_PATH, file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                file_contents = file.read()
            file_size = len(file_contents)
            return f"{SEQ_COUNTER} ARQ {file_size} {file_contents}"
        except Exception as error:
            print(f"Error: {error}")
            return f"{SEQ_COUNTER} NOK"
    else:
        return f"{SEQ_COUNTER} NOK"


def client_connection(client_socket, user_list):
    """
    Manages the communication between the server and a connected client.
    
    Flow:
    1. The client sends the CUMP command for user validation.
    2. The server processes other commands like LIST, PEGA, and TERM based on the client's input.
    3. The connection is maintained until the client sends the TERM command or an error occurs.
    """

    global SEQ_COUNTER

    # Step 1: Initial CUMP (user validation)
    try:
        incoming_data = client_socket.recv(1024).decode()
        data_parts = incoming_data.split()
        SEQ_COUNTER = int(data_parts[0])  # Sequence number from the client
        command = data_parts[1]

        if command == "CUMP":
            username = data_parts[2]
            response = cump_command(username, user_list)
            client_socket.send(response.encode())
            if "NOK" in response:
                client_socket.close()  # Close connection if user is invalid
                return
        else:
            client_socket.send(f"{SEQ_COUNTER} NOK".encode())
            client_socket.close()
            return

        # Step 2: Handle other commands (LIST, PEGA, TERM)
        while True:
            incoming_data = client_socket.recv(1024).decode()
            data_parts = incoming_data.split()

            if len(data_parts) < 2:
                client_socket.send(f"{SEQ_COUNTER} NOK".encode())
                break

            SEQ_COUNTER = int(data_parts[0])
            command = data_parts[1]

            if command == "LIST":
                response = list_command()
                client_socket.send(response.encode())

            elif command == "PEGA":
                file_name = data_parts[2]
                response = pega_command(file_name)
                client_socket.send(response.encode())

            elif command == "TERM":
                client_socket.send(f"{SEQ_COUNTER} OK".encode())
                client_socket.close()
                break

            else:
                client_socket.send(f"{SEQ_COUNTER} NOK".encode())

    except Exception as error:
        print(f"Error: {error}")
        client_socket.send(f"{SEQ_COUNTER} NOK".encode())
        client_socket.close()


def shut_down(signal_type, frame):
    """
    Handles the SIGINT signal (Ctrl+C) to shut down the server.
    """
    print("Shutting down server")
    sys.exit(0)


def run_server():
    """
    Starts the server, listens for new client connections and handles them.

    - Loads the list of valid users.
    - Creates a TCP socket and binds it to the specified address and port.
    - Continuously accepts client connections and processes their requests.

    The server runs indefinitely until interrupted by SIGINT (Ctrl+C).
    """

    user_list = load_user_list()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST_ADDRESS, HOST_PORT))
    server_socket.listen(2)
    print(f"Waiting for connection on: {HOST_ADDRESS}:{HOST_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Establishing connection with: {client_address}")
        client_connection(client_socket, user_list)
        signal.signal(signal.SIGINT, shut_down) # Change this later


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shut_down)
    run_server()
