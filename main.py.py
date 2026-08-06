# ============================================================
# ЖУРНАЛ ПОСЕЩАЕМОСТИ — KIVY (ANDROID + DESKTOP)
# ============================================================
import os
import sys
import json
import threading
import traceback
import urllib.request
import urllib.error
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, List

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup

# ============================================================
# КОНФИГУРАЦИЯ И ТЕМЫ
# ============================================================
SERVER_URL = "https://jour.pythonanywhere.com"
TIMEOUT = 15

def rgba(h):
    h = h.lstrip('#')
    return tuple(round(int(h[i:i+2], 16) / 255, 3) for i in (0, 2, 4)) + (1,)

PALETTES = {
    'dark': {'BG': "#1e1e2e", 'BG2': "#2d2d3f", 'CARD': "#363649", 'HOV': "#40405a",
             'BLUE': "#7aa2f7", 'GREEN': "#9ece6a", 'RED': "#f7768e", 'YEL': "#e0af68",
             'PUR': "#bb9af7", 'TEXT': "#c0caf5", 'TEXT2': "#a9b1d6", 'MUT': "#565f89",
             'BORD': "#414868"},
    'light': {'BG': "#f2f4fa", 'BG2': "#e3e7f2", 'CARD': "#ffffff", 'HOV': "#d9dfee",
              'BLUE': "#3b6fd4", 'GREEN': "#3f9e63", 'RED': "#d4536a", 'YEL': "#b98322",
              'PUR': "#7c5cbf", 'TEXT': "#232936", 'TEXT2': "#4a5165", 'MUT': "#8a91a8",
              'BORD': "#c5cad9"}
}

