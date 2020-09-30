#!/usr/bin/env python3
import os
from pathlib import Path
from ffprobe import FFProbe
import win32file
import win32con
import time

ACTIONS = {1: "Created", 2: "Deleted", 3: "Updated", 4: "Renamed from", 5: "Renamed to"}
FILE_LIST_DIRECTORY = 0x0001

# path_to_watch = "."
path_to_watch = r".\watch_folder"
# ACCEPTED_FOLDER = r"\\HIRESFILESERVER\HiResStorage2\DV Watch Folder for Import"
# ACCEPTED_FOLDER = r"\\NAS3016A_ARTIST\artist\АРТИСТ\RU\Л\ЛОЛИТА\СУБТИТРЫ"


def get_destination_folder(parent_folder, move_folder):
    dest_folder = parent_folder / move_folder
    Path.mkdir(dest_folder, exist_ok=True)
    return dest_folder


def move_file(codec_tag, filename, folder=None):
    print(f"codec {codec_tag} {folder.lower()}!")
    pass


def process(filename):
    try:
        metadata = FFProbe(str(filename))
        codec_tag = metadata.streams[0].codec_tag_string
        if codec_tag and codec_tag == "dvsd":
            move_file(codec_tag, filename, folder="Accepted")
            dest_file = (
                get_destination_folder(filename.parent, "Accepted") / filename.name
            )
            # dest_file = os.path.join(ACCEPTED_FOLDER, filename.name)
            if dest_file.exists():
                print("file already exist in accepted folder")
                Path(filename).replace(dest_file)
            else:
                Path(filename).rename(dest_file)
        else:
            print(f"codec {codec_tag} rejected")
            dest_file = (
                get_destination_folder(filename.parent, "Rejected") / filename.name
            )
            if dest_file.exists():
                print("file already exists in rejected folder, replacing file")
                Path(filename).replace(dest_file)
            else:
                Path(filename).rename(dest_file)
    except IndexError as e:
        print("index error", e)
    except Exception as e:
        print("other error during process", e)
        raise


def convert_bytes(num):
    """convert os.stat(file).st_size to MB, GB etc"""
    for i in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.2f} {i}"
        num /= 1024


def run_watchfolder(path_to_watch):
    hDir = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ
        | win32con.FILE_SHARE_WRITE
        | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    while 1:

        # ReadDirectoryChangesW takes a previously-created
        # handle to a directory, a buffer size for results,
        # a flag to indicate whether to watch subtrees and
        # a filter of what changes to notify.

        results = win32file.ReadDirectoryChangesW(
            hDir,
            2048,
            False,  # bWatchSubtree
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
            | win32con.FILE_NOTIFY_CHANGE_SIZE
            | win32con.FILE_NOTIFY_CHANGE_FILE_NAME
            | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES,
            None,
            None,
        )
        for action, file in results:
            if action == 1:
                print(f"{ACTIONS.get(action)} {file}")
            full_filename = Path(path_to_watch) / file
            ext = full_filename.suffix
            if ext == ".avi":
                # check if file is accessible (not being copied at the moment)
                while True:
                    try:
                        new_path = str(full_filename) + "_"
                        os.rename(str(full_filename), new_path)
                        if not new_path:
                            break
                        os.rename(new_path, str(full_filename))
                        file_size = convert_bytes(os.stat(str(full_filename)).st_size)
                        print(
                            f"\nfile {file} is found, size: {file_size}"
                            "\nprocessing now..."
                        )
                        process(full_filename)
                        break
                    except OSError as e:
                        if e.winerror != 32:
                            break
                        time.sleep(.5)
                    except Exception as e:
                        print('unhandled error')
                        raise


if __name__ == "__main__":
    for file in os.listdir(path_to_watch):
        filename = Path(path_to_watch) / file
        if filename.is_file and filename.suffix.lower() == ".avi":
            print(f"processing {filename.name}")
            process(filename)
    run_watchfolder(path_to_watch)
