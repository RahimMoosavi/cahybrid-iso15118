import tkinter as tk

def main():
    print("Before creating Tk instance")
    root = tk.Tk()
    print("After creating Tk instance")

    w = tk.Label(root, text="Hello, world!")
    w.pack()
    root.mainloop()

    print("Before mainloop")
    root.mainloop()
    print("After mainloop")

if __name__ == "__main__":
    main()
