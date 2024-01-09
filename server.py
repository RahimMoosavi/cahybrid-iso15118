import os
import dotenv
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from threading import Thread
import subprocess
import time


def run_script(text_widget):
    def target():
        nonlocal process
        try:
            commands = ["make", "run-secc"]
            process = subprocess.Popen(
                commands,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            text_widget.insert(tk.END, f"Started the secc with PID: {process.pid}\n")
            text_widget.see(tk.END)
            for line in iter(process.stdout.readline, ""):
                text_widget.insert(tk.END, line)
                text_widget.see(tk.END)
            process.wait()
        except Exception as e:
            text_widget.insert(tk.END, f"Failed to run the secc: {e}\n")
            text_widget.see(tk.END)
        finally:
            if process:
                process.stdout.close()

    def terminate_process():
        time.sleep(20)
        if process and process.poll() is None:
            process.terminate()
            process.wait()  # Wait for the thread to complete

    process = None
    thread = Thread(target=target, daemon=True)
    thread.start()
    # return lambda: (process.terminate() if process and process.poll() is None else None)
    # return lambda: Thread(target=terminate_process, daemon=True).start()

    return lambda: (
        process.terminate(),
        process.wait() if process and process.poll() is None else None,
    )


def on_closing():
    if server_terminator:
        print("Terminating server...")
        server_button.config(state=tk.DISABLED)
        server_terminator()
        server_button.config(state=tk.NORMAL)
    root.destroy()


server_terminator = None


def run_server():
    global server_terminator

    if server_button.cget("text") == server_button_text_states[0]:
        server_response_box.delete("1.0", "end")
        server_button.config(text=server_button_text_states[1])
        server_terminator = run_script(server_response_box)
    else:
        server_button.config(state=tk.DISABLED)
        if server_terminator:
            print("Terminating server...")
            server_terminator()
        server_button.config(state=tk.NORMAL)
        server_button.config(text=server_button_text_states[0])
        server_response_box.delete("1.0", "end")


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

root.title("SECC Application")
root.geometry("700x800")


server_button_text_states = ["Start SECC", "Stop SECC"]


server_button = tk.Button(
    root, text=server_button_text_states, command=run_server, height=2
)
server_button.grid(row=0, column=0, sticky="nsew")


frame = ttk.Frame(root, padding=(10, 10, 10, 10))
frame.grid(row=0, column=1, sticky="nsew")


message_log_json_var = tk.BooleanVar(value=(os.environ["MESSAGE_LOG_JSON"]))
message_log_json_checkbox = ttk.Checkbutton(
    frame,
    text="MESSAGE LOG JSON",
    variable=message_log_json_var,
    command=message_log_json_changed,
)
message_log_json_checkbox.grid(row=0, column=0, sticky="w")


message_log_exi_var = tk.BooleanVar(value=(os.environ["MESSAGE_LOG_EXI"]))
message_log_json_checkbox = ttk.Checkbutton(
    frame,
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
    frame, values=log_level_options, textvariable=selected_option, state="readonly"
)
combobox.grid(row=2, column=0, sticky="nsew")
combobox.bind("<<ComboboxSelected>>", on_log_level_changed)


server_response_box = tk.Text(root)
server_response_box.grid(row=1, column=0, columnspan=2, sticky="nsew")


root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
