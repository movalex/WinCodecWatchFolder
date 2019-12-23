#!/usr/bin/env python3
import os
from pathlib import Path
from ffprobe import FFProbe
import win32file
import win32con

ACTIONS = {
  1 : "Created",
  2 : "Deleted",
  3 : "Updated",
  4 : "Renamed from",
  5 : "Renamed to"
}
# Thanks to Claudio Grondi for the correct set of numbers
FILE_LIST_DIRECTORY = 0x0001

path_to_watch = "."
hDir = win32file.CreateFile (
  path_to_watch,
  FILE_LIST_DIRECTORY,
  win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
  None,
  win32con.OPEN_EXISTING,
  win32con.FILE_FLAG_BACKUP_SEMANTICS,
  None
)


def move_path(file_path, move_folder):
    parent = file_path.parent
    dest_folder = parent / move_folder
    Path.mkdir(dest_folder, exist_ok = True)
    return dest_folder


while 1:
  #
  # ReadDirectoryChangesW takes a previously-created
  # handle to a directory, a buffer size for results,
  # a flag to indicate whether to watch subtrees and
  # a filter of what changes to notify.
  #
  results = win32file.ReadDirectoryChangesW (
    hDir,
    1024,
    False, # bWatchSubtree
     # win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
     # win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
     # win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
     # win32con.FILE_NOTIFY_CHANGE_SIZE |
     win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
     # win32con.FILE_NOTIFY_CHANGE_SECURITY
    None,
    None
  )
  for action, file in results:
    full_filename = Path(path_to_watch) / file
    # parent = full_filename.parent
    # dest_accepted = parent / 'Accepted'
    # dest_rejected = parent / 'Rejected'
    # Path.mkdir(dest_accepted, exist_ok = True)
    # Path.mkdir(dest_rejected, exist_ok = True)
    # print(ACTIONS.get (action, "Unknown"), full_filename)
    ext = full_filename.suffix
    if ext == '.avi':
        try:
            metadata = FFProbe(file)
            codec_tag = metadata.streams[0].codec_tag_string
            if codec_tag and codec_tag == 'dvsd':
                print(f'codec {codec_tag} accepted')
                try:
                    dest_file = move_path(full_filename, 'Accepted') / file
                    # dest_accepted / full_filename.name
                    # print('dest file - ', dest_file)
                    if dest_file.exists():
                        print('file exist in accepted folder')
                    else:
                        Path(full_filename).rename(dest_file)
                except Exception:
                    raise
                finally:
                    full_filename.unlink()
            else:
                print(f'codec {codec_tag} rejected')
                try:
                    dest_file = move_path(full_filename, 'Rejected') / file
                    if dest_file.exists():
                        print('file already exists in rejected folder')
                    else:
                        Path(full_filename).rename(dest_file)
                except Exception:
                    raise
                finally:
                    full_filename.unlink()
        except OSError:
            pass # ffprobe catch error
