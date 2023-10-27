
from tkinter import *
from tkinter import filedialog
from tkinter import ttk

import re
import sys
import ntpath
import numpy as np
import pandas as pd
import threading

from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib
matplotlib.use("TkAgg")


def plot_init() -> None:
    global canvas, figure, axes

    canvas = FigureCanvasTkAgg(figure, master=window)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, window)
    toolbar.update()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    if isinstance(axes, np.ndarray):
        [ax.clear() for ax in axes.flat]
        [ax.tick_params(axis='x', labelrotation=45) for ax in axes.flat]

        _, columns = data.shape
        for i in range(1, columns):
            [ax.plot(data[:, 0], data[:, i]) for ax in axes.flat[:2]]
        axes.flat[0].set_xlim((data[0, 0], data[100, 0]))


def load():
    global header, data
    path.set(filedialog.askopenfilename(title="Выберите файл", filetypes=[("CSV", "*.csv")], ))
    p = path.get()
    if not p:
        return

    csv = pd.read_csv(p)
    header = csv.columns
    data = csv.to_numpy()

    global window, figure, axes
    window = Toplevel(root)
    window.title('Графики')
    figure, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))
    plot_init()
    plt.tight_layout()


def repair():
    global window, figure, axes
    if isinstance(window, Toplevel):
        window.destroy()

    window = Toplevel(root)
    window.title('Графики')
    figure, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 4 * 2))
    plot_init()

    progress = IntVar(value=0)
    window2 = Toplevel(root)
    window2.title('Подождите...')
    window2.geometry('{:.0f}x{:.0f}'.format(400, 35))
    window2.resizable(width=False, height=False)
    window2.attributes("-topmost", True)
    s = ttk.Style()
    s.theme_use("default")
    s.configure("TProgressbar", thickness=33)
    progressbar = ttk.Progressbar(window2, orient="horizontal", variable=progress, length=100, style="TProgressbar")
    progressbar.pack(side=TOP, fill=BOTH, padx=1, pady=1)

    def progress_callback(*_):
        if progress.get() >= 100:
            window2.destroy()

    progress.trace('w', progress_callback)

    def do_repair():

        ts = data[:, 0].copy()

        d = np.argwhere(np.logical_not(np.isclose(np.diff(np.insert(data[:, 0], 0, -sys.maxsize)), 0.)))[:, 0]

        avg_step = 0
        for k, (i, j) in enumerate(zip(d[1:-1], d[2:])):
            ts[i:j] = np.linspace(ts[i], ts[j], j - i, endpoint=False)
            avg_step += ts[i + 1] - ts[i]

            if not (k % int(len(d) // 1000 + 1)):
                p = (k + 1) / (len(d) - 1) * 100
                print('\r{:.2f} %'.format(p), flush=True, end='     ')
                progress.set(int(p))

        avg_step /= len(d) - 1
        ts[:d[1]] = ts[d[1]] + avg_step * np.arange(-d[1], 0)
        ts[d[-1]:] = ts[d[-1]] + avg_step * np.arange(0, len(ts) - d[-1])

        print('\r100.00 %')
        progress.set(100)

        data[:, 0] = ts

        repaired.set(value=True)

    threading.Thread(target=do_repair).start()


def path_leaf(_path: str):
    head, tail = ntpath.split(_path)
    return tail or ntpath.basename(head)


def save():
    export = filedialog.asksaveasfilename(title="Сохранить как...", filetypes=[("CSV", "*.csv")], defaultextension='.csv',
                                          initialfile=re.sub(r'\.csv', '_fixed.csv', path_leaf(path.get())))
    if export:
        df = pd.DataFrame(data, columns=header)
        df.to_csv(export, header=True, index=False)


def destroy():
    if isinstance(window, Toplevel):
        window.destroy()
    plt.close(figure)
    root.destroy()
    root.quit()


if __name__ == '__main__':
    root = Tk()
    root.title('GUI')
    root.geometry('{:.0f}x{:.0f}+{}+{}'.format(250, 175, 5, 10))
    root.resizable(width=False, height=False)
    root.columnconfigure(index=0, weight=1)

    header = []
    data: np.ndarray = np.array([])

    path = StringVar()
    button_load = Button(root, text="Открыть файл", width=25, height=1, cursor='hand2', state=NORMAL)
    button_load.grid(row=0, column=0, ipadx=5, ipady=10, pady=5)
    button_load.configure(command=load)

    def path_callback(*_):
        if path.get():
            button_repair.configure(state=NORMAL)
            button_save.configure(state=NORMAL)

    path.trace('w', path_callback)

    window, canvas, figure, axes = None, None, None, None

    repaired = BooleanVar(value=False)

    def repaired_callback(*_):
        if repaired.get() and isinstance(axes, np.ndarray) and isinstance(canvas, FigureCanvasTkAgg):
            _, columns = data.shape
            for i in range(1, columns):
                [ax.plot(data[:, 0], data[:, i]) for ax in axes.flat[2:4]]
            axes.flat[2].set_xlim((data[0, 0], data[100, 0]))
            canvas.draw()

    repaired.trace('w', repaired_callback)

    button_repair = Button(root, text="Исправить баг", width=25, height=1, cursor='hand2', state=DISABLED)
    button_repair.grid(row=1, column=0, ipadx=5, ipady=10, pady=5)
    button_repair.configure(command=repair)

    button_save = Button(root, text="Сохранить", width=25, height=1, cursor='hand2', state=DISABLED)
    button_save.grid(row=2, column=0, ipadx=5, ipady=10, pady=5)
    button_save.configure(command=save)

    root.protocol("WM_DELETE_WINDOW", destroy)

    root.mainloop()
