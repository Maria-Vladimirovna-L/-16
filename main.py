import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- Настройки ---
API_KEY = 'YOUR_API_KEY'  # Замените на свой ключ
API_URL = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
HISTORY_FILE = 'history.json'

# --- Функции работы с историей ---
def load_history():
    """Загружает историю конвертаций из JSON."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    """Сохраняет историю конвертаций в JSON."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        messagebox.showerror('Ошибка записи', f'Не удалось сохранить историю: {e}')

# --- Функции интерфейса ---
def get_currencies():
    """Получает список доступных валют с помощью API."""
    try:
        response = requests.get(API_URL)
        data = response.json()
        if data['result'] == 'success':
            return sorted(data['conversion_rates'].keys())
    except Exception as e:
        messagebox.showerror('Ошибка сети', f'Не удалось получить список валют: {e}')
    # Если API недоступно, возвращаем базовые валюты
    return ['USD', 'EUR', 'RUB', 'GBP', 'JPY']

def convert():
    """Выполняет конвертацию и обновляет историю."""
    from_cur = from_var.get()
    to_cur = to_var.get()
    amount_str = amount_entry.get()

    # Проверка ввода
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Сумма должна быть больше нуля.")
    except ValueError:
        messagebox.showerror('Ошибка ввода', 'Пожалуйста, введите положительное число в поле суммы.')
        return

    try:
        # Запрос к API для получения курса
        response = requests.get(f'{API_URL}/{from_cur}')
        data = response.json()
        
        if data['result'] != 'success':
            raise Exception(f"API Error: {data.get('error-type', 'Unknown error')}")
        
        rate = data['conversion_rates'][to_cur]
        result = round(amount * rate, 2)

        # Обновление результата на экране
        result_label.config(text=f'Результат: {result} {to_cur}')

        # Добавление в историю
        entry = {
            "from": from_cur,
            "to": to_cur,
            "amount": amount,
            "result": result,
            "rate": rate,
            "timestamp": data['time_last_update_utc']
        }
        
        history.insert(0, entry) # Добавляем в начало списка
        if len(history) > 20: # Ограничиваем историю 20 записями
            history.pop()
        
        save_history(history)
        update_history_table()

    except requests.exceptions.RequestException as e:
        messagebox.showerror('Ошибка сети', 'Проверьте подключение к интернету и правильность API-ключа.')
    except KeyError:
        messagebox.showerror('Ошибка данных', 'Не удалось получить курс для выбранных валют.')
    except Exception as e:
        messagebox.showerror('Ошибка', str(e))

def update_history_table():
    """Обновляет виджет таблицы с историей."""
    for i in history_tree.get_children():
        history_tree.delete(i)
    for entry in history:
        history_tree.insert('', 'end', values=(
            entry['timestamp'],
            f"{entry['amount']} {entry['from']}",
            f"→ {entry['result']} {entry['to']}",
            f"1 {entry['from']} = {entry['rate']} {entry['to']}"
        ))

# --- Инициализация данных ---
history = load_history()

# --- Создание окна ---
root = tk.Tk()
root.title('Currency Converter')
root.geometry('700x500')

# Получаем список валют
currencies = get_currencies()

# Вкладки (Notebook) для удобства
notebook = ttk.Notebook(root)
notebook.pack(padx=10, pady=5, fill='both', expand=True)

# Вкладка "Конвертация"
conv_frame = ttk.Frame(notebook)
notebook.add(conv_frame, text='Конвертировать')

# Виджеты для конвертации (расположение Grid)
tk.Label(conv_frame, text='Из:').grid(row=0, column=0, padx=5, pady=5, sticky='e')
tk.Label(conv_frame, text='В:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
tk.Label(conv_frame, text='Сумма:').grid(row=2, column=0, padx=5, pady=5, sticky='e')

from_var = tk.StringVar(value='USD')
to_var = tk.StringVar(value='EUR')
amount_entry = tk.Entry(conv_frame)

from_menu = ttk.OptionMenu(conv_frame, from_var, *currencies)
to_menu = ttk.OptionMenu(conv_frame, to_var, *currencies)

from_menu.grid(row=0, column=1, padx=5, pady=5)
to_menu.grid(row=1, column=1, padx=5, pady=5)
amount_entry.grid(row=2, column=1, padx=5, pady=5)

convert_btn = tk.Button(conv_frame, text='Конвертировать', command=convert)
convert_btn.grid(row=3, column=0, columnspan=2, pady=10)

result_label = tk.Label(conv_frame, text='Результат: ', font=('Arial', 12))
result_label.grid(row=4, column=0, columnspan=2, pady=5)


# Вкладка "История"
hist_frame = ttk.Frame(notebook)
notebook.add(hist_frame, text='История')

history_tree = ttk.Treeview(hist_frame,
                            columns=('Дата', 'Операция', 'Курс'),
                            show='headings')
history_tree.heading('Дата', text='Дата и время')
history_tree.heading('Операция', text='Операция')
history_tree.heading('Курс', text='Курс обмена')
history_tree.column('Дата', width=180)
history_tree.column('Операция', width=200)
history_tree.column('Курс', width=180)
history_tree.pack(padx=10, pady=10, fill='both', expand=True)

update_history_table()
root.mainloop()
