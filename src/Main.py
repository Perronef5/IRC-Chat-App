import tkinter as tk
from tkinter import messagebox
import ChatClient as client
import BaseDialog as dialog
import BaseEntry as entry
import threading

class SocketThreadedTask(threading.Thread):
    def __init__(self, socket, **callbacks):
        threading.Thread.__init__(self)
        self.socket = socket
        self.callbacks = callbacks
        self.current_channel = ''


    def run(self):
        while True:
            try:
                message = self.socket.receive()

                if message == '/quit':
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> You have been disconnected from the server.\n')
                    self.socket.disconnect()
                    break
                elif '/supdate' in message:
                    split_message = message.split('|')
                    self.callbacks['clear_user_list']()
                    self.callbacks['update_user_list'](split_message[1])
                    break
                elif message == '/squit':
                    self.callbacks['clear_user_list']()
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window']('\n> The server was forcibly shutdown. No further messages are able to be sent\n')
                    self.socket.disconnect()
                    break
                elif 'joined' in message:
                    split_message = message.split('|')
                    self.current_channel = (message.split(' ')[6]).split('!')[0]
                    self.callbacks['clear_chat_window']()
                    self.callbacks['update_chat_window_special_text'](split_message[0] + '\n' + split_message[2])
                    self.callbacks['update_user_list'](split_message[1])
                    self.callbacks['add_channel_tab'](self.current_channel)
                elif '<||>' in message:
                    self.callbacks['update_chat_window_special_text'](message)
                elif '<|*|>' in message:
                    self.callbacks['clear_user_list']()
                    self.callbacks['update_chat_window_special_text'](message)
                elif '/clear' in message:
                    self.callbacks['clear_only_chat_window']()
                elif 'left' in message:
                    self.callbacks['update_chat_window'](message)
                    self.callbacks['remove_user_from_list'](message.split(' ')[2])
                else:
                    self.callbacks['update_chat_window'](message)
            except OSError:
                break

class ChatDialog(dialog.BaseDialog):
    def body(self, master):
        tk.Label(master, text="Enter host:").grid(row=0, sticky="w")
        tk.Label(master, text="Enter port:").grid(row=1, sticky="w")

        self.hostEntryField = entry.BaseEntry(master, placeholder="Enter host")
        self.portEntryField = entry.BaseEntry(master, placeholder="Enter port")

        self.hostEntryField.grid(row=0, column=1)
        self.portEntryField.grid(row=1, column=1)
        return self.hostEntryField

    def validate(self):
        host = str(self.hostEntryField.get())

        try:
            port = int(self.portEntryField.get())

            if(port >= 0 and port < 65536):
                self.result = (host, port)
                return True
            else:
                tk.messagebox.showwarning("Error", "The port number has to be between 0 and 65535. Both values are inclusive.")
                return False
        except ValueError:
            tk.messagebox.showwarning("Error", "The port number has to be an integer.")
            return False

