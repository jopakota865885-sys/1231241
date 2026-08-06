import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass
import urllib.request
import urllib.error

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
@dataclass
class AppConfig:
    server_url: str = "https://jour.pythonanywhere.com"
    session_file: str = "session.json"
    timeout: int = 15
    min_login_length: int = 3
    min_password_length: int = 4
    default_subscription_price: float = 4000.0


# ============================================================
# ИКОНКА ПРИЛОЖЕНИЯ
# ============================================================
def get_icon_path():
    """Получить путь к иконке (работает и в собранном виде)"""
    try:
        if getattr(sys, 'frozen', False):
            # Программа собрана PyInstaller
            base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # Запуск из исходников
            base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, 'icon.ico')
        return path if os.path.exists(path) else None
    except:
        return None


# ============================================================
# ТЕМЫ ОФОРМЛЕНИЯ
# ============================================================
PALETTES = {
    'dark': {
        'BG_PRIMARY': "#1e1e2e",
        'BG_SECONDARY': "#2d2d3f",
        'BG_CARD': "#363649",
        'BG_HOVER': "#40405a",
        'ACCENT_BLUE': "#7aa2f7",
        'ACCENT_GREEN': "#9ece6a",
        'ACCENT_RED': "#f7768e",
        'ACCENT_YELLOW': "#e0af68",
        'ACCENT_PURPLE': "#bb9af7",
        'TEXT_PRIMARY': "#c0caf5",
        'TEXT_SECONDARY': "#a9b1d6",
        'TEXT_MUTED': "#565f89",
        'BORDER': "#414868",
        'BTN_PRIMARY': "#7aa2f7",
    },
    'light': {
        'BG_PRIMARY': "#f2f4fa",
        'BG_SECONDARY': "#e3e7f2",
        'BG_CARD': "#ffffff",
        'BG_HOVER': "#d9dfee",
        'ACCENT_BLUE': "#3b6fd4",
        'ACCENT_GREEN': "#3f9e63",
        'ACCENT_RED': "#d4536a",
        'ACCENT_YELLOW': "#b98322",
        'ACCENT_PURPLE': "#7c5cbf",
        'TEXT_PRIMARY': "#232936",
        'TEXT_SECONDARY': "#4a5165",
        'TEXT_MUTED': "#8a91a8",
        'BORDER': "#c5cad9",
        'BTN_PRIMARY': "#3b6fd4",
    }
}


class _Colors:
    """Динамическая палитра — меняется при переключении темы"""
    def set_theme(self, name):
        for key, value in PALETTES[name].items():
            setattr(self, key, value)


Colors = _Colors()


class Theme:
    """Менеджер темы с сохранением в файл"""
    current = 'dark'
    
    @staticmethod
    def load():
        try:
            if os.path.exists('theme.json'):
                with open('theme.json', 'r', encoding='utf-8') as f:
                    Theme.current = json.load(f).get('theme', 'dark')
        except:
            pass
        Colors.set_theme(Theme.current)
    
    @staticmethod
    def save():
        try:
            with open('theme.json', 'w', encoding='utf-8') as f:
                json.dump({'theme': Theme.current}, f)
        except:
            pass
    
    @staticmethod
    def toggle(root_widget):
        old = Theme.current
        new = 'light' if old == 'dark' else 'dark'
        Theme.current = new
        Colors.set_theme(new)
        Theme.save()
        setup_styles()
        
        cmap = {PALETTES[old][k]: PALETTES[new][k] for k in PALETTES[old]}
        recolor_tree(root_widget, cmap)
        return new


class Fonts:
    TITLE = ("Segoe UI", 18, "bold")
    SUBTITLE = ("Segoe UI", 14, "bold")
    HEADING = ("Segoe UI", 12, "bold")
    BODY = ("Segoe UI", 11)
    SMALL = ("Segoe UI", 9)
    BUTTON = ("Segoe UI", 10, "bold")


# ============================================================
# ПЕРЕКРАСКА ВИДЖЕТОВ ПРИ СМЕНЕ ТЕМЫ
# ============================================================
def _recolor_widget(w, cmap):
    opts = ['bg', 'fg', 'activebackground', 'activeforeground',
            'insertbackground', 'highlightbackground', 'highlightcolor',
            'selectbackground', 'selectforeground']
    for opt in opts:
        try:
            val = str(w.cget(opt))
            if val in cmap:
                w.config(**{opt: cmap[val]})
        except Exception:
            pass
    if hasattr(w, 'default_bg') and str(w.default_bg) in cmap:
        w.default_bg = cmap[str(w.default_bg)]
    if hasattr(w, 'hover_bg') and str(w.hover_bg) in cmap:
        w.hover_bg = cmap[str(w.hover_bg)]


def recolor_tree(w, cmap):
    _recolor_widget(w, cmap)
    for child in w.winfo_children():
        recolor_tree(child, cmap)


# ============================================================
# МОДЕЛИ ДАННЫХ
# ============================================================
@dataclass
class Student:
    id: int
    name: str
    deleted: bool = False
    
    def to_dict(self) -> Dict:
        return {'id': self.id, 'name': self.name, 'deleted': self.deleted}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Student':
        return cls(data.get('id', 0), data.get('name', ''), data.get('deleted', False))


@dataclass
class Lesson:
    id: int
    datetime: str
    
    def to_dict(self) -> Dict:
        return {'id': self.id, 'datetime': self.datetime}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Lesson':
        return cls(data.get('id', 0), data.get('datetime', ''))


@dataclass
class Group:
    id: str
    name: str
    students: List[Student]
    lessons: List[Lesson]
    attendance: Dict[int, Dict[int, bool]]
    subscription_price: float
    next_student_id: int = 1
    next_lesson_id: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'students': [s.to_dict() for s in self.students],
            'lessons': [l.to_dict() for l in self.lessons],
            'attendance': {str(k): {str(lk): lv for lk, lv in v.items()} 
                          for k, v in self.attendance.items()},
            'subscription_price': self.subscription_price,
            'next_student_id': self.next_student_id,
            'next_lesson_id': self.next_lesson_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Group':
        students = [Student.from_dict(s) for s in data.get('students', [])]
        lessons = [Lesson.from_dict(l) for l in data.get('lessons', [])]
        attendance = {}
        for k, v in data.get('attendance', {}).items():
            attendance[int(k)] = {int(lk): lv for lk, lv in v.items()}
        return cls(
            id=data.get('id', 'default'),
            name=data.get('name', 'Группа'),
            students=students,
            lessons=lessons,
            attendance=attendance,
            subscription_price=data.get('subscription_price', 4000.0),
            next_student_id=data.get('next_student_id', 1),
            next_lesson_id=data.get('next_lesson_id', 1)
        )


