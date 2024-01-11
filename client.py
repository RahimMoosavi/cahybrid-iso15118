import os
import random
import dotenv
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from tkinter import filedialog
from threading import Thread
import subprocess
import time


def run_script(text_widget):
    def target():
        nonlocal process
        try:
            commands = ["make", "run-evcc"]
            process = subprocess.Popen(
                commands,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            text_widget.insert(tk.END, f"Started The EVCC with PID: {process.pid}\n")
            text_widget.see(tk.END)
            for line in iter(process.stdout.readline, ""):
                text_widget.insert(tk.END, line)
                text_widget.see(tk.END)
            process.wait()
        except Exception as e:
            text_widget.insert(tk.END, f"Failed to run The EVCC {e}\n")
            text_widget.see(tk.END)
        finally:
            if process:
                process.stdout.close()

    process = None
    thread = Thread(target=target, daemon=True)
    thread.start()
    return lambda: (process.terminate() if process and process.poll() is None else None)


def on_closing():
    if server_terminator:
        print("Terminating server...")
        server_terminator()
        time.sleep(1)
    root.destroy()


def save_communications(communications):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    if file_path:
        with open(file_path, "w") as file:
            file.write(communications)


server_terminator = None


def run_client():
    if client_button.cget("text") == client_button_text_status[0]:
        client_button.config(text=client_button_text_status[1])
        run_script(client_response_box)
    else:
        client_button.config(text=client_button_text_status[0])
        save_communications(client_response_box.get("1.0", "end-1c"))
        client_response_box.delete("1.0", "end")


def save_env_variables(key, value):
    os.environ[key] = value
    dotenv.set_key(dotenv_file, key, os.environ[key])


def on_log_level_changed(*args):
    selected_index = combobox.current()
    selected_value = log_level_options[selected_index]
    save_env_variables("LOG_LEVEL", selected_value)


def message_log_json_changed():
    if message_log_json_var.get():
        save_env_variables("MESSAGE_LOG_JSON", "True")

    else:
        save_env_variables("MESSAGE_LOG_JSON", "False")


def message_log_exi_changed():
    if message_log_json_var.get():
        save_env_variables("MESSAGE_LOG_EXI", "True")

    else:
        save_env_variables("MESSAGE_LOG_EXI", "False")


# Load env environment
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

root = tk.Tk()

root.title("EVCC Application")
root.geometry("700x800")

client_button_text_status = ["Connect EV", "Disconnect EV"]


client_button = tk.Button(
    root, text=client_button_text_status[0], command=run_client, height=2
)
client_button.grid(row=0, column=0, sticky="nsew")


config_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
config_frame.grid(row=0, column=1, sticky="nsew")


message_log_json_var = tk.BooleanVar(value=(os.environ["MESSAGE_LOG_JSON"]))
message_log_json_checkbox = ttk.Checkbutton(
    config_frame,
    text="MESSAGE LOG JSON",
    variable=message_log_json_var,
    command=message_log_json_changed,
)
message_log_json_checkbox.grid(row=0, column=0, sticky="w")


message_log_exi_var = tk.BooleanVar(value=(os.environ["MESSAGE_LOG_EXI"]))
message_log_json_checkbox = ttk.Checkbutton(
    config_frame,
    text="MESSAGE LOG EXI",
    variable=message_log_exi_var,
    command=message_log_exi_changed,
)
message_log_json_checkbox.grid(row=1, column=0, sticky="w")


log_level_options = ["INFO", "DEBUG"]
selected_option = tk.StringVar(
    value=log_level_options[log_level_options.index(os.environ["LOG_LEVEL"])]
)
combobox = ttk.Combobox(
    config_frame,
    values=log_level_options,
    textvariable=selected_option,
    state="readonly",
)
combobox.grid(row=2, column=0, sticky="nsew")
combobox.bind("<<ComboboxSelected>>", on_log_level_changed)


client_response_box = tk.Text(root)
client_response_box.grid(row=1, column=0, columnspan=2, sticky="nsew")


status_bar = ttk.Frame(root)
status_bar.grid(row=2, column=0, columnspan=2, sticky="nsew")


battery_value_label = tk.Label(status_bar, text=f"Battery : {random.randint(0 , 100)}%")
battery_value_label.grid(row=0, column=0, sticky="w")

is_plugged_label = tk.Label(status_bar, text="Is Plugged : ")
is_plugged_label.grid(row=0, column=1, sticky="nsew")
is_plugged_checkbox = tk.Checkbutton(status_bar, state="disabled")
is_plugged_checkbox.grid(row=0, column=2, sticky="nsew")
status_bar.grid_columnconfigure(0, weight=1)


root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
