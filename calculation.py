import json
import math
import locale
import os
import sys
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Treeview
from tkinter import messagebox as mb

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import psutil
from datetime import datetime
from pathlib import Path

import webbrowser
from ttkthemes import ThemedStyle

from cryptography.fernet import Fernet

import Save_ration_in_Excel
import Dialog_save_file
import Help_messages

# создаем словарь, куда ниже собираем результаты расчета питательных веществ в собранном рационе
t2 = []
t4 = {}
data_feeds = {}  # Справочник с кормами
data_minerals = {}  # Справочник с минеральными веществами
data_prices = {}  # Справочник с ценами кормов и минеральных веществ

psv, nsc, need_rp = 0.0, 0.0, 0.0

"""Словарь, куда загружается описание параметров питательности кормов из файла JSON"""
data_discriptions_parameters_feeds = {}

t_minerals = []
list_filter = ["Все элементы"]
icon_main = "icon.ico"
step = 65
data_status = False
code_status = False
data_control = None
# Ключ шифрования
key_gen = b'eHA0hjPHvLMV1RkRS5nRghzdjHsm97NBwC34eLe13bQ='
# Для смены ключа шифрования нужно раскомментировать нижние две строки, запустить программу, скопировать и вставить
# новый ключ в переменную key_gen и закомментировать строки. Этот же ключ нужно заменить в файле по генерации
# ключа CodeActivation в др. проекте
# key = Fernet.generate_key()
# print(key)

# Получаем путь к директории, где находится исполняемый файл (exe)
executable_directory = sys.argv[0]
current_directory = os.path.dirname(executable_directory)

# Задаем имя папки, где будут размещены файлы с картинками
folder_pictures = "Pictures"
# Задаем имя папки, где будут размещены файлы с данными
folder_data = "Data"

# icon_path = os.path.join(os.path.dirname(sys.executable), 'icon.ico')
# app.iconbitmap(icon_path)


