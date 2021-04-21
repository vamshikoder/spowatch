
# * spowatch v1.3
# ! I donot encourage to use this. It is for educational purposes only.
# ! upgrade to Spotify Premium
# * updates
'''
-> no need of any watch files.
-> watch files when deleted cause an error.
-> added comments to the file for good understanding.
-> added threshold.
->[LATEST] now skip ad without lossing focus on spotify restart. focus is set back to the app that you were using before
'''

from colorama import Fore
from winrt.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
import asyncio
import time
import os
import psutil
import win32process
from win32gui import IsWindowVisible, GetWindowText, EnumWindows, GetForegroundWindow, SetForegroundWindow
import getpass


# & change threshold according to your system speed.
# & threshold denotes how fast the spowatch starts playing after an Advertisement.
THRESHOLD = 2

# & XD if you make your own changes then change version lol
VERSION = 1.3

skiped_ads = 0
spotify_pids = []
previous_song = ""
user = getpass.getuser()
focused_window = 0

# * Spotify can be a windows app downloaded from [Microsoft Store]. or direct .exe download
# * from Spotify website. which have different install locations.

reg_spotify_path = "C:/Users/"+user+"/AppData/Roaming/Spotify/Spotify.exe"
winapp_spotify_path = "C:/Users/"+user + \
    "/AppData/Local/Microsoft/WindowsApps/SpotifyAB.SpotifyMusic_zpdnekdrzrea0/Spotify.exe"

# * correct install location of Spotify, will be updated on runtime.
spotify_install_path = ""


# * This gets the media that is playing in this case we are interseted in Spotify
# * so we set the target to Spotify