# ============================================================
# KV-РАЗМЕТКА (ДИЗАЙН)
# ============================================================
KV = '''
<CustButton@Button>:
    size_hint_y: None
    height: dp(46)
    font_size: sp(14)
    color: 1, 1, 1, 1
    background_normal: ''
    background_down: ''
    background_color: app.c['BLUE']

<SoftButton@Button>:
    size_hint_y: None
    height: dp(46)
    font_size: sp(14)
    color: app.c['TEXT']
    background_normal: ''
    background_down: ''
    background_color: app.c['CARD']

<DarkInput@TextInput>:
    size_hint_y: None
    height: dp(46)
    font_size: sp(15)
    multiline: False
    foreground_color: app.c['TEXT']
    background_color: app.c['CARD']
    cursor_color: app.c['BLUE']
    padding: [dp(12), dp(12)]

<CustLabel@Label>:
    color: app.c['TEXT']
    font_size: sp(14)

<MutLabel@Label>:
    color: app.c['MUT']
    font_size: sp(12)

<LoginScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: app.c['BG']
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: None
            height: dp(90)
            orientation: 'vertical'
            Label:
                text: '📚 Журнал посещаемости'
                font_size: sp(24)
                bold: True
                color: app.c['TEXT']
            Label:
                text: 'Войдите или создайте аккаунт'
                font_size: sp(12)
                color: app.c['MUT']
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(4)
            padding: [dp(30), 0]
            Button:
                id: tab_login
                text: '🔑 Вход'
                background_normal: ''
                background_color: app.c['BLUE']
                color: 1, 1, 1, 1
                on_press: root.show_form('login')
            Button:
                id: tab_reg
                text: '📝 Регистрация'
                background_normal: ''
                background_color: app.c['CARD']
                color: app.c['TEXT']
                on_press: root.show_form('reg')
        BoxLayout:
            id: form_box
            orientation: 'vertical'
            padding: [dp(30), dp(10)]
            spacing: dp(10)
        Label:
            id: status
            text: ''
            size_hint_y: None
            height: dp(30)
            color: app.c['RED']
            font_size: sp(13)
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: [dp(30), dp(8)]
            SoftButton:
                text: '🌓 Тема'
                size_hint_x: 0.3
                on_press: app.toggle_theme()
            Widget:
            SoftButton:
                text: 'Закрыть'
                size_hint_x: 0.3
                on_press: app.stop()

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: app.c['BG']
            Rectangle:
                pos: self.pos
                size: self.size
        # ШАПКА
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: [dp(12), dp(8)]
            spacing: dp(8)
            canvas.before:
                Color:
                    rgba: app.c['BG2']
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: '📚 Журнал'
                font_size: sp(18)
                bold: True
                color: app.c['TEXT']
                size_hint_x: 0.25
            Label:
                id: user_label
                text: ''
                color: app.c['TEXT2']
                size_hint_x: 0.35
            Label:
                id: mode_label
                text: '🟢'
                size_hint_x: 0.15
                color: app.c['GREEN']
            SoftButton:
                text: '🌓'
                size_hint_x: 0.12
                on_press: app.toggle_theme()
            SoftButton:
                text: '⋮'
                size_hint_x: 0.12
                on_press: root.open_menu()
        # ГРУППА
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(12), dp(8)]
            spacing: dp(6)
            canvas.before:
                Color:
                    rgba: app.c['CARD']
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: '👥'
                size_hint_x: 0.08
                color: app.c['TEXT']
            Spinner:
                id: group_spinner
                size_hint_x: 0.4
                background_normal: ''
                background_color: app.c['BG2']
                color: app.c['TEXT']
                font_size: sp(14)
                on_text: root.on_group_changed(self.text)
            SoftButton:
                text: '➕'
                size_hint_x: 0.1
                on_press: root.create_group()
            SoftButton:
                text: '✏️'
                size_hint_x: 0.1
                on_press: root.rename_group()
            SoftButton:
                text: '🗑️'
                size_hint_x: 0.1
                on_press: root.delete_group()
        # ТУЛБАР
        ScrollView:
            size_hint_y: None
            height: dp(56)
            do_scroll_x: True
            do_scroll_y: False
            BoxLayout:
                size_hint_x: None
                width: self.minimum_width
                padding: [dp(8), dp(8)]
                spacing: dp(6)
                CustButton:
                    text: '➕ Ученик'
                    size_hint_x: None
                    width: dp(110)
                    background_color: app.c['BLUE']
                    on_press: root.add_student()
                CustButton:
                    text: '➖ Удалить'
                    size_hint_x: None
                    width: dp(110)
                    background_color: app.c['RED']
                    on_press: root.delete_student()
                CustButton:
                    text: '📅 Занятие'
                    size_hint_x: None
                    width: dp(110)
                    background_color: app.c['GREEN']
                    on_press: root.add_lesson()
                CustButton:
                    text: '📊 Сводка'
                    size_hint_x: None
                    width: dp(100)
                    background_color: app.c['YEL']
                    on_press: root.show_summary()
                CustButton:
                    text: '💾 Экспорт'
                    size_hint_x: None
                    width: dp(100)
                    background_color: app.c['PUR']
                    on_press: root.export_txt()
        # ТАБЛИЦА
        ScrollView:
            id: table_scroll
            do_scroll_x: True
            do_scroll_y: True
            bar_color: app.c['BLUE']
            GridLayout:
                id: table_grid
                size_hint_y: None
                height: self.minimum_height
                size_hint_x: None
                width: max(table_scroll.width, self.minimum_width)
                spacing: dp(2)
                padding: dp(4)
        # СТАТУС-БАР
        Label:
            id: status_bar
            text: 'Готов'
            size_hint_y: None
            height: dp(30)
            color: app.c['MUT']
            font_size: sp(12)
            canvas.before:
                Color:
                    rgba: app.c['BG2']
                Rectangle:
                    pos: self.pos
                    size: self.size
'''

# ============================================================
# МОДЕЛИ ДАННЫХ (те же, что в Tkinter-версии)
# ============================================================
@dataclass
class Student:
    id: int
    name: str
    deleted: bool = False
    def to_dict(self): return {'id': self.id, 'name': self.name, 'deleted': self.deleted}
    @classmethod
    def from_dict(cls, d): return cls(d.get('id', 0), d.get('name', ''), d.get('deleted', False))

