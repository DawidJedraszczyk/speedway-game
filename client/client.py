import socket
import threading
from collections import deque
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw
import re
import time

# Global variables
player_labels = []
sock = None
nick = None
player_color = None
players = {}
pressed_keys = {"Left": False, "Right": False, "Up": False, "Down": False}
checkpoints_list = ['left', 'down', 'right', 'up']
player_unreached_checkpoints = ['left', 'down', 'right', 'up']
player_lap = 0
player_points = 0
block_moving = True
round = 0
players_coordinates = {}
disconnected_colors = []
game_started = False

#main loop
def listen_for_updates():
    global sock, player_color, canvas, square, players, round, players_coordinates, block_moving, game_started
    while True:
        try:
            data_rec = sock.recv(1024).decode()
            if not data_rec:
                break
            data_parts = data_rec.split(';')
            for data in data_parts:
                if "Game starts in" in data:
                    root.after(0, update_timer, data)
                if "Game started" in data:
                    game_started = True
                    load_stadium_view()
                if "COORD" in data:
                    res = decode_coordinates(data)
                    for move in res:
                        color, x, y = move
                        if color != player_color:
                            players_coordinates[color].append([x, y])
                if "LAP" in data:
                    laps = decode_laps(data)
                    for lap in laps:
                        color, lap_number = lap
                        player = players[color][0]
                        players[color][1] = lap_number
                        if color != player_color:
                            update_lap_count(player, lap_number)
                if "TIMES" in data:
                    times = decode_times(data)
                    show_times_modal(times)
                if "POINTS" in data:
                    points = decode_points(data)
                    for player_points in points:
                        color, points = player_points
                        player = players[color][0]
                        players[color][2] = points
                        update_points_modal(player, points)
                if "NEXT-ROUND" in data:
                    time.sleep(5)
                    round = decode_round(data)
                    load_stadium_view()
                if "END" in data:
                    block_moving = True
                    best_time = decode_best_time(data)
                    create_end_game_modal(best_time)
                if "PLAYERS" in data:
                    root.after_idle(update_player_list, data)
                if "DISCONNECTED" in data:
                    color = data.split(": ")[1]
                    if game_started:
                        hide_player(color)
                    else:
                        disconnected_colors.append(color)
        except socket.error as e:
            print(f"Error: {e}")
            break


#logic
def connect_to_server(nick, server_address=('127.0.0.1', 8000)):
    global sock
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(server_address)
        sock.sendall(nick.encode())

        threading.Thread(target=listen_for_updates, daemon=True).start()
        active_players_label = tk.Label(root, text='Ready players: ', bg='#ffffff', fg='black', font=("Helvetica", 12))
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
    global root, stadium_photo, canvas, dots, disconnected_colors
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
    for color, [player, laps, points] in players.items():
        if color in dot_positions and color not in disconnected_colors:
            pos = dot_positions[color]
            dots[color] = canvas.create_oval(pos[0], pos[1], pos[0] + dot_size, pos[1] + dot_size, fill=color)

    create_lap_modal()
    create_points_modal()
    create_times_modal()
    canvas.update()
    start_game()

def update_player_list(input_string):
    global player_labels, player_color, dots, players_coordinates
    for label in player_labels:
        label.destroy()
    player_labels.clear()

    player_list = input_string.replace("PLAYERS: ", "")
    for player in player_list.split(', '):
        nickname, color = player.rsplit(' (', 1)
        color = color.rstrip(')\n').strip() 
        laps = 0
        points = 0
        players[color] = [nickname, laps, points]

        
        label = tk.Label(root, text=player, bg='#ffffff', fg='black', font=("Helvetica", 12))
        label.pack()
        
        player_labels.append(label)
        if nickname == nick:
            player_color = color
        if color not in players_coordinates and nickname != nick:
            players_coordinates[color] = deque()

def start_game():
    global canvas, start_time, block_moving, player_lap, stop_event
    player_lap = 0
    for color, [player, lap, points] in players.items():
        if color not in disconnected_colors:
            lap = 0
            update_lap_count(player, lap)
    line_id = canvas.create_line(640, 110, 640, 210, fill="white", width=2)
    time.sleep(3)
    canvas.delete(line_id)
    start_time = time.time()
    block_moving = False
    stop_event = threading.Event()
    updating_dots_position_thread = threading.Thread(target=update_dot_position)
    updating_dots_position_thread.start()
    moving_thread = threading.Thread(target=moving)
    moving_thread.start()


#movement