async def get_media_info():
    found = True
    while found:
        try:
            sessions = await MediaManager.request_async()
            TARGET_ID = "Spotify.exe"
            current_session = sessions.get_current_session()
            if current_session:
                if current_session.source_app_user_model_id == TARGET_ID:
                    info = await current_session.try_get_media_properties_async()

                    info_dict = {song_attr: info.__getattribute__(
                        song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

                    info_dict['genres'] = list(info_dict['genres'])

                    found = False
                    return info_dict

#! some computers might be slow to open Spotify so the get_media_info will not
#! find Spotify and throws an exception.
        except Exception:
            print("make sure Spotify is open")
            found = True

# * This pauses the song [not required/not used]


async def pause():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    await current_session.try_pause_async()

# * This plays the song used at the app start.


async def play():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    await current_session.try_play_async()

# * This plays the song next song. when the Spotify restarts it points the last
# * played track.


async def next():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    await current_session.try_skip_next_async()

# * this gets the current user which helps to start Spotify according to the username


def get_spotify_pid():
    global spotify_pids
    process_name = "Spotify"
    pid = []
    for proc in psutil.process_iter():
        if process_name in proc.name():
            pid.append(proc.pid)
    spotify_pids = pid

# * starts Spotify with init variable which is True if Spotify is started for the first time.
# * else it is set to False.


# def start_spotify(init, path):
#     global focused_window
#     global spotify_pids
#     os.startfile(path)
#     time.sleep(0.1)
#     if not init:
#         focused_window = GetForegroundWindow()
#         _, pid = win32process.GetWindowThreadProcessId(focused_window)
#         if pid in spotify_pids:
#             ShowWindow(focused_window, win32con.SW_MINIMIZE)
#         else:
#             pass
#     time.sleep(THRESHOLD)
#     get_spotify_pid()
#     try:
#         if init:
#             asyncio.run(play())
#         else:
#             asyncio.run(next())
#     except AttributeError:
#         pass

timerdone = False


def start_spotify(init, path):
    global spotify_pids
    os.startfile(path)
    if not init:
        global timerdone
        import threading
        h = threading.Thread(target=change_focus)
        h.start()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(timer)
            timerdone = future.result()
    time.sleep(THRESHOLD)
    get_spotify_pid()
    try:
        if init:
            asyncio.run(play())
        else:
            asyncio.run(next())
    except AttributeError:
        pass
    timerdone = False


def timer():
    for _ in range(1, 3):
        time.sleep(1)
    return True


def change_focus():
    global timerdone
    focused_window = GetForegroundWindow()
    print("[info]: switching focus to -> "+GetWindowText(focused_window))
    while not timerdone:
        try:
            SetForegroundWindow(focused_window)
        except:
            pass


# * This checks if Spotify is running or not which


def spotify_running():
    process_name = "Spotify"
    pid = []
    for proc in psutil.process_iter():
        if process_name in proc.name():
            pid.append(proc.pid)
    if pid == []:
        return False
    else:
        return True


def song_name(wintext, pid):
    global spotify_pids
    global previous_song

    if pid in spotify_pids:
        if "Spotify" not in wintext:
            current_song = wintext.rstrip().lstrip()
            # * when dragging the songs this prints drag so drag doesnot count
            if previous_song != current_song and current_song != "Drag":
                print("[info]: playing ->", end=" ")
                print(current_song)
                previous_song = current_song

# * This kills the Spotify thread.


def kill_spotify():
    print("[info]: terminating Spotify...")
    process_name = "Spotify"
    for proc in psutil.process_iter():
        if process_name in proc.name():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass


def winEnumHandler(hwnd, _):
    global focused_window
    global skiped_ads
    global spotify_install_path
    if IsWindowVisible(hwnd):
        wintext = GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        if wintext != None and wintext != "" and wintext != " ":
            if wintext == "Spotify Free" or wintext == "Advertisement":
                # if wintext == "Spotify Free" or wintext == "Advertisement":
                current_media_info = asyncio.run(get_media_info())
                if((current_media_info["title"] == "Spotify Free") or (current_media_info["title"] == "Advertisement")):
                    print(Fore.RED + "[info]: Ad dectected")
                    print(Fore.RESET, end="")
                    skiped_ads = skiped_ads + 1
                    kill_spotify()
                    # time.sleep(0.5)
                    print("[info]: starting Spotify")
                    start_spotify(False, spotify_install_path)

            song_name(wintext, pid)


def details():
    print(Fore.GREEN + '\nspowatch v' + str(VERSION) +
          '\nLicense & Copyright © vanhsirki')
    print(Fore.RESET, end="")
    print(Fore.RED + "donot use, educational purposes only.")
    print("Support by Upgrading to Spotify Premium :)")
    print()
    print(Fore.RESET, end="")


def main():
    global spotify_install_path
    global reg_spotify_path
    global winapp_spotify_path
    global skiped_ads
    details()
    print("[info]: trying to start Spotify...")

    if not spotify_running():
        try:
            start_spotify(True, reg_spotify_path)
        except FileNotFoundError:
            try:
                start_spotify(True, winapp_spotify_path)
            except FileNotFoundError:
                print(
                    Fore.RED + "[error]: Spotify not found in default locations.")
                print(Fore.RESET, end="")
            else:
                spotify_install_path = winapp_spotify_path
        else:
            spotify_install_path = reg_spotify_path
    else:
        print("[info]: Spotify already running...")
        if os.path.exists(reg_spotify_path):
            spotify_install_path = reg_spotify_path
        else:
            spotify_install_path = winapp_spotify_path
        get_spotify_pid()
    try:
        print("[info]: running spowatch...")
        while True:
            EnumWindows(winEnumHandler, None)
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("[info]: keyboard interrupt, ending watch")
        if("y" == input("close Spotify? (y/n): ")):
            kill_spotify()
        print(Fore.GREEN + "[info]: ads skipped: "+str(skiped_ads))
        print(Fore.RESET, end="")
        try:
            input("press Enter key to exit...")
        except [KeyboardInterrupt, EOFError]:
            pass

    except psutil.NoSuchProcess:
        print("[info]: process no longer exist, ending watch")
        if("y" == input("close Spotify? (y/n): ")):
            kill_spotify()
        print(Fore.GREEN + "[info]: ads skipped: "+str(skiped_ads))
        print(Fore.RESET, end="")
        try:
            input("press Enter key to exit...")
        except [KeyboardInterrupt, EOFError]:
            pass


if __name__ == "__main__":
    main()