class ChatWindow(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg="#111111")

        self.initUI(parent)

    def initUI(self, parent):
        self.config(bg="#fcfcfa")
        self.messageTextArea = tk.Text(parent, bg="#111111", state=tk.DISABLED, wrap=tk.WORD, highlightbackground='#111111', foreground="green")
        self.messageTextArea.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.messageTextArea.tag_configure("user", foreground="green")
        self.messageTextArea.tag_configure("nonuser", foreground="yellow")

        self.messageScrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=self.messageTextArea.yview, highlightbackground='#111111', bg='#111111', troughcolor='#111111')
        self.messageScrollbar.grid(row=0, column=3, sticky="nsew")

        self.messageTextArea['yscrollcommand'] = self.messageScrollbar.set

        self.usersListBox = tk.Listbox(parent, bg="#212121", foreground="#fcfcfa")
        self.usersListBox.grid(row=0, column=4, padx=5, sticky="nsew")

        self.entryField = entry.BaseEntry(parent, placeholder="Enter message.", width=80, highlightbackground='#313131')
        self.entryField.grid(row=1, column=0, padx=7, pady=10, sticky="we")

        self.send_message_button = tk.Button(parent, text="Send", width=10, bg="green", highlightbackground='#313131')
        self.send_message_button.grid(row=1, column=1, padx=5, sticky="we")

    def update_chat_window(self, message):
        self.messageTextArea.configure(state='normal')
        tag = "user"
        self.messageTextArea.insert(tk.END, message, tag)
        self.messageTextArea.configure(state='disabled')

    def update_chat_window_special_text(self, message):
        tag = "nonuser"
        self.messageTextArea.configure(state='normal')
        self.messageTextArea.insert(tk.END, message, tag)
        self.messageTextArea.configure(state='disabled')

    def update_user_list(self, user_message):
        users = user_message.split(' ')

        for user in users:
            if user not in self.usersListBox.get(0, tk.END):
                self.usersListBox.insert(tk.END, user)

    def clear_user_list(self):
        for user in self.usersListBox.get(0, tk.END):
            index = self.usersListBox.get(0, tk.END).index(user)
            self.usersListBox.delete(index)

    def remove_user_from_list(self, user):
        print(user)
        index = self.usersListBox.get(0, tk.END).index(user)
        self.usersListBox.delete(index)

    def clear_only_chat_window(self):
        if not self.messageTextArea.compare("end-1c", "==", "1.0"):
            self.messageTextArea.configure(state='normal')
            self.messageTextArea.delete('1.0', tk.END)
            self.messageTextArea.configure(state='disabled')

    def clear_chat_window(self):
        if not self.messageTextArea.compare("end-1c", "==", "1.0"):
            self.messageTextArea.configure(state='normal')
            self.messageTextArea.delete('1.0', tk.END)
            self.messageTextArea.configure(state='disabled')

        if self.usersListBox.size() > 0:
            self.usersListBox.delete(0, tk.END)

    def send_message(self, **callbacks):
        message = self.entryField.get()
        self.set_message("")

        callbacks['send_message_to_server'](message)

    def set_message(self, message):
        self.entryField.delete(0, tk.END)
        self.entryField.insert(0, message)

    def bind_widgets(self, callback):
        self.send_message_button['command'] = lambda sendCallback = callback : self.send_message(send_message_to_server=sendCallback)
        self.entryField.bind("<Return>", lambda event, sendCallback = callback : self.send_message(send_message_to_server=sendCallback))
        self.messageTextArea.bind("<1>", lambda event: self.messageTextArea.focus_set())

class ChatGUI(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg= "#111111")

        self.initUI(parent)

        self.ChatWindow = ChatWindow(self.parent)

        self.clientSocket = client.Client()

        self.channelTabs = []


        self.ChatWindow.bind_widgets(self.clientSocket.send)
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initUI(self, parent):
        self.parent = parent
        self.parent.title("ChatApp")

        screenSizeX = self.parent.winfo_screenwidth()
        screenSizeY = self.parent.winfo_screenheight()

        frameSizeX = 800
        frameSizeY = 600

        framePosX = (screenSizeX - frameSizeX) / 2
        framePosY = (screenSizeY - frameSizeY) / 2

        self.parent.geometry('%dx%d+%d+%d' % (frameSizeX, frameSizeY, framePosX, framePosY))
        self.parent.resizable(True, True)
        self.parent.configure(background="#313131")

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        self.mainMenu = tk.Menu(self.parent)
        self.parent.config(menu=self.mainMenu)

        self.subMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label='File', menu=self.subMenu)
        self.subMenu.add_command(label='Connect', command=self.connect_to_server)
        self.subMenu.add_command(label='Exit', command=self.on_closing)

    def add_channel_tab(self, channelName):

        if channelName not in self.channelTabs:
            self.mainMenu.add_command(label=channelName, command=lambda: self.clientSocket.send('/join ' + channelName))

            self.channelTabs.append(channelName)

    def connect_to_server(self):
        if self.clientSocket.isClientConnected:
            tk.messagebox.showwarning("Info", "Already connected to the server.")
            return

        dialogResult = ChatDialog(self.parent).result

        if dialogResult:
            self.clientSocket.connect(dialogResult[0], dialogResult[1])

            if self.clientSocket.isClientConnected:
                self.ChatWindow.clear_chat_window()
                SocketThreadedTask(self.clientSocket, update_chat_window=self.ChatWindow.update_chat_window,
                                                      update_chat_window_special_text=self.ChatWindow.update_chat_window_special_text,
                                                      update_user_list=self.ChatWindow.update_user_list,
                                                      clear_user_list=self.ChatWindow.clear_user_list,
                                                      clear_chat_window=self.ChatWindow.clear_chat_window,
                                                      clear_only_chat_window=self.ChatWindow.clear_only_chat_window,
                                                      remove_user_from_list=self.ChatWindow.remove_user_from_list,
                                                      add_channel_tab = self.add_channel_tab).start()

            else:
                tk.messagebox.showwarning("Error", "Unable to connect to the server.")

    def on_closing(self):
        if self.clientSocket.isClientConnected:
            self.clientSocket.send('/quit')

        self.parent.quit()
        self.parent.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    chatGUI = ChatGUI(root)
    root.mainloop()
