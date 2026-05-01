#!/usr/bin/env python3
"""
GUI-менеджер виртуальных машин на QEMU (Tkinter).
"""
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

CONFIG_FILE = "vm_configs.json"
DEFAULT_ISO_DIR = "./isos"
DEFAULT_DISK_DIR = "./disks"

def ensure_dirs():
    Path(DEFAULT_ISO_DIR).mkdir(parents=True, exist_ok=True)
    Path(DEFAULT_DISK_DIR).mkdir(parents=True, exist_ok=True)

class VMManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Менеджер виртуальных машин (QEMU)")
        self.root.geometry("700x500")
        self.root.resizable(True, True)

        # Загружаем конфиг
        self.configs = self.load_configs()

        # Создаём интерфейс
        self.create_widgets()
        self.refresh_list()

    # ---------- Работа с конфигом ----------
    def load_configs(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_configs(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.configs, f, indent=4, ensure_ascii=False)

    # ---------- UI-компоненты ----------
    def create_widgets(self):
        # Рамка для списка
        list_frame = ttk.LabelFrame(self.root, text="Ваши виртуальные машины", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Treeview: имя, память, ISO, диск
        self.tree = ttk.Treeview(list_frame, columns=("memory", "iso", "disk"), show="headings", selectmode="browse")
        self.tree.heading("memory", text="ОЗУ (МБ)")
        self.tree.heading("iso", text="ISO образ")
        self.tree.heading("disk", text="Виртуальный диск")
        self.tree.column("memory", width=80, anchor=tk.CENTER)
        self.tree.column("iso", width=250)
        self.tree.column("disk", width=250)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Панель кнопок
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Создать ВМ", command=self.create_vm).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Запустить", command=self.start_vm).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_vm).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Обновить список", command=self.refresh_list).pack(side=tk.RIGHT, padx=2)

        # Строка состояния
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_list(self):
        """Обновляет содержимое Treeview из self.configs."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        for name, cfg in self.configs.items():
            self.tree.insert("", tk.END, iid=name, values=(cfg.get("memory", ""), cfg.get("iso", ""), cfg.get("disk", "")))
        self.status_var.set(f"Загружено ВМ: {len(self.configs)}")

    # ---------- Операции с ВМ ----------
    def create_disk(self, disk_path, size_gb):
        """Создаёт виртуальный диск, возвращает True при успехе."""
        if os.path.exists(disk_path):
            overwrite = messagebox.askyesno("Файл существует", f"Диск {disk_path} уже существует.\nПерезаписать?")
            if not overwrite:
                return False
        cmd = ["qemu-img", "create", "-f", "qcow2", disk_path, f"{size_gb}G"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка создания диска", f"qemu-img завершился с ошибкой:\n{e.stderr}")
            return False
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "qemu-img не найден. Установите QEMU и добавьте в PATH.")
            return False

    def create_vm(self):
        """Диалог создания новой ВМ."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание виртуальной машины")
        dialog.geometry("450x350")
        dialog.resizable(False, False)
        dialog.grab_set()  # Модальное

        ttk.Label(dialog, text="Имя ВМ:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=35).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="ISO образ:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        # Получаем список .iso в папке
        isos = self.list_isos()
        if not isos:
            messagebox.showwarning("Нет ISO", f"В папке {DEFAULT_ISO_DIR} нет .iso файлов.\nДобавьте установочный образ.", parent=dialog)
            dialog.destroy()
            return
        iso_var = tk.StringVar()
        iso_combo = ttk.Combobox(dialog, textvariable=iso_var, values=isos, state="readonly", width=32)
        iso_combo.grid(row=1, column=1, padx=10, pady=5)
        iso_combo.current(0)

        ttk.Label(dialog, text="Размер диска (ГБ):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        disk_size_var = tk.StringVar(value="20")
        ttk.Entry(dialog, textvariable=disk_size_var, width=10).grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)

        ttk.Label(dialog, text="ОЗУ (МБ):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        mem_var = tk.StringVar(value="2048")
        ttk.Entry(dialog, textvariable=mem_var, width=10).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        # Статус
        status_label = ttk.Label(dialog, text="")
        status_label.grid(row=4, column=0, columnspan=2, pady=10)

        def do_create():
            name = name_var.get().strip()
            if not name:
                status_label.config(text="Введите имя!", foreground="red")
                return
            if name in self.configs:
                status_label.config(text="ВМ с таким именем уже существует!", foreground="red")
                return
            if not iso_var.get():
                status_label.config(text="Выберите ISO!", foreground="red")
                return
            try:
                disk_size = int(disk_size_var.get())
            except ValueError:
                status_label.config(text="Размер диска должен быть целым числом!", foreground="red")
                return
            try:
                memory = int(mem_var.get())
            except ValueError:
                status_label.config(text="Объём ОЗУ должен быть целым числом!", foreground="red")
                return

            iso_path = os.path.join(DEFAULT_ISO_DIR, iso_var.get())
            disk_filename = f"{name}.qcow2"
            disk_path = os.path.join(DEFAULT_DISK_DIR, disk_filename)

            # Создаём диск
            if not self.create_disk(disk_path, disk_size):
                return

            # Сохраняем конфиг
            self.configs[name] = {
                "iso": iso_path,
                "disk": disk_path,
                "memory": memory
            }
            self.save_configs()
            self.refresh_list()
            messagebox.showinfo("Успех", f"Виртуальная машина '{name}' создана!", parent=dialog)
            dialog.destroy()

        ttk.Button(dialog, text="Создать", command=do_create).grid(row=5, column=0, columnspan=2, pady=15)
        # Центрирование окна
        dialog.update_idletasks()

    def list_isos(self):
        """Возвращает список имён файлов .iso в папке isos."""
        if not os.path.isdir(DEFAULT_ISO_DIR):
            return []
        return sorted([f for f in os.listdir(DEFAULT_ISO_DIR) if f.lower().endswith(".iso")])

    def start_vm(self):
        """Запускает выбранную в списке ВМ."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Не выбрано", "Выберите виртуальную машину в списке.")
            return
        name = selection[0]
        vm = self.configs[name]

        iso = vm["iso"]
        disk = vm["disk"]
        memory = vm["memory"]

        if not os.path.exists(disk):
            messagebox.showerror("Ошибка", f"Виртуальный диск {disk} не найден.")
            return
        if not os.path.exists(iso):
            messagebox.showerror("Ошибка", f"ISO образ {iso} не найден.")
            return

        cmd = [
            "qemu-system-x86_64",
            "-name", name,
            "-m", str(memory),
            "-drive", f"file={disk},format=qcow2",
            "-cdrom", iso,
            "-boot", "d",
            "-display", "sdl",
            "-usb", "-device", "usb-tablet"
        ]
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.status_var.set(f"ВМ '{name}' запущена в отдельном окне.")
        except FileNotFoundError:
            messagebox.showerror("QEMU не найден", "Программа qemu-system-x86_64 не обнаружена.\nПроверьте установку QEMU и PATH.")
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    def delete_vm(self):
        """Удаляет выбранную ВМ и её диск."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Не выбрано", "Выберите виртуальную машину.")
            return
        name = selection[0]
        vm = self.configs[name]
        disk = vm.get("disk", "")

        if messagebox.askyesno("Подтверждение", f"Удалить ВМ '{name}' и её виртуальный диск?\n{disk}"):
            try:
                if os.path.exists(disk):
                    os.remove(disk)
            except OSError as e:
                messagebox.showerror("Ошибка удаления диска", str(e))
            del self.configs[name]
            self.save_configs()
            self.refresh_list()
            self.status_var.set(f"ВМ '{name}' удалена.")

if __name__ == "__main__":
    ensure_dirs()
    root = tk.Tk()
    app = VMManagerGUI(root)
    root.mainloop()