def player_reached_checkpoint(checkpoint):
    global player_unreached_checkpoints, player_points, player_lap, start_time, end_time, square, canvas, player_race_time, block_moving
    if checkpoint == player_unreached_checkpoints[0]:
        player_unreached_checkpoints = player_unreached_checkpoints[1:]
        if len(player_unreached_checkpoints) == 0:
            player_lap += 1
            players[player_color] = [nick, player_lap, player_points]
            update_lap_count(nick, player_lap)
            send_lap()
            if player_lap == 4:
                end_time = time.time()
                player_race_time = end_time - start_time
                time.sleep(1)
                block_moving = True
                send_time()
            player_unreached_checkpoints = checkpoints_list

def check_if_player_reached_checkpoint(x, y):
    # Pierwszy punkt: x=640 y=od 120do210 
    if x == 630 and (120 <= y <= 210):
        player_reached_checkpoint('up')

    # drugi punkt: x=od90 do 230 y=360
    if (90 <= x <= 230) and y == 360:
        player_reached_checkpoint('left')

    # trzeci punkt: x=650 yod520 do 610 
    if x==650 and (520 <= y <= 610):
        player_reached_checkpoint('down')

    # czwart punkt: x=1080 do 1200 y =360.
    if (1080 <= x <= 1200) and y == 360:
        player_reached_checkpoint('right')

def moving():
    global root, pressed_keys
    root.bind("<KeyPress>", key_press)
    root.bind("<KeyRelease>", key_release)

def key_press(event):
    global block_moving
    if not block_moving:
        pressed_keys[event.keysym] = True
        check_keys()

def key_release(event):
    pressed_keys[event.keysym] = False

def check_keys():
    if pressed_keys["Left"]:
        move_user_dot(-10, 0)
    if pressed_keys["Right"]:
        move_user_dot(10, 0)
    if pressed_keys["Up"]:
        move_user_dot(0, -10)
    if pressed_keys["Down"]:
        move_user_dot(0, 10)

def move_user_dot(dx, dy):
    global dots, player_color
    if player_color in dots:
        current_x, current_y = canvas.coords(dots[player_color])[:2]
        new_x = current_x + dx
        new_y = current_y + dy

        if 90 <= new_x <= 1200 and 120 <= new_y <= 610:
            canvas.move(dots[player_color], dx, dy)

            send_coordinates(new_x, new_y)
            check_if_player_reached_checkpoint(new_x, new_y)

def update_dot_position():
    global players_coordinates, dots, stop_event, disconnected_colors
    dot_size = 8
    while not stop_event.is_set():
        for color, moves in list(players_coordinates.items()):
            if color in dots and color in disconnected_colors:
                canvas.move(dots[color], 2000, 2000)
                dots.pop(color)
            if moves:
                x, y = moves.popleft()
                if color in dots and color not in disconnected_colors:
                    current_coords = canvas.coords(dots[color])
                    if current_coords[:2] != [x, y]:
                        canvas.coords(dots[color], x, y, x + dot_size, y + dot_size)
            
        time.sleep(0.01)


#decoders

def decode_best_time(input_string):
    pattern = r'END:\s*([a-zA-Z]+),\s*([\d.]+)'
    match = re.search(pattern, input_string)
    if match:
        return [match.group(1), match.group(2)]
    else:
        return [None, None]

def decode_round(input_string):
    pattern = r'NEXT-ROUND:\s*(\d)'
    match = re.search(pattern, input_string)

    return match.group(1)

def decode_points(input_string):
    matches = re.findall(r'(\w+), (\d+)', input_string)

    result = [[color, int(number)] for color, number in matches]
    return result

def decode_times(input_string):
    timePattern = re.compile(r'(\w+), (\d+\.\d+)')
    matches = re.findall(timePattern, input_string)

    times_list = [[match[0].lower(), match[1]] for match in matches]
    return times_list

def decode_laps(input_string):
    pattern = r"(red|blue|white|yellow)-LAP: ?(\d+)"
    matches = re.findall(pattern, input_string)

    # Create a list of lists including the color and lap number
    laps_list = [[match[0].lower(), int(match[1])] for match in matches]
    return laps_list

def decode_coordinates(input_string):
    pattern = r"(red|blue|white|yellow)-COORD:([+-]?[0-9]*\.?[0-9]+), ([+-]?[0-9]*\.?[0-9]+)"
    matches = re.findall(pattern, input_string)

    # Create a list of lists including the color and coordinates
    coordinates_list = [[match[0].lower(), float(match[1]), float(match[2])] for match in matches]

    return coordinates_list


#gui(modals)

def update_timer(message):
    timer_label.config(text=message)