@dataclass
class UserData:
    login: str
    groups: Dict[str, Group]
    current_group_id: str
    
    def to_dict(self) -> Dict:
        return {
            'login': self.login,
            'groups': {gid: g.to_dict() for gid, g in self.groups.items()},
            'current_group': self.current_group_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserData':
        groups = {}
        for gid, gdata in data.get('groups', {}).items():
            groups[gid] = Group.from_dict(gdata)
        return cls(
            login=data.get('login', ''),
            groups=groups,
            current_group_id=data.get('current_group', 'default')
        )


# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================
def log_error(message: str, error: Exception = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("client_error.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            if error:
                f.write(f"Error: {str(error)}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
            f.write("\n")
    except:
        pass


# ============================================================
# СЕРВИСЫ
# ============================================================
class AttendanceService:
    @staticmethod
    def calculate_percent(attendance: Dict[int, bool]) -> float:
        if not attendance:
            return 0.0
        attended = sum(1 for v in attendance.values() if v)
        return attended / len(attendance)
    
    @staticmethod
    def calculate_cost(percent: float, price: float) -> float:
        return price * percent


# ============================================================
# РАБОТА С СЕРВЕРОМ
# ============================================================
def http_request(url: str, data: Optional[Dict] = None, 
                method: str = 'GET', timeout: int = 10) -> tuple:
    try:
        if data is not None:
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                url, data=body, method=method,
                headers={'Content-Type': 'application/json'}
            )
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode('utf-8'))
        except:
            err_data = {"error": str(e)}
        return e.code, err_data
    except urllib.error.URLError as e:
        return 0, {"error": f"Сервер недоступен: {str(e.reason)}"}
    except Exception as e:
        return 0, {"error": str(e)}


# ============================================================
# ЛОКАЛЬНОЕ ХРАНЕНИЕ
# ============================================================
def load_local_data(login: str) -> Optional[UserData]:
    file_path = f"jour_{login}_local.json"
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return UserData.from_dict(json.load(f))
    except Exception as e:
        log_error("Ошибка загрузки локальных данных", e)
        return None


def save_local_data(user_data: UserData) -> bool:
    file_path = f"jour_{user_data.login}_local.json"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(user_data.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_error("Ошибка сохранения локальных данных", e)
        return False


def create_default_user_data(login: str) -> UserData:
    default_group = Group(
        id="default", name="Моя первая группа",
        students=[], lessons=[], attendance={},
        subscription_price=4000.0
    )
    return UserData(
        login=login,
        groups={"default": default_group},
        current_group_id="default"
    )


# ============================================================
# СОВРЕМЕННЫЕ ВИДЖЕТЫ
# ============================================================
class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None, 
                 bg=None, fg="#ffffff", hover_bg=None, width=15, **kwargs):
        self.default_bg = bg or Colors.BTN_PRIMARY
        self.hover_bg = hover_bg or Colors.BG_HOVER
        
        super().__init__(
            parent, text=text, command=command,
            bg=self.default_bg, fg=fg, activebackground=self.hover_bg,
            activeforeground=fg, relief=tk.FLAT,
            font=Fonts.BUTTON, width=width,
            cursor="hand2", bd=0, padx=15, pady=8, **kwargs
        )
        
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=self.hover_bg)
    
    def _on_leave(self, event):
        self.config(bg=self.default_bg)


class ModernEntry(tk.Entry):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.TEXT_PRIMARY,
            relief=tk.FLAT, font=Fonts.BODY,
            highlightthickness=2, highlightcolor=Colors.ACCENT_BLUE,
            highlightbackground=Colors.BORDER, **kwargs
        )


class ModernFrame(tk.Frame):
    def __init__(self, parent, bg=None, **kwargs):
        super().__init__(parent, bg=bg or Colors.BG_CARD, **kwargs)


class StatusBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=Colors.BG_SECONDARY, height=30)
        
        self.status_label = tk.Label(
            self, text="Готов к работе", bg=Colors.BG_SECONDARY,
            fg=Colors.TEXT_MUTED, font=Fonts.SMALL, anchor='w'
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=3)
        
        self.mode_label = tk.Label(
            self, text="", bg=Colors.BG_SECONDARY,
            fg=Colors.ACCENT_GREEN, font=Fonts.SMALL, anchor='e'
        )
        self.mode_label.pack(side=tk.RIGHT, padx=10, pady=3)
    
    def set_status(self, text, color=None):
        self.status_label.config(text=text, fg=color or Colors.TEXT_MUTED)
    
    def set_mode(self, text, color=None):
        self.mode_label.config(text=text, fg=color or Colors.ACCENT_GREEN)


# ============================================================
# НАСТРОЙКА СТИЛЕЙ
# ============================================================
def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure("TNotebook", background=Colors.BG_PRIMARY, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=Colors.BG_SECONDARY, foreground=Colors.TEXT_PRIMARY,
        font=Fonts.BUTTON, padding=[15, 8]
    )
    style.map(
        "TNotebook.Tab",
        background=[('selected', Colors.ACCENT_BLUE)],
        foreground=[('selected', '#ffffff')]
    )
    
    style.configure(
        "Modern.Treeview",
        background=Colors.BG_CARD, foreground=Colors.TEXT_PRIMARY,
        fieldbackground=Colors.BG_CARD, font=Fonts.BODY, rowheight=35
    )
    style.configure(
        "Modern.Treeview.Heading",
        background=Colors.BG_SECONDARY, foreground=Colors.TEXT_PRIMARY,
        font=Fonts.HEADING
    )
    style.map(
        "Modern.Treeview",
        background=[('selected', Colors.ACCENT_BLUE)],
        foreground=[('selected', '#ffffff')]
    )
    
    style.configure(
        "Modern.TCombobox",
        fieldbackground=Colors.BG_CARD,
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY
    )


# ============================================================
# ТЕМОВЫЕ ДИАЛОГИ (замена системным)
# ============================================================
def _get_parent():
    return getattr(tk, '_default_root', None)


