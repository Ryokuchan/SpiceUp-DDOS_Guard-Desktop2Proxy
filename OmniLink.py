import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import json
import socket
from datetime import datetime
import webbrowser
import re

class NetworkConnector:
    def __init__(self, root):
        self.root = root
        self.root.title("OmniLink programm")
        self.root.geometry("1400x900")
        self.root.configure(bg="#2b2b2b")
        
        self.center_window()

        self.data_folder = "network_data"
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        self.devices = self.load_devices()
        self.connection_attempts = {}
        self.scanning = False
        
        self.setup_ui()
        self.refresh_device_list()
        
        self.log_to_console("Приложение запущено")
        self.log_to_console("Готов к работе с сетью провайдера")

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Custom.TFrame", background="#3c3c3c")
        style.configure("Custom.TLabel", background="#3c3c3c", foreground="#dcdcdc")

        main_container = ttk.Frame(self.root, style="Custom.TFrame")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_container, style="Custom.TFrame", height=80)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="OmniLink",
            font=("Arial", 18, "bold"),
            bg="#3c3c3c",
            fg="#ffffff"
        )
        title_label.pack(expand=True, pady=20)

        control_frame = ttk.Frame(main_container, style="Custom.TFrame", height=60)
        control_frame.pack(fill="x", pady=(0, 10))
        control_frame.pack_propagate(False)

        buttons_data = [
            ("Добавить IP", self.add_device, "#4a904a"),
            ("Сканировать все", self.scan_all_devices, "#5a7db5"),
            ("Сканировать выбранное", self.scan_selected_device, "#7b5bb5"),
            ("Проверить сеть", self.scan_network, "#9b59b6"),
            ("Очистить", self.clear_devices, "#b54a4a")
        ]

        for text, command, color in buttons_data:
            btn = tk.Button(
                control_frame,
                text=text,
                command=command,
                bg=color,
                fg="#ffffff",
                font=("Arial", 10, "bold"),
                relief="flat",
                padx=15,
                pady=8,
                cursor="hand2",
                bd=0
            )
            btn.pack(side="left", padx=5)

        content_frame = ttk.Frame(main_container, style="Custom.TFrame")
        content_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(content_frame, style="Custom.TFrame", width=800)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        list_header = tk.Label(
            left_frame,
            text="Список устройств",
            font=("Arial", 12, "bold"),
            bg="#4d4d4d",
            fg="#ffffff",
            pady=10
        )
        list_header.pack(fill="x")

        table_container = ttk.Frame(left_frame, style="Custom.TFrame")
        table_container.pack(fill="both", expand=True, pady=(5, 0))

        columns = ("IP", "Статус", "Порт", "Протокол", "ОС", "Последнее сканирование")
        self.device_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            selectmode="browse"
        )

        column_widths = [150, 120, 80, 100, 120, 150]
        for col, width in zip(columns, column_widths):
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=width, minwidth=50)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=scrollbar.set)
        
        self.device_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.device_tree.bind("<<TreeviewSelect>>", self.on_device_select)
        self.device_tree.bind("<Double-1>", self.on_double_click)

        right_frame = ttk.Frame(content_frame, style="Custom.TFrame", width=400)
        right_frame.pack(side="right", fill="both", padx=(5, 0))

        info_header = tk.Label(
            right_frame,
            text="Информация об устройстве",
            font=("Arial", 12, "bold"),
            bg="#4d4d4d",
            fg="#ffffff",
            pady=10
        )
        info_header.pack(fill="x")

        self.info_text = scrolledtext.ScrolledText(
            right_frame,
            font=("Courier New", 10),
            bg="#1e1e1e",
            fg="#dcdcdc",
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill="both", expand=True, pady=5, padx=5)

        action_frame = ttk.Frame(right_frame, style="Custom.TFrame", height=100)
        action_frame.pack(fill="x", pady=(5, 0))
        action_frame.pack_propagate(False)

        action_buttons = [
            ("Подключиться", self.connect_selected),
            ("Пересканировать", self.rescan_selected),
            ("Подробности", self.show_details)
        ]

        for text, command in action_buttons:
            btn = tk.Button(
                action_frame,
                text=text,
                command=command,
                bg="#3498db",
                fg="#ffffff",
                font=("Arial", 9),
                relief="flat",
                padx=10,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side="left", padx=5, pady=10)

        console_frame = ttk.Frame(main_container, style="Custom.TFrame", height=200)
        console_frame.pack(fill="x", pady=(10, 0))
        console_frame.pack_propagate(False)

        console_header = tk.Label(
            console_frame,
            text="Консоль приложения",
            font=("Arial", 12, "bold"),
            bg="#4d4d4d",
            fg="#ffffff",
            pady=10
        )
        console_header.pack(fill="x")

        console_controls = ttk.Frame(console_frame, style="Custom.TFrame", height=30)
        console_controls.pack(fill="x")
        console_controls.pack_propagate(False)

        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            font=("Courier New", 9),
            bg="#1e1e1e",
            fg="#dcdcdc",
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)

        clear_console_btn = tk.Button(
            console_controls,
            text="Очистить консоль",
            command=self.clear_console,
            bg="#e74c3c",
            fg="#ffffff",
            font=("Arial", 8),
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2"
        )
        clear_console_btn.pack(side="right", padx=5, pady=2)

        self.status_frame = tk.Frame(self.root, bg="#34495e", height=25)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Готов к работе",
            font=("Arial", 9),
            bg="#34495e",
            fg="#ecf0f1"
        )
        self.status_label.pack(side="left", padx=10, pady=3)

        self.progress = ttk.Progressbar(
            self.status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side="right", padx=10, pady=3)

    def log_to_console(self, message, message_type="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, log_message)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
        
        print(f"{message_type}: {log_message.strip()}")

    def validate_ip(self, ip):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        parts = ip.split('.')
        for part in parts:
            if not 0 <= int(part) <= 255:
                return False
        return True

    def scan_network(self):
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except:
                return "192.168.1.1"

        base_ip = get_local_ip()
        network_prefix = '.'.join(base_ip.split('.')[:-1])
        
        self.log_to_console(f"Сканирую сеть: {network_prefix}.0/24")
        self.update_status("Сканирование сети...")
        self.progress.start()

        threading.Thread(target=self._scan_network_thread, args=(network_prefix,), daemon=True).start()

    def _scan_network_thread(self, network_prefix):
        found_devices = []
        self.scanning = True
        
        for i in range(1, 255):
            if not self.scanning:
                break
                
            ip = f"{network_prefix}.{i}"
            self.root.after(0, lambda ip=ip: self.update_status(f"Проверка {ip}..."))
            
            if self.ping_host(ip):
                device = {
                    "ip": ip,
                    "status": "Доступно",
                    "port": "Неизвестно",
                    "protocol": "Неизвестно",
                    "os": "Неизвестно",
                    "hostname": self.get_hostname(ip),
                    "last_scan": datetime.now().strftime("%H:%M:%S")
                }
                found_devices.append(device)
                self.log_to_console(f"Найдено устройство: {ip}")
        
        for device in found_devices:
            if not any(d['ip'] == device['ip'] for d in self.devices):
                self.devices.append(device)
        
        self.save_devices()
        self.root.after(0, self.refresh_device_list)
        self.root.after(0, self.progress.stop)
        self.root.after(0, lambda: self.update_status(f"Сканирование завершено. Найдено устройств: {len(found_devices)}"))
        self.root.after(0, lambda: self.log_to_console(f"Сканирование сети завершено. Найдено устройств: {len(found_devices)}"))
        self.scanning = False

    def get_hostname(self, ip):
        try:
            return socket.getfqdn(ip)
        except:
            return "Неизвестно"

    def improved_port_scan(self, ip):
        common_ports = {
            3389: ("RDP", "Remote Desktop Protocol"),
            5900: ("VNC", "Virtual Network Computing"),
            5901: ("VNC", "VNC Display 1"),
            5902: ("VNC", "VNC Display 2"),
            22: ("SSH", "Secure Shell"),
            23: ("Telnet", "Telnet"),
            80: ("HTTP", "HyperText Transfer Protocol"),
            443: ("HTTPS", "HTTP Secure"),
            21: ("FTP", "File Transfer Protocol"),
            25: ("SMTP", "Simple Mail Transfer Protocol"),
            53: ("DNS", "Domain Name System"),
            110: ("POP3", "Post Office Protocol v3"),
            143: ("IMAP", "Internet Message Access Protocol"),
            993: ("IMAPS", "IMAP Secure"),
            995: ("POP3S", "POP3 Secure"),
            1433: ("MSSQL", "Microsoft SQL Server"),
            1434: ("MSSQL", "Microsoft SQL Monitor"),
            1723: ("PPTP", "Point-to-Point Tunneling Protocol"),
            3306: ("MySQL", "MySQL Database"),
            5432: ("PostgreSQL", "PostgreSQL Database"),
            8080: ("HTTP", "HTTP Alternate"),
            8443: ("HTTPS", "HTTPS Alternate"),
            8888: ("HTTP", "HTTP Alternate"),
        }

        open_ports = []
        
        for port, (service, description) in common_ports.items():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        banner = self.get_banner(sock)
                        open_ports.append((port, service, description, banner))
            except:
                continue
        
        return open_ports

    def get_banner(self, sock):
        try:
            sock.settimeout(2)
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner[:100]
        except:
            return ""

    def scan_device_ports(self, device):
        ip = device["ip"]
        
        if not self.ping_host(ip):
            device.update({
                "status": "Недоступно",
                "port": "-",
                "protocol": "-",
                "os": "-",
                "last_scan": datetime.now().strftime("%H:%M:%S %d.%m")
            })
            return

        priority_ports = [
            (3389, "RDP", "Windows"),
            (5900, "VNC", "Linux"),
            (5901, "VNC", "Linux"),
            (5902, "VNC", "Linux"),
            (22, "SSH", "Linux"),
            (23, "Telnet", "Linux"),
            (80, "HTTP", "Web"),
            (443, "HTTPS", "Web"),
            (21, "FTP", "FTP"),
            (25, "SMTP", "Mail"),
            (53, "DNS", "DNS"),
            (110, "POP3", "Mail"),
            (143, "IMAP", "Mail"),
            (8080, "HTTP", "Web"),
            (8443, "HTTPS", "Web"),
            (3388, "RDP", "Windows"),
            (3390, "RDP", "Windows")
        ]

        found_ports = []
        
        for port, protocol, os_type in priority_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        found_ports.append((port, protocol, os_type))
                        if protocol == "RDP":
                            break
            except:
                continue
        
        if found_ports:
            port, protocol, default_os = found_ports[0]
            
            os_info = self.detect_os_banner(ip, port)
            if os_info == "Неизвестная ОС":
                os_info = default_os
            
            device.update({
                "status": "Доступно",
                "port": str(port),
                "protocol": protocol,
                "os": os_info,
                "hostname": self.get_hostname(ip),
                "last_scan": datetime.now().strftime("%H:%M:%S %d.%m"),
                "all_ports": found_ports  # Сохраняем все найденные порты
            })
            
            self.log_to_console(f"{ip}: обнаружена ОС '{os_info}', открыт порт {port} ({protocol})")
        else:
            device.update({
                "status": "Нет открытых портов",
                "port": "-",
                "protocol": "-",
                "os": "-",
                "last_scan": datetime.now().strftime("%H:%M:%S %d.%m")
            })
            self.log_to_console(f"{ip}: нет открытых портов")

    def detect_os_banner(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect((ip, port))
                banner = sock.recv(1024).decode('utf-8', errors='ignore').lower()
                
                if port == 3389:
                    return "Windows (RDP)"
                elif port == 22:
                    if 'windows' in banner:
                        return "Windows (SSH)"
                    elif 'ubuntu' in banner:
                        return "Ubuntu Linux"
                    elif 'debian' in banner:
                        return "Debian Linux"
                    elif 'centos' in banner:
                        return "CentOS Linux"
                    else:
                        return "Linux/Unix"
                elif port == 23:
                    if 'cisco' in banner:
                        return "Cisco IOS"
                    elif 'mikrotik' in banner:
                        return "MikroTik RouterOS"
                    else:
                        return "Network Device"
                elif port in [80, 443]:
                    if 'iis' in banner or 'microsoft' in banner:
                        return "Windows (IIS)"
                    elif 'apache' in banner:
                        return "Linux (Apache)"
                    elif 'nginx' in banner:
                        return "Linux (nginx)"
                    else:
                        return "Web Server"
                
                return "Неизвестная ОС"
        except:
            return "Неизвестная ОС"

    def detect_os_by_banner(self, banner):
        banner_lower = banner.lower()
        
        os_mappings = {
            'Windows Server 2019': ['windows server 2019', 'server 2019'],
            'Windows Server 2016': ['windows server 2016', 'server 2016'],
            'Windows Server 2012': ['windows server 2012', 'server 2012'],
            'Windows 10/11': ['windows 10', 'windows 11', 'win10', 'win11'],
            'Windows 8/8.1': ['windows 8', 'win8'],
            'Windows 7': ['windows 7', 'win7'],
            'Ubuntu Linux': ['ubuntu'],
            'Debian Linux': ['debian'],
            'CentOS Linux': ['centos'],
            'Red Hat Linux': ['red hat', 'redhat'],
            'FreeBSD': ['freebsd'],
            'Cisco IOS': ['cisco'],
            'MikroTik RouterOS': ['mikrotik', 'routeros'],
            'Apache HTTP Server': ['apache', 'httpd'],
            'nginx': ['nginx'],
            'IIS': ['microsoft-iis', 'iis']
        }
        
        for os_name, patterns in os_mappings.items():
            if any(pattern in banner_lower for pattern in patterns):
                return os_name
        
        return "Неизвестная ОС"

    def on_device_select(self, event):
        selection = self.device_tree.selection()
        if selection:
            item = selection[0]
            ip = self.device_tree.item(item, "values")[0]
            device = next((d for d in self.devices if d['ip'] == ip), None)
            if device:
                self.show_device_info(device)

    def on_double_click(self, event):
        selection = self.device_tree.selection()
        if selection:
            self.connect_selected()

    def scan_selected_device(self):
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство для сканирования!")
            return
        
        item = selection[0]
        ip = self.device_tree.item(item, "values")[0]
        device = next((d for d in self.devices if d['ip'] == ip), None)
        
        if device:
            self.update_status(f"Сканирую {device['ip']}...")
            self.log_to_console(f"Сканирую {device['ip']}...")
            threading.Thread(target=self._scan_single_thread, args=(device,), daemon=True).start()

    def connect_selected(self):
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство для подключения!")
            return
        
        item = selection[0]
        ip = self.device_tree.item(item, "values")[0]
        device = next((d for d in self.devices if d['ip'] == ip), None)
        
        if device and device['status'] != "Недоступно":
            self.connect_to_device(device)
        else:
            messagebox.showerror("Ошибка", "Устройство недоступно!")

    def rescan_selected(self):
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство для сканирования!")
            return
        
        item = selection[0]
        ip = self.device_tree.item(item, "values")[0]
        device = next((d for d in self.devices if d['ip'] == ip), None)
        
        if device:
            self.log_to_console(f"Пересканирование устройства: {ip}")
            threading.Thread(target=self._scan_single_thread, args=(device,), daemon=True).start()

    def show_details(self):
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство!")
            return
        
        item = selection[0]
        ip = self.device_tree.item(item, "values")[0]
        device = next((d for d in self.devices if d['ip'] == ip), None)
        
        if device:
            self.show_detailed_info(device)

    def show_detailed_info(self, device):
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Подробности: {device['ip']}")
        detail_window.geometry("700x600")
        detail_window.configure(bg="#2b2b2b")
        detail_window.resizable(True, True)
        
        detail_window.transient(self.root)
        detail_window.grab_set()
        
        text_widget = scrolledtext.ScrolledText(
            detail_window,
            font=("Courier New", 10),
            bg="#1e1e1e",
            fg="#dcdcdc",
            wrap=tk.WORD
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        hostname = device.get('hostname', 'Неизвестно')
        os_info = device.get('os', 'Неизвестно')
        port = device.get('port', '-')
        protocol = device.get('protocol', '-')
        status = device.get('status', 'Неизвестно')
        last_scan = device.get('last_scan', 'Никогда')
        
        all_ports = device.get('all_ports', [])
        
        info_text = f"""
    ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ
    {'='*50}

    Основная информация:
    IP-адрес: {device['ip']}
    Статус подключения: {status}
    Имя хоста: {hostname}
    Операционная система: {os_info}

    Сетевые параметры:
    Основной порт: {port}
    Протокол: {protocol}
    Всего открытых портов: {len(all_ports)}

    Временные метки:
    Последнее сканирование: {last_scan}

    ОТКРЫТЫЕ ПОРТЫ И СЛУЖБЫ:
    {'='*50}
    """
        
        if all_ports:
            sorted_ports = sorted(all_ports, key=lambda x: x[0])
            
            for port_info in sorted_ports:
                if len(port_info) >= 3:
                    port_num, port_protocol, port_os = port_info
                    description = self.get_port_description(port_num)
                    
                    info_text += f"\nПорт {port_num}/tcp - {port_protocol}"
                    info_text += f"\n   Описание: {description}"
                    info_text += f"\n   Тип ОС: {port_os}"
                    
                    if len(port_info) > 3 and port_info[3]:
                        banner = port_info[3]
                        info_text += f"\n   Баннер: {banner}"
                    
                    info_text += "\n" + "-" * 40 + "\n"
        else:
            info_text += "\n   Нет информации об открытых портах\n"

        connection_attempts = self.connection_attempts.get(device['ip'], 0)
        info_text += f"\n\nИСТОРИЯ ПОДКЛЮЧЕНИЙ:\n{'='*30}"
        info_text += f"\nПопыток подключения: {connection_attempts}"
        
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
        
        close_btn = tk.Button(
            detail_window,
            text="Закрыть",
            command=detail_window.destroy,
            bg="#b54a4a",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5
        )
        close_btn.pack(pady=10)

    def get_port_description(self, port):
        port_descriptions = {
            21: "FTP - File Transfer Protocol",
            22: "SSH - Secure Shell",
            23: "Telnet - Terminal Network",
            25: "SMTP - Simple Mail Transfer Protocol",
            53: "DNS - Domain Name System",
            80: "HTTP - HyperText Transfer Protocol",
            110: "POP3 - Post Office Protocol v3",
            143: "IMAP - Internet Message Access Protocol",
            443: "HTTPS - HTTP Secure",
            993: "IMAPS - IMAP Secure",
            995: "POP3S - POP3 Secure",
            1433: "MSSQL - Microsoft SQL Server",
            1434: "MSSQL - Microsoft SQL Monitor",
            1723: "PPTP - Point-to-Point Tunneling Protocol",
            3306: "MySQL - MySQL Database",
            3389: "RDP - Remote Desktop Protocol",
            3390: "RDP - Remote Desktop Protocol (Alternate)",
            5432: "PostgreSQL - PostgreSQL Database",
            5900: "VNC - Virtual Network Computing",
            5901: "VNC - VNC Display 1",
            5902: "VNC - VNC Display 2",
            8080: "HTTP - HTTP Alternate",
            8443: "HTTPS - HTTPS Alternate",
            8888: "HTTP - HTTP Alternate"
        }
        return port_descriptions.get(port, "Неизвестный порт")

    def show_device_info(self, device):
            info_text = f"""IP-адрес: {device['ip']}
        Статус: {device['status']}
        Основной порт: {device.get('port', '-')}
        Протокол: {device.get('protocol', '-')}
        Операционная система: {device.get('os', '-')}
        Имя устройства: {device.get('hostname', 'Неизвестно')}
        Последнее сканирование: {device.get('last_scan', 'Никогда')}

        Открытые порты: {len(device.get('all_ports', []))}"""
            
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, info_text)
            self.info_text.config(state=tk.DISABLED)

    def refresh_device_list(self):
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        for device in self.devices:
            values = (
                device['ip'],
                device['status'],
                device.get('port', '-'),
                device.get('protocol', '-'),
                device.get('os', '-'),
                device.get('last_scan', 'Никогда')
            )
            self.device_tree.insert("", "end", values=values)

    def update_status(self, message):
        self.status_label.config(text=message)

    def add_device(self):
        dialog = IPDialog(self.root, "Добавить IP-адрес")
        if dialog.result:
            ip = dialog.result
            if not self.validate_ip(ip):
                messagebox.showerror("Ошибка", "Неверный формат IP-адреса!")
                return
                
            device = {
                "ip": ip,
                "status": "Не проверено",
                "port": "-",
                "protocol": "-",
                "os": "-",
                "hostname": "Неизвестно",
                "last_scan": "Никогда"
            }
            self.devices.append(device)
            self.save_devices()
            self.refresh_device_list()
            self.update_status(f"Добавлен IP: {ip}")
            self.log_to_console(f"Добавлен IP: {ip}")

    def scan_all_devices(self):
        if not self.devices:
            messagebox.showwarning("Предупреждение", "Список IP-адресов пуст!")
            return
        
        self.update_status("Сканирование всех устройств...")
        self.progress.start()
        self.log_to_console("Запуск сканирования всех устройств...")
        threading.Thread(target=self._scan_all_thread, daemon=True).start()

    def _scan_all_thread(self):
        self.scanning = True
        for i, device in enumerate(self.devices):
            if not self.scanning:
                break
            self.root.after(0, lambda d=device: self.update_status(f"Сканирую {d['ip']}..."))
            self.scan_device_ports(device)
            time.sleep(0.1)
        
        self.scanning = False
        self.root.after(0, self.refresh_device_list)
        self.root.after(0, self.progress.stop)
        self.root.after(0, lambda: self.update_status("Сканирование завершено"))
        self.root.after(0, lambda: self.log_to_console("Сканирование всех устройств завершено"))

    def _scan_single_thread(self, device):
        self.scan_device_ports(device)
        self.root.after(0, self.refresh_device_list)
        self.root.after(0, lambda: self.update_status(f"Сканирование {device['ip']} завершено"))
        self.root.after(0, lambda: self.log_to_console(f"Сканирование {device['ip']} завершено"))

    def ping_host(self, ip):
        try:
            if os.name == 'posix':
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', ip],
                    capture_output=True, text=True, timeout=2
                )
            else:
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '1000', ip],
                    capture_output=True, text=True, timeout=2
                )
            return result.returncode == 0
        except:
            return False

    def connect_to_device(self, device):
        if device["status"] == "Недоступно":
            messagebox.showerror("Ошибка", f"Устройство {device['ip']} недоступно!")
            return
        
        ip = device["ip"]
        port = device.get("port", "")
        
        if port and port != "-":
            if not self.check_port_open(ip, int(port)):
                messagebox.showwarning("Предупреждение", 
                                    f"Порт {port} на устройстве {ip} недоступен!\n"
                                    f"Проверьте правильность порта или выполните повторное сканирование.")
                return
        
        if ip not in self.connection_attempts:
            self.connection_attempts[ip] = 0
        if self.connection_attempts[ip] >= 3:
            if not messagebox.askyesno("Предупреждение", 
                f"Уже было 3 попытки подключения к {ip}. Продолжить?"):
                return

        self.connection_attempts[ip] += 1
        self.show_console(device)

    def check_port_open(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                result = sock.connect_ex((ip, port))
                return result == 0
        except:
            return False

    def show_console(self, device):
        console_window = tk.Toplevel(self.root)
        console_window.title(f"Подключение к {device['ip']}")
        console_window.geometry("800x600")
        console_window.configure(bg="#2b2b2b")
        console_window.resizable(True, True)

        console_header = tk.Label(
            console_window,
            text=f"ПОДКЛЮЧЕНИЕ К {device['ip']}",
            font=("Arial", 14, "bold"),
            bg="#3c3c3c",
            fg="#dcdcdc"
        )
        console_header.pack(pady=(20, 10))

        device_info = f"""
    IP-адрес: {device['ip']}
    Порт: {device['port']}
    Протокол: {device['protocol']}
    ОС: {device['os']}
    Статус: {device['status']}
    Введите логин и пароль для подключения:
    """
        console_text = scrolledtext.ScrolledText(
            console_window,
            font=("Courier New", 11),
            bg="#1e1e1e",
            fg="#dcdcdc",
            height=15,
            width=80,
            wrap=tk.WORD
        )
        console_text.pack(pady=10, padx=20, fill="both", expand=True)
        console_text.insert(tk.END, device_info)
        console_text.config(state=tk.DISABLED)

        input_frame = tk.Frame(console_window, bg="#2b2b2b")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        login_frame = tk.Frame(input_frame, bg="#2b2b2b")
        login_frame.pack(fill="x", pady=5)
        tk.Label(
            login_frame,
            text="Логин:",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#dcdcdc"
        ).pack(side="left")
        login_entry = tk.Entry(
            login_frame,
            font=("Arial", 11),
            bg="#3c3c3c",
            fg="#dcdcdc",
            insertbackground="#dcdcdc",
            relief="flat",
            bd=1
        )
        login_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        password_frame = tk.Frame(input_frame, bg="#2b2b2b")
        password_frame.pack(fill="x", pady=5)
        tk.Label(
            password_frame,
            text="Пароль:",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#dcdcdc"
        ).pack(side="left")
        password_entry = tk.Entry(
            password_frame,
            font=("Arial", 11),
            bg="#3c3c3c",
            fg="#dcdcdc",
            insertbackground="#dcdcdc",
            show="*",
            relief="flat",
            bd=1
        )
        password_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        button_frame = tk.Frame(console_window, bg="#2b2b2b")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def connect():
            username = login_entry.get().strip()
            password = password_entry.get().strip()
            
            if not password:
                messagebox.showwarning("Предупреждение", "Пароль обязателен!")
                return
            
            if not username:
                username = "admin"
                self.log_to_console(f"Логин не указан, используем по умолчанию: {username}")
            
            self.log_to_console(f"Попытка подключения к {device['ip']}:{device['port']} ({device['protocol']})")
            self.log_to_console(f"Пользователь: {username}")
            self.log_to_console(f"Попытка #{self.connection_attempts[device['ip']]}")
            
            success = self.connect_with_credentials(device, username, password)
            if success:
                self.log_to_console(f"Подключение к {device['ip']} запущено успешно!")
                messagebox.showinfo("Успех", f"Подключение к {device['ip']} запущено!")
                console_window.destroy()
            else:
                self.log_to_console(f"Ошибка подключения к {device['ip']}")
                messagebox.showerror("Ошибка", "Не удалось подключиться!")
        
        def cancel():
            console_window.destroy()
        
        connect_btn = tk.Button(
            button_frame,
            text="Подключиться",
            command=connect,
            bg="#4a904a",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        connect_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame,
            text="Отмена",
            command=cancel,
            bg="#b54a4a",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        cancel_btn.pack(side="left")
        
        password_entry.focus()

    def connect_with_credentials(self, device, username, password):
        ip = device["ip"]
        port = device["port"]
        protocol = device["protocol"]
        
        try:
            self.log_to_console(f"Пытаюсь подключиться к {ip}:{port} через {protocol}")
            
            if protocol == "SSH":
                return self.connect_ssh(ip, port, username, password)
            
            elif protocol == "RDP":
                return self.connect_rdp(ip, port)
            
            elif protocol == "HTTP":
                url = f"http://{ip}:{port}"
                self.log_to_console(f"Открываю браузер: {url}")
                webbrowser.open(url)
                self.update_status(f"HTTP подключение к {ip}:{port}")
                return True
            
            elif protocol == "HTTPS":
                url = f"https://{ip}:{port}"
                self.log_to_console(f"Открываю браузер: {url}")
                webbrowser.open(url)
                self.update_status(f"HTTPS подключение к {ip}:{port}")
                return True
            
            elif protocol == "VNC":
                return self.connect_vnc(ip, port)
            
            elif protocol == "FTP":
                url = f"ftp://{ip}:{port}"
                self.log_to_console(f"Открываю FTP: {url}")
                webbrowser.open(url)
                self.update_status(f"FTP подключение к {ip}:{port}")
                return True
            
            else:
                self.log_to_console(f"Протокол {protocol} не поддерживается для автоматического подключения")
                messagebox.showwarning("Предупреждение", 
                                    f"Протокол {protocol} не поддерживается для автоматического подключения.\n"
                                    f"IP: {ip}\nПорт: {port}\n"
                                    f"Используйте специализированное ПО для подключения.")
                return False
        
        except Exception as e:
            error_msg = f"Ошибка подключения к {ip}:{port}: {str(e)}"
            self.log_to_console(error_msg)
            messagebox.showerror("Ошибка", error_msg)
            return False

    def connect_ssh(self, ip, port, username, password):
        if self.try_putty_ssh(ip, port, username, password):
            return True
        if self.try_windows_ssh(ip, port, username, password):
            return True
        self.show_ssh_instructions(ip, port, username, password)
        return True

    def try_putty_ssh(self, ip, port, username, password):
        try:
            putty_paths = [
                r"C:\Program Files\PuTTY\putty.exe",
                r"C:\Program Files (x86)\PuTTY\putty.exe",
                r"C:\Windows\System32\putty.exe",
                "putty.exe"
            ]
            
            for path in putty_paths:
                if os.path.exists(path):
                    if username and password:
                        cmd = f'"{path}" {username}@{ip} -P {port} -ssh -pw {password}'
                    else:
                        cmd = f'"{path}" {ip} -P {port} -ssh'
                    
                    self.log_to_console(f"Запускаю PuTTY: {cmd}")
                    subprocess.Popen(cmd, shell=True)
                    return True
            return False
        except Exception as e:
            self.log_to_console(f"Ошибка PuTTY: {e}")
            return False

    def try_windows_ssh(self, ip, port, username, password):
        try:
            if username:
                cmd = f'ssh {username}@{ip} -p {port}'
            else:
                cmd = f'ssh {ip} -p {port}'
            
            self.log_to_console(f"Запускаю Windows SSH: {cmd}")
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception as e:
            self.log_to_console(f"Ошибка Windows SSH: {e}")
            return False

    def connect_rdp(self, ip, port):
        try:
            mstsc_paths = [
                r"C:\Windows\System32\mstsc.exe",
                r"C:\Windows\SysWOW64\mstsc.exe",
                "mstsc.exe"
            ]
            mstsc_path = None
            for path in mstsc_paths:
                if os.path.exists(path):
                    mstsc_path = path
                    break
            if mstsc_path:
                cmd = f'"{mstsc_path}" /v:{ip}:{port}'
                self.log_to_console(f"Запускаю RDP: {cmd}")
                subprocess.Popen(cmd, shell=True)
                return True
            else:
                self.log_to_console("mstsc не найден, показываю инструкции")
                self.show_rdp_instructions(ip, port)
                return True
        except Exception as e:
            self.log_to_console(f"Ошибка RDP подключения: {e}")
            return False

    def connect_vnc(self, ip, port):
        try:
            vnc_clients = [
                ('vncviewer', f'vncviewer {ip}:{port}'),
                ('xtightvncviewer', f'xtightvncviewer {ip}:{port}'),
                ('vncviewer.exe', f'vncviewer {ip}:{port}'),
                ('tightvnc.exe', f'tightvnc {ip}:{port}')
            ]
            
            for client_name, client_cmd in vnc_clients:
                try:
                    if os.name == 'posix':
                        result = subprocess.run(['which', client_name], capture_output=True)
                    else:
                        result = subprocess.run(['where', client_name], capture_output=True)
                    
                    if result.returncode == 0:
                        self.log_to_console(f"Найден {client_name}, запускаю: {client_cmd}")
                        subprocess.Popen(client_cmd, shell=True)
                        self.log_to_console(f"VNC подключение через {client_name} запущено")
                        return True
                except:
                    continue

            self.show_vnc_instructions(ip, port)
            return True
            
        except Exception as e:
            self.log_to_console(f"Ошибка VNC подключения: {e}")
            self.show_vnc_instructions(ip, port)
            return True

    def clear_console(self):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)
        self.log_to_console("Консоль очищена")

    def clear_devices(self):
        if messagebox.askyesno("Подтверждение", "Удалить все IP-адреса?"):
            self.devices = []
            self.save_devices()
            self.refresh_device_list()
            self.update_status("Список очищен")
            self.log_to_console("Список устройств очищен")

    def load_devices(self):
        file_path = os.path.join(self.data_folder, "devices.json")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log_to_console(f"Ошибка загрузки данных: {e}")
        return []

    def save_devices(self):
        file_path = os.path.join(self.data_folder, "devices.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_to_console(f"Ошибка сохранения: {e}")


class IPDialog:
    def __init__(self, parent, title):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.configure(bg="#2b2b2b")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        tk.Label(
            self.dialog,
            text="Введите IP-адрес:",
            font=("Arial", 11),
            bg="#2b2b2b",
            fg="#dcdcdc"
        ).pack(pady=10)

        self.ip_entry = tk.Entry(
            self.dialog,
            font=("Arial", 11),
            width=30,
            bg="#3c3c3c",
            fg="#dcdcdc",
            insertbackground="#dcdcdc"
        )
        self.ip_entry.pack(pady=5, padx=20, fill="x")
        self.ip_entry.bind("<Return>", lambda e: self.ok())

        button_frame = tk.Frame(self.dialog, bg="#2b2b2b")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Добавить",
            command=self.ok,
            bg="#27ae60",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Отмена",
            command=self.cancel,
            bg="#e74c3c",
            fg="#ffffff",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=5
        ).pack(side="left", padx=5)

        self.ip_entry.focus()
        self.dialog.wait_window()
    
    def ok(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("Предупреждение", "Введите IP-адрес!")
            return
        self.result = ip
        self.dialog.destroy()
    
    def cancel(self):
        self.dialog.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkConnector(root)
    root.mainloop()