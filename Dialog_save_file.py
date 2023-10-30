from tkinter import filedialog
import json


def save_file(data):
    """Функция открытия диалогового окна для ввода имени файла в формате JSON для сохранения рациона"""
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Ration Files", "*.json")])
    # Выбранное имя файла будет храниться в переменной file_path
    if file_path:
        with open(file_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


def open_file():
    """Функция открытия диалогового окна для загрузки файла сохраненного в формате JSON"""
    file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("Ration Files", "*.json")])
    # Выбранное имя файла будет храниться в переменной file_path
    if file_path:
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        return None