def show_times_modal(times):
    for color, time in times:
        if color not in disconnected_colors:
            player = players[color][0]
            update_times_modal(player, time)
    times_frame.place(x=0, y=0)
    root.after(5000, hide_times_modal)

def hide_times_modal():
    global times_frame
    times_frame.place_forget()

def create_end_game_modal(data):
    global root, end_game_frame, player_times_labels, players
    end_game_frame = tk.Frame(root, width=1280, height=720)
    end_game_frame.pack_propagate(False)
    try:
        color, best_time = data
        player = players[color][0]
    except :
        color = 'None'
        best_time = 'None'
        player = 'None'

    best_time_label = tk.Label(end_game_frame, text=f'Best time of this game: {player} {best_time}')
    best_time_label.pack(expand=True)

    points_label = tk.Label(end_game_frame, text='Players points: ')
    points_label.pack(expand=True)

    for color, [player, lap, points] in players.items():
        player_label = tk.Label(end_game_frame, text=f'{player}: {points}')
        player_label.pack(expand=True)
    
    end_game_frame.place(x=0, y=0)

def create_times_modal():
    global root, times_frame, player_times_labels, players
    times_frame = tk.Frame(root, width=1280, height=720)
    times_frame.pack_propagate(False)

    player_times_labels = {}
    for color, [player, lap, points] in players.items():
        player_label = tk.Label(times_frame, text=f'{player}: {0}')
        player_label.pack(expand=True)
        player_times_labels[player] = player_label

def update_times_modal(player, new_time):
    global player_times_labels
    if player in player_times_labels:
        player_times_labels[player].config(text=f"{player}: {new_time}")

def create_points_modal():
    global root, points_frame, player_points_labels
    points_frame = tk.Frame(root, width=200, height=150)
    points_frame.place(x=0, y=0)
    points_frame.pack_propagate(False)

    label = tk.Label(points_frame, text="Player's Points", fg='white')
    label.pack()

    player_points_labels = {}
    for color, [player, lap, points] in players.items():
        player_points_label = tk.Label(points_frame, text=f"{player}:  {points}", fg=color)
        player_points_label.pack(expand=True)
        player_points_labels[player] = player_points_label

def update_points_modal(player, new_points):
    global player_points_labels
    if player in player_points_labels:
        player_points_labels[player].config(text=f"{player}: {new_points}")

def create_lap_modal():
    global players, root, square, player_lap_labels
    square = tk.Frame(root, width=200, height=200)
    square.place(x=550, y=250)
    square.pack_propagate(False)

    # Label with white text
    label = tk.Label(square, text="Player's Laps", fg='white')
    label.pack()
    
    player_lap_labels = {}
    for color, [player, lap, points] in players.items():
        if color not in disconnected_colors:
            player_lap_label = tk.Label(square, text=f"{player}: lap no. {lap}", fg=color)
            player_lap_label.pack(expand=True)
            player_lap_labels[player] = player_lap_label

def update_lap_count(player, new_lap):
    global player_lap_labels
    if player in player_lap_labels:
        player_lap_labels[player].config(text=f"{player}: lap no. {new_lap}")

def hide_player(color):
    global disconnected_colors, dots
    if color not in disconnected_colors:
        disconnected_colors.append(color)
    player = players[color][0]
    update_times_modal(player, 'DISCONNECTED')
    update_lap_count(player, "DISCONNECTED")


#sending

def send_coordinates(x, y):
    global sock, player_color
    coordinates = f"{player_color}-COORD:{x}, {y};"
    sock.sendall(coordinates.encode())

def send_lap():
    global sock, player_lap
    message = f"{player_color}-LAP: {player_lap}"
    sock.sendall(message.encode())

def send_time():
    global sock, player_race_time
    message = f"{player_color}-TIME: {player_race_time}"
    sock.sendall(message.encode())



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
logo_label.pack(pady=100)

# GUI Elements
root.configure(bg='#ffffff')
root.geometry("1280x720")
style_label = tk.Label(root, text="Input Your nickname:", bg='#ffffff', fg='black', font=("Helvetica", 12))
style_label.pack(pady=(0, 10))
nick_entry = tk.Entry(root, font=("Helvetica", 12), fg='black')
nick_entry.pack(pady=(0, 10))
connect_button = tk.Button(root, text="Connect", command=on_connect, fg='black', font=("Helvetica", 12))
connect_button.pack(pady=10)
timer_label = tk.Label(root, text="", bg='#ffffff', fg='black', font=("Helvetica", 12))
timer_label.pack(pady=10)

root.mainloop()

if sock:
    sock.close()