def _center_window(win, width, height):
    win.update_idletasks()
    x = (win.winfo_screenwidth() - width) // 2
    y = (win.winfo_screenheight() - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


class DarkMessagebox:
    @staticmethod
    def _show(title, message, icon, color):
        parent = _get_parent()
        win = tk.Toplevel(parent)
        win.title(title)
        win.configure(bg=Colors.BG_PRIMARY)
        win.resizable(False, False)
        if parent:
            win.transient(parent)
        
        # Иконка для диалога
        icon_path = get_icon_path()
        if icon_path:
            try:
                win.iconbitmap(icon_path)
            except:
                pass
        
        frame = tk.Frame(win, bg=Colors.BG_PRIMARY)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        tk.Label(frame, text=icon, font=("Segoe UI", 28),
                 bg=Colors.BG_PRIMARY, fg=color).pack(anchor='w')
        tk.Label(frame, text=title, font=Fonts.HEADING,
                 bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY,
                 anchor='w', justify='left').pack(fill=tk.X, pady=(5, 5))
        tk.Label(frame, text=message, font=Fonts.BODY,
                 bg=Colors.BG_PRIMARY, fg=Colors.TEXT_SECONDARY,
                 anchor='w', justify='left', wraplength=360).pack(fill=tk.X)
        
        ModernButton(frame, text="ОК", command=win.destroy,
                     bg=color, width=12).pack(pady=(20, 0))
        
        _center_window(win, 440, 230)
        win.grab_set()
        win.wait_window()

    @staticmethod
    def showinfo(title, message):
        DarkMessagebox._show(title, message, "ℹ️", Colors.ACCENT_BLUE)

    @staticmethod
    def showwarning(title, message):
        DarkMessagebox._show(title, message, "⚠️", Colors.ACCENT_YELLOW)

    @staticmethod
    def showerror(title, message):
        DarkMessagebox._show(title, message, "❌", Colors.ACCENT_RED)

    @staticmethod
    def askyesno(title, message):
        result = {'value': False}
        parent = _get_parent()
        win = tk.Toplevel(parent)
        win.title(title)
        win.configure(bg=Colors.BG_PRIMARY)
        win.resizable(False, False)
        if parent:
            win.transient(parent)
        
        icon_path = get_icon_path()
        if icon_path:
            try:
                win.iconbitmap(icon_path)
            except:
                pass
        
        frame = tk.Frame(win, bg=Colors.BG_PRIMARY)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        tk.Label(frame, text="❓", font=("Segoe UI", 28),
                 bg=Colors.BG_PRIMARY, fg=Colors.ACCENT_PURPLE).pack(anchor='w')
        tk.Label(frame, text=title, font=Fonts.HEADING,
                 bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY,
                 anchor='w').pack(fill=tk.X, pady=(5, 5))
        tk.Label(frame, text=message, font=Fonts.BODY,
                 bg=Colors.BG_PRIMARY, fg=Colors.TEXT_SECONDARY,
                 anchor='w', justify='left', wraplength=360).pack(fill=tk.X)
        
        btn_frame = tk.Frame(frame, bg=Colors.BG_PRIMARY)
        btn_frame.pack(pady=(20, 0))
        
        def on_yes():
            result['value'] = True
            win.destroy()
        
        def on_no():
            result['value'] = False
            win.destroy()
        
        ModernButton(btn_frame, text="Да", command=on_yes,
                     bg=Colors.ACCENT_GREEN, width=10).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, text="Нет", command=on_no,
                     bg=Colors.ACCENT_RED, width=10).pack(side=tk.LEFT, padx=5)
        
        _center_window(win, 440, 250)
        win.grab_set()
        win.wait_window()
        return result['value']


class DarkSimpledialog:
    @staticmethod
    def askstring(title, prompt, initialvalue=None):
        result = {'value': None}
        parent = _get_parent()
        win = tk.Toplevel(parent)
        win.title(title)
        win.configure(bg=Colors.BG_PRIMARY)
        win.resizable(False, False)
        if parent:
            win.transient(parent)
        
        icon_path = get_icon_path()
        if icon_path:
            try:
                win.iconbitmap(icon_path)
            except:
                pass
        
        frame = tk.Frame(win, bg=Colors.BG_PRIMARY)
        frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        tk.Label(frame, text=prompt, font=Fonts.BODY,
                 bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY,
                 anchor='w', justify='left').pack(fill=tk.X)
        
        entry = ModernEntry(frame, width=40)
        entry.pack(fill=tk.X, pady=(10, 5), ipady=5)
        if initialvalue:
            entry.insert(0, str(initialvalue))
        
        def on_ok(event=None):
            result['value'] = entry.get()
            win.destroy()
        
        def on_cancel(event=None):
            result['value'] = None
            win.destroy()
        
        entry.bind('<Return>', on_ok)
        entry.bind('<Escape>', on_cancel)
        
        btn_frame = tk.Frame(frame, bg=Colors.BG_PRIMARY)
        btn_frame.pack(pady=(15, 0))
        ModernButton(btn_frame, text="ОК", command=on_ok,
                     bg=Colors.ACCENT_BLUE, width=10).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, text="Отмена", command=on_cancel,
                     bg=Colors.BG_CARD, fg=Colors.TEXT_SECONDARY,
                     hover_bg=Colors.BG_HOVER, width=10).pack(side=tk.LEFT, padx=5)
        
        _center_window(win, 440, 200)
        entry.focus_set()
        win.grab_set()
        win.wait_window()
        return result['value']

    @staticmethod
    def askfloat(title, prompt, initialvalue=None, minvalue=None):
        value = DarkSimpledialog.askstring(title, prompt, initialvalue)
        if value is None:
            return None
        try:
            f = float(value.replace(',', '.'))
            if minvalue is not None and f < minvalue:
                DarkMessagebox.showwarning("Ошибка", f"Значение не меньше {minvalue}")
                return None
            return f
        except ValueError:
            DarkMessagebox.showerror("Ошибка", "Введите корректное число")
            return None


# ⬇️ ПОДМЕНА СТАНДАРТНЫХ ДИАЛОГОВ ТЕМОВЫМИ
messagebox = DarkMessagebox
simpledialog = DarkSimpledialog