@dataclass
class Lesson:
    id: int
    datetime: str
    def to_dict(self): return {'id': self.id, 'datetime': self.datetime}
    @classmethod
    def from_dict(cls, d): return cls(d.get('id', 0), d.get('datetime', ''))

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
    def to_dict(self):
        return {'id': self.id, 'name': self.name,
                'students': [s.to_dict() for s in self.students],
                'lessons': [l.to_dict() for l in self.lessons],
                'attendance': {str(k): {str(lk): lv for lk, lv in v.items()} for k, v in self.attendance.items()},
                'subscription_price': self.subscription_price,
                'next_student_id': self.next_student_id, 'next_lesson_id': self.next_lesson_id}
    @classmethod
    def from_dict(cls, d):
        return cls(d.get('id', 'default'), d.get('name', 'Группа'),
                   [Student.from_dict(s) for s in d.get('students', [])],
                   [Lesson.from_dict(l) for l in d.get('lessons', [])],
                   {int(k): {int(lk): lv for lk, lv in v.items()} for k, v in d.get('attendance', {}).items()},
                   d.get('subscription_price', 4000.0),
                   d.get('next_student_id', 1), d.get('next_lesson_id', 1))

@dataclass
class UserData:
    login: str
    groups: Dict[str, Group]
    current_group_id: str
    def to_dict(self):
        return {'login': self.login, 'groups': {g: gr.to_dict() for g, gr in self.groups.items()},
                'current_group': self.current_group_id}
    @classmethod
    def from_dict(cls, d):
        return cls(d.get('login', ''), {g: Group.from_dict(gr) for g, gr in d.get('groups', {}).items()},
                   d.get('current_group', 'default'))

# ============================================================
# СЕТЬ И ХРАНЕНИЕ
# ============================================================
def http_request(url, data=None, method='GET', timeout=TIMEOUT):
    try:
        if data is not None:
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=body, method=method,
                                         headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try: err = json.loads(e.read().decode('utf-8'))
        except: err = {"error": str(e)}
        return e.code, err
    except Exception as e:
        return 0, {"error": str(e)}

def async_request(url, data, method, callback):
    def work():
        st, res = http_request(url, data, method)
        Clock.schedule_once(lambda dt: callback(st, res), 0)
    threading.Thread(target=work, daemon=True).start()

def calc_percent(att): return (sum(1 for v in att.values() if v) / len(att)) if att else 0.0

# ============================================================
# ДИАЛОГИ
# ============================================================
def info_dialog(title, message):
    box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
    lbl = Label(text=message, color=App.get_running_app().c['TEXT'], size_hint_y=0.7)
    btn = Button(text='ОК', background_normal='', background_color=App.get_running_app().c['BLUE'])
    popup = Popup(title=title, content=box, size_hint=(0.85, 0.5),
                  background_color=App.get_running_app().c['BG2'], title_color=App.get_running_app().c['TEXT'])
    btn.bind(on_press=popup.dismiss)
    box.add_widget(lbl); box.add_widget(btn)
    popup.open()

def confirm_dialog(title, message, on_yes):
    box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
    lbl = Label(text=message, color=App.get_running_app().c['TEXT'], size_hint_y=0.6)
    btns = BoxLayout(spacing=dp(10), size_hint_y=0.4)
    popup = Popup(title=title, content=box, size_hint=(0.85, 0.45),
                  background_color=App.get_running_app().c['BG2'], title_color=App.get_running_app().c['TEXT'])
    yes = Button(text='Да', background_normal='', background_color=App.get_running_app().c['GREEN'])
    no = Button(text='Нет', background_normal='', background_color=App.get_running_app().c['RED'])
    yes.bind(on_press=lambda w: (popup.dismiss(), on_yes()))
    no.bind(on_press=popup.dismiss)
    btns.add_widget(yes); btns.add_widget(no)
    box.add_widget(lbl); box.add_widget(btns)
    popup.open()

