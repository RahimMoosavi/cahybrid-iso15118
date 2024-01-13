import json
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
    return lambda: (
        process.terminate(),
        process.wait() if process and process.poll() is None else None,
    )


def on_closing():
    if server_terminator:
        print("Terminating server...")
        client_button.config(state=tk.DISABLED)
        server_terminator()
        client_button.config(state=tk.NORMAL)
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
    global server_terminator
    global sync_time
    global delayed_run
    global correct_sync_time

    if client_button.cget("text") == client_button_text_status[0]:
        is_plugged_checkbox.select()
        delayed_run = True
        client_response_box.delete("1.0", "end")
        client_button.config(text=client_button_text_status[1])
        server_terminator = run_script(client_response_box)
        change_all_input_status("disabled")
    else:
        is_plugged_checkbox.deselect()
        sync_time = correct_sync_time
        client_button.config(state=tk.DISABLED)
        if server_terminator:
            print("Terminating Client...")
            server_terminator()
        client_button.config(state=tk.NORMAL)
        client_button.config(text=client_button_text_status[0])
        save_communications(client_response_box.get("1.0", "end-1c"))
        client_response_box.delete("1.0", "end")
        change_all_input_status("normal")
        server_terminator = None


def change_all_input_status(status):
    max_discharge_power_input.config(state=status)
    max_discharge_power_label.config(state=status)
    present_soc_input.config(state=status)
    present_soc_label.config(state=status)
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


def update_communication_file(data, key, value):
    with open(communication_file, "w") as f:
        data[key] = int(value)
        json.dump(data, f)


def sync_with_server():
    global sync_time
    global large_delay_time
    global light_delay_time
    global delayed_run
    try:
        with open(communication_file, "r") as f:
            data = json.load(f)
            max_charge_power_input.config(state=tk.NORMAL)
            max_charge_power_input.delete("1.0", tk.END)
            max_charge_power_input.insert("1.0", data["max_charge_power"])
            max_charge_power_input.config(state=tk.DISABLED)

            if max_discharge_power_input.get("1.0", "end-1c") == "":
                max_discharge_power_input.delete("1.0", tk.END)
                max_discharge_power_input.insert("1.0", data["max_discharge_power"])
            elif not server_terminator:
                update_communication_file(
                    data,
                    "max_discharge_power",
                    max_discharge_power_input.get("1.0", "end-1c"),
                )

            # TODO: SHould check if the connection is happened correctly
            if present_soc_input.get("1.0", "end-1c") == "":
                present_soc_input.delete("1.0", tk.END)
                present_soc_input.insert("1.0", data["present_soc"])
            if server_terminator and data["present_soc"] < 100:
                if delayed_run:
                    sync_time = large_delay_time
                    delayed_run = False
                else:
                    update_communication_file(
                        data,
                        "present_soc",
                        min(data["present_soc"] + increment_charge_value, 100),
                    )
                    present_soc_input.config(state=tk.NORMAL)
                    present_soc_input.delete("1.0", tk.END)
                    present_soc_input.insert("1.0", min(data["present_soc"], 100))
                    present_soc_input.config(state=tk.DISABLED)
                    if sync_time == large_delay_time:
                        sync_time = light_delay_time
            elif not server_terminator:
                update_communication_file(
                    data, "present_soc", present_soc_input.get("1.0", "end-1c")
                )

    except FileNotFoundError:
        tk.messagebox.showerror("Error", "File not found")
    root.after(sync_time, sync_with_server)


delayed_run = False
increment_charge_value = 10
communication_file = "communication.json"
correct_sync_time = 500
light_delay_time = 500
large_delay_time = 6000
sync_time = correct_sync_time

# Load env environment
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

root = tk.Tk()

root.title("EVCC Application")
root.geometry("820x850")

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
message_log_exi_checkbox = ttk.Checkbutton(
    config_frame,
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
    config_frame,
    values=log_level_options,
    textvariable=selected_option,
    state="readonly",
)
log_level_select.grid(row=2, column=0, sticky="nsew")
log_level_select.bind("<<ComboboxSelected>>", on_log_level_changed)


# Inputs frame

user_inputs_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
user_inputs_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
user_inputs_frame.grid_columnconfigure(0, weight=1)

present_soc_label = tk.Label(user_inputs_frame, text="Present SOC")
present_soc_input = tk.Text(user_inputs_frame, height=1)
present_soc_label.grid(row=0, column=0, sticky="w")
present_soc_input.grid(row=0, column=1, sticky="nsew")

max_discharge_power_label = tk.Label(user_inputs_frame, text="Max Discharge Power")
max_discharge_power_input = tk.Text(user_inputs_frame, height=1)

max_discharge_power_label.grid(row=1, column=0, sticky="w")
max_discharge_power_input.grid(row=1, column=1, sticky="nsew")

max_charge_power_label = tk.Label(user_inputs_frame, text="Max Charge Power")
max_charge_power_label.config(state=tk.DISABLED)
max_charge_power_input = tk.Text(user_inputs_frame, height=1)
max_charge_power_input.config(state=tk.DISABLED)
max_charge_power_label.grid(row=2, column=0, sticky="w")
max_charge_power_input.grid(row=2, column=1, sticky="nsew")


client_response_box = tk.Text(root)
client_response_box.grid(row=2, column=0, columnspan=2, sticky="nsew")


status_bar = ttk.Frame(root)
status_bar.grid(row=3, column=0, columnspan=2, sticky="nsew")


# battery_value_label = tk.Label(status_bar, text=f"Battery : {random.randint(0 , 100)}%")
# battery_value_label.grid(row=0, column=0, sticky="w")

is_plugged_label = tk.Label(status_bar, text="Is Plugged : ")
is_plugged_label.grid(row=0, column=1, sticky="nsew")
is_plugged_checkbox = tk.Checkbutton(status_bar, state="disabled")
is_plugged_checkbox.grid(row=0, column=2, sticky="nsew")
status_bar.grid_columnconfigure(0, weight=1)


root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

sync_with_server()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
