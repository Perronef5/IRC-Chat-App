
class Channel:
    def __init__(self, name):
        self.users = [] # A list of the users in this channel.
        self.channel_name = name
        self.channel_topic = ""

    def welcome_user(self, username, channel_text_history):
        all_users = self.get_all_users_in_channel()

        for user in self.users:
            if user.username is username:
                chatMessage = '\n\n> {0} have joined the channel {1}!\n|{2}|'.format("You", self.channel_name, all_users)
                user.socket.sendall((chatMessage + channel_text_history).encode('utf8'))
            else:
                chatMessage = '\n\n> {0} has joined the channel {1}!\n|{2}|'.format(username, self.channel_name, all_users)
                user.socket.sendall((chatMessage + channel_text_history).encode('utf8'))

    def broadcast_message(self, chatMessage, username=''):
        for user in self.users:
            if user.username is username:
                user.socket.sendall("You: {0}".format(chatMessage).encode('utf8'))
            else:
                user.socket.sendall("{0} {1}".format(username, chatMessage).encode('utf8'))

    def broadcast_server_message(self, message):
        for user in self.users:
            user.socket.sendall(message.encode('utf8'))

    def get_all_users_in_channel(self):
        return ' '.join([user.username for user in self.users])

    def update(self):
        all_users = self.get_all_users_in_channel()

        for user in self.users:
            chatMessage = '/supdate |' + all_users
            user.socket.sendall(chatMessage.encode('utf8'))

    def remove_user_from_channel(self, user):
        self.users.remove(user)
        leave_message = "\n> {0} has left the channel {1}\n".format(user.username, self.channel_name)
        self.broadcast_message(leave_message)