def input_dialog(title, prompt, initial='', on_ok=None, password=False):
    app = App.get_running_app()
    box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
    lbl = Label(text=prompt, color=app.c['TEXT'], size_hint_y=0.3)
    ti = TextInput(text=initial, multiline=False, password=password,
                   foreground_color=app.c['TEXT'], background_color=app.c['CARD'],
                   cursor_color=app.c['BLUE'], size_hint_y=0.3)
    btns = BoxLayout(spacing=dp(10), size_hint_y=0.4)
    popup = Popup(title=title, content=box, size_hint=(0.85, 0.45),
                  background_color=app.c['BG2'], title_color=app.c['TEXT'])
    ok = Button(text='ОК', background_normal='', background_color=app.c['BLUE'])
    cancel = Button(text='Отмена', background_normal='', background_color=app.c['CARD'], color=app.c['TEXT'])
    ok.bind(on_press=lambda w: (popup.dismiss(), on_ok(ti.text) if on_ok else None))
    cancel.bind(on_press=popup.dismiss)
    btns.add_widget(ok); btns.add_widget(cancel)
    box.add_widget(lbl); box.add_widget(ti); box.add_widget(btns)
    popup.open()

# ============================================================
# ЭКРАНЫ
# ============================================================
class LoginScreen(Screen):
    def on_pre_enter(self):
        self.show_form('login')
    
    def show_form(self, kind):
        app = App.get_running_app()
        self.ids.tab_login.background_color = app.c['BLUE'] if kind == 'login' else app.c['CARD']
        self.ids.tab_login.color = (1, 1, 1, 1) if kind == 'login' else app.c['TEXT']
        self.ids.tab_reg.background_color = app.c['GREEN'] if kind == 'reg' else app.c['CARD']
        self.ids.tab_reg.color = (1, 1, 1, 1) if kind == 'reg' else app.c['TEXT']
        
        box = self.ids.form_box
        box.clear_widgets()
        
        def lab(t):
            l = Label(text=t, color=app.c['TEXT2'], font_size=sp(12), size_hint_y=None, height=dp(24))
            l.bind(size=l.setter('text_size'))
            return l
        
        if kind == 'login':
            box.add_widget(lab('Логин'))
            self.li_login = DarkInputFactory()
            box.add_widget(self.li_login)
            box.add_widget(lab('Пароль'))
            self.li_pass = DarkInputFactory(password=True)
            box.add_widget(self.li_pass)
            btn = Button(text='🔑 Войти', background_normal='', background_color=app.c['BLUE'],
                         color=(1, 1, 1, 1), size_hint_y=None, height=dp(50))
            btn.bind(on_press=lambda w: self.do_login())
            box.add_widget(btn)
        else:
            box.add_widget(lab('Логин (мин. 3 символа)'))
            self.rg_login = DarkInputFactory()
            box.add_widget(self.rg_login)
            box.add_widget(lab('Пароль (мин. 4 символа)'))
            self.rg_pass = DarkInputFactory(password=True)
            box.add_widget(self.rg_pass)
            box.add_widget(lab('Повторите пароль'))
            self.rg_pass2 = DarkInputFactory(password=True)
            box.add_widget(self.rg_pass2)
            btn = Button(text='📝 Зарегистрироваться', background_normal='', background_color=app.c['GREEN'],
                         color=(1, 1, 1, 1), size_hint_y=None, height=dp(50))
            btn.bind(on_press=lambda w: self.do_register())
            box.add_widget(btn)
    
    def do_login(self):
        login = self.li_login.text.strip()
        password = self.li_pass.text
        if not login or not password:
            self.ids.status.text = '⚠ Введите логин и пароль'; return
        self.ids.status.text = '⏳ Подключение...'; self.ids.status.color = App.get_running_app().c['BLUE']
        def cb(st, data):
            if st == 200:
                app = App.get_running_app()
                app.start_session(login, password, UserData.from_dict(data), offline=False)
            elif st == 0:
                def go_offline():
                    ud = app_load_local(login) or create_default(login)
                    save_local(ud)
                    app = App.get_running_app()
                    app.start_session(login, password, ud, offline=True)
                confirm_dialog('Сервер недоступен', 'Работать в локальном режиме?', go_offline)
                self.ids.status.text = ''
            else:
                self.ids.status.text = f"❌ {data.get('error', 'Ошибка')}"
                self.ids.status.color = App.get_running_app().c['RED']
        async_request(f"{SERVER_URL}/login", {'login': login, 'password': password}, 'POST', cb)
    
    def do_register(self):
        login = self.rg_login.text.strip()
        p1, p2 = self.rg_pass.text, self.rg_pass2.text
        if not login or not p1:
            self.ids.status.text = '⚠ Заполните все поля'; return
        if len(login) < 3:
            self.ids.status.text = '⚠ Логин минимум 3 символа'; return
        if len(p1) < 4:
            self.ids.status.text = '⚠ Пароль минимум 4 символа'; return
        if p1 != p2:
            self.ids.status.text = '⚠ Пароли не совпадают'; return
        self.ids.status.text = '⏳ Регистрация...'
        def cb(st, data):
            if st == 200:
                info_dialog('Успех', '✅ Регистрация успешна!\nТеперь войдите.')
                self.show_form('login')
                self.ids.status.text = ''
            elif st == 0:
                info_dialog('Ошибка', 'Сервер недоступен.\nРегистрация только онлайн.')
            else:
                self.ids.status.text = f"❌ {data.get('error', 'Ошибка')}"
        async_request(f"{SERVER_URL}/register", {'login': login, 'password': p1}, 'POST', cb)