# Проверяем наличие и действительность кода активации
def check_right_user():
    global data_status, code_status, data_control

    file_path = Path('encrypted.json') # Файл, где в зашифрованном виде хранится код активации

    if file_path.is_file():
        # Создаем объект Fernet с использованием ключа шифрования
        cipher_suite = Fernet(key_gen)

        # Загружаем зашифрованные данные из файла
        with open('encrypted.json', 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()

            # Расшифровываем данные в JSON строку
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            # Преобразуем JSON строку в словарь
            data_active = json.loads(decrypted_data.decode('utf-8'))

            input_code = data_active["code_activation"]
            l = input_code.split('-', maxsplit=-1)
            m = [i[1:len(i) - 1] for i in l]
            l.clear()
            l = [int(i, 16) for i in m]

            l = [i // 10 for i in l]
            m.clear()
            m = [hex(int(l[i]))[2:] for i in range(6)]
            m = [str(i).upper() for i in m]
            mac = "-".join(m)
            d = [str(l[i]) for i in range(6, len(l))]
            data_control = "-".join(d)
            data_control = datetime.strptime(data_control, '%Y-%m-%d')
            if data_control > datetime.today():
                data_status = True

            mac_addresses = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK:
                        mac_addresses.append(addr.address)
            if mac in mac_addresses:
                code_status = True

    if not data_status or not code_status:
        # root.configure(bg="red")
        # Пункты меню и кнопки недоступны в демо режиме
        filemenu.entryconfig("Открыть расчет...", state="disabled")
        filemenu.entryconfig("Сохранить расчет...", state="disabled")
        filemenu.entryconfig("Экспорт в Excel", state="disabled")
        # Страница "Расчеты"
        btn_save_ration.config(state="disabled")
        btn_load_ration.config(state="disabled")
        btn_export_ration.config(state="disabled")
        # Страница "Корма"
        btn_change_feed.config(state="disabled")
        btn_new_feed.config(state="disabled")
        btn_copy_feed.config(state="disabled")
        btn_delete.config(state="disabled")
        # Страница "Минералы"
        btn_change_mineral.config(state="disabled")
        btn_new_mineral.config(state="disabled")
        btn_copy_mineral.config(state="disabled")
        btn_delete_mineral.config(state="disabled")

        return


# Сохраняем код активации в зашифрованный файл
def save_code_activation(code, window):
    global key_gen

    # Создаем объект Fernet с использованием ключа шифрования
    cipher_suite = Fernet(key_gen)

    if len(code) > 0:
        result_code = {"code_activation": code}
        # Преобразуем словарь в JSON-строку
        json_data = json.dumps(result_code)
        # Шифруем данные
        encrypted_data = cipher_suite.encrypt(json_data.encode('utf-8'))
        # Сохраняем зашифрованные данные в файл
        with open('encrypted.json', 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

        window.destroy()
    else:
        mb.showinfo("Предупреждение", """Не введен код активации программы!""")


# Создаем код запроса в форме "Активация программы"
def creat_code_question() -> str:
    global step
    mac_addresses, l = [], []
    result_string = ""
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac_addresses.append(addr.address)
    if len(mac_addresses) > 0:
        mac_str = mac_addresses[0]

        if mac_str.count('-') == 5:
            l = mac_str.split('-', maxsplit=-1)
        elif mac_str.count(':') == 5:
            l = mac_str.split(':', maxsplit=-1)

        l = [str(int(i, 16)) for i in l]
        m = []
        for i in l:
            _str = ""
            for j in range(len(i)):
                _str += chr(int(i[j]) + step)
            m.append(_str)

        result_string = "-".join(m)
    return result_string


# Открываем форму для активации программы
def activation_program():
    global icon_main

    def copy_text():
        """Копируем текст в буфер обмена"""
        selected_text = entry_question.get()
        forma.clipboard_clear()
        forma.clipboard_append(selected_text)
        forma.update()

    def popup_menu_copy(event):
        """Открываем контекстное меню по правому клику мыши в поле с кодом запроса"""
        context_menu_copy.post(event.x_root, event.y_root)

    def paste_text():
        """Вставляем текст из буфера обмена"""
        text = forma.clipboard_get()
        entry_code.insert(INSERT, text)

    def popup_menu_paste(event):
        """Открываем контекстное меню по правому клику мыши в поле ввода кода активации"""
        context_menu_paste.post(event.x_root, event.y_root)

    def callback(event):
        webbrowser.open_new(r"https://2c-animal.ru/buy-program")

    forma = Toplevel(root)
    w = forma.winfo_screenwidth()
    h = forma.winfo_screenheight()
    w = w // 2  # середина экрана
    h = h // 2
    w = w - 200  # смещение от середины
    h = h - 250
    """Устанавливаем размер окна"""
    forma.geometry(f'500x250+{w}+{h}')
    forma.title('Активация программы')
    forma.iconbitmap(icon_main)

    """Делаем окно модальным, то есть основное окно не доступно, пока мы не закроем это"""
    forma.transient(root)
    forma.grab_set()
    forma.focus_set()

    label_name_act = Label(forma, text="Активация программы", font=("Arial", 12, "bold"))
    label_name_act.place(x=10, y=20, width=300, height=20)

    if not data_status or not code_status:
        """Добавляем на форму текст и поле для отображения кода запроса"""
        label_question = Label(forma, text="1. Скопируйте код запроса (справа)", font=("Arial", 11))
        label_question.place(x=10, y=50, width=250, height=20)
        str_question = StringVar()
        str_question.set(creat_code_question())
        entry_question = Entry(forma, textvariable=str_question)
        entry_question.place(x=280, y=50, width=200, height=20)
        """Создаём контекстное меню и назначаем функцию для поля кода запроса по правому клику мыши"""
        context_menu_copy = Menu(forma, tearoff=0)
        context_menu_copy.add_command(label="Копировать", command=copy_text)
        entry_question.bind("<Button-3>", popup_menu_copy)

        """Добавляем на форму текст и поле для отображения адреса e-mail для отправки запроса"""
        label_email = Label(forma, text="2. Отправьте код на e-mail", font=("Arial", 11), anchor=W)
        label_email.place(x=10, y=80, width=250, height=25)
        str_email = StringVar()
        str_email.set("animal-computing@yandex.ru")
        entry_email = Entry(forma, textvariable=str_email)
        entry_email.place(x=280, y=80, width=200, height=25)

        """Добавляем на форму текст c указанием оплаты"""
        txt = '3. Оплатите лицензию (на 1 год) и подтвердите оплату по e-mail'
        label_payment = Label(forma, text=txt, cursor="hand2", font=("Arial", 11), foreground='blue', anchor=W)
        label_payment.configure(font="Arial 11 underline")
        label_payment.place(x=10, y=110, width=450, height=25)
        label_payment.bind("<Button-1>", callback)

        """Добавляем на форму текст и поле для ввода кода активации"""
        label_code = Label(forma, text="4. Вставьте из ответного письма код активации и сохраните:", font=("Arial", 11), anchor=W)
        label_code.place(x=10, y=140, width=450, height=25)

        str_code = StringVar()
        entry_code = Entry(forma, textvariable=str_code)
        entry_code.place(x=20, y=170, width=350, height=25)
        """Создаём контекстное меню и назначаем функцию для поля ввода по правому клику мыши"""
        context_menu_paste = Menu(forma, tearoff=0)
        context_menu_paste.add_command(label="Вставить", command=paste_text)
        entry_code.bind("<Button-3>", popup_menu_paste)

        btn_save_code = Button(forma, text="Сохранить", width=15,
                               command=lambda: save_code_activation(str_code.get(), forma))
        btn_save_code.place(x=380, y=170, width=100, height=25)

        """Добавляем на форму текст о перезапуске программы"""
        label_code = Label(forma, text="5. Перезапустите программу", font=("Arial", 11),
                           anchor=W)
        label_code.place(x=10, y=200, width=450, height=25)
    else:
        txt = "Программа активирована до " + str(data_control)
        label_info = Label(forma, text=txt, font=("Arial", 10), fg="green", anchor=W)
        label_info.place(x=10, y=80, width=300, height=25)


# Проверка ввода пользователем числа с плавающей точкой
def validate_input(p):
    """Функция контроля ввода пользователем числа с плавающей точкой"""
    # P - предполагаемый ввод
    try:
        if p == "" or p == "-" or isinstance(float(p), float):
            return True
        else:
            return False
    except ValueError:
        return False


# Проверка ввода пользователем целого числа
def validate_input_int(P):
    """Функция контроля ввода пользователем целого числа"""
    # P - предполагаемый ввод
    if P == "" or P.isdigit():
        return True
    else:
        return False


# Конвертируем число с запятой в число с точкой
def convert_number(num_str) -> float:
    num_str = num_str.replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        mb.showerror("Ошибка", "Недопустимое значение!")
        return None


# Расчет необходимого СУХОГО ВЕЩЕСТВА - Источник формулы указан внутри
def dry_material() -> float:
    # a = (0.0968 * weight_live.get() ** 0.75 + 0.372 * fat_milk.get() * milk_yield.get() / 4)
    # a = a * (1 - math.exp(-0.192 * (week_lactation.get() + 3.67)))
    # https://agrovesti.net/lib/tech/feeding-tech/polnotsennoe-kormlenie-molochnogo-skota-osnova-realizatsii
    # -geneticheskogo-potentsiala-produktivnosti-prilozhenie.html
    a = 0.0
    if weight_live.get() > 0.0 or milk_yield.get() > 0.0:
        a = 0.011 * weight_live.get() + 0.3 * milk_yield.get() + 4.0
    return a


# Расчет потребности в ОБМЕННОЙ ЭНЕРГИИ - Рядчиков "Основы кормления с/х животных", 2012г., стр.170-171
def change_energy() -> float:
    pd, st = 0, 0
    pd = 0.54 * weight_live.get() ** 0.75
    if days_pregnancy.get() > 190:
        st = (2 * 0.00159 * days_pregnancy.get() - 0.0352) / 0.14 * 4.184

    lact = (0.389 * fat_milk.get() + 0.229 * protein.get() + 0.8) * 1.61 * milk_yield.get()
    return pd + st + lact


# Расчет чистой энергии лактации (ЧЭЛ, NEL) - Рядчиков "Основы кормления с/х животных", 2012г., стр.170-171
def pure_lactation_energy() -> float:
    pd, st = 0.0, 0.0

    pd = 0.293 * weight_live.get() ** 0.75
    if 250 < days_pregnancy.get() < 270:
        st = 13
    elif 270 < days_pregnancy.get():
        st = 18

    lact = (0.389 * fat_milk.get() + 0.229 * protein.get() + 0.8) * milk_yield.get()
    return pd + st + lact


# Расчет потребности в ОБМЕННОМ ПРОТЕИНЕ - Рядчиков "Основы кормления с/х животных", 2012г., стр.138-141
def need_change_protein() -> float:
    pd, st, lact = 0, 0, 0
    # потребность в ОБ на эндогенные (мочевина, креатин, креатинин) затраты основного обмена белка
    pd_1 = 4.1 * weight_live.get() ** 0.5
    pd_2 = 0.3 * weight_live.get() ** 0.6  # потребность в ОБ на поверхностный чистый белок
    pd_3 = 1.9 * 6.25 * psv * 0.4  # Чистый эндогенный белок (ЧЭБ) переднего отдела пищеварительного тракта
    # Расчет потребности в бактериальном ОП
    bact = 130 * 0.8 * (psv * 0.75 * 0.965 * 0.92) * 0.8 * 0.8
    # Расчет потребности в ОБ для метаболического белка кала
    pd_4 = 30 * psv - 0.5 * (bact / 0.8 - bact)
    """обменный протеин на поддержание"""
    pd = pd_1 + pd_2 + pd_3 / 0.67 + pd_4
    """обменный протеин на рост / потерю веса"""
    if weight_gain.get() > 0:
        rost = 225 * weight_gain.get()
    else:
        rost = 144 * weight_gain.get()
    """обменный протеин на стельность"""
    if 190 < days_pregnancy.get() < 280:
        st = (6.25 * weight_live.get() / 100 / 45) / 0.33
    """обменный протеин на лактацию"""
    lact = 0.95 * protein.get() * 10 * milk_yield.get() / 0.67
    total = pd + rost + st + lact
    return total


# Расчет потребности в СЫРОМ ПРОТЕИНЕ - СТАРАЯ
def need_raw_protein_old() -> float:
    """Функция расчета потребности в сыром протеине"""
    return need_change_protein() / 0.65


# Функция расчета потребности в сыром протеине - Рядчиков "Основы кормления с/х животных", 2012г., стр.173-175
def need_raw_protein() -> float:
    """Функция расчета потребности в сыром протеине"""
    pd, lact, rost, st = 0.0, 0.0, 0.0, 0.0
    # На поддержание жизни
    pd_1 = 0.01 * psv * 1000.0
    pd_2 = 2.75 * weight_live.get() ** 0.5
    pd_3 = 0.2 * weight_live.get() ** 0.6
    pd = pd_1 + pd_2 + pd_3
    # На производство молока (лактацию)
    lact = 0.95 * protein.get() * 10 * milk_yield.get()
    # На изменение живой массы
    if weight_gain.get() > 0:
        rost = 225 * weight_gain.get()  # При приросте массы требуется протеин
    else:
        rost = 144 * weight_gain.get()  # При потере массы высвобождается протеин
    # На стельность
    if 190 < days_pregnancy.get() < 280:
        # 0,06 в формуле - это коэффициент для расчета массы теленка, как 6% от массы матери
        st = 5.0 * (weight_live.get() * 0.06) ** 0.75
    return (pd + lact + rost + st) / 0.34


# Расчет значения усвоенного протеина nXP - источник данных указан внутри
def digested_protein() -> float:
    """Функция расчета значения усвоенного протеина nXP"""
    # https://agrovesti.net/lib/tech/feeding-tech/polnotsennoe-kormlenie-molochnogo-skota-osnova-realizatsii
    # -geneticheskogo-potentsiala-produktivnosti-prilozhenie.html
    if need_rp > 0:
        return (11.93 - 6.82 * need_nrb() / need_rp) * change_energy() + 1.03 * need_nrb()
    else:
        return 0.0


# Расчет распадающегося в рубце протеина - Рядчиков "Основы кормления с/х животных", 2012г., стр.134-135
def need_rrb() -> float:
    """Функция расчета распадающегося в рубце протеина"""
    rrb = 130 * (psv * 0.75 * 0.965 * 0.92) / 0.85 / 0.9
    return rrb


# Расчет нераспадающегося в рубце протеина
def need_nrb() -> float:
    """Функция расчета нераспадающегося в рубце протеина"""
    nrb = need_rp - need_rrb()
    return nrb


# Расчет потребности в кальции - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.117
def need_calcium() -> float:
    """Функция расчета потребности в кальции"""
    pd, rost, st, lact = 0, 0, 0, 0
    weight_adult_cow = 700
    wl = weight_live.get()
    d_p = days_pregnancy.get()
    pd = 0.031 * wl
    if wl > 0:
        rost = 9.83 * weight_adult_cow ** 0.22 * wl ** (-0.22) * weight_gain.get()
    if d_p > 190:
        st = 0.02456 * (
                math.exp((0.05581 - 0.00007 * d_p) * d_p) - math.exp((0.05581 - 0.00007 * (d_p - 1)) * (d_p - 1)))
    lact = 1.3 * milk_yield.get()
    return (pd + rost + st + lact) / 0.68


# Расчет потребности в фосфоре - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.121
def need_phosphorus() -> float:
    """Функция расчета потребности в фосфоре"""
    pd, rost, st, lact = 0, 0, 0, 0
    weight_adult_cow = 700
    d_p = days_pregnancy.get()
    pd = psv + 0.002 * weight_live.get()
    wl = weight_live.get()
    if wl > 0:
        rost = (1.2 + 4.635 * weight_adult_cow ** 0.22 * wl ** (-0.22)) * weight_gain.get()
    if d_p > 190:
        st = 0.02743 * (
                math.exp((0.05527 - 0.000075 * d_p) * d_p) - math.exp((0.05527 - 0.000075 * (d_p - 1)) * (d_p - 1)))
    lact = 0.9 * milk_yield.get()
    return (pd + rost + st + lact) / 0.67


# Расчет потребности в натрии - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.128-129
def need_sodium() -> float:
    """Функция расчета потребности в натрии"""
    pd, rost, st, lact = 0, 0, 0, 0
    koef = 0.038
    d_p = days_pregnancy.get()
    t_vozd = tvozd.get()
    if (d_p == 0) or (weight_live.get() < 150):
        koef = 0.015
    if t_vozd > 25:
        koef += 0.001
    if t_vozd > 30:
        koef += 0.004
    pd = koef * weight_live.get()
    if weight_live.get() > 150:
        rost = 1.4 * weight_gain.get()
    if d_p > 190:
        st = 1.39
    lact = 0.63 * milk_yield.get()
    return (pd + rost + st + lact) / 0.91


# Расчет потребности в хлоре - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.131-132
def need_chlorine() -> float:
    """Функция расчета потребности в хлоре"""
    pd, rost, st, lact = 0, 0, 0, 0
    pd = 0.022 * weight_live.get()
    if weight_live.get() > 150:
        rost = 1.0 * weight_gain.get()
    if days_pregnancy.get() > 190:
        st = 1.0
    lact = 1.15 * milk_yield.get()
    return (pd + rost + st + lact) / 0.9


# Расчет потребности в калии - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.134
def need_kalium() -> float:
    """Функция расчета потребности в калии"""
    pd, rost, st, lact = 0, 0, 0, 0
    koef_1, koef_2 = 0.038, 6.1
    d_p = days_pregnancy.get()
    t_vozd = tvozd.get()
    if (d_p == 0) or (weight_live.get() < 150):  # Для нелактирующих коров меняем коэффициент при ПСВ рациона
        koef_2 = 2.6
    if t_vozd > 25:  # Вводим коррекцию на температуру содержания
        koef_1 += 0.04
    if t_vozd > 30:  # Вводим дополнительную коррекцию на температуру содержания
        koef_1 += 0.0036
    pd = koef_1 * weight_live.get() + koef_2 * psv
    if weight_live.get() > 150:
        rost = 1.6 * weight_gain.get()
    if days_pregnancy.get() > 190:
        st = 1.027
    lact = 1.5 * milk_yield.get()
    return (pd + rost + st + lact) / 0.9


# Расчет потребности в магнии - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.138-139
def need_magnesium() -> float:
    """Функция расчета потребности в магнии"""
    pd, st, lact = 0, 0, 0
    if weight_live.get() > 100:
        pd = 0.003 * weight_live.get()
    if days_pregnancy.get() > 190:
        st = 0.33
    lact = 0.15 * milk_yield.get()
    return (pd + st + lact) / 0.5


# Расчет потребности в сере - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.140
def need_sera() -> float:
    """Функция расчета потребности в сере"""
    global psv
    return psv * 1000 * 0.2 / 100


# Расчет потребности в кобальте - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.141
def need_cobalt() -> float:
    """Функция расчета потребности в кобальте"""
    return psv * 0.11


# Расчет потребности в меди - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.142
def need_cuprum() -> float:
    """Функция расчета потребности в меди"""
    pd = 7.0 * psv  # В источнике указаны эндогенные потери меди 7,1 мг в 1 кг живой массы тела
    # Эта зависимость расчета потребности на поддержание взята с сайта Direct Farm по адресу:
    # https://direct.farm/post/normy-potrebleniya-mineralnykh-veshchestv-krs-6818?ysclid=lo5nwu8nyy631964892
    rost = 1.5 * weight_gain.get()
    if days_pregnancy.get() < 100:
        st = 0.5
    elif 100 <= days_pregnancy.get() < 225:
        st = 1.5
    else:
        st = 2.0
    lact = 0.15 * milk_yield.get()
    cuprum = (pd + rost + st + lact) / 0.7
    return min(cuprum, 115 * psv)


# Расчет потребности в йоде - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.146
def need_iod() -> float:
    """Функция расчета потребности в йоде"""
    iod = 0.006 * weight_live.get()
    if milk_yield.get() > 0:
        iod = 0.015 * weight_live.get()
    return iod


# Расчет потребности в железе - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.147
def need_ferrum() -> float:
    """Функция расчета потребности в железе"""
    return (34 * weight_gain.get() + 1.0 * milk_yield.get()) / 0.1


# Расчет потребности в марганце - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.149
def need_marganese() -> float:
    """Функция расчета потребности в марганце"""
    st = 0
    pd = 0.002 * weight_live.get()
    rost = 0.7 * weight_gain.get()
    if days_pregnancy.get() > 190:
        st = 0.3
    lact = 0.03 * milk_yield.get()
    return (pd + rost + st + lact) / 0.0075


# Расчет потребности в селене - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.151-152
def need_selen() -> float:
    """Функция расчета потребности в селене"""
    st = 0
    pd = 0.3 * psv
    if days_pregnancy.get() > 190:
        st = 0.055
    lact = 0.017 * milk_yield.get()
    return (pd + st + lact) / 0.4


# Расчет потребности в цинке - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.153
def need_zink() -> float:
    """Функция расчета потребности в цинке"""
    rost, st = 0.0, 0.0
    pd = 0.045 * weight_live.get()
    if weight_gain.get() > 0:
        rost = 24 * weight_gain.get()
    if days_pregnancy.get() > 190:
        st = 12.0
    lact = 4.0 * milk_yield.get()
    return (pd + rost + st + lact) / 0.15


# Расчет потребности в витамине А - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.180
def need_vitamin_a() -> float:
    """Функция расчета потребности в витамине А, (МЕ)"""
    return 110.0 * weight_live.get()


# Расчет потребности в витамине D - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.181
def need_vitamin_d() -> float:
    """Функция расчета потребности в витамине D"""
    st = 0
    pd = 30.0 * weight_live.get()
    if days_pregnancy.get() > 190:
        st = 16.0 * weight_live.get()
    return pd + st


# Расчет потребности в витамине Е - "Нормы потребности молочного скота в питательных веществах. NRC", 2001г., стр.183
def need_vitamin_e() -> float:
    """Функция расчета потребности в витамине Е"""
    global psv
    st = 0
    pd = 15.0 * psv
    if days_pregnancy.get() > 190:
        st = 1.6 * weight_live.get()
    lact = 0.8 * weight_live.get()
    return pd + st + lact


# Очищаем значения в таблице Потребности в питательных веществах
def clear_all():
    for item in tree_main.get_children():
        tree_main.delete(item)


# Окрашиваем строки таблицы потребности в зависимости от значений питательности выбранного рациона
class MyTree(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Элементам с тегом green назначить зеленый фон, элементам с тегом red назначить розовый фон
        self.tag_configure('green', background='lightgreen')
        self.tag_configure('red', background='pink')
        self.tag_configure('white', background='white')
        self.tag_configure('yellow', background='yellow')

    def insert(self, parent_node, index, **kwargs):
        """Назначение тега при добавлении элемента в дерево"""

        item = super().insert(parent_node, index, **kwargs)

        values = kwargs.get('values', None)

        if values:
            if 0 < values[2] <= convert_number(str(values[6])):
                super().item(item, tag='yellow')
            elif convert_number(str(values[6])) < values[2] <= values[4]:
                super().item(item, tag='white')
            elif values[4] < values[2] < values[7]:
                super().item(item, tag='green')
            elif 0 < values[7] < values[2]:
                super().item(item, tag='red')

        return item


def format_digital(number):
    # Установка локали для форматирования чисел
    locale.setlocale(locale.LC_ALL, '')
    # Форматирование числа с разделением на триады
    formatted_number = locale.format_string("%.2f", number, grouping=True)
    return formatted_number


# Рассчитываем катионно-анионный баланс собранного рациона
def calc_cab() -> float:
    global t4
    dry, kalium, sodium, chlorine, sera = 0, 0, 0, 0, 0
    for k, v in t4.items():
        if k == 'Сухое вещество (Dry)':
            dry = v
        if "Калий" in k:
            kalium = v * 1000 / 34
        if "Натрий" in k:
            sodium = v * 1000 / 23
        if "Хлор" in k:
            chlorine = v * 1000 / 35.5
        if "Сера" in k:
            sera = v * 1000 / 32 * 2
    if dry > 0:
        return ((kalium + sodium) - (chlorine + sera)) / dry / 10.0

    return 0.0


# Рассчитываем влажность собранного рациона
def calc_tree_total() -> tuple:
    """Функция расчета влажности собранного рациона"""
    global t4
    weight, dry, total_coin = 0.0, 0.0, 0.0
    for k, v in t4.items():
        if k == 'Сухое вещество (Dry)':
            dry = v

    for k in tree_ration.get_children():
        weight += float(tree_ration.item(k)['values'][1])
        total_coin += float(tree_ration.item(k)['values'][8])

    if weight > 0:
        return round(weight, 1), round(100 - dry / weight * 100.0, 2), round(total_coin, 2)

    return 0.00, 0.00, 0.00


# Формируем кортежи данных для заполнения таблицы питательности
def calc_tuple(*args) -> tuple:
    """Функция, где формируются кортежи данных для добавления строк в таблицу расчета питательности"""
    global psv, nsc
    real_ud, need, need_ud, _min, _max = 0.0, 0.0, 0.0, 0.0, 0.0

    # psv = dry_material()
    real = round(t4.get(args[1], 0.0), 1)
    # Проверяем условие ненулевого знаменателя, когда СВ ещё не посчитано
    if t4.get('Сухое вещество (Dry)', 0.0) > 0:
        # Считаем значение показателя питательности на 1 кг СВ кормов
        real_ud = round(t4.get(args[1], 0.0) / t4.get('Сухое вещество (Dry)', 1.0), 1)

    if args[0] == 'Сухое вещество (Dry)':
        need = round(dry_material(), 1)
        _max = round(weight_live.get() * 0.035, 1)

    elif args[0] == 'Обменная энергия (ME)':
        need = round(change_energy(), 1)
        _min = round(11.2 * psv, 1)

    elif args[0] == 'Чистая энергия лактации (NEL)':
        need = round(pure_lactation_energy(), 1)
        if 0 < days_pregnancy.get() <= 100:
            _min = round(7.0 * psv, 1)
            _max = round(7.4 * psv, 1)
        elif 100 < days_pregnancy.get() <= 200:
            _min = round(6.8 * psv, 1)
            _max = round(7.0 * psv, 1)
        elif 200 < days_pregnancy.get():
            _min = round(6.5 * psv, 1)
            _max = round(6.8 * psv, 1)

    elif args[0] == 'Сырой протеин (Crude protein)':
        need = round(need_rp, 1)
        nsc -= need
        if 0 < days_pregnancy.get() <= 100:
            _min = round(160.0 * psv, 1)
            _max = round(175.0 * psv, 1)
        elif 100 < days_pregnancy.get() <= 200:
            _min = round(145.0 * psv, 1)
            _max = round(170.0 * psv, 1)
        elif 200 < days_pregnancy.get():
            _min = round(130.0 * psv, 1)
            _max = round(160.0 * psv, 1)

    elif args[0] == 'Усвоенный протеин (nXP)':
        need = round(digested_protein(), 1)
        if 0 < days_pregnancy.get() <= 100:
            _min = round(160.0 * psv, 1)
            _max = round(175.0 * psv, 1)
        elif 100 < days_pregnancy.get() <= 200:
            _min = round(145.0 * psv, 1)
            _max = round(155.0 * psv, 1)
        elif 200 < days_pregnancy.get():
            _min = round(130.0 * psv, 1)
            _max = round(140.0 * psv, 1)

    elif args[0] == 'Баланс азота в рубце (RNB)':
        need = round((need_rp - digested_protein()) / 6.25, 1)
        _min = round(psv * 1.0, 1)
        _max = round(psv * 50.0, 1)
    elif args[0] == 'Нераспадаемый в рубце протеин (RUP)':
        need = round(need_nrb(), 1)
        _max = round(psv * 400.0, 1)
    elif args[0] == 'Распадаемый в рубце протеин (RDP)':
        need = round(need_rrb(), 1)
        _max = round(psv * 650.0, 1)
    elif args[0] == 'Обменный протеин (MP)':
        need = round(need_change_protein(), 1)
    elif args[0] == 'Сырая клетчатка (Crude fiber)':
        if 0 < days_pregnancy.get() <= 100:
            need = round(152.0 * psv, 1)
            _min = round(145.0 * psv, 1)
            _max = round(160.0 * psv, 1)
        elif 100 < days_pregnancy.get() <= 200:
            need = round(180.0 * psv, 1)
            _min = round(170.0 * psv, 1)
            _max = round(190.0 * psv, 1)
        elif 200 < days_pregnancy.get():
            need = round(210.0 * psv, 1)
            _min = round(200.0 * psv, 1)
            _max = round(220.0 * psv, 1)
    elif args[0] == 'Нейтрально-детергентная клетчатка (NDF)':
        if 0 < days_pregnancy.get() <= 200:
            need = round(320.0 * psv, 1)
            _min = round(280.0 * psv, 1)
            _max = round(360.0 * psv, 1)
        elif 200 < days_pregnancy.get():
            need = round(380.0 * psv, 1)
            _min = round(360.0 * psv, 1)
            _max = round(400.0 * psv, 1)
        nsc -= need
    elif args[0] == 'Кислотно-детергентная клетчатка (ADF)':
        need = round(psv * 200.0, 1)
        _min = round(psv * 190.0, 1)
        _max = round(psv * 210.0, 1)
    elif args[0] == 'Сырой жир (Crude fat)':
        need = round(psv * 50.0, 1)
        _min = round(psv * 30.0, 1)
        _max = round(psv * 70.0, 1)
        nsc -= need
    elif args[0] == 'Сырая зола (Crude ash)':
        need = 0.0  # Пока не знаю формулу
        _max = round(psv * 100.0, 1)
        nsc -= need
    elif args[0] == 'Неструктурные углеводы (NSC)':
        need = round(psv * 50.0, 1)
        nsc += need
        if week_lactation.get() > 0 or milk_yield.get() > 0:
            _max = round(psv * 440.0, 1)
        else:
            _max = round(psv * 270.0, 1)
    elif args[0] == 'Безазотистые экстрактивные вещества (NFC)':
        need = round(nsc, 1)
    elif args[0] == 'Крахмал (Starch)':
        if 0 < week_lactation.get() * 7 <= 45:
            need = round(psv * 235.0, 1)
            _min = round(psv * 220.0, 1)
            _max = round(psv * 250.0, 1)
        elif 45 < week_lactation.get() * 7 <= 150:
            need = round(psv * 250.0, 1)
            _min = round(psv * 220.0, 1)
            _max = round(psv * 280.0, 1)
        elif 150 < week_lactation.get() * 7 <= 250:
            need = round(psv * 205.0, 1)
            _min = round(psv * 180.0, 1)
            _max = round(psv * 230.0, 1)
        elif 250 < week_lactation.get():
            need = round(psv * 185.0, 1)
            _min = round(psv * 170.0, 1)
            _max = round(psv * 200.0, 1)
    elif args[0] == 'Сахар (Sugar)':
        need = round(psv * 55.0, 1)
        _min = round(psv * 20.0, 1)
        _max = round(psv * 90.0, 1)
    elif args[0] == 'Кальций (Ca)':
        need = round(need_calcium(), 1)
    elif args[0] == 'Фосфор (Ph)':
        need = round(need_phosphorus(), 1)
        _max = round(0.01 * psv * 1000.0, 1)
    elif args[0] == 'Магний (Mg)':
        need = round(need_magnesium(), 1)
        _max = round(0.45 / 100 * psv * 1000.0, 1)
    elif args[0] == 'Калий (K)':
        need = round(need_kalium(), 1)
        _max = round(0.03 * psv * 1000.0, 1)
    elif args[0] == 'Натрий (Na)':
        need = round(need_sodium(), 1)
    elif args[0] == 'Хлор (Cl)':
        need = round(need_chlorine(), 1)
    elif args[0] == 'Сера (S)':
        need = round(need_sera(), 1)
        _min = round(0.08 / 100 * psv * 1000.0, 1)
        _max = round(0.15 / 100 * psv * 1000.0, 1)
    elif args[0] == 'Кобальт (Co)':
        need = round(need_cobalt(), 1)
        _max = round(5.0 / 100 * psv * 1000.0, 1)
    elif args[0] == 'Медь (Cu)':
        need = round(need_cuprum(), 1)
        _min = round(4.0 * psv, 1)
        _max = round(115.0 * psv, 1)
    elif args[0] == 'Йод (I)':
        need = round(need_iod(), 1)
        _min = round(0.1 * psv, 1)
        _max = round(50 * psv, 1)
    elif args[0] == 'Железо (Fe)':
        need = round(need_ferrum(), 1)
        _max = round(1000 * psv, 1)
    elif args[0] == 'Марганец (Mn)':
        need = round(need_marganese(), 1)
        _max = round(1000.0 * psv, 1)
    elif args[0] == 'Селен (Se)':
        need = round(need_selen(), 1)
        _max = round(2.0 * psv, 1)
    elif args[0] == 'Цинк (Zn)':
        need = round(need_zink(), 1)
        _max = round(500.0 * psv, 1)
    elif args[0] == 'Молибден (Mo)':
        _max = round(6.0 * psv, 1)
    elif args[0] == 'Витамин А':
        need = round(need_vitamin_a() / 1000, 1)
    elif args[0] == 'Витамин D':
        need = round(need_vitamin_d() / 1000, 1)
    elif args[0] == 'Витамин E':
        need = round(need_vitamin_e() / 1000, 1)

    # Считаем значение показателя питательности на 1 кг необходимого СВ кормов
    if psv > 0:
        need_ud = round(need / psv, 1)

    return args[0], args[2], real, real_ud, need, need_ud, _min, _max


# Рассчитываем показатели таблицы потребности в питательных веществах
def click_button():
    global psv, nsc, need_rp

    clear_all()
    need_sum = []  # создаем список, в который собираем кортежи данных для отображения в итоговой таблице

    psv = dry_material()
    nsc = dry_material() * 1000.0
    need_rp = need_raw_protein()
    need_sum.append(calc_tuple('Сухое вещество (Dry)', 'Сухое вещество (Dry)', 'кг'))
    need_sum.append(calc_tuple('Обменная энергия (ME)', 'Обменная энергия (ME)', 'МДж'))
    need_sum.append(calc_tuple('Чистая энергия лактации (NEL)', 'Чистая энергия лактации (NEL)', 'МДж'))
    need_sum.append(calc_tuple('Сырой протеин (Crude protein)', 'Сырой протеин (Crude protein)', 'г'))
    need_sum.append(calc_tuple('Усвоенный протеин (nXP)', 'Усвоенный протеин (nXP)', 'г'))
    need_sum.append(calc_tuple('Баланс азота в рубце (RNB)', 'Баланс азота в рубце (RNB)', 'г'))
    need_sum.append(calc_tuple('Нераспадаемый в рубце протеин (RUP)', 'Нераспадаемый в рубце протеин (RUP)', 'г'))
    need_sum.append(calc_tuple('Распадаемый в рубце протеин (RDP)', 'Распадаемый в рубце протеин (RDP)', 'г'))
    need_sum.append(calc_tuple('Обменный протеин (MP)', 'Обменный протеин (MP)', 'г'))
    need_sum.append(calc_tuple('Сырая клетчатка (Crude fiber)', 'Сырая клетчатка (Crude fiber)', 'г'))
    need_sum.append(calc_tuple('Нейтрально-детергентная клетчатка (NDF)', 'Нейтрально-детергентная клетчатка (NDF)', 'г'))
    need_sum.append(calc_tuple('Кислотно-детергентная клетчатка (ADF)', 'Кислотно-детергентная клетчатка (ADF)', 'г'))
    need_sum.append(calc_tuple('Сырой жир (Crude fat)', 'Сырой жир (Crude fat)', 'г'))
    need_sum.append(calc_tuple('Сырая зола (Crude ash)', 'Сырая зола (Crude ash)', 'г'))
    need_sum.append(calc_tuple('Неструктурные углеводы (NSC)', 'Неструктурные углеводы (NSC)', 'г'))
    need_sum.append(calc_tuple('Безазотистые экстрактивные вещества (NFC)', 'Безазотистые экстрактивные вещества (NFC)', 'г'))
    need_sum.append(calc_tuple('Крахмал (Starch)', 'Крахмал (Starch)', 'г'))
    need_sum.append(calc_tuple('Сахар (Sugar)', 'Сахар (Sugar)', 'г'))
    need_sum.append(calc_tuple('Кальций (Ca)', 'Кальций (Ca)', 'г'))
    need_sum.append(calc_tuple('Фосфор (Ph)', 'Фосфор (Ph)', 'г'))
    need_sum.append(calc_tuple('Магний (Mg)', 'Магний (Mg)', 'г'))
    need_sum.append(calc_tuple('Калий (K)', 'Калий (K)', 'г'))
    need_sum.append(calc_tuple('Натрий (Na)', 'Натрий (Na)', 'г'))
    need_sum.append(calc_tuple('Хлор (Cl)', 'Хлор (Cl)', 'г'))
    need_sum.append(calc_tuple('Сера (S)', 'Сера (S)', 'г'))
    need_sum.append(calc_tuple('Кобальт (Co)', 'Кобальт (Co)', 'мг'))
    need_sum.append(calc_tuple('Медь (Cu)', 'Медь (Cu)', 'мг'))
    need_sum.append(calc_tuple('Йод (I)', 'Йод (I)', 'мг'))
    need_sum.append(calc_tuple('Железо (Fe)', 'Железо (Fe)', 'мг'))
    need_sum.append(calc_tuple('Марганец (Mn)', 'Марганец (Mn)', 'мг'))
    need_sum.append(calc_tuple('Селен (Se)', 'Селен (Se)', 'мг'))
    need_sum.append(calc_tuple('Цинк (Zn)', 'Цинк (Zn)', 'мг'))
    need_sum.append(calc_tuple('Молибден (Mo)', 'Молибден (Mo)', 'мг'))
    need_sum.append(calc_tuple('Витамин А', '', 'тыс. МЕ'))
    need_sum.append(calc_tuple('Витамин D', '', 'тыс. МЕ'))
    need_sum.append(calc_tuple('Витамин E', '', 'тыс. МЕ'))

    for val in need_sum:
        tree_main.insert("", END, values=val)

    return 0


# Экспортируем собранный рацион в таблицу Excel
def export_calc():
    data_ration = [["Сырье", "Масса, кг", "Доля, %", "СВ, кг", "ЧЭЛ, МДж", "СП, г", "nXP", "Сумма, руб."]]
    data = []
    data_input = ("Живая масса, кг: " + str(weight_live.get()) +
                  ", День стельности: " + str(days_pregnancy.get()) +
                  ", Неделя лактации: " + str(week_lactation.get()) +
                  ", Суточный прирост ЖМ, кг: " + str(weight_gain.get()) +
                  ", Удой, кг: " + str(milk_yield.get()) +
                  ", Жирность молока, %: " + str(fat_milk.get()) +
                  ", Белок, %: " + str(protein.get()) +
                  ", Температура содержания, град.: " + str(tvozd.get())
                  )
    text_title = str(combobox_type.get()) + ', ЖМ: ' + str(weight_live.get()) + ', удой: ' + str(milk_yield.get())
    # Заполнение таблицы данными
    sum_ration, sum_feed = 0.0, 0.0
    for k in tree_ration.get_children():
        sum_ration += float(tree_ration.item(k)['values'][1])
        sum_feed += float(tree_ration.item(k)['values'][8])

    if sum_ration > 0:

        for k in tree_ration.get_children():
            part = round(float(tree_ration.item(k)['values'][1]) / sum_ration * 100, 2)
            data_ration.append(
                [
                    tree_ration.item(k)['values'][0],
                    float(tree_ration.item(k)['values'][1]),
                    part,
                    float(tree_ration.item(k)['values'][3]),
                    float(tree_ration.item(k)['values'][4]),
                    float(tree_ration.item(k)['values'][5]),
                    float(tree_ration.item(k)['values'][6]),
                    round(float(tree_ration.item(k)['values'][8]),2)
                ]
            )
        data_ration.append(["Всего:", sum_ration, 100, "", "", "", "", sum_feed])

        data.append(["Показатель", "Ед. изм", "Факт.", "на 1кг СВ", "Необх.", "на 1кг СВ"])
        for m in tree_main.get_children():
            sel = tree_main.item(m)['values']
            data.append([sel[0], sel[1], sel[2], sel[3], sel[4], sel[5]])

    Save_ration_in_Excel.save_file(data_ration, data, data_input, text_title)


# Очищаем исходные данные и таблицу рациона при выборе пункта меню "Новый расчет"
def clear_data():
    weight_live.set(0.0)
    weight_gain.set(0.0)
    days_pregnancy.set(0)
    week_lactation.set(0)
    fat_milk.set(0.0)
    protein.set(0.0)
    milk_yield.set(0.0)
    tvozd.set(0)

    # очищаем таблицу рациона
    for item in tree_ration.get_children():
        tree_ration.delete(item)

    total_ration()
    plot_pie_chart()


# Загружаем сохраненный ранее рацион из файла формата JSON
def load_ration():
    data = Dialog_save_file.open_file()
    if data:
        weight_live.set(data['input_data']['body_weight'])
        combobox_type.set(data['input_data']['Animal_Type'])
        weight_gain.set(data['input_data']['weight_gain'])
        days_pregnancy.set(data['input_data']['days_pregnancy'])
        week_lactation.set(data['input_data']['week_lactation'])
        fat_milk.set(data['input_data']['fat_milk'])
        protein.set(data['input_data']['protein'])
        milk_yield.set(data['input_data']['milk_yield'])
        tvozd.set(data['input_data']['tvozd'])

        # Предварительно очищаем таблицу с собранным рационом
        for item in tree_ration.get_children():
            tree_ration.delete(item)
        # Заполняем таблицу рациона
        for k, v in data['feeds'].items():
            _feed = [k, v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7]]
            tree_ration.insert("", END, values=_feed)

        total_ration()
        plot_pie_chart()
        sorted_ration()


# Сохраняем составленный рацион и исходные данные в файл формата JSON
def save_ration():
    data_calc = {}
    data = {
        'Animal_Type': combobox_type.get(),
        'body_weight': weight_live.get(),
        'weight_gain': weight_gain.get(),
        'days_pregnancy': days_pregnancy.get(),
        'week_lactation': week_lactation.get(),
        'fat_milk': fat_milk.get(),
        'protein': protein.get(),
        'milk_yield': milk_yield.get(),
        'tvozd': tvozd.get()
    }
    data_calc['input_data'] = data
    # Теперь заполняем данными о составе рациона
    data_f = {}
    for k in tree_ration.get_children(""):
        data_f[tree_ration.item(k)['values'][0]] = (
            float(tree_ration.item(k)['values'][1]),
            tree_ration.item(k)['values'][2],
            tree_ration.item(k)['values'][3],
            tree_ration.item(k)['values'][4],
            tree_ration.item(k)['values'][5],
            float(tree_ration.item(k)['values'][6]),
            float(tree_ration.item(k)['values'][7]),
            float(tree_ration.item(k)['values'][8])
        )

    data_calc['feeds'] = data_f
    Dialog_save_file.save_file(data_calc)


# Принудительно закрываем процеес рисования диаграммы и главное окно
def close_plot():
    plt.close()
    root.destroy()


def change_tree_minerals(selected_value):
    global t_minerals

    # Очищаем таблицу минеральных веществ
    t_minerals = []
    for item in tree_minerals.get_children():
        tree_minerals.delete(item)
    #
    if selected_value == "Все элементы":
        for key, val in data_minerals.items():
            price = get_price("minerals", key)
            t_minerals.append([key, price])
    else:
        for key, val in data_minerals.items():
            for k, v in val.items():
                if k == selected_value and v[0] > 0 and k != 'Цена':
                    price = get_price("minerals", key)
                    t_minerals.append([key, price])

    for mineral in sorted(t_minerals):
        tree_minerals.insert("", END, values=mineral)
    # Конец заполнения таблицы минеральных веществ
    # Выбираем строку по умолчанию (первую строку)
    tree_minerals.selection_set(tree_minerals.get_children()[0])


def on_combobox_select(event):
    """Функция обработки выбранного значения в виджете Combobox - фильтра элементов минералов"""
    selected_value = combobox.get()  # Получаем выбранное значение
    change_tree_minerals(selected_value)


def update_data_input(selected_value):

    if selected_value == list_type_animal[0]: # "Дойная корова"
        entry_days_pregnancy.configure(state="normal")
        entry_week_lactation.configure(state="normal")
        entry_fat_milk.configure(state="normal")
        entry_protein.configure(state="normal")
        entry_milk_yield.configure(state="normal")
    elif selected_value == list_type_animal[1]: # "Сухостойная корова"
        entry_days_pregnancy.configure(state="normal")
        entry_week_lactation.configure(state="disabled")
        entry_fat_milk.configure(state="disabled")
        entry_protein.configure(state="disabled")
        entry_milk_yield.configure(state="disabled")
    elif selected_value == list_type_animal[2]: # "Ремонтный молодняк"
        entry_days_pregnancy.configure(state="disabled")
        entry_week_lactation.configure(state="disabled")
        entry_fat_milk.configure(state="disabled")
        entry_protein.configure(state="disabled")
        entry_milk_yield.configure(state="disabled")
    elif selected_value == list_type_animal[3]: # "Теленок"
        entry_days_pregnancy.configure(state="disabled")
        entry_week_lactation.configure(state="disabled")
        entry_fat_milk.configure(state="disabled")
        entry_protein.configure(state="disabled")
        entry_milk_yield.configure(state="disabled")
    else:
        entry_days_pregnancy.configure(state="normal")
        entry_week_lactation.configure(state="normal")
        entry_fat_milk.configure(state="normal")
        entry_protein.configure(state="normal")
        entry_milk_yield.configure(state="normal")


def on_combobox_select_type(event):
    """Функция обработки выбранного значения в виджете Combobox - фильтра типа животного"""
    selected_value = combobox_type.get()  # Получаем выбранное значение
    update_data_input(selected_value)


def update_tree_minerals():
    global data_minerals, t_minerals, list_filter

    # Указываем имя файла с данными о минеральных веществах
    file_data = 'minerals.json'
    path_data = os.path.join(current_directory, folder_data, file_data)
    try:
        with open(path_data, "r") as file:
            data_minerals = json.load(file)
            change_tree_minerals(selected_value="Все элементы")
            # Конец заполнения таблицы минеральных веществ

            # Заполняем фильтр элементов, входящих в минеральные вещества
            for key in data_minerals.values():
                for val in key.keys():
                    if val != 'Цена':
                        list_filter.append(val)
                break
    except FileNotFoundError:
        mb.showerror("Ошибка", "Файл со справочником минеральных веществ не найден!")


def update_tree_rations():
    for selected_item in tree_ration.get_children(""):
        _item = tree_ration.item(selected_item)
        kol_v0 = float(_item['values'][1])
        if _item['values'][0] in data_feeds:
            for k in tree_feeds.get_children(""):
                if tree_feeds.item(k)['values'][0] == _item['values'][0]:
                    tree_ration.item(selected_item, values=tuple_ration(tree_feeds.item(k), kol_v0))
                    break
        elif _item['values'][0] in data_minerals:
            for k in tree_minerals.get_children(""):
                if tree_minerals.item(k)['values'][0] == _item['values'][0]:
                    tree_ration.item(selected_item, values=tuple_ration(tree_minerals.item(k), kol_v0))
                    break


def save_price(price, window, parameter, _tree):
    global data_prices

    for selected_item in _tree.selection():
        current_item = _tree.index(_tree.selection())
    item = _tree.item(selected_item)
    if item:
        data_prices[parameter][item['values'][0]] = price

        # Указываем имя файла с ценами
        file_data = 'prices.json'
        path_data = os.path.join(current_directory, folder_data, file_data)
        with open(path_data, "w") as file:
            json.dump(data_prices, file, ensure_ascii=False, indent=2)
            window.destroy()

    if parameter == 'minerals':
        update_tree_minerals()
    elif parameter == 'feeds':
        update_dict_feeds()

    update_tree_rations()
    total_ration()

    # """Оставляем текущую строку"""
    _tree.selection_set(_tree.get_children()[current_item])


def on_item_double_click(event, parameter, _tree):
    item = _tree.selection()[0]  # Получаем выбранный элемент
    column = _tree.identify_column(event.x)  # Определяем, в каком столбце был клик
    if column == "#1" or (column == "#2" and parameter == 'feeds'):
        save_digit(event, parameter, _tree)
    elif (column == "#2" and parameter == 'minerals') or (column == "#3" and parameter == 'feeds'):
        cell_value = _tree.item(item, "values")[int(column.split("#")[-1]) - 1]

        forma = Toplevel(root)
        """Делаем окно модальным, то есть основное окно не доступно, пока мы не закроем это"""
        forma.transient(root)
        forma.grab_set()
        forma.focus_set()

        w = forma.winfo_screenwidth()
        h = forma.winfo_screenheight()
        w = w // 2  # середина экрана
        h = h // 2
        w = w - 200  # смещение от середины
        h = h - 250
        """Устанавливаем размер окна"""
        forma.geometry(f'250x120+{w}+{h}')
        forma.title('Введите цену')
        forma.iconbitmap(icon_main)

        """Добавляем на форму текст и поле для ввода цены"""

        label_price = Label(forma, text="Цена, руб./кг:", font=("Arial", 11))
        label_price.pack(pady=5)
        kol_vo = DoubleVar()
        kol_vo.set(float(cell_value))
        entry_price = Entry(forma, textvariable=kol_vo, font="Arial 12", width=10, validate="key", validatecommand=(validate_input_cmd, "%P"))
        entry_price.pack(pady=5)
        entry_price.focus_set()
        entry_price.select_range(0, "end")
        btn_save = Button(forma, text="Сохранить", width=15, command=lambda: save_price(kol_vo.get(), forma, parameter, _tree))
        btn_save.pack(pady=10)


def creat_data_table_1(select_feed):
    """функция заполняет таблицу характеристиками выбранного минерала"""
    # очищаем таблицу перед заполнением
    for item in tree_min_param.get_children():
        tree_min_param.delete(item)
    t3 = []
    for k, v in data_minerals[select_feed].items():
        if k != 'Цена':
            # Пропускаем ключ "Цена", так это значение мы добавляем в таблицу минералов (слева)
            if float(v[0]) != 0:
                t3.append((k, round(v[0], 2), v[1]))
    # заполняем таблицу параметров
    for par in t3:
        tree_min_param.insert("", END, values=par)

    if len(t3) > 0:
        """Выбираем строку по умолчанию (первую строку)"""
        tree_min_param.selection_set(tree_min_param.get_children()[0])


def item_selected_1(event):
    for selected_item in tree_minerals.selection():
        item = tree_minerals.item(selected_item)
        if item:
            creat_data_table_1(item["values"][0])


def item_selected_parameters(event, _tree, _discription, _data):
    """Функция подгрузки описания параметров"""
    for selected_item in _tree.selection():
        item = _tree.item(selected_item)
        if item:
            for _k, _v in _data.items():
                if _k == item["values"][0]:
                    _discription.config(state=NORMAL)
                    _discription.replace("1.0", END, "   " + _v)
                    _discription.config(state=DISABLED)
                    break


# Заполняем таблицу с общими показателями на вкладке Расчет
def update_tree_total():
    t5 = [["Общий вес рациона", "кг", calc_tree_total()[0]]]
    # t5.append(["Общий вес рациона", "кг", calc_tree_total()[0]])
    t5.append(["Влажность рациона", "%", calc_tree_total()[1]])
    if calc_cab() > 0:
        str_cab = "+" + str(round(calc_cab(), 1))
    else:
        str_cab = str(round(calc_cab(), 1))
    t5.append(["Катионно-анионный баланс", "мг экв./100г СВ", str_cab])
    t5.append(["Стоимость суточного рациона", "руб.", calc_tree_total()[2]])
    cost_price = 0.0
    if milk_yield.get() > 0:
        cost_price = round(calc_tree_total()[2] / milk_yield.get(), 2)
    t5.append(["Себестоимость 1 л молока", "руб.", cost_price])

    for item in tree_total.get_children():
        tree_total.delete(item)

    for val in t5:
        tree_total.insert("", END, values=val)


# Получаем цену корма или минерального вещества
def get_price(group, value):

    download_data_prices()  # Обновляем словарь с ценами путем загрузки из файла

    if value in data_prices[group]:
        return data_prices[group][value]
    else:
        return 0.0


# Загружаем прайс цен на корма и минеральные вещества из файла prices.json
def download_data_prices():
    global data_prices

    """Функция загрузки данных из файла prices.json, в котором хранятся цены на корма и минеральные вещества
    Переменная data_prices используется для заполнения таблицы кормов и минеральных веществ,
    а также при выгрузке данных обратно в файл"""
    global data_feeds, t2, t4

    # Указываем имя файла с данными о ценах
    file_data = 'prices.json'
    file_path = os.path.join(current_directory, folder_data, file_data)

    try:
        with open(file_path, "r") as file:
            data_prices = json.load(file)
    except FileNotFoundError:
        # Создаем файл, если он отсутствует
        with open(file_path, 'w') as file:
            data_prices["feeds"] = {}
            data_prices["minerals"] = {}
            json.dump(data_prices, file, ensure_ascii=False, indent=2)


# Загружаем справочник кормов из файла feeds.json
def update_dict_feeds():
    """Функция загрузки данных из файла feeds.json, в котором хранятся данные о кормах с показателями
    Переменная data_feeds используется для заполнения таблицы кормов, а также при выгрузке данных обратно в файл"""
    global data_feeds, t2, t4

    # Указываем имя файла с данными о показателях питательности кормов
    file_data = 'feeds.json'
    file_path = os.path.join(current_directory, folder_data, file_data)

    try:
        with open(file_path, "r") as file_feeds:
            data_feeds = json.load(file_feeds)
            """Заполняем словарь c показателями питательности, который используется при наполнении таблицы питательности
            показателями. Эти показатели мы берем из первого элемента в словаре data_feeds, данные в который мы
            загружаем из файла data_feeds. То есть по параметрам первого корма. Поэтому цикл мы прерываем после
            первого прохождения внутренних ключей"""
            """Предварительно очищаем словарь"""
            t4.clear()
            for val in data_feeds.values():
                for _key in val.keys():
                    if _key != 'Группа кормов':
                        t4[_key] = 0
                break
            """Заполняем таблицу питательности расчётными данными потребности по исходным данным"""
            click_button()
            """Загружаем в список кормов из глобального справочника data_feeds данные о названии и группе """
            """Предварительно очищаем список, так как функция вызывается не один раз"""
            t2.clear()
            """Заполняем список кортежами (название, группа кормов, цена кормов)"""
            for key, val in data_feeds.items():
                for _k, _v in val.items():
                    if _k == 'Группа кормов':
                        group = _v
                price = get_price("feeds", key)
                t2.append([key, group, price])
            """Очищаем предварительно визуальную таблицу кормов"""
            for item in tree_feeds.get_children():
                tree_feeds.delete(item)
            """Заполняем визуальную таблицу кормов tree_feeds"""
            for feed in sorted(t2):
                tree_feeds.insert("", END, values=feed)
            """Конец заполнения таблицы"""

            """Выбираем строку по умолчанию (первую строку)"""
            tree_feeds.selection_set(tree_feeds.get_children()[0])
    except FileNotFoundError:
        mb.showerror("Ошибка!", "Не найден файл со справочником кормов!")


# Загружаем описание показателей питательности кормов. Эти же данные используем на вкладке Минералы
def download_discriptions_parameters_feeds():
    global data_discriptions_parameters_feeds

    # Указываем имя файла с данными о показателях питательности кормов
    file_data = 'indicators_feeds.json'
    path_data = os.path.join(current_directory, folder_data, file_data)
    try:
        with open(path_data, "r") as file:
            data_discriptions_parameters_feeds = json.load(file)
    except FileNotFoundError:
        mb.showerror("Ошибка", "Не найден файл с описанием показателей питательности кормов!")


# Заполняем таблицу показателей корма при выборе строки в справочнике кормов
def creat_data_table(select_feed):
    """функция заполняет таблицу характеристиками выбранного корма"""
    # очищаем таблицу перед заполнением
    for item in tree_param.get_children():
        tree_param.delete(item)
    t3 = []
    for k, v in data_feeds[select_feed].items():
        """Игнорируем записи с ключами "Группа кормов" и "Цена", так как их мы используем в таблице кормов"""
        if k != 'Группа кормов' and k != 'Цена':
            t3.append((k, v[0], v[1]))
    """Заполняем таблицу параметров выбранного корма"""
    for par in t3:
        tree_param.insert("", END, values=par)

    if len(t3) > 0:
        """Выбираем строку по умолчанию (первую строку)"""
        tree_param.selection_set(tree_param.get_children()[0])


# Здесь обрабатываем выбор строки в справочнике кормов
def item_selected(event):
    for selected_item in tree_feeds.selection():
        item = tree_feeds.item(selected_item)
        """Вызов функции заполнения таблицы с параметрами выбранного пользователем корма"""
        creat_data_table(item["values"][0])


# Выделяем строку с кормом или минеральным веществом в своих таблицах, если они включены в рацион
def color_rows():
    """Функция меняет цвет строк таблиц кормов и минералов, которые собраны пользователем в таблицу рациона"""
    """Составляем список рациона для проверки вхождения"""
    list_ration = [tree_ration.item(k)['values'][0] for k in tree_ration.get_children()]

    """Проверяем вхождение кормов в список"""
    for k in tree_feeds.get_children():
        if tree_feeds.item(k)['values'][0] in list_ration:
            """Устанавливаем желто-зеленый фон для строк кормов, включенных в рацион"""
            tree_feeds.tag_configure('coloryellow', background='YellowGreen')  # Конфигурируем тэг 'coloryellow'
            tree_feeds.item(k, tags=('coloryellow',))  # Применяем тэг 'coloryellow' к выбранной строке
        else:
            """Устанавливаем белый фон для кормов, не вошедших в рацион"""
            tree_feeds.tag_configure('colorwhite', background='white')  # Конфигурируем тэг 'colorwhite' с белым фоном
            tree_feeds.item(k, tags=('colorwhite',))  # Применяем тэг 'colorwhite' к выбранной строке

    """Проверяем вхождение минералов в список"""
    for k in tree_minerals.get_children():
        if tree_minerals.item(k)['values'][0] in list_ration:
            """Устанавливаем желто-зеленый фон для строк минералов, включенных в рацион"""
            tree_minerals.tag_configure('coloryellow', background='YellowGreen')  # Конфигурируем тэг 'coloryellow'
            tree_minerals.item(k, tags=('coloryellow',))  # Применяем тэг 'coloryellow' к выбранной строке
        else:
            """Устанавливаем белый фон для минералов, не вошедших в рацион"""
            tree_minerals.tag_configure('colorwhite',
                                        background='white')  # Конфигурируем тэг 'colorwhite' с белым фоном
            tree_minerals.item(k, tags=('colorwhite',))  # Применяем тэг 'colorwhite' к выбранной строке


# Рассчитываем питательность собранного рациона и записываем в таблицу питательности
def total_ration():
    """Функция предназначена для расчета питательности кормов, собранных пользователем в рацион"""
    global t4
    # Очищаем таблицу питательности выбранного сырья рациона кормов
    for k in t4.keys():
        t4[k] = 0

    for k in tree_ration.get_children(""):
        koef = float(tree_ration.item(k)['values'][1])
        dry = 0
        if tree_ration.item(k)['values'][0] in data_feeds:
            for key, val in data_feeds[tree_ration.item(k)['values'][0]].items():
                if key != 'Группа кормов' and key != 'Цена':
                    if key == 'Сухое вещество (Dry)':
                        if key in t4:
                            t4[key] = t4[key] + float(val[0]) * koef / 100
                        else:
                            t4[key] = float(val[0]) * koef / 100
                        dry = float(val[0]) * koef / 100
                    else:
                        if key in t4:
                            t4[key] = t4[key] + float(val[0]) * dry
                        else:
                            t4[key] = float(val[0]) * dry
            t4["Баланс азота в рубце (RNB)"] = (
                    (t4["Сырой протеин (Crude protein)"] - t4["Усвоенный протеин (nXP)"]) / 6.25)
        elif tree_ration.item(k)['values'][0] in data_minerals:
            for key, val in data_minerals[tree_ration.item(k)['values'][0]].items():
                if key != 'Цена':
                    if val[1] == "%":
                        quantity = val[0] * 1000 * koef / 100
                    else:
                        quantity = val[0] * koef

                    if key in t4:
                        t4[key] = t4[key] + quantity
                    else:
                        t4[key] = quantity

    click_button()
    update_tree_total()
    color_rows()


# Создаем кортеж данных для добавления строкой в таблицу собранного рациона
def tuple_ration(_item, kol_v0) -> tuple:
    dry, dp, price, nxp, nel = 0.0, 0.0, 0.0, 0.0, 0.0
    group = ""

    if _item['values'][0] in data_feeds:
        price = float(_item["values"][2])
        group = _item["values"][1]
        for key, val in data_feeds[_item['values'][0]].items():
            if key != 'Группа кормов':
                if key == 'Сухое вещество (Dry)':
                    dry = float(val[0]) / 100
                elif key == 'Сырой протеин (Crude protein)':
                    dp = float(val[0]) * dry
                elif key == 'Усвоенный протеин (nXP)':
                    nxp = float(val[0]) * dry
                elif key == 'Чистая энергия лактации (NEL)':
                    nel = float(val[0]) * dry
    elif _item['values'][0] in data_minerals:
        price = float(_item["values"][1])
        group = "минералы"

    total = kol_v0 * price
    _val = (
        _item["values"][0],
        kol_v0,
        group,
        round(dry * kol_v0, 2),  # Сухое вещество в сырье корма
        round(nel * kol_v0, 1),  # Чистая энергия лактации ЧЭЛ (NEL)
        round(dp * kol_v0, 1),  # Сырой протеин в сырье корма
        round(nxp * kol_v0, 1),  # Усвоенный протеин nXP
        round(price, 2),  # Цена корма
        round(total, 2)
    )  # Стоимость корма в рационе

    return _val


def sorted_ration():
    # получаем все значения столбца "группа кормов" в виде отдельного списка
    l = [[tree_ration.set(k, 2), k] for k in tree_ration.get_children("")]
    # задаем порядок сортировки
    for k in l:
        if k[0] == "концентрированные":
            k[0] = 1
        elif k[0] == "основные":
            k[0] = 2
        elif k[0] == "минералы":
            k[0] = 3
    # сортируем список
    l.sort(reverse=False)
    # # переупорядочиваем значения в отсортированном порядке
    for index,  (_, k) in enumerate(l):
        tree_ration.move(k, "", index)


# Добавляем корм или минеральное вещество в таблицу собранного рациона
def add_in_ration(digit, window, ver, _tree):
    kol_v0 = convert_number(digit)
    """Проверяем, есть ли сырье уже в рационе"""
    # Здесь нужно добавить проверку

    if ver == "feeds":
        for selected_item in _tree.selection():
            item = _tree.item(selected_item)
            tree_ration.insert("", END, values=tuple_ration(item, kol_v0))
    elif ver == "minerals":
        for selected_item in _tree.selection():
            item = _tree.item(selected_item)
            _val = [item["values"][0], kol_v0, 'минералы']
            tree_ration.insert("", END, values=tuple_ration(item, kol_v0))
    else:
        return
    total_ration()
    window.destroy()
    plot_pie_chart()
    sorted_ration()


# Записываем новое количество сырья в выбранной строке рациона
def save_in_ration(digit, window):
    kol_v0 = convert_number(digit)
    selected_item = tree_ration.selection()
    _item = tree_ration.item(selected_item)
    if kol_v0 > 0:
        if _item['values'][0] in data_feeds:
            for k in tree_feeds.get_children(""):
                if tree_feeds.item(k)['values'][0] == _item['values'][0]:
                    tree_ration.item(selected_item, values=tuple_ration(tree_feeds.item(k), kol_v0))
                    break
        elif _item['values'][0] in data_minerals:
            for k in tree_minerals.get_children(""):
                if tree_minerals.item(k)['values'][0] == _item['values'][0]:
                    tree_ration.item(selected_item, values=tuple_ration(tree_minerals.item(k), kol_v0))
                    break
    else:
        tree_ration.delete(selected_item)
    total_ration()
    window.destroy()
    plot_pie_chart()


# Открываем форму для изменения количества сырья в таблице рациона
def change_count(event):
    global icon_main

    in_digit = Toplevel()
    w = in_digit.winfo_screenwidth()
    h = in_digit.winfo_screenheight()
    in_digit.iconbitmap(icon_main)
    w = w // 2  # середина экрана
    h = h // 2
    w = w - 200  # смещение от середины
    h = h - 200

    selected_item = tree_ration.selection()
    item = tree_ration.item(selected_item)

    """Получаем количество корма в строке"""
    kol_vo = StringVar()
    kol_vo.set(item["values"][1])
    """Устанавливаем размер окна"""
    in_digit.geometry(f'250x120+{w}+{h}')
    in_digit.title('Введите')
    Label(in_digit, text="Суточный расход сырья в кг", font="Arial 11").pack(pady=15)
    entry = Entry(in_digit, textvariable=kol_vo,
                  font="Arial 12", width=10, validate="key", validatecommand=(validate_input_cmd, "%P"))
    entry.pack(pady=5)
    entry.focus()
    entry.select_range(0, "end")
    Button(in_digit, text="Сохранить", width=15, command=lambda: save_in_ration(kol_vo.get(), in_digit)).pack()


# Функция для обработки выбора вкладки
def on_tab_selected(event):
    selected_tab = notebook.index(notebook.select())  # Получаем индекс выбранной закладки
    total_ration()


# Сохраняем новое значение выбранного параметра при редактировании корма или минерального вещества
def save_parameter(digit, window, _tree):
    """Функция сохранения значения выбранного параметра"""
    kol_v0 = convert_number(digit)
    selected_item = _tree.selection()
    item = _tree.item(selected_item)
    if item["values"][2] == "%" and kol_v0 > 100.0:
        mb.showerror("Ошибка!", "Недопустимое значение в процентах!")
    else:
        _tree.set(selected_item, 1, kol_v0)
        window.destroy()


# В этой функции мы открываем форму для ввода количества сырья при добавлении корма или минерального вещества
# в рацион. А также при изменении количества параметра при редактировании справочников кормов или минералов
def save_digit(event, ver, _tree):
    global icon_main

    in_digit = Toplevel(root)

    in_digit.transient(root)
    in_digit.grab_set()
    in_digit.focus_set()
    w = in_digit.winfo_screenwidth()
    h = in_digit.winfo_screenheight()
    w = w // 2  # середина экрана
    h = h // 2
    w = w - 200  # смещение от середины
    h = h - 200
    kol_vo = StringVar(value='0.0')
    in_digit.geometry(f'250x120+{w}+{h}')
    in_digit.title('Введите')
    in_digit.iconbitmap(icon_main)

    if ver == "parameter":
        # Блок ввода нового значения параметра корма или минерального вещества
        if _tree.selection():
            item = _tree.item(_tree.selection())
            kol_vo.set(item["values"][1])
        Label(in_digit, text="Значение выбранного параметра:").pack(pady=15)
        entry = Entry(in_digit, textvariable=kol_vo, font="Arial 12", width=10)
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, "end")
        Button(in_digit, text="Сохранить", width=15,
               command=lambda: save_parameter(kol_vo.get(), in_digit, _tree)).pack()
    else:
        # Блок для добавление сырья в рацион
        Label(in_digit, text="Суточный расход сырья в кг", font="Arial 11").pack(pady=15)
        entry = Entry(in_digit, textvariable=kol_vo,
                      font="Arial 12", width=10, validate="key", validatecommand=(validate_input_cmd, "%P"))
        entry.pack()
        entry.focus()
        entry.select_range(0, "end")
        Button(in_digit, text="Добавить", width=15,
               command=lambda: add_in_ration(kol_vo.get(), in_digit, ver, _tree)).pack(pady=10)


# Удаление выбранного корма в справочнике кормов
def delete_feed():
    global data_feeds, data_prices

    if tree_feeds.selection():
        answer = mb.askyesno(title="Вопрос", message="Удалить выбранный корм?")
        if answer:
            item = tree_feeds.item(tree_feeds.selection())
            if item['values'][0] in data_feeds:
                del data_feeds[item["values"][0]]

                file_data = 'feeds.json'
                path_data = os.path.join(current_directory, folder_data, file_data)
                with open(path_data, "w") as file:
                    json.dump(data_feeds, file, ensure_ascii=False, indent=2)

            if item['values'][0] in data_prices["feeds"]:
                del data_prices["feeds"][item["values"][0]]

                file_data = 'prices.json'
                path_data = os.path.join(current_directory, folder_data, file_data)
                with open(path_data, "w") as file:
                    json.dump(data_prices, file, ensure_ascii=False, indent=2)

            tree_feeds.delete(tree_feeds.selection())
            update_dict_feeds()
    else:
        mb.showerror("Предупреждение", "Не выбрана строка в таблице кормов")


# Удаление выбранного минерала в справочнике минеральных веществ
def delete_mineral():
    global data_minerals, data_prices

    if tree_minerals.selection():
        answer = mb.askyesno(title="Вопрос", message="Удалить выбранный элемент?")
        if answer:
            item = tree_minerals.item(tree_minerals.selection())
            if item['values'][0] in data_minerals:
                del data_minerals[item['values'][0]]

                file_data = 'minerals.json'
                path_data = os.path.join(current_directory, folder_data, file_data)
                with open(path_data, "w") as file:
                    json.dump(data_minerals, file, ensure_ascii=False, indent=2)

            if item['values'][0] in data_prices["minerals"]:
                del data_prices["minerals"][item["values"][0]]

                file_data = 'prices.json'
                path_data = os.path.join(current_directory, folder_data, file_data)
                with open(path_data, "w") as file:
                    json.dump(data_prices, file, ensure_ascii=False, indent=2)

            tree_minerals.delete(tree_minerals.selection())
            update_tree_minerals()
    else:
        mb.showerror("Предупреждение", "Не выбрана строка в таблице минеральных веществ!")


# Сохраняем новые значения параметров корма и новую цену
def save_form_feed(window, name, group, _tree, mode, price, old_name):
    global data_feeds

    window.focus_set()
    answer = mb.askyesno(title="Вопрос", message="Сохранить данные?")
    if answer:
        if (mode != 'change') and (name in data_feeds):
            mb.showerror("Ошибка", "Корм с таким названием уже существует!")
            window.focus_set()
            return
        if len(group) == 0:
            mb.showerror("Ошибка", "Не указана группа кормов!")
            window.focus_set()
            return

        if (mode == 'change') and (old_name != name):
            del data_feeds[old_name]
            # Обновляем файл с ценами
            if old_name in data_prices["feeds"]:
                del data_prices["feeds"][old_name]

        # Обновляем файл с ценами
        data_prices["feeds"][name] = price
        # Указываем имя файла с ценами
        file_data = 'prices.json'
        path_data = os.path.join(current_directory, folder_data, file_data)
        with open(path_data, "w") as file:
            json.dump(data_prices, file, ensure_ascii=False, indent=2)
        # Завершаем запись в файл

        v = {"Группа кормов": group}
        for k in _tree.get_children():
            v[_tree.item(k)['values'][0]] = (float(_tree.item(k)['values'][1]), _tree.item(k)['values'][2])
        data_feeds[name] = v

        # Указываем имя файла с данными о минеральных веществах
        file_data = 'feeds.json'
        path_data = os.path.join(current_directory, folder_data, file_data)
        try:
            with open(path_data, "w") as file:
                json.dump(data_feeds, file, ensure_ascii=False, indent=2)
                window.destroy()
        except FileNotFoundError:
            mb.showerror("Ошибка", "Файл со справочником кормов не найден!")

        update_dict_feeds()
        update_tree_rations()
        color_rows()


# Сохраняем новые значения параметров минерального вещества и новую цену
def save_form_mineral(window, name, _tree, mode, price, old_name):
    global data_minerals

    window.focus_set()
    current_item = tree_minerals.index(tree_minerals.selection()) # Запоминаем текущую строку в списке минералов

    answer = mb.askyesno(title="Вопрос", message="Сохранить данные?")
    if answer:
        if (mode != 'change') and (name in data_minerals):
            mb.showerror("Ошибка", "Элемент с таким названием уже существует!")
            window.focus_set()
            return

        if (mode == 'change') and (old_name != name):
            del data_minerals[old_name]
            if old_name in data_prices["minerals"]:
                del data_prices["minerals"][old_name]

        # Обновляем файл с ценами
        data_prices["minerals"][name] = price
        # Указываем имя файла с ценами
        file_data = 'prices.json'
        path_data = os.path.join(current_directory, folder_data, file_data)
        with open(path_data, "w") as file:
            json.dump(data_prices, file, ensure_ascii=False, indent=2)
        # Завершаем запись в файл

        v = {}
        for k in _tree.get_children():
            v[_tree.item(k)['values'][0]] = (float(_tree.item(k)['values'][1]), _tree.item(k)['values'][2])
        data_minerals[name] = v

        # Указываем имя файла с данными о минеральных веществах
        file_data = 'minerals.json'
        path_data = os.path.join(current_directory, folder_data, file_data)
        try:
            with open(path_data, "w") as file:
                json.dump(data_minerals, file, ensure_ascii=False, indent=2)
                window.destroy()
        except FileNotFoundError:
            mb.showerror("Ошибка", "Файл со справочником минеральных веществ не найден!")

        update_tree_minerals()
        update_tree_rations()
        color_rows()
        # """Оставляем текущую строку"""
        tree_minerals.selection_set(tree_minerals.get_children()[current_item])


# Открываем форму  параметров корма и цены
def open_form_feed(mode_form):
    """Функция открывает форму с параметрами качества корма.
    Два варианта:
    1. NEW. Тогда таблица с пустыми значениями
    2. COPY. Копия параметров на основе выбранного в таблице tree_feeds корма"""

    global icon_main

    forma_feed = Toplevel(root)
    w = forma_feed.winfo_screenwidth()
    h = forma_feed.winfo_screenheight()
    w = w // 2  # середина экрана
    h = h // 2
    w = w - 200  # смещение от середины
    h = h - 250
    """Устанавливаем размер окна"""
    forma_feed.geometry(f'420x600+{w}+{h}')
    forma_feed.title('Карточка корма')
    forma_feed.iconbitmap(icon_main)

    """Делаем окно модальным, то есть основное окно не доступно, пока мы не закроем это"""
    forma_feed.transient(root)
    forma_feed.grab_set()
    forma_feed.focus_set()

    """Добавляем на форму текст и поле для ввода названия корма"""
    label_name = Label(forma_feed, text="Название:", font=("Arial", 11))
    label_name.place(x=10, y=20, width=75, height=20)
    str_name = StringVar()
    entry_name = Entry(forma_feed, textvariable=str_name)
    entry_name.place(x=90, y=20, width=250, height=20)
    """Добавляем блок: текст (label_group) и элемент Combobox для ввода списка групп кормов"""
    label_group = Label(forma_feed, text="Группа:", font=("Arial", 11))
    label_group.place(x=10, y=50, width=75, height=20)
    old_name = ""

    """Добавляем блок: текст (label_price) и элемент Entry для ввода цены корма"""
    label_price = Label(forma_feed, text="Цена, руб./кг:", font=("Arial", 11))
    label_price.place(x=10, y=80, width=100, height=20)
    str_price = DoubleVar(value=0.0)
    entry_price = Entry(forma_feed, textvariable=str_price)
    entry_price.place(x=120, y=80, width=120, height=20)

    list_group = ["основные", "концентрированные"]
    combo_groups = ttk.Combobox(forma_feed, values=list_group, state="readonly")
    # Размещаем список с использованием метода place()
    combo_groups.place(x=90, y=50, width=150, height=20)  # Координаты и размеры

    """В зависимости от варианта открытия формы (NEW или COPY) меняем значение поля названия и вариант заполнения
    таблицы параметров: с пустыми значениями или заполненными значениями корма, выбранного пользователем как образец
    (выделенная строка в таблице tree_feeds)"""
    if mode_form == "new":
        str_name.set("Новый")
        # str_price.set(0.0)
    elif mode_form == "copy" or mode_form == "change":
        if tree_feeds.selection():
            item = tree_feeds.item(tree_feeds.selection())
            if mode_form == "copy":
                str_name.set("Копия")
                str_price.set(item['values'][2])
            else:
                str_name.set(item['values'][0])
                str_price.set(item['values'][2])
                old_name = str_name.get()

            if item['values'][1] == 'основные':
                combo_groups.set("основные")
            else:
                combo_groups.set("концентрированные")

    # определяем столбцы таблицы параметров
    columns_param = ('name_parametre', 'value', 'unit')
    # создаем таблицу с параметрами выбранного корма
    tree_param = ttk.Treeview(forma_feed, columns=columns_param, show="headings", height=19, selectmode="browse")
    tree_param.place(x=10, y=110, width=400, height=440)

    tree_param.heading('name_parametre', text='Показатель', anchor=W)
    tree_param.column("#1", stretch=NO, width=250)
    tree_param.heading('value', text='Значение')
    tree_param.column("#2", stretch=NO, width=75, anchor=E)
    tree_param.heading('unit', text='Ед. изм.', anchor=W)
    tree_param.column("#3", stretch=NO, width=75)

    # добавляем вертикальную прокрутку
    scrollbar = ttk.Scrollbar(forma_feed, orient=VERTICAL, command=tree_param.yview)
    tree_param.configure(yscrollcommand=scrollbar.set)
    scrollbar.place(x=450, y=110, width=10, height=440)

    """В зависимости от параметра mode_form заполняем таблицу параметров корма
    1. NEW: в таблицу заносятся параметры кормов с нулевыми их значениями
    2. COPY: в таблицу заносятся параметры кормов на основе выбранного в качестве образца корма
    3. CHANGE: в таблицу заносятся параметры выбранного корма"""

    t3 = []
    if mode_form == "new":
        for val in data_feeds.values():
            for k, v in val.items():
                if k != 'Группа кормов' and k != 'Цена':
                    t3.append((k, 0.0, v[1]))
            break
    elif mode_form == "copy" or mode_form == "change":
        for k, v in data_feeds[item["values"][0]].items():
            if k != 'Группа кормов' and k != 'Цена':
                t3.append((k, v[0], v[1]))

    # заполняем таблицу параметров
    for par in t3:
        tree_param.insert("", END, values=par)
    """Конец заполнения таблицы"""

    btn_save = Button(
        forma_feed, text="Сохранить", command=lambda: save_form_feed(
            forma_feed,
            entry_name.get(),
            combo_groups.get(),
            tree_param,
            mode_form,
            float(entry_price.get()),
            old_name)
    )
    btn_save.place(x=30, y=560, width=100, height=25)
    btn_close = Button(forma_feed, text="Закрыть", command=forma_feed.destroy)
    btn_close.place(x=210, y=560, width=100, height=25)

    """Обработчик события "двойной клик левой кнопки мыши" по строке параметра корма
    Результат: открывается форма ввода количества выбранного параметра корма"""
    tree_param.bind("<Double-1>", lambda event, a1="parameter": save_digit(event, a1, tree_param))


# Открываем форму  параметров минерала и цены
def open_form_mineral(mode_form):
    """Функция открывает форму с параметрами качества корма.
    Два варианта:
    1. NEW. Тогда таблица с пустыми значениями
    2. COPY. Копия параметров на основе выбранного в таблице tree_feeds корма"""

    global icon_main

    forma_mineral = Toplevel(root)
    w = forma_mineral.winfo_screenwidth()
    h = forma_mineral.winfo_screenheight()
    w = w // 2  # середина экрана
    h = h // 2
    w = w - 200  # смещение от середины экрана
    h = h - 250
    """Устанавливаем размер окна"""
    forma_mineral.geometry(f'350x450+{w}+{h}')
    forma_mineral.title('Карточка минерального вещества')
    forma_mineral.iconbitmap(icon_main)

    """Делаем окно модальным, то есть основное окно не доступно, пока мы не закроем это"""
    forma_mineral.transient(root)
    forma_mineral.grab_set()
    forma_mineral.focus_set()

    """Добавляем на форму текст и поле для ввода названия минерального вещества"""
    label_name_m = Label(forma_mineral, text="Название:", font=("Arial", 11))
    label_name_m.place(x=10, y=20, width=75, height=20)
    str_name = StringVar()
    entry_name = Entry(forma_mineral, textvariable=str_name, font=("Arial", 10))
    entry_name.place(x=90, y=20, width=250, height=20)
    old_name = ""

    """Добавляем блок: текст (label_price) и элемент Entry для ввода цены минерального вещества"""
    label_price_m = Label(forma_mineral, text="Цена, руб./кг:", font=("Arial", 11))
    label_price_m.place(x=10, y=50, width=100, height=20)
    str_price = DoubleVar(value=0.0)
    entry_price = Entry(forma_mineral, textvariable=str_price, font=("Arial", 10))
    entry_price.place(x=120, y=50, width=120, height=20)

    """В зависимости от варианта открытия формы (NEW или COPY) меняем значение поля названия и вариант заполнения
    таблицы параметров: с пустыми значениями или заполненными значениями корма, выбранного пользователем как образец
    (выделенная строка в таблице tree_feeds)"""
    if mode_form == "new":
        str_name.set("Новый")
    elif mode_form == "copy" or mode_form == "change":
        if tree_minerals.selection():
            item = tree_minerals.item(tree_minerals.selection())
            if mode_form == "copy":
                str_name.set("Копия")
                str_price.set(item['values'][1])
            else:
                str_name.set(item['values'][0])
                str_price.set(item['values'][1])
                # Запоминаем имя при открытии формы при редактировании, чтобы при записи с новым именем не дублировать
                # в справочнике минеральных веществ. Это проверяется в функции сохранения save_form_mineral()
                old_name = str_name.get()

    # определяем столбцы таблицы параметров
    columns_m = ('name_parameter', 'value', 'unit')
    # создаем таблицу с параметрами выбранного минерального вещества
    tree_param_m = ttk.Treeview(forma_mineral, columns=columns_m, show="headings", height=19, selectmode="browse")
    tree_param_m.place(x=30, y=80, width=275, height=320)

    tree_param_m.heading('name_parameter', text='Показатель', anchor=W)
    tree_param_m.column("#1", stretch=NO, width=125)
    tree_param_m.heading('value', text='Значение')
    tree_param_m.column("#2", stretch=NO, width=75, anchor=E)
    tree_param_m.heading('unit', text='Ед. изм.', anchor=W)
    tree_param_m.column("#3", stretch=NO, width=75)

    # добавляем вертикальную прокрутку
    scrollbar_m = ttk.Scrollbar(forma_mineral, orient=VERTICAL, command=tree_param_m.yview)
    tree_param_m.configure(yscrollcommand=scrollbar_m.set)
    scrollbar_m.place(x=310, y=80, width=10, height=320)

    """В зависимости от параметра mode_form заполняем таблицу параметров минерального вещества
    1. NEW: в таблицу заносятся параметры кормов с нулевыми их значениями
    2. COPY: в таблицу заносятся параметры кормов на основе выбранного в качестве образца вещества
    3. CHANGE: в таблицу заносятся параметры выбранного вещества"""

    t3 = []
    if mode_form == "new":
        for val in data_minerals.values():
            for k, v in val.items():
                if k != 'Цена':
                    t3.append((k, 0.0, v[1]))
            break
    elif mode_form == "copy" or mode_form == "change":
        for k, v in data_minerals[item["values"][0]].items():
            if k != 'Цена':
                t3.append((k, round(v[0],2), v[1]))

    # заполняем таблицу параметров
    for par in t3:
        tree_param_m.insert("", END, values=par)
    """Конец заполнения таблицы"""

    btn_save = Button(
        forma_mineral, text="Сохранить", command=lambda: save_form_mineral(
            forma_mineral, entry_name.get(), tree_param_m, mode_form, float(entry_price.get()), old_name))
    btn_save.place(x=30, y=410, width=100, height=25)
    btn_close = Button(forma_mineral, text="Закрыть", command=forma_mineral.destroy)
    btn_close.place(x=210, y=410, width=100, height=25)

    """Обработчик события "двойной клик левой кнопки мыши" по строке параметра минерала
    Результат: открывается форма ввода количества выбранного параметра"""
    tree_param_m.bind("<Double-1>", lambda event, a1="parameter": save_digit(event, a1, tree_param_m))


# Рисуем диаграмму структуры рациона
def plot_pie_chart():
    labels = []
    sizes = []
    sum_basic = 0
    sum_minerals = 0
    sum_concentrate = 0
    for k in tree_ration.get_children():
        if tree_ration.item(k)['values'][2] == 'основные':
            sum_basic += float(tree_ration.item(k)['values'][3])
        elif tree_ration.item(k)['values'][2] == 'минералы':
            sum_minerals += float(tree_ration.item(k)['values'][3])
        else:
            sum_concentrate += float(tree_ration.item(k)['values'][3])

    if sum_basic > 0:
        labels.append('основные')
        sizes.append(sum_basic)
    if sum_concentrate > 0:
        labels.append('концентрат')
        sizes.append(sum_concentrate)
    if sum_minerals > 0:
        labels.append('минералы')
        sizes.append(sum_minerals)

        # labels.append(tree_ration.item(k)['values'][0])
        # sizes.append(float(tree_ration.item(k)['values'][1]))

    if len(labels) == 0:
        # Создаем данные для диаграммы
        labels = ['Рацион не создан']
        sizes = [1]

    # Создаем фигуру Matplotlib
    fig = Figure(figsize=(4, 4))
    ax = fig.add_subplot(111)

    # Строим круговую диаграмму с использованием pyplot
    ax.pie(sizes, labels=None, autopct='%1.1f%%')
    ax.legend(labels, loc='lower left', fontsize=8)
    ax.set_title("Структура кормов в рационе")

    # Создаем виджет Canvas для отображения диаграммы в Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame4)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.place(x=390, y=350, width=300, height=280)

    plt.close()


root = Tk()
root.title("2С: Рацион (КРС)")
root.geometry("1300x700")
root.resizable(width=False, height=False)  # Запрещаем менять размер окна программы
# Устанавливаем иконку для окна
root.iconbitmap(icon_main)


validate_input_cmd = root.register(validate_input)  # Регистрируем функцию валидации вещественного числа
validate_input_int = root.register(validate_input_int)  # Регистрируем функцию валидации целого числа

# Создаем меню
mainmenu = Menu(root)
root.config(menu=mainmenu)
filemenu = Menu(mainmenu, tearoff=0)
filemenu.add_command(label="Новый расчет", command=clear_data)
filemenu.add_command(label="Открыть расчет...", command=load_ration)
filemenu.add_separator()
filemenu.add_command(label="Сохранить расчет...", command=save_ration)
filemenu.add_separator()
filemenu.add_command(label="Экспорт в Excel", command=export_calc)
filemenu.add_separator()
filemenu.add_command(label="Активация программы", command=activation_program)
filemenu.add_separator()
filemenu.add_command(label="Выход", command=close_plot)
mainmenu.add_cascade(label="Файл", menu=filemenu)

# создаем набор вкладок
notebook = ttk.Notebook(root, style="TNotebook")
notebook.pack(expand=True, fill=BOTH)

# Создание стиля с ttkthemes
style = ThemedStyle(notebook)
style.set_theme("aquativo")  # Выбор темы

# создаем фреймы (Закладки)
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)
frame3 = ttk.Frame(notebook)
frame4 = ttk.Frame(notebook)

# добавляем фреймы в качестве вкладок
notebook.add(frame1, text="Исходные данные")
notebook.add(frame2, text="Корма")
notebook.add(frame3, text="Минералы")
notebook.add(frame4, text="Расчеты")

# отображаем тексты меток и поля для ввода данных
label_name = ttk.Label(frame1, text="Исходные данные для расчета:", font=("Arial", 14))
label_name.place(x=50, y=30, width=500, height=30)

label_type = ttk.Label(frame1, text="Тип животного:", font=("Arial", 12), foreground='blue')
label_type.place(x=50, y=80, width=200, height=20)

list_type_animal = ["Дойная корова", "Сухостойная корова", "Ремонтный молодняк", "Теленок"]
# по умолчанию будет выбран первый элемент из list_type_animal
type_animal = StringVar(value=list_type_animal[0])
combobox_type = ttk.Combobox(frame1, textvariable=type_animal,
                             values=list_type_animal, state="readonly", font=("Arial", 11))
# Размещаем бокс с использованием метода place()
combobox_type.place(x=270, y=80, width=180, height=25)  # Координаты и размеры

# Привязываем обработчик события к combobox_type
combobox_type.bind("<<ComboboxSelected>>", on_combobox_select_type)
"""Конец размещения"""

weight_live = DoubleVar()
label_weight_live = ttk.Label(frame1, text="Живая масса, кг", font=("Arial", 12), foreground='blue')
label_weight_live.place(x=50, y=150, width=200, height=20)
entry_weight_live = ttk.Entry(frame1, textvariable=weight_live, font=("Arial", 12),
                              validate="key", validatecommand=(validate_input_cmd, "%P"))
entry_weight_live.place(x=350, y=150, width=100, height=25)

weight_gain = DoubleVar()
label_weight_gain = ttk.Label(frame1, text="Среднесуточный прирост массы, кг:", font=("Arial", 12), foreground='blue')
label_weight_gain.place(x=50, y=190, width=280, height=20)
entry_weight_gain = ttk.Entry(frame1, textvariable=weight_gain, font=("Arial", 12),
                              validate="key", validatecommand=(validate_input_cmd, "%P"))
entry_weight_gain.place(x=350, y=190, width=100, height=25)

days_pregnancy = IntVar()
label_days_pregnancy = ttk.Label(frame1, text="Количество дней стельности", font=("Arial", 12), foreground='blue')
label_days_pregnancy.place(x=50, y=250, width=280, height=20)
entry_days_pregnancy = ttk.Entry(frame1, textvariable=days_pregnancy, font=("Arial", 12),
                                 validate="key", validatecommand=(validate_input_int, "%P"))
entry_days_pregnancy.place(x=350, y=250, width=100, height=20)

week_lactation = IntVar()
label_week_lactation = ttk.Label(frame1, text="Неделя лактации", font=("Arial", 12), foreground='blue')
label_week_lactation.place(x=50, y=290, width=280, height=20)
entry_week_lactation = ttk.Entry(frame1, textvariable=week_lactation, font=("Arial", 12),
                                 validate="key", validatecommand=(validate_input_int, "%P"))
entry_week_lactation.place(x=350, y=290, width=100, height=20)

fat_milk = DoubleVar()
label_fat_milk = ttk.Label(frame1, text="Жирность молока, %", font=("Arial", 12), foreground='blue')
label_fat_milk.place(x=50, y=350, width=280, height=20)
entry_fat_milk = ttk.Entry(frame1, textvariable=fat_milk, font=("Arial", 12),
                           validate="key", validatecommand=(validate_input_cmd, "%P"))
entry_fat_milk.place(x=350, y=350, width=100, height=25)

protein = DoubleVar()
label_protein = ttk.Label(frame1, text="Содержание белка в молоке, %", font=("Arial", 12), foreground='blue')
label_protein.place(x=50, y=390, width=280, height=20)
entry_protein = ttk.Entry(frame1, textvariable=protein, font=("Arial", 12),
                          validate="key", validatecommand=(validate_input_cmd, "%P"))
entry_protein.place(x=350, y=390, width=100, height=25)

milk_yield = DoubleVar()
label_milk_yield = ttk.Label(frame1, text="Суточный удой молока, кг:", font=("Arial", 12), foreground='blue')
label_milk_yield.place(x=50, y=430, width=280, height=20)
entry_milk_yield = ttk.Entry(frame1, textvariable=milk_yield, font=("Arial", 12),
                             validate="key", validatecommand=(validate_input_cmd, "%P"))
entry_milk_yield.place(x=350, y=430, width=100, height=25)

tvozd = IntVar()
label_tvozd = ttk.Label(frame1, text="Температура воздуха, град. С:", font=("Arial", 12), foreground='blue')
label_tvozd.place(x=50, y=490, width=280, height=20)
entry_tvozd = ttk.Entry(frame1, textvariable=tvozd, font=("Arial", 12),
                        validate="key", validatecommand=(validate_input_int, "%P"))
entry_tvozd.place(x=350, y=490, width=100, height=20)

txt = Help_messages.instruction()
label_instruction = ttk.Label(frame1, text=txt, wraplength=400, font=("Arial", 13))
label_instruction.place(x=500, y=30, width=400, height=500)

# Указываем имя файла с изображением минералов
file_image = 'cowreadme.png'
path_image_readme = os.path.join(current_directory, folder_pictures, file_image)
try:
    # Загружаем изображение
    image_readme = PhotoImage(file=path_image_readme)

    # Устанавливаем размеры изображения
    image_width = 330
    image_height = 450
    image_readme = image_readme.subsample(image_readme.width() // image_width, image_readme.height() // image_height)

    # Создём метку с изображением и устанавливаем размеры
    image_label_readme = Label(frame1, image=image_readme, width=image_width, height=image_height)
    image_label_readme.place(x=950, y=50)
except Exception as e:
    mb.showinfo("Предупреждение", "Не найден файл с изображением /Прочитай/!")

# Создаем таблицу со списком минеральных веществ
tree_minerals = ttk.Treeview(frame3, columns=("mineral", "price"), show="headings")
tree_minerals.place(x=20, y=90, width=550, height=550)

# определяем заголовки
tree_minerals.heading("mineral", text="Минеральное вещество", anchor=W)
tree_minerals.column("#1", stretch=NO, width=470)
tree_minerals.heading("price", text="Цена, руб./кг", anchor=W)
tree_minerals.column("#2", stretch=NO, width=80, anchor=E)

# добавляем вертикальную прокрутку
scrollbar_minerals = ttk.Scrollbar(frame3, orient=VERTICAL, command=tree_minerals.yview)
tree_minerals.configure(yscrollcommand=scrollbar_minerals.set)
scrollbar_minerals.place(x=570, y=90, width=10, height=550)

label_filter = ttk.Label(frame3, text="Фильтр:", font=("Arial", 10))
label_filter.place(x=600, y=70, width=100, height=20)

"""Загружаем прайс цен, установленные пользователем на корма и минеральные вещества"""
download_data_prices()

"""Заполняем таблицу минеральных веществ путем загрузки данных из файла minerals.json"""
update_tree_minerals()

"""Размещаем виджет Combobox в окне. Список list_filter заполняется в функции update_tree_minerals()"""
# по умолчанию будет выбран первый элемент из list_filter
filter_var = StringVar(value=list_filter[0])
combobox = ttk.Combobox(frame3, textvariable=filter_var, values=list_filter, state="readonly")
# Размещаем фильтр с использованием метода place()
combobox.place(x=680, y=70, width=120, height=20)  # Координаты и размеры
# Привязываем обработчик события к Combobox
combobox.bind("<<ComboboxSelected>>", on_combobox_select)
"""Конец размещения"""

# Создаем таблицу с показателями минеральных веществ
tree_min_param: Treeview = ttk.Treeview(frame3, columns=("name", "value", "ed"), show="headings")
tree_min_param.place(x=600, y=100, width=250, height=150)

# определяем заголовки
tree_min_param.heading("name", text="Элемент")
tree_min_param.heading("value", text="Кол-во")
tree_min_param.heading("ed", text="Ед.изм")

tree_min_param.column("#1", stretch=NO, width=120, anchor=W)
tree_min_param.column("#2", stretch=NO, width=70, anchor=E)
tree_min_param.column("#3", stretch=NO, width=50, anchor=W)

# добавляем вертикальную прокрутку
scrollbar_min_param = ttk.Scrollbar(frame3, orient=VERTICAL, command=tree_min_param.yview)
tree_min_param.configure(yscrollcommand=scrollbar_min_param.set)
scrollbar_min_param.place(x=850, y=100, width=10, height=150)

"""Обработчик события "двойной клик левой кнопки мыши" по строке минеральных веществ
Результат: открывается форма ввода количества выбранного минерала и добавление в рацион"""
# tree_minerals.bind("<Double-1>", lambda event, a1="minerals": save_digit(event, a1, tree_minerals))
tree_minerals.bind("<Double-1>", lambda event, a1="minerals": on_item_double_click(event, a1, tree_minerals))

"""Заголовки таблиц на вкладке Минералы"""
label_name_tree_minerals = ttk.Label(frame3,
                                     text="Справочник минеральных веществ:", font=("Arial", 11, "bold"))
label_name_tree_minerals.place(x=20, y=15, width=280, height=20)

btn_help_minerals = Button(frame3, text="?", command=Help_messages.about_tree_minerals)
btn_help_minerals.place(x=300, y=12, width=25, height=25)

label_name_tree_par_minerals = ttk.Label(frame3,
                                         text="Список входящих элементов:", font=("Arial", 11, "bold"))
label_name_tree_par_minerals.place(x=600, y=15, width=300, height=20)

"""Добавляем кнопки работы со справочником минералов"""
btn_change_mineral = Button(frame3, text="Редактировать", command=lambda: open_form_mineral("change"))
btn_change_mineral.place(x=140, y=50, width=100, height=25)

btn_new_mineral = Button(frame3, text="Создать", command=lambda: open_form_mineral("new"))
btn_new_mineral.place(x=250, y=50, width=100, height=25)

btn_copy_mineral = Button(frame3, text="Копировать", command=lambda: open_form_mineral("copy"))
btn_copy_mineral.place(x=360, y=50, width=100, height=25)

btn_delete_mineral = Button(frame3, text="Удалить", command=delete_mineral)
btn_delete_mineral.place(x=470, y=50, width=100, height=25)
"""Конец добавления кнопок"""

# Обработка выделения строки в таблице минеральных веществ
tree_minerals.bind("<<TreeviewSelect>>", item_selected_1)

"""Размещаем текстовое поле, в котором будем выводить текст с описанием параметров минералов"""
discription_minerals = Text(
    frame3, height=25, wrap="word", bg="azure", font=("Verdana", 10), relief=GROOVE, state=NORMAL
)
discription_minerals.place(x=880, y=90, width=410, height=300)
"""Конец размещения"""

# Обработка выделения строки в таблице параметров минеральных веществ
tree_min_param.bind(
    "<<TreeviewSelect>>", lambda event: item_selected_parameters(
        event, tree_min_param, discription_minerals, data_discriptions_parameters_feeds)
)

# Указываем имя файла с изображением минералов
file_image = 'minerals.png'
path_image_minerals = os.path.join(current_directory, folder_pictures, file_image)
try:
    image_minerals = PhotoImage(file=path_image_minerals)

    # Устанавливаем размеры изображения
    image_width = 685
    image_height = 225
    image_minerals = image_minerals.subsample(image_minerals.width() // image_width, image_minerals.height() // image_height)

    # Создаем метку с изображением и установливаем размеры
    image_label = Label(frame3, image=image_minerals, width=image_width, height=image_height)
    image_label.place(x=600, y=410)
    image_label = image_minerals
except Exception as e:
    mb.showinfo("Предупреждение", "Не найден файл с изображением минералов!")


"""Наполняем вкладку Расчеты"""

"""Размещаем название таблицы расчета питательности"""
label_name_tree = ttk.Label(frame4,
                            text="Таблица питательных веществ:", font=("Arial", 11, "bold"))
label_name_tree.place(x=710, y=10, width=350, height=20)

"""Размещаем кнопку справки (?)"""
btn_help_tree = Button(frame4, text="?", command=Help_messages.about_tree_result)
btn_help_tree.place(x=950, y=10, width=25, height=25)

btn_green = Button(frame4, text="?", command=Help_messages.about_tree_green, bg="lightgreen")
btn_green.place(x=980, y=10, width=25, height=25)

btn_yellow = Button(frame4, text="?", command=Help_messages.about_tree_yellow, bg="lightyellow")
btn_yellow.place(x=1010, y=10, width=25, height=25)

btn_red = Button(frame4, text="?", command=Help_messages.about_tree_red, bg="pink")
btn_red.place(x=1040, y=10, width=25, height=25)

"""Создаем таблицу расчета потребности в питательных веществах и фактических значениях в собранном рационе по
по данным из справочников кормов и минеральных веществ"""
# Определяем столбцы перед созданием таблицы расчета потребности в питательных веществах
columns = ("name", "ed_izm", 'real', "real_ud", "need", "need_ud", 'minimum', 'maximum')
tree_main = MyTree(frame4, columns=columns, show="headings", height=19)
# Размещаем таблицу с использованием метода place()
tree_main.place(x=710, y=50, width=550, height=580)  # Координаты и размеры

# определяем заголовки
tree_main.heading("name", text="Показатели", anchor=W)
tree_main.heading("ed_izm", text="Ед.", anchor=W)
tree_main.heading("real", text="Факт", anchor=W)
tree_main.heading("real_ud", text="на кг СВ", anchor=W)
tree_main.heading("need", text="Необх.", anchor=W)
tree_main.heading("need_ud", text="на кг СВ", anchor=W)
tree_main.heading("minimum", text="Мин.", anchor=W)
tree_main.heading("maximum", text="Макс.", anchor=W)

tree_main.column("#1", stretch=NO, width=260)
tree_main.column("#2", stretch=NO, width=50)
tree_main.column("#3", stretch=NO, width=60, anchor=E)
tree_main.column("#4", stretch=NO, width=60, anchor=E)
tree_main.column("#5", stretch=NO, width=60, anchor=E)
tree_main.column("#6", stretch=NO, width=60, anchor=E)
tree_main.column("#7", stretch=NO, width=0, anchor=E)
tree_main.column("#8", stretch=NO, width=0, anchor=E)

# добавляем вертикальную прокрутку
scrollbar = ttk.Scrollbar(frame4, orient=VERTICAL, command=tree_main.yview)
tree_main.configure(yscrollcommand=scrollbar.set)
scrollbar.place(x=1260, y=50, width=10, height=580)

# Создаем таблицу Состав рациона
# Определяем столбцы
columns = ("feed", "kol_vo", 'group', "dry", "energy", "protein", "nxp", "price", "total")

tree_ration: Treeview = ttk.Treeview(frame4, columns=columns, show="headings")
tree_ration.place(x=10, y=50, width=680, height=250)

# определяем заголовки
tree_ration.heading("feed", text="Наименование сырья", anchor=W)
tree_ration.heading("kol_vo", text="Кол-во", anchor=W)
tree_ration.heading("group", text="Группа", anchor=W)
tree_ration.heading("dry", text="СВ", anchor=W)
tree_ration.heading("energy", text="ЧЭЛ", anchor=W)
tree_ration.heading("protein", text="СП", anchor=W)
tree_ration.heading("nxp", text="nXP", anchor=W)
tree_ration.heading("price", text="Цена", anchor=W)
tree_ration.heading("total", text="Сумма", anchor=W)

tree_ration.column("#1", stretch=NO, width=250)
tree_ration.column("#2", stretch=NO, width=50)
tree_ration.column("#3", stretch=NO, width=70)
tree_ration.column("#4", stretch=NO, width=50, anchor=E)
tree_ration.column("#5", stretch=NO, width=50, anchor=E)
tree_ration.column("#6", stretch=NO, width=50, anchor=E)
tree_ration.column("#7", stretch=NO, width=50, anchor=E)
tree_ration.column("#8", stretch=NO, width=50, anchor=E)
tree_ration.column("#9", stretch=NO, width=60, anchor=E)

# добавляем вертикальную прокрутку
scrollbar_feed = ttk.Scrollbar(frame4, orient=VERTICAL, command=tree_ration.yview)
tree_ration.configure(yscrollcommand=scrollbar_feed.set)
scrollbar_feed.place(x=690, y=50, width=15, height=250)

label_help_ration = ttk.Label(frame4, text="Состав рациона:", font=("Arial", 11, "bold"))
label_help_ration.place(x=10, y=10, width=350, height=20)

btn = Button(frame4, text="?", command=Help_messages.about_tree_ration)
btn.place(x=140, y=10, width=25, height=25)

btn_save_ration = Button(frame4, text="Сохранить рацион", command=save_ration)
btn_save_ration.place(x=100, y=310, width=125, height=25)

btn_load_ration = Button(frame4, text="Загрузить рацион", command=load_ration)
btn_load_ration.place(x=250, y=310, width=125, height=25)

btn_export_ration = Button(frame4, text="Экспорт в Excel", command=export_calc)
btn_export_ration.place(x=400, y=310, width=125, height=25)

# Создаем сводную таблицу данных - слева от круговой диаграммы
# Определяем столбцы
columns = ("name", "ed_izm", 'value')
tree_total: Treeview = ttk.Treeview(frame4, columns=columns, show="headings")
tree_total.place(x=10, y=350, width=360, height=280)

# определяем заголовки
tree_total.heading("name", text="Показатель", anchor=W)
tree_total.heading("ed_izm", text="Ед.изм.", anchor=W)
tree_total.heading("value", text="Значение", anchor=W)

tree_total.column("#1", stretch=NO, width=195)
tree_total.column("#2", stretch=NO, width=95)
tree_total.column("#3", stretch=NO, width=70, anchor=E)

# ==============================================================
# Создаем таблицу со списком кормов
tree_feeds = ttk.Treeview(frame2, columns=('name_feed', 'group', 'price'), show="headings", height=19,
                          selectmode="browse")
tree_feeds.place(x=20, y=90, width=570, height=540)

tree_feeds.heading('name_feed', text='Наименование корма')
tree_feeds.column("#1", stretch=NO, width=350, anchor=W)
tree_feeds.heading('group', text='Группа')
tree_feeds.column("#2", stretch=NO, width=130, anchor=W)
tree_feeds.heading('price', text='Цена, руб./кг')
tree_feeds.column("#3", stretch=NO, width=90, anchor=W)
# ----------------------------------------------------
# добавляем вертикальную прокрутку для таблицы кормов
scrollbar_v = ttk.Scrollbar(frame2, orient=VERTICAL, command=tree_feeds.yview)
tree_feeds.configure(yscrollcommand=scrollbar_v.set)
scrollbar_v.place(x=590, y=90, width=10, height=540)
# ----------------------------------------------------
label_name_tree_feeds = ttk.Label(frame2, text="Справочник кормов:", font=("Arial", 11, "bold"))
label_name_tree_feeds.place(x=20, y=15, width=160, height=20)

btn_help_feeds = Button(frame2, text="?", command=Help_messages.about_tree_feeds)
btn_help_feeds.place(x=180, y=10, width=25, height=25)

label_name_tree_parameters = ttk.Label(frame2, text="Показатели кормов:", font=("Arial", 11, "bold"))
label_name_tree_parameters.place(x=620, y=15, width=160, height=20)

btn_help_parameters = Button(frame2, text="?", command=Help_messages.about_tree_parameters)
btn_help_parameters.place(x=780, y=10, width=25, height=25)

"""Добавляем на форму текст с пояснением работы с кнопками"""
label_btns = Label(frame2, text="Используйте кнопки для редактирования", font=("Arial", 10), fg="blue")
label_btns.place(x=620, y=50, width=300, height=25)

"""Добавляем кнопки работы со справочником кормов"""
btn_change_feed = Button(frame2, text="Редактировать", command=lambda: open_form_feed("change"))
btn_change_feed.place(x=160, y=50, width=100, height=25)

btn_new_feed = Button(frame2, text="Создать", command=lambda: open_form_feed("new"))
btn_new_feed.place(x=270, y=50, width=100, height=25)

btn_copy_feed = Button(frame2, text="Копировать", command=lambda: open_form_feed("copy"))
btn_copy_feed.place(x=380, y=50, width=100, height=25)

btn_delete = Button(frame2, text="Удалить", command=delete_feed)
btn_delete.place(x=490, y=50, width=100, height=25)
"""Конец добавления кнопок"""

"""Обновляем визуальную таблицу кормов tree_feeds с учетом обновленных данных в файле feeds.json
Эта же функция вызывается после добавления пользователем нового корма.
Так как новый корм сразу записывается в файл, то эта функция обновляет таблицу кормов с учетом изменений"""
update_dict_feeds()

"""Создаем таблицу, где при выборе корма отображаются его параметры"""
# определяем столбцы таблицы параметров
columns_2 = ('name_parametre', 'value', 'unit')
# создаем таблицу с параметрами выбранного корма
tree_param = ttk.Treeview(frame2, columns=columns_2, show="headings", height=19, selectmode="browse")
tree_param.place(x=620, y=90, width=400, height=540)

tree_param.heading('name_parametre', text='Показатель', anchor=W)
tree_param.column("#1", stretch=NO, width=260)
tree_param.heading('value', text='Значение')
tree_param.column("#2", stretch=NO, width=75, anchor=E)
tree_param.heading('unit', text='Ед. изм.', anchor=W)
tree_param.column("#3", stretch=NO, width=75)

# добавляем вертикальную прокрутку к таблице параметров корма (справа от таблицы кормов)
scrollbar_v2 = ttk.Scrollbar(frame2, orient=VERTICAL, command=tree_param.yview)
tree_param.configure(yscrollcommand=scrollbar_v2.set)
scrollbar_v2.place(x=1020, y=90, width=10, height=540)
"""Завершение создания таблицы параметров кормов"""

"""Заполняем словарь из файла JSON с описанием параметров кормов"""
download_discriptions_parameters_feeds()
"""Размещаем текстовое поле, в котором будем выводить текст с описанием параметров кормов"""
discription_parameter = Text(
    frame2, height=25, wrap="word", bg="azure", font=("Verdana", 10), relief=GROOVE, state=NORMAL
)
discription_parameter.place(x=1040, y=90, width=250, height=540)
"""Конец размещения"""

# Обработка выделения строки в таблице параметров кормов для загрузки текста с описанием параметров кормов
tree_param.bind(
    "<<TreeviewSelect>>", lambda event: item_selected_parameters(
        event, tree_param, discription_parameter, data_discriptions_parameters_feeds)
)

# Назначение исполняющей функции при выборе строки в таблице кормов
# Вызывается функция, с помощью которой заполняется таблица параметров (справа от таблицы кормов)
tree_feeds.bind("<<TreeviewSelect>>", item_selected)

# Назначение исполняющей функции при двойном клике по строке в таблице собранного рациона
# Открывается модальная форма для изменения количества корма в собранном рационе
tree_ration.bind("<Double-1>", change_count)

# Привязываем обработчик события к виджету Notebook
"""Делаем для того, чтобы таблица потребностей пересчитывалась каждый раз при открытии закладки /Расчеты/"""
notebook.bind("<ButtonRelease-1>", on_tab_selected)

"""Обработчик события "двойной клик левой кнопки мыши" по строке кормов
Результат: открывается форма ввода количества выбранного корма и добавление в рацион или изменения цены"""
tree_feeds.bind("<Double-1>", lambda event, a1="feeds": on_item_double_click(event, a1, tree_feeds))

# Вызов функции рисования круговой диаграммы
plot_pie_chart()

# Назначение функции прерывания процесса рисования диаграммы при закрытии программы
# Без этого процесс висит в трее процессов
root.protocol("WM_DELETE_WINDOW", close_plot)

"""Проверяем активацию программы. При отсутствии кода активации или просроченной дате активации программа доступна
в демо режиме, то есть ограничены функции в меню и не доступны кнопки управления"""
check_right_user()

if not data_status or not code_status:
    mb.showinfo("Предупреждение", """ВНИМАНИЕ! Функционал программы ограничен.
    
    Воспользуйтесь разделом "Активация программы" в меню "Файл" """)

root.mainloop()
