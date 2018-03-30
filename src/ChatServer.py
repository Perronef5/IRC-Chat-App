import socket
import sys
import threading
import Channel
import User
import Util
from time import gmtime, strftime


class Server:
    SERVER_CONFIG = {"MAX_CONNECTIONS": 15}
    CHANNEL_OPERATOR_PASSWORD = "operator"
    HELP_MESSAGE = """\n<||> The list of commands available are: <||>

/away                       - User can set status to away and set an away message.
/connect [server] [port]    - Instructs the server to shutdown.
/clear                      - Extra command implemented to clear the chat window
/die                        - Instructs the server to shutdown.
/help                       - Show the instructions.
/info                       - Returns information about the server.
/invite [name] [channel]    - Invite a user to a channel.
/ison [nickname]            - Check to see if users are online.
/join [channel_name]        - To create or switch to a channel.
/kick [channel] [user]      - kick user from channel.    
/knock [channel] [message]  - Sends a message to the target_channel.
/kill [client]              - Forcibly removes client from the network.                            
/list                       - Lists all available channels.
/nick [nickname]            - Changes users nickname.
/notice [nickname] [msg]    - Similar to PRIVMSG, except no automatic replies.
/oper [username] [password] - Authenticates a user as an IRC operator.
/ping                       - A Ping message results in a Pong Reply.
/pong                       - A Pong message results in a Ping Reply.
/privmsg [nickname] [msg]   - Send a private message to a user.
/quit                       - Exits the program.
/restart                    - Restart the server.
/rules                      - Requests the server rules.
/setname [fullname]         - Allows a client to change the "real name" specified when registering a connection.
/time                       - Returns the local time on the server.
/topic [channel] [topic]    - Returns or sets the channels topic.
/userhost [nicknames]       - Returns a list of information about the nicknames specified.
/userip [nickname]          - Returns the direct IP address of the user with the specified nickname.
/users                      - Returns a list of the users on the network.
/version                    - Returns the version of the server.
/wallops [message]          - Sends [message] to all channel operators.
/who [fullname]             - Returns a list of users who match the full name.
/whois [username]           - Returns information about the give nicknames.\n\n""".encode('utf8')


    WELCOME_MESSAGE = "\n> Welcome to our chat app!!! What is your name?\n".encode('utf8')

    def __init__(self, host=socket.gethostbyname('localhost'), port=50000, allowReuseAddress=True, timeout=3):
        self.address = (host, port)
        self.channels = {} # Channel Name -> Channel
        self.channel_files = {} # Channel Name -> Channel File
        self.users_channels_map = {} # User Name -> Channel Name
        self.client_thread_list = [] # A list of all threads that are either running or have finished their task.
        self.users = [] # A list of all the users who are connected to the server.
        self.exit_signal = threading.Event()

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as errorMessage:
            sys.stderr.write("Failed to initialize the server. Error - {0}".format(errorMessage))
            raise

        self.serverSocket.settimeout(timeout)

        if allowReuseAddress:
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write('Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0],
                                                                                             self.address[1],
                                                                                             errorMessage))
            raise

    def start_listening(self, defaultGreeting="\n> Welcome to our chat app!!! What is your full name?\n"):
        self.serverSocket.listen(Server.SERVER_CONFIG["MAX_CONNECTIONS"])

        try:
            while not self.exit_signal.is_set():
                try:
                    print("Waiting for a client to establish a connection\n")
                    clientSocket, clientAddress = self.serverSocket.accept()
                    print("Connection established with IP address {0} and port {1}\n".format(clientAddress[0],
                                                                                             clientAddress[1]))
                    user = User.User(clientSocket)
                    self.users.append(user)
                    self.welcome_user(user)
                    clientThread = threading.Thread(target=self.client_thread, args=(user,))
                    clientThread.start()
                    self.client_thread_list.append(clientThread)
                except socket.timeout:
                    pass
        except KeyboardInterrupt:
            self.exit_signal.set()

        for client in self.client_thread_list:
            if client.is_alive():
                client.join()

    def welcome_user(self, user):
        user.socket.sendall(Server.WELCOME_MESSAGE)

    def client_thread(self, user, size=4096):
        fullname = user.socket.recv(size).decode('utf8')
        username = Util.generate_username(fullname).lower()

        while not username:
            user.socket.sendall("\n> Please enter your full name(first and last. middle optional).\n".encode('utf8'))
            fullname = user.socket.recv(size).decode('utf8')
            username = Util.generate_username(fullname).lower()

        user.username = username
        user.nickname = username
        user.fullname = fullname

        welcomeMessage = '\n> Welcome {0}, type /help for a list of helpful commands.\n\n'.format(user.username)\
            .encode('utf8')
        user.socket.sendall(welcomeMessage)

        while True:
            chatMessage = user.socket.recv(size).decode('utf8').lower()

            if self.exit_signal.is_set():
                break

            if not chatMessage:
                break

            if '/away' in chatMessage:
                self.away(user, chatMessage)
            elif '/connect' in chatMessage:
                self.connect(chatMessage)
            elif '/clear' in chatMessage:
                self.clear(user)
            elif '/die' in chatMessage:
                self.die()
            elif '/help' in chatMessage:
                self.help(user)
            elif '/info' in chatMessage:
                self.info(user)
            elif '/invite' in chatMessage:
                self.invite(user, chatMessage)
            elif '/ison' in chatMessage:
                self.ison(user, chatMessage)
            elif '/join' in chatMessage:
                self.join(user, chatMessage)
            elif '/kick' in chatMessage:
                self.kick(user, chatMessage)
            elif '/kill' in chatMessage:
                self.kill(user, chatMessage)
            elif '/list' in chatMessage:
                self.list_all_channels(user)
            elif '/nick' in chatMessage:
                self.nick(user, chatMessage)
            elif '/notice' in chatMessage:
                self.notice(user, chatMessage)
            elif '/oper' in chatMessage:
                self.oper(user, chatMessage)
            elif '/ping' in chatMessage:
                self.ping(user)
            elif '/pong' in chatMessage:
                self.pong(user)
            elif '/privmsg' in chatMessage:
                self.privateMessage(user, chatMessage)
            elif '/quit' in chatMessage:
                self.quit(user)
                break
            elif '/restart' in chatMessage:
                self.restart()
            elif '/rules' in chatMessage:
                self.rules(user)
            elif '/setname' in chatMessage:
                self.setname(user, chatMessage)
            elif '/time' in chatMessage:
                self.time(user)
            elif '/topic' in chatMessage:
                self.topic(user, chatMessage)
            elif '/userhost' in chatMessage:
                self.userhost(user, chatMessage)
            elif '/userip' in chatMessage:
                self.user_ip(user, chatMessage)
            elif '/users' in chatMessage:
                self.users_list(user)
            elif '/version' in chatMessage:
                self.version(user)
            elif '/wallops' in chatMessage:
                self.wallops(user, chatMessage)
            elif '/who' in chatMessage:
                self.who(user, chatMessage)
            elif '/whois' in chatMessage:
                self.who_is(user, chatMessage)
            else:
                self.send_message(user, chatMessage + '\n')

        if self.exit_signal.is_set():
            user.socket.sendall('/squit'.encode('utf8'))

        user.socket.close()

    def away(self, user, chatMessage):
        if len(chatMessage.split()) > 1:
            awayMessage = chatMessage.split(" ", 1)[1]
            user.status = "Away"
            user.awaymessage = awayMessage
            user.socket.sendall("<||> Status changed to Away. <||>\n".encode('utf8'))
        else:
            user.status = "Online"
            user.awayMessage = ""

    def connect(self, chatMessage):
        host = chatMessage.split()[1]
        port = chatMessage.split()[2]
        self.address = (host, port)

        try:
            self.serverSocket.bind(self.address)
        except socket.error as errorMessage:
            sys.stderr.write(
                'Failed to bind to address {0} on port {1}. Error - {2}'.format(self.address[0], self.address[1],
                                                                                errorMessage))
            raise

    def clear(self, user):
        user.socket.sendall("/clear".encode('utf8'))

    def die(self):
        self.broadcast_message("/squit")
        self.server_shutdown()

    def help(self, user):
        user.socket.sendall(Server.HELP_MESSAGE)

    def info(self, user):
        user.socket.sendall(
            '<||> This is a Chat Server that follows the IRC Protocol Written By Luis Perrone for CNT4713. <||>\n'
                .encode(
                'utf8'))

    def invite(self, user, chatMessage):
        if len(chatMessage.split()) < 3:
            user.socket.sendall('\n<||>  Must provide a target name and a channel to invite. <||>\n'.encode('utf8'))
        else:
            targetName = chatMessage.split()[1]
            channel = chatMessage.split()[2]
            channelExists = False

            if channel in self.channels:
                channelExists = True

            for targetuser in self.users:
                if targetuser.username == targetName:
                    if channelExists:
                        if user in self.channels[channel].users:
                            targetSocket = targetuser.socket
                            user.socket.send(
                                ("<||> Invitation to " + targetName + " to join " + channel + " sent. <||>\n")
                                    .encode('utf8'))
                            targetSocket.send(
                                ("<||> " +user.username + " has invited you to join " + channel + ". <||>\n")
                                    .encode('utf8'))
                            break
                        else:
                            user.socket.send("<||>  Must be a member of the channel to invite. <||>\n".encode('utf8'))
                    else:
                        targetSocket = targetuser.socket
                        user.socket.send(("<||> Invitation to " + targetName + " to join " + channel + " sent. <||>\n")
                                         .encode('utf8'))
                        targetSocket.send(("<||> " + user.username + " has invited you to join " + channel + ". <||>\n")
                                          .encode('utf8'))
                        break

    def ison(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall('\n<||>  Must provide at least one nickname. <||>\n'.encode('utf8'))
        else:
            onlineUsers = ""
            nicknames = chatMessage.split()
            for name in nicknames:
                for targetUser in self.users:
                    if targetUser.username == name:
                        if targetUser.status == "Online":
                            onlineUsers = onlineUsers + " " + targetUser.username
                            break
            if onlineUsers != "":
                user.socket.sendall(('\n<||>  Online Users: ' + onlineUsers + ' <||>\n').encode('utf8'))
            else:
                user.socket.sendall('\n<||>  None of the specified users are currently online. <||>\n'.encode('utf8'))

    def join(self, user, chatMessage):
        channel_text_history = ''
        isInSameRoom = False

        if len(chatMessage.split()) >= 2:
            channelName = chatMessage.split()[1]

            if user.username in self.users_channels_map: # Here we are switching to a new channel.
                if self.users_channels_map[user.username] == channelName:
                    user.socket.sendall("\n<||>  You are already in channel: {0}".format(channelName).encode('utf8'))
                    isInSameRoom = True
                else: # switch to a new channel
                    oldChannelName = self.users_channels_map[user.username]
                    self.channels[oldChannelName].remove_user_from_channel(user) # remove them from the previous channel

            if not isInSameRoom:
                if not channelName in self.channels:
                    newChannel = Channel.Channel(channelName)
                    self.channels[channelName] = newChannel

                self.channel_files[channelName] = open(channelName + ".txt", "a+")

                self.channel_files[channelName].close()

                self.channel_files[channelName] = open(channelName + ".txt", "r+")

                channel_text_history = ('\n' + self.channel_files[channelName].read())

                self.channel_files[channelName].close()

                self.channels[channelName].users.append(user)
                self.channels[channelName].welcome_user(user.username, channel_text_history)
                self.users_channels_map[user.username] = channelName
        else:
            self.help(user.socket)

    def kick(self, user, chatMessage):
        if user.usertype != "user":
            if len(chatMessage.split()) > 2:
                channelName = chatMessage.split()[1]
                targetName = chatMessage.split()[2]
                for targetUser in self.users:
                    if targetUser.username == targetName:
                        self.channels[channelName].remove_user_from_channel(targetUser)
                        targetUser.socket.send((
                                "<|*|>  You have been removed from channel " + channelName + " by " + user.username
                                + ". <|*|>\n").encode(
                            'utf8'))
                        break
            else:
                user.socket.sendall('\n<||>  Must provide a channel name and a client to kick. <||>\n'.encode('utf8'))

        else:
            user.socket.sendall('\n<||>  Must be a Channel Operator or Admin to kick. <||>\n'.encode('utf8'))

    def kill(self, user, chatMessage):
        if user.usertype != "user":
            if len(chatMessage.split() < 2):
                user.socket.sendall('\n<||> Must provide a client name. <||>\n'.encode('utf8'))
            else:
                targetFound = False
                targetName = chatMessage.split()[1]
                for targetUser in self.users:
                    if targetUser.name == targetName:
                        targetUser.socket.sendall("/squit".encode('utf8'))
                        targetUser.serverSocket.close()
                        user.socket.sendall('\n<||> Client was removed from the network <||>\n'.encode('utf8'))
                        targetFound = True
                        break

                if targetFound != True:
                    user.socket.sendall('\n<||> Please choose a client that is on the network. <||>\n'.encode('utf8'))

        else:
            user.socket.sendall('\n<||>  Must be a Channel Operator or Admin to kill. <||>\n'.encode('utf8'))

    def knock(self, user, chatMessage):

        if len(chatMessage.split()) < 2:
            user.socket.sendall('\n> Must provide a target channel and message to the channel.\n'.encode('utf8'))

        else:
            smallChatMessage = chatMessage.replace('/knock', '')
            targetChannel = chatMessage.split(' ')[1]
            requestMessage = smallChatMessage.replace(targetChannel, '')

            if len(chatMessage.split()) == 2:
                if targetChannel in self.channels:
                    self.channels[targetChannel].broadcast_message(': Requesting Invite\n', user.username)
                else:
                    user.socket.sendall('\n> Channel does not exist.\n'.encode('utf8'))

            elif len(chatMessage.split()) > 2:
                if targetChannel in self.channels:
                    self.channels[targetChannel].broadcast_message((':' + requestMessage + '\n'), user.username)

            else:
                user.socket.sendall('\n> Channel does not exist.\n'.encode('utf8'))

    def list_all_channels(self, user):
        if len(self.channels) == 0:
            chatMessage = "\n<||> No rooms available. Create your own by typing /join [channel_name] <||>\n"\
                .encode('utf8')
            user.socket.sendall(chatMessage)
        else:
            chatMessage = '\n\n<||> Current channels available are: <||>\n'
            for channel in self.channels:
                chatMessage += "    \n" + channel + ": " + str(len(self.channels[channel].users)) + " user(s)"
            chatMessage += "\n"
            user.socket.sendall(chatMessage.encode('utf8'))

    def nick(self, user, chatMessage):
        nickname = chatMessage.split()[1]
        usernametaken = False
        for user2 in self.users:
            if user2.nickname == nickname:
                user.socket.sendall('<||> Nickname is taken! Try again. <||> \n'.encode('utf8'))
                usernametaken = True
                break

        if  usernametaken != True:
            self.users.remove(user)
            channel = self.channels[self.users_channels_map[user.username]]
            del self.users_channels_map[user.username]
            channel.users.remove(user)
            oldusername = user.username
            user.nickname = nickname
            user.username = nickname
            self.users_channels_map[user.username] = channel
            if oldusername in self.users_channels_map:
                oldchannel = self.users_channels_map[oldusername]
                del self.users_channels_map[oldusername]
                self.users_channels_map[user.username] = oldchannel
            msg = '<||> You have changed your nickname to ' + user.username + " from " + oldusername + ". <||> \n"
            user.socket.sendall((msg.encode('utf8')))

            if user.username in self.users_channels_map:
                self.users.append(user)
                channel.users.append(user)
                channel.update()

    def notice(self, user, chatMessage):
        if len(chatMessage.split()) < 3:
            user.socket.sendall('\n <||> Must provide a target name and a message to send a notice. <||> \n'
                                .encode('utf8'))
        else:
            targetName = chatMessage.split()[1]
            privMessage = chatMessage.split()[2]
            for targetuser in self.users:
                if targetuser.username == targetName:
                    targetSocket = targetuser.socket
                    user.socket.send(("<||> Notice to " + targetName + ": " + privMessage + " <||>\n")
                                     .encode('utf8'))
                    targetSocket.send(("<||> Notice from " + user.username + ": " + privMessage + " <||>\n")
                                      .encode('utf8'))
                    break

    def oper(self, user, chatMessage):
        if len(chatMessage.split()) < 3:
            user.socket.sendall('\n <||> Must provide a username and password to become a Channel OP. <||> \n'
                                .encode('utf8'))
        else:
            username = chatMessage.split()[1]
            password = chatMessage.split()[2]
            print(password)
            if password == "operator":
                user.usertype = "ChannelOp"
                user.socket.sendall(
                    '\n <||> Successfully changed from user to Channel Operator. <||> \n'.encode('utf8'))
            else:
                user.socket.sendall(
                    '\n <||> Please use a valid Channel Operator Username and Password. <||> \n'.encode('utf8'))

    def ping(self, user):
        user.socket.sendall('\n<||> Pong\n'.encode('utf8'))

    def pong(self, user):
        user.socket.sendall('\n<||> Ping\n'.encode('utf8'))

    def privateMessage(self, user, chatMessage):
        if len(chatMessage.split()) < 3:
            user.socket.sendall('\n <||> Must provide a target name and a message to send. <||> \n'.encode('utf8'))
        else:
            targetName = chatMessage.split()[1]
            privMessage = chatMessage.split()[2]
            for targetuser in self.users:
                if targetuser.username == targetName:
                    targetSocket = targetuser.socket
                    user.socket.send(("<||> PrivMsg to " + targetName + ": " + privMessage + " <||>\n")
                                     .encode('utf8'))
                    targetSocket.send(("<||> PrivMsg from " + user.username + ": " + privMessage + " <||>\n")
                                      .encode('utf8'))
                    if targetuser.status == "Away":
                        user.socket.send(("<||> Current Status Away: " + targetuser.awaymessage + "\n").encode('utf8'))
                    break

    def quit(self, user):
        user.socket.sendall('/quit'.encode('utf8'))
        self.remove_user(user)

    def restart(self):
        self.broadcast_message("\n <||> Restarting Server! <||> \n")
        self.broadcast_message("/squit")
        main()
        self.server_shutdown()

    def rules(self, user):
        user.socket.sendall("<||> The Rules in this server are simple. Chat away! <||>\n".encode('utf8'))

    def setname(self, user, chatMessage):
        if len(chatMessage.split()) < 3:
            user.socket.sendall("<||> Please enter your full name(first and last. middle optional). <||>\n"
                                .encode('utf8'))
        else:
            new_name = chatMessage.split(" ", 1)[1]
            old_name = user.fullname
            user.fullname = new_name
            message = "<||> Successfully changed name to " + user.fullname + " from " + old_name + ". <||>\n"
            user.socket.sendall(message.encode('utf8'))

    def time(self, user):
        time = strftime("\n<||> %a, %d %b %Y %H:%M:%S +0000 <||>\n", gmtime())
        user.socket.sendall(time.encode('utf8'))

    def topic(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("<||> Must provide a channel name to view channel topic. <||>\n".encode('utf8'))
        else:
            if len(chatMessage.split()) > 2:
                channelName = chatMessage.split()[1]
                topicName = chatMessage.split(" ", 2)[2]
                self.channels[channelName].topic = topicName
                self.channels[channelName].broadcast_server_message(("<||> Channel Topic has been changed to "
                                                                     + topicName + ". <||>\n"))
            else:
                channelName = chatMessage.split()[1]
                if self.channels[channelName].topic == "":
                    user.socket.sendall("<||> No channel topic has been set yet. <||>\n".encode('utf8'))
                else:
                    message = "<||> Channel " + channelName + " topic: " + self.channels[channelName].topic + " <||>\n"
                    user.socket.sendall(message.encode('utf8'))

    def userhost(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("<||> Must provide a nickname or list of nicknames. <||>\n".encode('utf8'))
        else:
            information = "\n<||> List of user information <||>\n\n"
            nicknames = chatMessage.split(" ", 1)
            for name in nicknames:
                for targetUser in self.users:
                    if targetUser.username == name:
                        user_info = "<fullname>: " + targetUser.fullname + ", <username>: " + targetUser.username \
                                    + ", <status>: " + targetUser.status + "\n"
                        information = information + user_info
                        break
            if information == "\n<||> List of user information <||>\n\n":
                user.socket.sendall("<||> No user information found for users with those nicknames. <||>\n"
                                    .encode('utf8'))
            else:
                user.socket.sendall(information.encode('utf8'))

    def user_ip(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("<||> Must provide a nickname. <||>\n".encode('utf8'))
        else:
            nickname = chatMessage.split()[1]
            userfound = False
            for targetUser in self.users:
                if targetUser.username == nickname:
                    message = "<||> " + targetUser.username + " IP Address: " + socket.gethostbyname(socket.gethostname()) \
                              + ". <||>\n"
                    user.socket.sendall(message.encode('utf8'))
                    userfound = True
                    break
            if userfound != True:
                user.socket.sendall("<||> User not in the network. <||>\n".encode('utf8'))

    def users_list(self, user):
        information = "\n<||> List of users: <||>\n\n"
        for targetUser in self.users:
            user_info = "<fullname>: " + targetUser.fullname + ", <username>: " + targetUser.username + ", <status>: "\
                        + targetUser.status + "\n"
            information = information + user_info
            user.socket.sendall(information.encode('utf8'))

    def version(self, user):
        user.socket.sendall('\n<||> Version: 1.0 <||>\n'.encode('utf8'))

    def wallops(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("<||> Must provide a message to be sent. <||>\n".encode('utf8'))
        else:
            message = chatMessage.split(" ", 1)[1]
            self.broadcast_message_to_operators(message)
            user.socket.sendall("\n<||> Message sent to all Channel Operators. <||>\n".encode('utf8'))

    def who(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("\n<||> Please enter your full name(first and last. middle optional <||>\n".encode('utf8'))
        else:
            message = ""
            targetFullName = chatMessage.split(" ", 1)[1]
            print(targetFullName)
            for targetUser in self.users:
                if targetUser.fullname.lower() == targetFullName.lower():
                    user_info = "\n<||> <fullname>: " + targetUser.fullname + ", <username>: " + targetUser.username + ", <status>: " \
                                + targetUser.status + " <||>\n"
                    message = user_info
                    user.socket.sendall(message.encode('utf8'))

            if message == "":
                    user.socket.sendall("\n<||> No User with that name found. <||>\n".encode('utf8'))

    def who_is(self, user, chatMessage):
        if len(chatMessage.split()) < 2:
            user.socket.sendall("\n<||> Must provide a username. <||>\n".encode('utf8'))
        else:
            information = ""
            targetUserName = chatMessage.split(" ", 1)[1]
            for targetUser in self.users:
                if targetUser.username.lower() == targetUserName.lower():
                    user_info = "\n<||> <fullname>: " + targetUser.fullname + ", <username>: " + \
                                    targetUser.username + ", <status>: " + targetUser.status + " <||>\n"
                    information = information + user_info

            if information == "":
                print(information)
                user.socket.sendall("\n<||> No User with that username found. <||>\n".encode('utf8'))
            else:
                user.socket.sendall(information.encode('utf8'))

    def send_message(self, user, chatMessage):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].broadcast_message(chatMessage, "{0}: "
                                                                                    .format(user.username))

            self.channel_files[self.users_channels_map[user.username]] = open(
                self.users_channels_map[user.username] + ".txt", "a+")

            self.channel_files[self.users_channels_map[user.username]].write(user.username + ': ' + chatMessage)

            self.channel_files[self.users_channels_map[user.username]].close()
        else:
            chatMessage = """\n> You are currently not in any channels:

Use /list to see a list of available channels.
Use /join [channel name] to join a channel.\n\n""".encode('utf8')

            user.socket.sendall(chatMessage)

    def remove_user(self, user):
        if user.username in self.users_channels_map:
            self.channels[self.users_channels_map[user.username]].remove_user_from_channel(user)
            del self.users_channels_map[user.username]

        self.users.remove(user)
        print("Client: {0} has left\n".format(user.username))

    def server_shutdown(self):
        print("<||> Shutting down chat server. <||>\n")
        self.serverSocket.close()

    def broadcast_message(self, message):
        for user in self.users:
            user.socket.sendall(message.encode('utf8'))

    def broadcast_message_to_operators(self, message):
        for user in self.users:
            if user.usertype == "ChannelOp":
                user.socket.sendall(message.encode('utf8'))

def main():
    chatServer = Server()

    print("\nListening on port {0}".format(chatServer.address[1]))
    print("Waiting for connections...\n")

    chatServer.start_listening()
    chatServer.server_shutdown()

if __name__ == "__main__":
    main()