def DarkInputFactory(password=False):
    app = App.get_running_app()
    return TextInput(multiline=False, password=password,
                     foreground_color=app.c['TEXT'], background_color=app.c['CARD'],
                     cursor_color=app.c['BLUE'], size_hint_y=None, height=dp(46),
                     font_size=sp(15), padding=[dp(12), dp(12)])

class MainScreen(Screen):
    selected_student = None
    
    def on_pre_enter(self):
        app = App.get_running_app()
        self.ids.user_label.text = f"👤 {app.login}"
        self.ids.mode_label.text = '🔴 ОФЛАЙН' if app.offline else '🟢 ОНЛАЙН'
        self.refresh_groups()
        self.load_group()
        self.build_table()
    
    # ---------- ГРУППЫ ----------
    def refresh_groups(self):
        app = App.get_running_app()
        names = [g.name for g in app.user_data.groups.values()]
        sp_ = self.ids.group_spinner
        sp_.values = names
        cur = app.user_data.groups.get(app.user_data.current_group_id)
        sp_.text = cur.name if cur else (names[0] if names else '')
    
    def on_group_changed(self, name):
        app = App.get_running_app()
        for gid, g in app.user_data.groups.items():
            if g.name == name and gid != app.user_data.current_group_id:
                self.save_data()
                app.user_data.current_group_id = gid
                self.load_group(); self.build_table()
    
    def load_group(self):
        app = App.get_running_app()
        g = app.user_data.groups.get(app.user_data.current_group_id)
        if g is None:
            g = Group('default', 'Основная группа', [], [], {}, 4000.0)
            app.user_data.groups['default'] = g
            app.user_data.current_group_id = 'default'
        self.group = g
    
    def create_group(self):
        def on_ok(name):
            if not name.strip(): return
            app = App.get_running_app()
            gid = f"group_{int(datetime.now().timestamp() * 1000)}"
            app.user_data.groups[gid] = Group(gid, name.strip(), [], [], {}, 4000.0)
            app.user_data.current_group_id = gid
            self.save_data(); self.refresh_groups(); self.load_group(); self.build_table()
        input_dialog('Новая группа', 'Название группы:', on_ok=on_ok)
    
    def rename_group(self):
        def on_ok(name):
            if name.strip():
                self.group.name = name.strip()
                self.save_data(); self.refresh_groups()
        input_dialog('Переименовать', 'Новое название:', initial=self.group.name, on_ok=on_ok)
    
    def delete_group(self):
        app = App.get_running_app()
        if len(app.user_data.groups) <= 1:
            info_dialog('Внимание', 'Нельзя удалить единственную группу!'); return
        def do():
            del app.user_data.groups[app.user_data.current_group_id]
            app.user_data.current_group_id = next(iter(app.user_data.groups))
            self.save_data(); self.refresh_groups(); self.load_group(); self.build_table()
        confirm_dialog('Удаление', f"Удалить группу '{self.group.name}'?", do)
    
    # ---------- ТАБЛИЦА ----------
    def build_table(self):
        app = App.get_running_app()
        grid = self.ids.table_grid
        grid.clear_widgets()
        lessons = sorted(self.group.lessons, key=lambda l: l.datetime)
        grid.cols = 4 + len(lessons)
        
        def header(t, w):
            l = Label(text=t, bold=True, color=app.c['TEXT'], size_hint_x=None, width=dp(w),
                      size_hint_y=None, height=dp(44))
            grid.add_widget(l)
        
        header('ID', 45); header('Ученик', 170); header('%', 70); header('💰', 90)
        for l in lessons:
            header(l.datetime[8:10] + '/' + l.datetime[5:7], 70)
        
        active = [s for s in self.group.students if not s.deleted]
        for s in active:
            att = self.group.attendance.get(s.id, {})
            p = calc_percent(att)
            cost = p * self.group.subscription_price
            for txt, w in [(str(s.id), 45), (s.name, 170), (f"{round(p * 100)}%", 70), (f"{cost:.0f} ₽", 90)]:
                l = Label(text=txt, color=app.c['TEXT'], size_hint_x=None, width=dp(w),
                          size_hint_y=None, height=dp(44))
                grid.add_widget(l)
            for les in lessons:
                present = att.get(les.id, False)
                b = Button(text='✓' if present else '—',
                           background_normal='', background_down='',
                           background_color=app.c['GREEN'] if present else app.c['CARD'],
                           color=(1, 1, 1, 1) if present else app.c['MUT'],
                           size_hint_x=None, width=dp(70), size_hint_y=None, height=dp(44))
                b.bind(on_press=lambda btn, sid=s.id, lid=les.id: self.toggle_attendance(sid, lid))
                grid.add_widget(b)
        
        self.ids.status_bar.text = f"✅ Учеников: {len(active)} · Занятий: {len(lessons)}"
    
    def toggle_attendance(self, sid, lid):
        att = self.group.attendance.setdefault(sid, {})
        att[lid] = not att.get(lid, False)
        self.save_data(); self.build_table()
    
    # ---------- УЧЕНИКИ / ЗАНЯТИЯ ----------
    def add_student(self):
        def on_ok(name):
            if not name.strip(): return
            if any(s.name.lower() == name.strip().lower() and not s.deleted for s in self.group.students):
                info_dialog('Внимание', 'Такой ученик уже есть!'); return
            self.group.students.append(Student(self.group.next_student_id, name.strip()))
            self.group.next_student_id += 1
            self.save_data(); self.build_table()
        input_dialog('Ученик', 'ФИО ученика:', on_ok=on_ok)
    
    def delete_student(self):
        def on_ok(name):
            st = next((s for s in self.group.students if s.name.lower() == name.strip().lower() and not s.deleted), None)
            if not st:
                info_dialog('Ошибка', 'Ученик не найден'); return
            def do():
                st.deleted = True
                self.save_data(); self.build_table()
            confirm_dialog('Удаление', f"Удалить '{st.name}'?", do)
        input_dialog('Удалить ученика', 'ФИО ученика для удаления:', on_ok=on_ok)
    
    def add_lesson(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        def on_ok(dt):
            try: datetime.strptime(dt, "%Y-%m-%d %H:%M")
            except:
                info_dialog('Ошибка', 'Формат: ГГГГ-ММ-ДД ЧЧ:ММ'); return
            if any(l.datetime == dt for l in self.group.lessons):
                info_dialog('Внимание', 'Такое занятие уже есть!'); return
            self.group.lessons.append(Lesson(self.group.next_lesson_id, dt))
            self.group.next_lesson_id += 1
            self.group.lessons.sort(key=lambda x: x.datetime)
            self.save_data(); self.build_table()
        input_dialog('Занятие', 'Дата и время (ГГГГ-ММ-ДД ЧЧ:ММ):', initial=now, on_ok=on_ok)
    
    # ---------- СВОДКА / ЭКСПОРТ ----------
    def show_summary(self):
        text = "📊 Сводка\n" + "═" * 30 + "\n"
        for s in [s for s in self.group.students if not s.deleted]:
            p = calc_percent(self.group.attendance.get(s.id, {}))
            c = p * self.group.subscription_price
            text += f"{s.name}: {p * 100:.0f}% · {c:.0f} ₽\n"
        info_dialog('Сводка', text)
    
    def export_txt(self):
        app = App.get_running_app()
        path = os.path.join(app.user_data_dir, f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"Аккаунт: {app.login}\nГруппа: {self.group.name}\n\n")
            for s in [s for s in self.group.students if not s.deleted]:
                p = calc_percent(self.group.attendance.get(s.id, {}))
                f.write(f"{s.name}: {p * 100:.0f}% · {p * self.group.subscription_price:.2f} ₽\n")
        info_dialog('Успех', f"✅ Сохранено:\n{path}")
    
    # ---------- МЕНЮ ----------
    def open_menu(self):
        app = App.get_running_app()
        box = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=dp(8))
        box.bind(minimum_height=box.setter('height'))
        popup = Popup(title='Меню', content=box, size_hint=(0.8, 0.6),
                      background_color=app.c['BG2'], title_color=app.c['TEXT'])
        items = [('💰 Стоимость абонемента', self.set_price),
                 ('🔑 Сменить пароль', self.change_password),
                 ('ℹ Об аккаунте', self.account_info),
                 ('🚪 Выйти', self.logout)]
        for text, cmd in items:
            b = Button(text=text, size_hint_y=None, height=dp(48), background_normal='',
                       background_color=app.c['CARD'], color=app.c['TEXT'])
            b.bind(on_press=lambda w, c=cmd: (popup.dismiss(), c()))
            box.add_widget(b)
        popup.open()
    
    def set_price(self):
        def on_ok(v):
            try:
                self.group.subscription_price = float(v.replace(',', '.'))
                self.save_data(); self.build_table()
            except: info_dialog('Ошибка', 'Введите число')
        input_dialog('Стоимость', 'Стоимость абонемента (руб):',
                     initial=str(self.group.subscription_price), on_ok=on_ok)
    
    def change_password(self):
        app = App.get_running_app()
        if app.offline:
            info_dialog('Офлайн', 'Только в онлайн-режиме.'); return
        box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(10))
        box.bind(minimum_height=box.setter('height'))
        o = TextInput(multiline=False, password=True, background_color=app.c['CARD'], foreground_color=app.c['TEXT'], size_hint_y=None, height=dp(44))
        n = TextInput(multiline=False, password=True, background_color=app.c['CARD'], foreground_color=app.c['TEXT'], size_hint_y=None, height=dp(44))
        btn = Button(text='Сменить', size_hint_y=None, height=dp(46), background_normal='', background_color=app.c['BLUE'])
        box.add_widget(o); box.add_widget(n); box.add_widget(btn)
        popup = Popup(title='🔑 Новый пароль', content=box, size_hint=(0.8, 0.45),
                      background_color=app.c['BG2'], title_color=app.c['TEXT'])
        def do(w):
            if len(n.text) < 4:
                info_dialog('Ошибка', 'Минимум 4 символа'); return
            def cb(st, data):
                popup.dismiss()
                if st == 200:
                    app.password = n.text
                    info_dialog('Успех', '✅ Пароль изменён!')
                else:
                    info_dialog('Ошибка', data.get('error', 'Ошибка'))
            async_request(f"{SERVER_URL}/change_password",
                          {'login': app.login, 'old_password': o.text, 'new_password': n.text}, 'POST', cb)
        btn.bind(on_press=do)
        popup.open()
    
    def account_info(self):
        app = App.get_running_app()
        info_dialog('Аккаунт',
            f"👤 {app.login}\n📡 {'ОФЛАЙН' if app.offline else 'ОНЛАЙН'}\n🌐 {SERVER_URL}\n👥 Групп: {len(app.user_data.groups)}")
    
    def logout(self):
        def do():
            App.get_running_app().logout()
        confirm_dialog('Выход', 'Выйти из аккаунта?', do)
    
    # ---------- СОХРАНЕНИЕ ----------
    def save_data(self):
        app = App.get_running_app()
        data = app.user_data.to_dict()
        try:
            with open(os.path.join(app.user_data_dir, f"jour_{app.login}_local.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass
        if not app.offline:
            def cb(st, res):
                self.ids.status_bar.text = '✅ Сохранено' if st == 200 else '⚠ Ошибка сервера'
            async_request(f"{SERVER_URL}/save",
                          {'login': app.login, 'password': app.password, 'data': data}, 'POST', cb)
        else:
            self.ids.status_bar.text = '💾 Сохранено локально'

# ============================================================
# ХРАНЕНИЕ
# ============================================================
def app_load_local(login):
    p = os.path.join(App.get_running_app().user_data_dir, f"jour_{login}_local.json")
    if not os.path.exists(p): return None
    try: return UserData.from_dict(json.load(open(p, encoding='utf-8')))
    except: return None

def save_local(ud):
    p = os.path.join(App.get_running_app().user_data_dir, f"jour_{ud.login}_local.json")
    json.dump(ud.to_dict(), open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def create_default(login):
    return UserData(login, {'default': Group('default', 'Моя первая группа', [], [], {}, 4000.0)}, 'default')

# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================
class JournalApp(App):
    theme = 'dark'
    login = password = ''
    user_data = None
    offline = False
    c = {}
    
    def build(self):
        self.load_theme()
        Builder.load_string(KV)
        if sys.platform not in ('android', 'linux'):
            Window.size = (500, 750)
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(MainScreen(name='main'))
        return self.sm
    
    def load_theme(self):
        try:
            if os.path.exists(os.path.join(self.user_data_dir, 'theme.json')):
                self.theme = json.load(open(os.path.join(self.user_data_dir, 'theme.json'))).get('theme', 'dark')
        except: pass
        self.apply_colors()
    
    def apply_colors(self):
        self.c = {k: rgba(v) for k, v in PALETTES[self.theme].items()}
    
    def toggle_theme(self):
        self.theme = 'light' if self.theme == 'dark' else 'dark'
        try: json.dump({'theme': self.theme}, open(os.path.join(self.user_data_dir, 'theme.json'), 'w'))
        except: pass
        self.apply_colors()
        self.rebuild()
    
    def rebuild(self):
        """Пересоздать экраны с новыми цветами"""
        current = self.sm.current
        Window.remove_widget(self.sm)
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.current = current if (self.user_data and current == 'main') else ('main' if self.user_data else 'login')
        Window.add_widget(self.sm)
    
    def start_session(self, login, password, user_data, offline):
        self.login, self.password, self.user_data, self.offline = login, password, user_data, offline
        self.sm.current = 'main'
    
    def logout(self):
        self.login = self.password = ''
        self.user_data = None
        self.sm.current = 'login'
        self.rebuild()

if __name__ == '__main__':
    JournalApp().run()