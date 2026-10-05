import tkinter as tk
from virtual_joy import virtual_joy_node as gui
original_tk = tk.Tk
def create_root():
    root = original_tk()
    def close_via_application_callback():
        print('GUI_CLOSE_CALLBACK_EXECUTED', flush=True)
        root.tk.call(root.protocol('WM_DELETE_WINDOW'))
    root.after(1500, close_via_application_callback)
    return root
tk.Tk = create_root
gui.main(args=['--ros-args', '-r', '__ns:=/virtual_joy_jazzy_close_check'])
print('GUI_MAIN_RETURNED', flush=True)
