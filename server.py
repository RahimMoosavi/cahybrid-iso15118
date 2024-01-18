import json
import os
import dotenv
import tkinter as tk
from tkinter import ttk
from threading import Thread
import subprocess
import time
from tkinter import filedialog
import requests


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


def save_communications(communications):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    if file_path:
        with open(file_path, "w") as file:
            file.write(communications)


server_terminator = None


def run_server():
    global server_terminator

    if server_button.cget("text") == server_button_text_states[0]:
        server_response_box.delete("1.0", "end")
        server_button.config(text=server_button_text_states[1])
        server_terminator = run_script(server_response_box)
        change_all_input_status("disabled")
    else:
        server_button.config(state=tk.DISABLED)
        if server_terminator:
            print("Terminating server...")
            server_terminator()
        server_button.config(state=tk.NORMAL)
        server_button.config(text=server_button_text_states[0])
        save_communications(server_response_box.get("1.0", "end-1c"))
        server_response_box.delete("1.0", "end")
        change_all_input_status("normal")
        server_terminator = None


def change_all_input_status(status):
    max_charge_power_input.config(state=status)
    max_charge_power_label.config(state=status)
    charge_limit_input.config(state=status)
    charge_limit_label.config(state=status)
    message_log_json_checkbox.config(state=status)
    message_log_exi_checkbox.config(state=status)
    log_level_select.config(state=status)


def save_env_variables(key, value):
    os.environ[key] = value
    dotenv.set_key(dotenv_file, key, os.environ[key])


def on_log_level_changed(*args):
    selected_index = log_level_select.current()
    selected_value = log_level_options[selected_index]
    save_env_variables("LOG_LEVEL", selected_value)


def message_log_json_changed():
    if message_log_json_var.get():
        save_env_variables("MESSAGE_LOG_JSON", "True")

    else:
        save_env_variables("MESSAGE_LOG_JSON", "False")


def message_log_exi_changed():
    if message_log_exi_var.get():
        save_env_variables("MESSAGE_LOG_EXI", "True")

    else:
        save_env_variables("MESSAGE_LOG_EXI", "False")


def sync_with_client():
    end_index = server_response_box.index("end-1c")
    line_count = server_response_box.get("1.0", end_index).count("\n") + 1
    if line_count > 26:
        try:
            response = requests.get(ev_hardware_address, proxies={})
            response.raise_for_status()  # Raise an exception for HTTP errors (status code other than 2xx)

            if response.status_code == 200:
                data = response.json()
                max_discharge_power_input.config(state="normal")
                max_discharge_power_input.delete("1.0", tk.END)
                max_discharge_power_input.insert("1.0", data["max_discharge_power"])
                max_discharge_power_input.config(state="disabled")
                present_soc_input.config(state="normal")
                present_soc_input.delete("1.0", tk.END)
                present_soc_input.insert("1.0", data["present_soc"])
                present_soc_input.config(state="disabled")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except requests.ConnectionError as e:
            print(e)
            print(
                "Failed to connect. Check the server address and make sure it's running."
            )
    root.after(sync_time, sync_with_client)


# ev_hardware_address = "http://192.168.43.241:8000/"
ev_hardware_address = "http://localhost:8000/"
correct_sync_time = 500
delayed_sync_time = 1500
fake_sync_time = 4000
sync_time = correct_sync_time


# Load env environment
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)


root = tk.Tk()

root.title("SECC Application")
root.geometry("850x850")


server_button_text_states = ["Start SECC", "Stop SECC"]


server_button = tk.Button(
    root, text=server_button_text_states[0], command=run_server, height=2
)
server_button.grid(row=0, column=0, sticky="nsew")


# Setting frame

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
message_log_exi_checkbox = ttk.Checkbutton(
    frame,
    text="MESSAGE LOG EXI",
    variable=message_log_exi_var,
    command=message_log_exi_changed,
)
message_log_exi_checkbox.grid(row=1, column=0, sticky="w")
log_level_options = ["INFO", "DEBUG"]
selected_option = tk.StringVar(
    value=log_level_options[log_level_options.index(os.environ["LOG_LEVEL"])]
)
log_level_select = ttk.Combobox(
    frame, values=log_level_options, textvariable=selected_option, state="readonly"
)
log_level_select.grid(row=2, column=0, sticky="nsew")
log_level_select.bind("<<ComboboxSelected>>", on_log_level_changed)

# Inputs frame

user_inputs_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
user_inputs_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
user_inputs_frame.grid_columnconfigure(0, weight=1)

charge_limit_label = tk.Label(user_inputs_frame, text="Charge Limit")
charge_limit_input = tk.Text(user_inputs_frame, height=1)
charge_limit_label.grid(row=0, column=0, sticky="w")
charge_limit_input.grid(row=0, column=1, sticky="nsew")

present_soc_label = tk.Label(user_inputs_frame, text="Present SOC")
present_soc_label.config(state=tk.DISABLED)
present_soc_input = tk.Text(user_inputs_frame, height=1)
present_soc_input.config(state=tk.DISABLED)
present_soc_label.grid(row=1, column=0, sticky="w")
present_soc_input.grid(row=1, column=1, sticky="nsew")


max_discharge_power_label = tk.Label(user_inputs_frame, text="Max Discharge Power (KW)")
max_discharge_power_label.config(state=tk.DISABLED)
max_discharge_power_input = tk.Text(user_inputs_frame, height=1)
max_discharge_power_input.config(state=tk.DISABLED)
max_discharge_power_label.grid(row=2, column=0, sticky="w")
max_discharge_power_input.grid(row=2, column=1, sticky="nsew")

max_charge_power_label = tk.Label(user_inputs_frame, text="Max Charge Power")
max_charge_power_input = tk.Text(user_inputs_frame, height=1)

max_charge_power_label.grid(row=3, column=0, sticky="w")
max_charge_power_input.grid(row=3, column=1, sticky="nsew")

server_response_box = tk.Text(root)
server_response_box.grid(row=2, column=0, columnspan=2, sticky="nsew")


root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)


sync_with_client()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