# ============================================================
# ОКНО ВХОДА
# ============================================================
class LoginWindow:
    def __init__(self, parent, config: AppConfig):
        self.parent = parent
        self.config = config
        self.result = None
        
        self.win = tk.Toplevel(parent)
        self.win.title("Журнал посещаемости")
        self.win.geometry("450x700")
        self.win.resizable(False, False)
        self.win.configure(bg=Colors.BG_PRIMARY)
        
        # ИКОНКА ОКНА
        icon = get_icon_path()
        if icon:
            try:
                self.win.iconbitmap(icon)
            except:
                pass
        
        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() - self.win.winfo_width()) // 2
        y = (self.win.winfo_screenheight() - self.win.winfo_height()) // 2
        self.win.geometry(f"+{x}+{y}")
        
        self._create_ui()
        self._load_session()
    
    def _toggle_theme(self):
        Theme.toggle(self.win)
    
    def _create_ui(self):
        theme_btn = tk.Button(
            self.win, text="🌓", command=self._toggle_theme,
            bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY,
            activebackground=Colors.BG_HOVER, activeforeground=Colors.TEXT_PRIMARY,
            relief=tk.FLAT, font=Fonts.BUTTON, cursor="hand2", bd=0
        )
        theme_btn.place(relx=1.0, x=-45, y=10)
        
        header = tk.Frame(self.win, bg=Colors.BG_PRIMARY)
        header.pack(fill=tk.X, pady=(15, 5))
        
        tk.Label(
            header, text="📚 Журнал посещаемости",
            font=Fonts.TITLE, bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY
        ).pack()
        
        tk.Label(
            header, text="Войдите в систему или создайте аккаунт",
            font=Fonts.SMALL, bg=Colors.BG_PRIMARY, fg=Colors.TEXT_MUTED
        ).pack(pady=(5, 0))
        
        self.notebook = ttk.Notebook(self.win, style="TNotebook")
        self.notebook.pack(fill=tk.X, padx=40, pady=10)
        
        self._create_login_tab()
        self._create_register_tab()
        
        self.status_label = tk.Label(
            self.win, text="", font=Fonts.BODY,
            bg=Colors.BG_PRIMARY, fg=Colors.ACCENT_RED
        )
        self.status_label.pack(pady=5, fill=tk.X, padx=40)
        
        close_btn = ModernButton(
            self.win, text="Закрыть", command=self._on_close,
            bg=Colors.BG_CARD, fg=Colors.TEXT_SECONDARY,
            hover_bg=Colors.BG_HOVER, width=10
        )
        close_btn.pack(pady=5)
    
    def _create_login_tab(self):
        frame = tk.Frame(self.notebook, bg=Colors.BG_SECONDARY)
        self.notebook.add(frame, text="  🔑 Вход  ")
        
        tk.Label(frame, text="Логин", font=Fonts.SMALL,
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_SECONDARY
        ).pack(anchor='w', padx=30, pady=(15, 3))
        
        self.login_entry = ModernEntry(frame, width=35)
        self.login_entry.pack(padx=30, pady=3, ipady=4)
        
        tk.Label(frame, text="Пароль", font=Fonts.SMALL,
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_SECONDARY
        ).pack(anchor='w', padx=30, pady=(8, 3))
        
        self.password_entry = ModernEntry(frame, width=35, show="●")
        self.password_entry.pack(padx=30, pady=3, ipady=4)
        self.password_entry.bind('<Return>', lambda e: self.do_login())
        
        login_btn = ModernButton(
            frame, text="🔑 Войти", command=self.do_login,
            bg=Colors.ACCENT_BLUE, fg="#ffffff", width=20
        )
        login_btn.pack(pady=15)
    
    def _create_register_tab(self):
        frame = tk.Frame(self.notebook, bg=Colors.BG_SECONDARY)
        self.notebook.add(frame, text="  📝 Регистрация  ")
        
        tk.Label(frame, text="Логин (мин. 3 символа)", font=Fonts.SMALL,
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_SECONDARY
        ).pack(anchor='w', padx=30, pady=(15, 3))
        
        self.reg_login_entry = ModernEntry(frame, width=35)
        self.reg_login_entry.pack(padx=30, pady=3, ipady=4)
        
        tk.Label(frame, text="Пароль (мин. 4 символа)", font=Fonts.SMALL,
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_SECONDARY
        ).pack(anchor='w', padx=30, pady=(8, 3))
        
        self.reg_password_entry = ModernEntry(frame, width=35, show="●")
        self.reg_password_entry.pack(padx=30, pady=3, ipady=4)
        
        tk.Label(frame, text="Повторите пароль", font=Fonts.SMALL,
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_SECONDARY
        ).pack(anchor='w', padx=30, pady=(8, 3))
        
        self.reg_password2_entry = ModernEntry(frame, width=35, show="●")
        self.reg_password2_entry.pack(padx=30, pady=3, ipady=4)
        self.reg_password2_entry.bind('<Return>', lambda e: self.do_register())
        
        reg_btn = ModernButton(
            frame, text="📝 Зарегистрироваться", command=self.do_register,
            bg=Colors.ACCENT_GREEN, fg="#ffffff", width=22
        )
        reg_btn.pack(pady=15)
    
    def _load_session(self):
        if os.path.exists(self.config.session_file):
            try:
                with open(self.config.session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    self.login_entry.insert(0, session.get('login', ''))
                    self.password_entry.insert(0, session.get('password', ''))
            except:
                pass
    
    def _save_session(self, login, password):
        try:
            with open(self.config.session_file, 'w', encoding='utf-8') as f:
                json.dump({'login': login, 'password': password}, f)
        except:
            pass
    
    def _on_close(self):
        self.result = None
        self.win.destroy()
    
    def do_login(self):
        try:
            login = self.login_entry.get().strip()
            password = self.password_entry.get()
            
            if not login or not password:
                self.status_label.config(text="⚠ Введите логин и пароль", fg=Colors.ACCENT_RED)
                return
            
            self.status_label.config(text="⏳ Подключение к серверу...", fg=Colors.ACCENT_BLUE)
            self.win.update()
            
            status, data = http_request(
                f"{self.config.server_url}/login",
                {'login': login, 'password': password},
                method='POST', timeout=self.config.timeout
            )
            
            if status == 200:
                self._save_session(login, password)
                self.result = {
                    'login': login, 'password': password,
                    'user_data': UserData.from_dict(data), 'offline': False
                }
                self.win.destroy()
            elif status == 0:
                self.status_label.config(text="⚠ Сервер недоступен", fg=Colors.ACCENT_YELLOW)
                self.win.update()
                
                if messagebox.askyesno(
                    "Сервер недоступен",
                    "Не удалось подключиться к серверу.\n\nРаботать в локальном режиме?"
                ):
                    user_data = load_local_data(login)
                    if user_data is None:
                        user_data = create_default_user_data(login)
                        save_local_data(user_data)
                    
                    self._save_session(login, password)
                    self.result = {
                        'login': login, 'password': password,
                        'user_data': user_data, 'offline': True
                    }
                    self.win.destroy()
                else:
                    self.status_label.config(text="")
            else:
                err = data.get('error', 'Неизвестная ошибка')
                self.status_label.config(text=f"❌ {err}", fg=Colors.ACCENT_RED)
        except Exception as e:
            log_error("Ошибка в do_login", e)
            self.status_label.config(text=f"❌ Ошибка: {str(e)}", fg=Colors.ACCENT_RED)
    
    def do_register(self):
        try:
            login = self.reg_login_entry.get().strip()
            password = self.reg_password_entry.get()
            password2 = self.reg_password2_entry.get()
            
            if not login or not password:
                self.status_label.config(text="⚠ Заполните все поля", fg=Colors.ACCENT_RED)
                return
            if len(login) < self.config.min_login_length:
                self.status_label.config(text=f"⚠ Логин минимум {self.config.min_login_length} символа", fg=Colors.ACCENT_RED)
                return
            if len(password) < self.config.min_password_length:
                self.status_label.config(text=f"⚠ Пароль минимум {self.config.min_password_length} символа", fg=Colors.ACCENT_RED)
                return
            if password != password2:
                self.status_label.config(text="⚠ Пароли не совпадают", fg=Colors.ACCENT_RED)
                return
            
            self.status_label.config(text="⏳ Регистрация...", fg=Colors.ACCENT_BLUE)
            self.win.update()
            
            status, data = http_request(
                f"{self.config.server_url}/register",
                {'login': login, 'password': password},
                method='POST', timeout=self.config.timeout
            )
            
            if status == 200:
                messagebox.showinfo("Успех", "✅ Регистрация успешна!\nТеперь войдите в систему.")
                self.notebook.select(0)
                self.login_entry.delete(0, tk.END)
                self.login_entry.insert(0, login)
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, password)
                self.status_label.config(text="", fg=Colors.ACCENT_RED)
            elif status == 0:
                messagebox.showerror("Ошибка", "Сервер недоступен.\nРегистрация возможна только онлайн.")
                self.status_label.config(text="⚠ Сервер недоступен", fg=Colors.ACCENT_YELLOW)
            else:
                err = data.get('error', 'Ошибка регистрации')
                self.status_label.config(text=f"❌ {err}", fg=Colors.ACCENT_RED)
        except Exception as e:
            log_error("Ошибка в do_register", e)
            self.status_label.config(text=f"❌ Ошибка: {str(e)}", fg=Colors.ACCENT_RED)


