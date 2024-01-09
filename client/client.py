import socket
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import re

# Global variables
player_labels = []
sock = None
nick = None
player_color = None
players = {}

def update_player_list(player_list):
    global player_labels, player_color, dots
    for label in player_labels:
        label.destroy()
    player_labels.clear()

    for player in player_list.split(', '):
        print(player.rsplit(' (', 1))
        nickname, color = player.rsplit(' (', 1)
        color = color.rstrip(')\n').strip() 

        players[nickname] = color
        
        label = tk.Label(root, text=player, bg='#ffffff', fg='black', font=("Helvetica", 12))
        label.pack()
        
        player_labels.append(label)
        if nickname == nick:
            player_color = color

def update_timer(message):
    timer_label.config(text=message)

def listen_for_updates():
    global sock, player_color
    while True:
        try:
            data = sock.recv(1024).decode()
            if data:
                print(data)
                if "Game starts in" in data:
                    root.after(0, update_timer, data)
                elif "Game started" in data:
                    load_stadium_view()
                elif "COORD" in data:
                    res = decode_coordinates(data)
                    for move in res:
                        print(move)
                        color, x, y = move
                        if color != player_color:
                            update_dot_position(x, y, color)
                else:
                    root.after(0, update_player_list, data)
            else:
                break
        except socket.error as e:
            print(f"Error: {e}")
            break

def decode_coordinates(input_string):
    pattern = r"(RED|BLUE|WHITE|YELLOW)-COORD:([+-]?[0-9]*\.?[0-9]+), ([+-]?[0-9]*\.?[0-9]+);"
    matches = re.findall(pattern, input_string)

    # Create a list of lists including the color and coordinates
    coordinates_list = [[match[0].lower(), float(match[1]), float(match[2])] for match in matches]

    return coordinates_list



def connect_to_server(nick, server_address=('192.168.1.63', 8000)):
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        sock.sendall(nick.encode())

        threading.Thread(target=listen_for_updates, daemon=True).start()
        active_players_label = tk.Label(root, text='Aktualni gracze: ', bg='#ffffff', fg='black', font=("Helvetica", 12))
        active_players_label.pack()
        return sock
    except socket.error as err:
        messagebox.showerror("Connection Error", f"Cannot connect to server: {err}")
        return None

def on_connect():
    global nick
    nick = nick_entry.get()
    if connect_to_server(nick):
        style_label.pack_forget()
        nick_entry.pack_forget()
        connect_button.pack_forget()

def load_stadium_view():
    global root, stadium_photo, canvas, dots
    # Load the stadium image
    stadium_image_path = './static/images/stadium.png'  # Adjust the path to your image
    stadium_image = Image.open(stadium_image_path)

    # Resize the image (optional, remove if causing issues)
    stadium_image = stadium_image.resize((1280, 720), Image.LANCZOS)

    stadium_photo = ImageTk.PhotoImage(stadium_image)

    # Clear the current view
    for widget in root.winfo_children():
        widget.pack_forget()

    # Create a canvas and put the image on it
    canvas = tk.Canvas(root, width=1280, height=720)
    canvas.pack(fill='both', expand=True)
    canvas.create_image(0, 0, image=stadium_photo, anchor='nw')

    # Draw the red dot
    dot_positions = {'red': (650, 200), 'blue': (650, 170), 'white': (650, 150), 'yellow': (650, 130)}
    dots = {}
    dot_size = 8
    for player, color in players.items():
        if color in dot_positions:
            pos = dot_positions[color]
            dots[color] = canvas.create_oval(pos[0], pos[1], pos[0] + dot_size, pos[1] + dot_size, fill=color)


    # Redraw the canvas
    canvas.update()

    moving_thread = threading.Thread(target=moving)
    moving_thread.start()
    
def moving():
    global root
    root.bind("<Left>", lambda e: move_user_dot(-10, 0))
    root.bind("<Right>", lambda e: move_user_dot(10, 0))
    root.bind("<Up>", lambda e: move_user_dot(0, -10))
    root.bind("<Down>", lambda e: move_user_dot(0, 10))



# Funkcja do przesuwania kropki
def move_user_dot(dx, dy):
    global dots, player_color
    if player_color in dots:
        x1, y1, x2, y2 = canvas.coords(dots[player_color])
        new_x = max(0, min(canvas.winfo_width(), x1 + dx))  # Prevent x-coordinate from going out of bounds
        new_y = max(0, min(canvas.winfo_height(), y1 + dy)) # Prevent y-coordinate from going out of bounds
       
        update_dot_position(new_x, new_y, player_color)
        send_coordinates(new_x, new_y)

def send_coordinates(x, y):
    global sock, player_color
    coordinates = f"{player_color.upper()}-COORD:{x}, {y};"
    sock.sendall(coordinates.encode())

def update_dot_position(x, y, color):
    global dots
    dot_size = 8
    if color in dots:
        canvas.coords(dots[color], x, y, x + dot_size, y + dot_size)


# GUI setup
root = tk.Tk()
root.title("Speedway game")

# Load and display an image (adjust the path to your image)
image_path = './static/images/logo.png'
original_image = Image.open(image_path)
max_size = (300, 300)
original_image.thumbnail(max_size, Image.LANCZOS)
logo_photo = ImageTk.PhotoImage(original_image)
logo_label = tk.Label(root, image=logo_photo, borderwidth=0, highlightthickness=0)
logo_label.pack(pady=20)

# GUI Elements
root.configure(bg='#ffffff')
root.geometry("1280x720")
style_label = tk.Label(root, text="Podaj swój nick:", bg='#ffffff', fg='black', font=("Helvetica", 12))
style_label.pack(pady=(0, 10))
nick_entry = tk.Entry(root, font=("Helvetica", 12), fg='black')
nick_entry.pack(pady=(0, 10))
connect_button = tk.Button(root, text="Connect", command=on_connect, fg='black', font=("Helvetica", 12))
connect_button.pack(pady=10)
timer_label = tk.Label(root, text="", bg='#ffffff', fg='black', font=("Helvetica", 12))
timer_label.pack(pady=10)

root.mainloop()

# Ensure the socket is closed when the GUI is closed
if sock:
    sock.close()