# ============================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ
# ============================================================
class AttendanceJournal:
    def __init__(self, root, config: AppConfig, login_info: Dict):
        self.root = root
        self.config = config
        self.login = login_info['login']
        self.password = login_info['password']
        self.user_data = login_info['user_data']
        self.offline_mode = login_info.get('offline', False)
        self.data_file = f"jour_{self.login}_local.json"
        
        self.root.title(f"📚 Журнал — {self.login}")
        self.root.geometry("1200x700")
        self.root.configure(bg=Colors.BG_PRIMARY)
        self.root.minsize(900, 600)
        
        # ИКОНКА ГЛАВНОГО ОКНА И ВСЕХ ДОЧЕРНИХ
        icon = get_icon_path()
        if icon:
            try:
                self.root.iconbitmap(icon)
                self.root.iconbitmap(default=icon)
            except:
                pass
        
        setup_styles()
        
        self.current_group_id = self.user_data.current_group_id
        self.groups = self.user_data.groups
        
        self._create_menu()
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        self._load_current_group()
        self._refresh_ui()
        
        if self.offline_mode:
            self.root.after(100, self._show_offline_message)
    
    def _show_offline_message(self):
        messagebox.showinfo(
            "Офлайн-режим",
            "Программа работает в локальном режиме.\n"
            "Данные сохраняются только на этом компьютере."
        )
    
    def _toggle_theme(self):
        Theme.toggle(self.root)
        self._create_menu()
        self._refresh_ui()
    
    def _get_current_group(self) -> Optional[Group]:
        return self.groups.get(self.current_group_id)
    
    def _load_current_group(self):
        group = self._get_current_group()
        if group is None:
            self.current_group_id = "default"
            if "default" not in self.groups:
                self.groups["default"] = Group(
                    id="default", name="Основная группа",
                    students=[], lessons=[], attendance={},
                    subscription_price=self.config.default_subscription_price
                )
            group = self.groups["default"]
        
        self.students = group.students
        self.lessons = group.lessons
        self.attendance = group.attendance
        self.next_student_id = group.next_student_id
        self.next_lesson_id = group.next_lesson_id
        self.subscription_price = group.subscription_price
    
    def _save_data(self):
        try:
            group = self._get_current_group()
            if group:
                group.students = self.students
                group.lessons = self.lessons
                group.attendance = self.attendance
                group.next_student_id = self.next_student_id
                group.next_lesson_id = self.next_lesson_id
                group.subscription_price = self.subscription_price
            
            self.user_data.groups = self.groups
            self.user_data.current_group_id = self.current_group_id
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_data.to_dict(), f, ensure_ascii=False, indent=2)
            
            if not self.offline_mode:
                status, data = http_request(
                    f"{self.config.server_url}/save",
                    {'login': self.login, 'password': self.password,
                     'data': self.user_data.to_dict()},
                    method='POST', timeout=self.config.timeout
                )
                if status != 200:
                    self.status_bar.set_status("⚠ Ошибка сохранения на сервер", Colors.ACCENT_YELLOW)
                else:
                    self.status_bar.set_status("✅ Данные сохранены", Colors.ACCENT_GREEN)
            else:
                self.status_bar.set_status("💾 Сохранено локально", Colors.ACCENT_GREEN)
        except Exception as e:
            log_error("Ошибка в _save_data", e)
            self.status_bar.set_status("❌ Ошибка сохранения", Colors.ACCENT_RED)
    
    def _create_menu(self):
        menubar = tk.Menu(self.root, bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY,
                         activebackground=Colors.ACCENT_BLUE, activeforeground="#ffffff")
        
        account_menu = tk.Menu(menubar, tearoff=0, bg=Colors.BG_SECONDARY,
                              fg=Colors.TEXT_PRIMARY, activebackground=Colors.ACCENT_BLUE)
        account_menu.add_command(label="ℹ Информация об аккаунте", command=self._show_account_info)
        account_menu.add_command(label="🔑 Сменить пароль", command=self._change_password)
        account_menu.add_separator()
        account_menu.add_command(label="🚪 Выйти", command=self._logout)
        menubar.add_cascade(label="Аккаунт", menu=account_menu)
        
        settings_menu = tk.Menu(menubar, tearoff=0, bg=Colors.BG_SECONDARY,
                               fg=Colors.TEXT_PRIMARY, activebackground=Colors.ACCENT_BLUE)
        settings_menu.add_command(label="🌓 Переключить тему", command=self._toggle_theme)
        settings_menu.add_command(label="💰 Стоимость абонемента", command=self._set_subscription_price)
        settings_menu.add_command(label="📡 Проверить связь", command=self._check_connection)
        if self.offline_mode:
            settings_menu.add_command(label="🔄 Перейти онлайн", command=self._go_online)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        
        self.root.config(menu=menubar)
    
    def _create_header(self):
        header = tk.Frame(self.root, bg=Colors.BG_SECONDARY, height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        left_frame = tk.Frame(header, bg=Colors.BG_SECONDARY)
        left_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(
            left_frame, text="📚 Журнал посещаемости",
            font=Fonts.SUBTITLE, bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY
        ).pack(anchor='w')
        
        right_frame = tk.Frame(header, bg=Colors.BG_SECONDARY)
        right_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        mode_text = "🔴 ОФЛАЙН" if self.offline_mode else "🟢 ОНЛАЙН"
        mode_color = Colors.ACCENT_RED if self.offline_mode else Colors.ACCENT_GREEN
        
        tk.Label(
            right_frame, text=f"👤 {self.login}",
            font=Fonts.BODY, bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY
        ).pack(anchor='e')
        
        tk.Label(
            right_frame, text=mode_text,
            font=Fonts.SMALL, bg=Colors.BG_SECONDARY, fg=mode_color
        ).pack(anchor='e')
    
    def _create_main_content(self):
        main_frame = tk.Frame(self.root, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self._create_toolbar(main_frame)
        self._create_group_panel(main_frame)
        self._create_table(main_frame)
    
    def _create_toolbar(self, parent):
        toolbar = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        buttons = [
            ("➕ Ученик", self._add_student, Colors.ACCENT_BLUE),
            ("➖ Удалить", self._delete_student, Colors.ACCENT_RED),
            ("📅 Занятие", self._add_lesson, Colors.ACCENT_GREEN),
            ("🔄 Обновить", self._refresh_ui, Colors.ACCENT_PURPLE),
            ("📊 Сводка", self._show_summary, Colors.ACCENT_YELLOW),
            ("💾 Экспорт", self._export_to_txt, Colors.BTN_PRIMARY),
        ]
        
        for text, cmd, color in buttons:
            btn = ModernButton(toolbar, text=text, command=cmd,
                             bg=color, fg="#ffffff", width=12)
            btn.pack(side=tk.LEFT, padx=3)
        
        ModernButton(toolbar, text="🌓 Тема", command=self._toggle_theme,
                    bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
                    hover_bg=Colors.BG_HOVER, width=10).pack(side=tk.LEFT, padx=3)
    
    def _create_group_panel(self, parent):
        panel = ModernFrame(parent, bg=Colors.BG_CARD)
        panel.pack(fill=tk.X, pady=(0, 10), ipady=8)
        
        tk.Label(
            panel, text="👥 Группа:", font=Fonts.BODY,
            bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(15, 5))
        
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(
            panel, textvariable=self.group_var,
            state='readonly', width=25, style="Modern.TCombobox"
        )
        self.group_combo.pack(side=tk.LEFT, padx=5)
        self.group_combo.bind('<<ComboboxSelected>>', self._on_group_changed)
        
        btn_frame = tk.Frame(panel, bg=Colors.BG_CARD)
        btn_frame.pack(side=tk.RIGHT, padx=10)
        
        ModernButton(btn_frame, text="➕", command=self._create_group,
                    bg=Colors.ACCENT_GREEN, width=3).pack(side=tk.LEFT, padx=2)
        ModernButton(btn_frame, text="✏️", command=self._rename_group,
                    bg=Colors.ACCENT_YELLOW, width=3).pack(side=tk.LEFT, padx=2)
        ModernButton(btn_frame, text="🗑️", command=self._delete_group,
                    bg=Colors.ACCENT_RED, width=3).pack(side=tk.LEFT, padx=2)
    
    def _create_table(self, parent):
        table_frame = ModernFrame(parent, bg=Colors.BG_CARD)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            table_frame, style="Modern.Treeview",
            show='tree headings', selectmode='browse'
        )
        
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        v_scroll.grid(row=0, column=1, sticky='ns', pady=5)
        h_scroll.grid(row=1, column=0, sticky='ew', padx=5)
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', self._show_student_stats)
        self.tree.bind('<Button-1>', self._on_cell_click)
    
    def _create_status_bar(self):
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        mode_text = "ОФЛАЙН" if self.offline_mode else "ОНЛАЙН"
        mode_color = Colors.ACCENT_RED if self.offline_mode else Colors.ACCENT_GREEN
        self.status_bar.set_mode(f"● {mode_text}", mode_color)
    
    def _refresh_ui(self):
        self._refresh_group_list()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        sorted_lessons = sorted(self.lessons, key=lambda x: x.datetime)
        
        columns = ['name', 'percent', 'cost'] + [f"lesson_{l.id}" for l in sorted_lessons]
        self.tree['columns'] = columns
        
        self.tree.heading('#0', text='ID')
        self.tree.column('#0', width=50, anchor='center', stretch=False)
        
        self.tree.heading('name', text='👤 ФИО ученика')
        self.tree.column('name', width=220, anchor='w')
        
        self.tree.heading('percent', text='📊 Посещаемость')
        self.tree.column('percent', width=130, anchor='center')
        
        self.tree.heading('cost', text='💰 Стоимость')
        self.tree.column('cost', width=130, anchor='center')
        
        for lesson in sorted_lessons:
            try:
                dt = datetime.strptime(lesson.datetime, "%Y-%m-%d %H:%M")
                self.tree.heading(f"lesson_{lesson.id}", text=dt.strftime("%d/%m"))
            except ValueError:
                self.tree.heading(f"lesson_{lesson.id}", text=lesson.datetime)
            self.tree.column(f"lesson_{lesson.id}", width=100, anchor='center')
        
        active_students = [s for s in self.students if not s.deleted]
        
        for student in active_students:
            percent = AttendanceService.calculate_percent(self.attendance.get(student.id, {}))
            cost = AttendanceService.calculate_cost(percent, self.subscription_price)
            
            values = [student.name, f"{round(percent * 100)}%", f"{cost:.2f} ₽"]
            for lesson in sorted_lessons:
                values.append('✓' if self.attendance.get(student.id, {}).get(lesson.id, False) else '—')
            
            self.tree.insert('', 'end', text=str(student.id), values=values)
        
        self.status_bar.set_status(f"✅ Загружено: {len(active_students)} учеников, {len(sorted_lessons)} занятий")
    
    def _refresh_group_list(self):
        names = []
        self._group_id_to_name = {}
        self._group_name_to_id = {}
        for gid, group in self.groups.items():
            name = group.name
            names.append(name)
            self._group_id_to_name[gid] = name
            self._group_name_to_id[name] = gid
        
        self.group_combo['values'] = names
        current_name = self._group_id_to_name.get(self.current_group_id, names[0] if names else '')
        self.group_var.set(current_name)
    
    def _on_group_changed(self, event=None):
        name = self.group_var.get()
        gid = self._group_name_to_id.get(name)
        if gid and gid != self.current_group_id:
            self._save_data()
            self.current_group_id = gid
            self._load_current_group()
            self._refresh_ui()
    
    def _on_cell_click(self, event):
        if self.tree.identify_region(event.x, event.y) != 'cell':
            return
        column = self.tree.identify_column(event.x)
        if not column:
            return
        col_index = int(column.replace('#', '')) - 1
        if col_index < 3:
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        student_id = int(self.tree.item(item, 'text'))
        col_name = self.tree['columns'][col_index]
        if not col_name.startswith('lesson_'):
            return
        lesson_id = int(col_name.replace('lesson_', ''))
        
        if student_id not in self.attendance:
            self.attendance[student_id] = {}
        self.attendance[student_id][lesson_id] = not self.attendance[student_id].get(lesson_id, False)
        self._save_data()
        self._refresh_ui()
    
    def _add_student(self):
        name = simpledialog.askstring("Добавление ученика", "Введите ФИО ученика:")
        if not name or not name.strip():
            return
        
        for s in self.students:
            if s.name.lower() == name.strip().lower() and not s.deleted:
                messagebox.showwarning("Предупреждение", f"Ученик '{name}' уже существует!")
                return
        
        self.students.append(Student(self.next_student_id, name.strip()))
        self.next_student_id += 1
        self._save_data()
        self._refresh_ui()
    
    def _delete_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите ученика!")
            return
        item = selected[0]
        student_id = int(self.tree.item(item, 'text'))
        student_name = self.tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Подтверждение", f"Удалить ученика '{student_name}'?"):
            for s in self.students:
                if s.id == student_id:
                    s.deleted = True
                    break
            self._save_data()
            self._refresh_ui()
    
    def _add_lesson(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        dt_str = simpledialog.askstring(
            "Добавление занятия",
            "Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ):",
            initialvalue=now
        )
        if dt_str:
            try:
                datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                for l in self.lessons:
                    if l.datetime == dt_str:
                        messagebox.showwarning("Предупреждение", "Такое занятие уже есть!")
                        return
                self.lessons.append(Lesson(self.next_lesson_id, dt_str))
                self.next_lesson_id += 1
                self.lessons.sort(key=lambda x: x.datetime)
                self._save_data()
                self._refresh_ui()
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты!")
    
    def _create_group(self):
        name = simpledialog.askstring("Новая группа", "Название группы:")
        if not name or not name.strip():
            return
        gid = f"group_{int(datetime.now().timestamp() * 1000)}"
        self.groups[gid] = Group(
            id=gid, name=name.strip(), students=[], lessons=[],
            attendance={}, subscription_price=self.config.default_subscription_price
        )
        self.current_group_id = gid
        self._load_current_group()
        self._refresh_ui()
        self._save_data()
    
    def _rename_group(self):
        group = self._get_current_group()
        if not group:
            return
        new_name = simpledialog.askstring("Переименование", "Новое название:", initialvalue=group.name)
        if new_name and new_name.strip():
            group.name = new_name.strip()
            self._refresh_group_list()
            self._save_data()
    
    def _delete_group(self):
        if len(self.groups) <= 1:
            messagebox.showwarning("Внимание", "Нельзя удалить единственную группу!")
            return
        group = self._get_current_group()
        if not group:
            return
        if messagebox.askyesno("Подтверждение", f"Удалить группу '{group.name}'?"):
            del self.groups[self.current_group_id]
            self.current_group_id = next(iter(self.groups.keys()))
            self._load_current_group()
            self._refresh_ui()
            self._save_data()
    
    def _show_summary(self):
        text = "📊 Сводная таблица посещаемости\n"
        text += "═" * 50 + "\n\n"
        
        active_students = [s for s in self.students if not s.deleted]
        for student in active_students:
            percent = AttendanceService.calculate_percent(self.attendance.get(student.id, {}))
            cost = AttendanceService.calculate_cost(percent, self.subscription_price)
            text += f"{student.name:25} {percent*100:>6.1f}% {cost:>10.2f} ₽\n"
        
        messagebox.showinfo("Сводка", text)
    
    def _export_to_txt(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt")],
            initialfile=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not path:
            return
        
        try:
            active = [s for s in self.students if not s.deleted]
            group = self._get_current_group()
            group_name = group.name if group else '—'
            mode_text = "ОФЛАЙН" if self.offline_mode else "ОНЛАЙН"
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Аккаунт: {self.login} [{mode_text}]\n")
                f.write(f"Группа: {group_name}\n")
                f.write(f"Стоимость абонемента: {self.subscription_price:.2f} руб.\n\n")
                f.write(f"{'ФИО':<25} {'%':<8} {'Стоимость':<12}\n")
                f.write("─" * 50 + "\n")
                for s in active:
                    percent = AttendanceService.calculate_percent(self.attendance.get(s.id, {}))
                    cost = AttendanceService.calculate_cost(percent, self.subscription_price)
                    f.write(f"{s.name:<25} {percent*100:>6.1f}% {cost:>10.2f}\n")
            
            messagebox.showinfo("Успех", f"✅ Сохранено в:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")
    
    def _show_student_stats(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        student_id = int(self.tree.item(item, 'text'))
        student_name = self.tree.item(item, 'values')[0]
        
        attendance = self.attendance.get(student_id, {})
        percent = AttendanceService.calculate_percent(attendance)
        cost = AttendanceService.calculate_cost(percent, self.subscription_price)
        attended = sum(1 for v in attendance.values() if v)
        total = len(attendance)
        
        win = tk.Toplevel(self.root)
        win.title(f"📊 Статистика: {student_name}")
        win.geometry("650x450")
        win.configure(bg=Colors.BG_PRIMARY)
        
        tk.Label(
            win, text=f"📊 {student_name}",
            font=Fonts.SUBTITLE, bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY
        ).pack(pady=15)
        
        stats_frame = tk.Frame(win, bg=Colors.BG_PRIMARY)
        stats_frame.pack(pady=10)
        
        stats = [
            ("Всего занятий", str(total), Colors.ACCENT_BLUE),
            ("Присутствовал", str(attended), Colors.ACCENT_GREEN),
            ("Отсутствовал", str(total - attended), Colors.ACCENT_RED),
            ("Процент", f"{round(percent * 100)}%", Colors.ACCENT_PURPLE),
            ("Стоимость", f"{cost:.2f} ₽", Colors.ACCENT_YELLOW),
        ]
        
        for label, value, color in stats:
            card = ModernFrame(stats_frame, bg=Colors.BG_CARD)
            card.pack(side=tk.LEFT, padx=5, ipady=10, ipadx=15)
            
            tk.Label(card, text=value, font=Fonts.HEADING,
                    bg=Colors.BG_CARD, fg=color).pack()
            tk.Label(card, text=label, font=Fonts.SMALL,
                    bg=Colors.BG_CARD, fg=Colors.TEXT_MUTED).pack()
        
        table_frame = ModernFrame(win, bg=Colors.BG_CARD)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        st = ttk.Treeview(table_frame, columns=['date', 'status'],
                         show='headings', height=10, style="Modern.Treeview")
        st.heading('date', text='📅 Дата')
        st.heading('status', text='Статус')
        st.column('date', width=300)
        st.column('status', width=250)
        
        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=st.yview)
        st.configure(yscrollcommand=scroll.set)
        st.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        sorted_lessons = sorted(self.lessons, key=lambda x: x.datetime)
        for lesson in sorted_lessons:
            try:
                dt = datetime.strptime(lesson.datetime, "%Y-%m-%d %H:%M")
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except ValueError:
                date_str = lesson.datetime
            is_present = attendance.get(lesson.id, False)
            st.insert('', 'end', values=[
                date_str,
                "✅ Присутствовал" if is_present else "❌ Отсутствовал"
            ])
        
        ModernButton(win, text="Закрыть", command=win.destroy,
                    bg=Colors.BG_CARD, fg=Colors.TEXT_PRIMARY,
                    hover_bg=Colors.BG_HOVER, width=15).pack(pady=10)
    
    def _show_account_info(self):
        group = self._get_current_group()
        group_name = group.name if group else '—'
        mode = "🔴 ОФЛАЙН" if self.offline_mode else "🟢 ОНЛАЙН"
        messagebox.showinfo(
            "Аккаунт",
            f"👤 Логин: {self.login}\n"
            f"📡 Режим: {mode}\n"
            f"🌐 Сервер: {self.config.server_url}\n\n"
            f"👥 Всего групп: {len(self.groups)}\n"
            f"📌 Текущая группа: {group_name}"
        )
    
    def _change_password(self):
        if self.offline_mode:
            messagebox.showwarning("Офлайн-режим", "Смена пароля возможна только онлайн.")
            return
        
        win = tk.Toplevel(self.root)
        win.title("🔑 Смена пароля")
        win.geometry("380x350")
        win.configure(bg=Colors.BG_PRIMARY)
        
        tk.Label(win, text="🔑 Смена пароля", font=Fonts.SUBTITLE,
                bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY).pack(pady=15)
        
        fields = [
            ("Текущий пароль", "old"),
            ("Новый пароль", "new"),
            ("Повторите пароль", "new2")
        ]
        
        entries = {}
        for label, key in fields:
            tk.Label(win, text=label, font=Fonts.SMALL,
                    bg=Colors.BG_PRIMARY, fg=Colors.TEXT_SECONDARY).pack(anchor='w', padx=30)
            entry = ModernEntry(win, width=35, show="●")
            entry.pack(padx=30, pady=4, ipady=3)
            entries[key] = entry
        
        status_label = tk.Label(win, text="", font=Fonts.SMALL,
                               bg=Colors.BG_PRIMARY, fg=Colors.ACCENT_RED)
        status_label.pack(pady=5)
        
        def do_change():
            old = entries['old'].get()
            new = entries['new'].get()
            new2 = entries['new2'].get()
            
            if not old or not new:
                status_label.config(text="⚠ Заполните все поля")
                return
            if len(new) < 4:
                status_label.config(text="⚠ Пароль слишком короткий")
                return
            if new != new2:
                status_label.config(text="⚠ Пароли не совпадают")
                return
            
            status_label.config(text="⏳ Отправка...", fg=Colors.ACCENT_BLUE)
            win.update()
            
            req_status, req_data = http_request(
                f"{self.config.server_url}/change_password",
                {'login': self.login, 'old_password': old, 'new_password': new},
                method='POST', timeout=self.config.timeout
            )
            
            if req_status == 200:
                self.password = new
                try:
                    with open(self.config.session_file, 'w', encoding='utf-8') as f:
                        json.dump({'login': self.login, 'password': self.password}, f)
                except:
                    pass
                status_label.config(text="✅ Пароль изменён!", fg=Colors.ACCENT_GREEN)
                win.after(1500, win.destroy)
            else:
                err = req_data.get('error', 'Ошибка')
                status_label.config(text=f"❌ {err}")
        
        ModernButton(win, text="Сменить пароль", command=do_change,
                    bg=Colors.ACCENT_BLUE, width=20).pack(pady=15)
    
    def _check_connection(self):
        status, data = http_request(f"{self.config.server_url}/ping", timeout=self.config.timeout)
        if status == 200:
            messagebox.showinfo("Успех", f"✅ Сервер доступен!\n{self.config.server_url}")
        else:
            messagebox.showerror("Ошибка", "❌ Сервер недоступен")
    
    def _set_subscription_price(self):
        price = simpledialog.askfloat(
            "💰 Стоимость абонемента", "Введите стоимость (руб):",
            initialvalue=self.subscription_price, minvalue=0.0
        )
        if price is not None:
            self.subscription_price = float(price)
            self._save_data()
            self._refresh_ui()
    
    def _logout(self):
        if messagebox.askyesno("Выход", "Выйти из аккаунта?"):
            if os.path.exists(self.config.session_file):
                try:
                    os.remove(self.config.session_file)
                except:
                    pass
            self.root.destroy()
    
    def _go_online(self):
        status, data = http_request(f"{self.config.server_url}/ping", timeout=self.config.timeout)
        if status != 200:
            messagebox.showerror("Ошибка", "Сервер недоступен.")
            return
        
        status, data = http_request(
            f"{self.config.server_url}/login",
            {'login': self.login, 'password': self.password},
            method='POST', timeout=self.config.timeout
        )
        if status == 200:
            self.offline_mode = False
            self.user_data = UserData.from_dict(data)
            self.current_group_id = self.user_data.current_group_id
            self.groups = self.user_data.groups
            self._load_current_group()
            self._refresh_ui()
            self.root.title(f"📚 Журнал — {self.login}")
            self.status_bar.set_mode("● ОНЛАЙН", Colors.ACCENT_GREEN)
            messagebox.showinfo("Успех", "✅ Перешли в онлайн-режим!")
        else:
            messagebox.showerror("Ошибка", "Не удалось войти на сервер.")


# ============================================================
# ТОЧКА ВХОДА
# ============================================================
def main():
    try:
        config = AppConfig()
        
        Theme.load()
        
        root = tk.Tk()
        root.withdraw()
        
        # ИКОНКА ГЛАВНОГО ОКНА (применится ко всем окнам)
        icon = get_icon_path()
        if icon:
            try:
                root.iconbitmap(icon)
                root.iconbitmap(default=icon)
            except:
                pass
        
        setup_styles()
        
        login_win = LoginWindow(root, config)
        root.wait_window(login_win.win)
        
        if login_win.result is None:
            root.destroy()
            return
        
        root.deiconify()
        app = AttendanceJournal(root, config, login_win.result)
        root.mainloop()
        
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        log_error("Критическая ошибка", e)
        sys.exit(1)


if __name__ == "__main__":
    main()