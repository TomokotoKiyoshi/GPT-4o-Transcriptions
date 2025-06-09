import pyaudio
import numpy as np
import threading
import queue
import time
import wave
import io
import requests
from collections import deque
import tkinter as tk
from tkinter import ttk
import os
from datetime import datetime
import json

class FloatingSubtitleWindow:
    """浮動字幕表示ウィンドウクラス / Floating Subtitle Display Window Class"""
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.is_visible = False
        
        # ドラッグ関連変数 / Dragging-related variables
        self.start_x = 0
        self.start_y = 0
        self.dragging = False
        
        # サイズ変更関連変数 / Resizing-related variables
        self.resizing = False
        self.resize_edge = None
        self.start_width = 0
        self.start_height = 0
        
        # 字幕履歴（最新2件を保持） / Subtitle history (keep last two entries)
        self.subtitle_history = deque(maxlen=2)
        
        # フォントサイズ設定 / Font size settings
        self.font_size = 14
        self.min_font_size = 8
        self.max_font_size = 24
        
    def create_window(self):
        """ウィンドウ作成 / Create window"""
        if self.window:
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("浮動字幕 / Floating Subtitle")
        
        # 画面下部中央位置を計算 / Calculate centered position at bottom of screen
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        window_width = 600
        window_height = 140
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 50  # 下から50ピクセル / 50 pixels from bottom
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ウィンドウ属性設定 / Set window attributes
        self.window.attributes('-alpha', 0.8)  # 半透明 / Semi-transparent
        self.window.attributes('-topmost', True)  # 最前面表示 / Keep on top
        self.window.overrideredirect(True)  # 枠なし / No border
        
        # ウィンドウ背景色設定 / Set window background color
        self.window.configure(bg='#808080')
        
        # メインコンテナフレーム作成 / Create main container frame
        main_frame = tk.Frame(self.window, bg='#808080')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # コントロールボタンフレーム（上部）作成 / Create control button frame (top)
        control_frame = tk.Frame(main_frame, bg='#808080', height=25)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        control_frame.pack_propagate(False)
        
        # フォントサイズ減少ボタン / Decrease font size button
        self.decrease_font_btn = tk.Button(
            control_frame,
            text="A-",
            bg='#606060',
            fg='white',
            font=('Arial', 8, 'bold'),
            relief='flat',
            width=3,
            height=1,
            command=self.decrease_font_size
        )
        self.decrease_font_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # フォントサイズ増加ボタン / Increase font size button
        self.increase_font_btn = tk.Button(
            control_frame,
            text="A+",
            bg='#606060',
            fg='white',
            font=('Arial', 8, 'bold'),
            relief='flat',
            width=3,
            height=1,
            command=self.increase_font_size
        )
        self.increase_font_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # フォントサイズ表示ラベル / Font size display label
        self.font_size_label = tk.Label(
            control_frame,
            text=f"フォント: {self.font_size}",
            bg='#808080',
            fg='white',
            font=('Arial', 8)
        )
        self.font_size_label.pack(side=tk.LEFT)
        
        # 字幕表示ラベル作成 / Create subtitle display label
        self.subtitle_label = tk.Label(
            main_frame,
            text="字幕オーバーレイが有効です。テキスト化を待機中... / Subtitle overlay is enabled. Waiting for transcription...",
            bg='#808080',
            fg='black',
            font=('Yu Gothic', self.font_size, 'bold'),
            wraplength=window_width - 20,
            justify=tk.LEFT,
            anchor='nw'
        )
        self.subtitle_label.pack(fill=tk.BOTH, expand=True)
        
        # イベントバインド / Bind events
        self.bind_events()
        
    def bind_events(self):
        """マウスイベントバインド / Bind mouse events"""
        # ウィンドウと字幕ラベルにバインド（ドラッグ用） / Bind to window and subtitle label for dragging
        for widget in [self.window, self.subtitle_label]:
            widget.bind('<Button-1>', self.on_click)
            widget.bind('<B1-Motion>', self.on_drag)
            widget.bind('<ButtonRelease-1>', self.on_release)
            widget.bind('<Motion>', self.on_motion)
            
    def decrease_font_size(self):
        """フォントサイズを減少 / Decrease font size"""
        if self.font_size > self.min_font_size:
            self.font_size -= 1
            self.update_font()
            
    def increase_font_size(self):
        """フォントサイズを増加 / Increase font size"""
        if self.font_size < self.max_font_size:
            self.font_size += 1
            self.update_font()
            
    def update_font(self):
        """フォントサイズ表示を更新 / Update font size display"""
        if self.subtitle_label:
            self.subtitle_label.configure(font=('Yu Gothic', self.font_size, 'bold'))
        if self.font_size_label:
            self.font_size_label.configure(text=f"Font: {self.font_size}")
            
    def on_click(self, event):
        """マウスクリックイベント / Mouse click event"""
        # ボタン操作以外の場合のみ反応 / Only respond if not clicking font buttons
        if event.widget in [self.decrease_font_btn, self.increase_font_btn]:
            return
            
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        # サイズ変更用のエッジ判定 / Check if on edge for resizing
        widget_x = event.x_root - self.window.winfo_rootx()
        widget_y = event.y_root - self.window.winfo_rooty()
        
        edge = self.get_resize_edge(widget_x, widget_y)
        if edge:
            self.resizing = True
            self.resize_edge = edge
            self.start_width = self.window.winfo_width()
            self.start_height = self.window.winfo_height()
        else:
            self.dragging = True
            
    def on_drag(self, event):
        """マウスドラッグイベント / Mouse drag event"""
        if self.dragging:
            # ウィンドウ移動 / Move window
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            
            new_x = self.window.winfo_x() + dx
            new_y = self.window.winfo_y() + dy
            
            self.window.geometry(f"+{new_x}+{new_y}")
            
            self.start_x = event.x_root
            self.start_y = event.y_root
            
        elif self.resizing:
            # ウィンドウサイズ変更 / Resize window
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            
            new_width = self.start_width
            new_height = self.start_height
            
            if 'right' in self.resize_edge:
                new_width = max(200, self.start_width + dx)
            elif 'left' in self.resize_edge:
                new_width = max(200, self.start_width - dx)
                
            if 'bottom' in self.resize_edge:
                new_height = max(80, self.start_height + dy)
            elif 'top' in self.resize_edge:
                new_height = max(80, self.start_height - dy)
                
            # 幅、高さを更新 / Update geometry
            geometry = f"{new_width}x{new_height}"
            if 'left' in self.resize_edge:
                new_x = self.window.winfo_x() + (self.start_width - new_width)
                geometry += f"+{new_x}+{self.window.winfo_y()}"
            if 'top' in self.resize_edge:
                new_y = self.window.winfo_y() + (self.start_height - new_height)
                geometry += f"+{self.window.winfo_x()}+{new_y}"
                
            self.window.geometry(geometry)
            
            # ラベルの wraplength を更新 / Update label wraplength
            self.subtitle_label.configure(wraplength=new_width - 20)
            
    def on_release(self, event):
        """マウスリリースイベント / Mouse release event"""
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        
    def on_motion(self, event):
        """マウス移動イベント（カーソル変更用） / Mouse motion event (change cursor)"""
        if not self.dragging and not self.resizing:
            widget_x = event.x_root - self.window.winfo_rootx()
            widget_y = event.y_root - self.window.winfo_rooty()
            
            edge = self.get_resize_edge(widget_x, widget_y)
            if edge:
                cursor = self.get_cursor_for_edge(edge)
                self.window.configure(cursor=cursor)
            else:
                self.window.configure(cursor="arrow")
                
    def get_resize_edge(self, x, y):
        """マウス位置に応じたエッジを取得 / Get edge based on mouse position"""
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        edge_size = 10
        
        edges = []
        
        if x <= edge_size:
            edges.append('left')
        elif x >= width - edge_size:
            edges.append('right')
            
        if y <= edge_size:
            edges.append('top')
        elif y >= height - edge_size:
            edges.append('bottom')
            
        return '+'.join(edges) if edges else None
        
    def get_cursor_for_edge(self, edge):
        """エッジに応じたカーソルを返す / Return cursor style based on edge"""
        cursor_map = {
            'top': 'top_side',
            'bottom': 'bottom_side',
            'left': 'left_side',
            'right': 'right_side',
            'top+left': 'top_left_corner',
            'top+right': 'top_right_corner',
            'bottom+left': 'bottom_left_corner',
            'bottom+right': 'bottom_right_corner'
        }
        return cursor_map.get(edge, 'arrow')
        
    def show(self):
        """浮動ウィンドウを表示 / Show floating window"""
        if not self.window:
            self.create_window()
        self.window.deiconify()
        self.is_visible = True
        
    def hide(self):
        """浮動ウィンドウを隠す / Hide floating window"""
        if self.window:
            self.window.withdraw()
        self.is_visible = False
        
    def destroy(self):
        """浮動ウィンドウを破棄 / Destroy floating window"""
        if self.window:
            self.window.destroy()
            self.window = None
        self.is_visible = False
        
    def update_subtitle(self, text):
        """字幕表示を更新 / Update subtitle display"""
        if text.strip():
            self.subtitle_history.append(text.strip())
            
            # 最新2件の字幕を表示 / Display the latest two subtitles
            display_text = '\n'.join(self.subtitle_history)
            
            if self.window and self.is_visible:
                self.subtitle_label.configure(text=display_text)
                # テキストの wraplength を更新 / Update wraplength for text
                current_width = self.window.winfo_width()
                self.subtitle_label.configure(wraplength=current_width - 20)

class RealtimeJapaneseTranscriber:
    """リアルタイム字幕転写システム（キーワード付き） / Real-time Japanese Subtitle Transcription System (with keyword)"""
    
    def __init__(self, api_key):
        # Multi-language support
        self.translations = {
            'ja': {
                'window_title': 'リアルタイム字幕システム（キーワード付き）',
                'main_title': 'リアルタイム字幕システム',
                'subtitle': 'Real-time Subtitle Transcription System',
                'keyword_label': 'キーワード：',
                'language_label': '転写言語：',
                'start_button': '🎙️ 録音開始',
                'stop_button': '⏹️ 録音停止',
                'floating_button': '🖥️ 浮動字幕',
                'floating_button_hide': '🖥️ 非表示',
                'system_status': 'システム状態',
                'waiting_status': '開始待ち',
                'recording_status': '録音中...',
                'stopped_status': '停止',
                'audio_level': 'オーディオレベル',
                'subtitle_display': 'リアルタイム字幕表示',
                'system_info': 'システム情報',
                'system_idle': 'システム待機中...',
                'font_label': 'フォント',
                'response_time': '応答時間',
                'prompt_length': 'プロンプト長',
                'buffer_length': 'バッファ長',
                'gui_language': '言語'
            },
            'en': {
                'window_title': 'Real-time Subtitle System (with keyword)',
                'main_title': 'Real-time Subtitle System',
                'subtitle': 'Real-time Subtitle Transcription System',
                'keyword_label': 'Keyword:',
                'language_label': 'Transcription Language:',
                'start_button': '🎙️ Start Recording',
                'stop_button': '⏹️ Stop Recording',
                'floating_button': '🖥️ Floating Subtitle',
                'floating_button_hide': '🖥️ Hide Floating',
                'system_status': 'System Status',
                'waiting_status': 'Waiting to start',
                'recording_status': 'Recording...',
                'stopped_status': 'Stopped',
                'audio_level': 'Audio Level',
                'subtitle_display': 'Real-time Subtitle Display',
                'system_info': 'System Information',
                'system_idle': 'System idle...',
                'font_label': 'Font',
                'response_time': 'Response time',
                'prompt_length': 'Prompt length',
                'buffer_length': 'Buffer length',
                'gui_language': 'Language'
            },
            'zh': {
                'window_title': '实时字幕系统（带关键词）',
                'main_title': '实时字幕系统',
                'subtitle': '实时字幕转录系统',
                'keyword_label': '关键词：',
                'language_label': '转录语言：',
                'start_button': '🎙️ 开始录音',
                'stop_button': '⏹️ 停止录音',
                'floating_button': '🖥️ 浮动字幕',
                'floating_button_hide': '🖥️ 隐藏浮动',
                'system_status': '系统状态',
                'waiting_status': '等待开始',
                'recording_status': '录音中...',
                'stopped_status': '已停止',
                'audio_level': '音频电平',
                'subtitle_display': '实时字幕显示',
                'system_info': '系统信息',
                'system_idle': '系统空闲...',
                'font_label': '字体',
                'response_time': '响应时间',
                'prompt_length': '提示长度',
                'buffer_length': '缓冲区长度',
                'gui_language': '语言'
            },
            'ko': {
                'window_title': '실시간 자막 시스템 (키워드 포함)',
                'main_title': '실시간 자막 시스템',
                'subtitle': '실시간 자막 전사 시스템',
                'keyword_label': '키워드:',
                'language_label': '전사 언어:',
                'start_button': '🎙️ 녹음 시작',
                'stop_button': '⏹️ 녹음 중지',
                'floating_button': '🖥️ 플로팅 자막',
                'floating_button_hide': '🖥️ 플로팅 숨기기',
                'system_status': '시스템 상태',
                'waiting_status': '시작 대기 중',
                'recording_status': '녹음 중...',
                'stopped_status': '중지됨',
                'audio_level': '오디오 레벨',
                'subtitle_display': '실시간 자막 표시',
                'system_info': '시스템 정보',
                'system_idle': '시스템 유휴...',
                'font_label': '글꼴',
                'response_time': '응답 시간',
                'prompt_length': '프롬프트 길이',
                'buffer_length': '버퍼 길이',
                'gui_language': '언어'
            }
        }
        
        # Current GUI language
        self.current_lang = 'ja'  # Default to Japanese
        
        # Load saved language preference
        self.load_language_preference()
        
        # オーディオ設定 / Audio configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK_DURATION = 4.0    # 各チャンクの長さ（秒） / Each chunk duration (seconds)
        self.OVERLAP_DURATION = 0.8    # 重なり部分の長さ（秒） / Overlap duration (seconds)
        
        # API設定 / API configuration
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        
        # 状態管理 / State management
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.context_history = deque(maxlen=4)  # 最新3チャンクの文脈を保持 / Keep last 3 chunks of context
        
        # キーワード / Keyword
        self.meeting_topic = ""  # GUIから入力されたキーワードを格納 / Store keyword entered in GUI
        
        # オーディオバッファ / Audio buffer
        self.audio_buffer = []
        self.overlap_buffer = []
        
        # PyAudio初期化 / Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # スレッド管理 / Thread management
        self.processing_thread = None
        self.transcription_thread = None
        
        # 浮動字幕ウィンドウ / Floating subtitle window
        self.floating_subtitle = None
        
        # カラーテーマ / Color theme
        self.colors = {
            'primary': '#2E3440',      # ダークブルーグレー / Dark blue-gray
            'secondary': '#3B4252',    # より明るいダークグレー / Lighter dark gray
            'accent': '#5E81AC',       # ブルーアクセント / Blue accent
            'success': '#A3BE8C',      # 緑 / Green
            'warning': '#EBCB8B',      # 黄 / Yellow
            'danger': '#BF616A',       # 赤 / Red
            'text': '#2E3440',         # ダークテキスト / Dark text
            'text_light': '#4C566A',   # ライトグレーのテキスト / Light gray text
            'background': '#ECEFF4',   # ライト背景 / Light background
            'surface': '#FFFFFF',      # 白表面 / White surface
            'border': '#D8DEE9'        # ライトボーダー / Light border
        }
        
        # GUI components that need text updates
        self.gui_components = {}
        
        # GUI初期化 / Initialize GUI
        self.setup_gui()
        
    def load_language_preference(self):
        """Load saved language preference"""
        try:
            if os.path.exists('gui_language.json'):
                with open('gui_language.json', 'r') as f:
                    data = json.load(f)
                    self.current_lang = data.get('language', 'ja')
        except:
            self.current_lang = 'ja'
            
    def save_language_preference(self):
        """Save language preference"""
        try:
            with open('gui_language.json', 'w') as f:
                json.dump({'language': self.current_lang}, f)
        except:
            pass
            
    def get_text(self, key):
        """Get translated text for current language"""
        return self.translations[self.current_lang].get(key, key)
        
    def setup_gui(self):
        """強化されたGUIセットアップ / Enhanced GUI setup"""
        self.root = tk.Tk()
        self.root.title(self.get_text('window_title'))
        # ウィンドウサイズを設定 / Set window size larger
        self.root.geometry("900x850")
        self.root.configure(bg=self.colors['background'])
        
        # ttkスタイル設定 / Configure ttk style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # カスタムスタイル設定 / Configure custom styles
        self.configure_styles()
        
        # パディング付きメインコンテナ作成 / Create main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # GUI言語選択セクション（右上）/ GUI language selection section (top-right)
        self.create_language_selector(main_container)
        
        # ヘッダーセクション作成 / Create header section
        self.create_header(main_container)
        
        # キーワード入力セクション作成 / Create keyword input section
        self.create_topic_section(main_container)
        
        # コントロールパネルセクション作成 / Create control panel section
        self.create_control_section(main_container)
        
        # ステータスとオーディオレベルセクション作成 / Create status and audio level section
        self.create_status_section(main_container)
        
        # 字幕表示セクション作成 / Create subtitle display section
        self.create_subtitle_section(main_container)
        
        # デバッグ情報セクション作成 / Create debug information section
        self.create_debug_section(main_container)
        
        # 浮動字幕ウィンドウ初期化 / Initialize floating subtitle window
        self.floating_subtitle = FloatingSubtitleWindow(self.root)
        
        # ウィンドウ閉じるイベント / Window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def configure_styles(self):
        """モダン表示のためのカスタムttkスタイル設定 / Configure custom ttk styles for modern appearance"""
        # ボタンスタイル設定 / Configure button styles
        self.style.configure('Primary.TButton',
                           background=self.colors['accent'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(20, 10))
        
        self.style.map('Primary.TButton',
                      background=[('active', '#4C7EA3'),
                                ('pressed', '#3E6D8F')])
        
        self.style.configure('Success.TButton',
                           background=self.colors['success'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(20, 10))
        
        self.style.map('Success.TButton',
                      background=[('active', '#8FA676'),
                                ('pressed', '#7A8F65')])
        
        self.style.configure('Danger.TButton',
                           background=self.colors['danger'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none',
                           padding=(20, 10))
        
        self.style.map('Danger.TButton',
                      background=[('active', '#A54A54'),
                                ('pressed', '#8B3E47')])
        
        # エントリースタイル設定 / Configure entry style
        self.style.configure('Modern.TEntry',
                           fieldbackground=self.colors['surface'],
                           borderwidth=2,
                           relief='solid',
                           bordercolor=self.colors['border'],
                           padding=(12, 8))
        
        # ラベルフレームスタイル設定 / Configure labelframe style
        self.style.configure('Modern.TLabelframe',
                           background=self.colors['surface'],
                           borderwidth=1,
                           relief='solid',
                           bordercolor=self.colors['border'])
        
        self.style.configure('Modern.TLabelframe.Label',
                           background=self.colors['surface'],
                           foreground=self.colors['text'],
                           font=('Segoe UI', 11, 'bold'))
        
        # コンボボックススタイル設定 / Configure combobox style
        self.style.configure('Modern.TCombobox',
                           fieldbackground=self.colors['surface'],
                           background=self.colors['surface'],
                           borderwidth=2,
                           relief='solid',
                           bordercolor=self.colors['border'],
                           selectbackground=self.colors['accent'],
                           selectforeground='white')
        
        # プログレスバースタイル設定 / Configure progressbar style
        self.style.configure('Modern.Horizontal.TProgressbar',
                           background=self.colors['accent'],
                           troughcolor=self.colors['border'],
                           borderwidth=0,
                           lightcolor=self.colors['accent'],
                           darkcolor=self.colors['accent'])
        
    def create_language_selector(self, parent):
        """Create GUI language selector in top-right corner"""
        lang_frame = tk.Frame(parent, bg=self.colors['background'])
        lang_frame.pack(anchor='ne', pady=(0, 10))
        
        lang_label = tk.Label(lang_frame,
                            text='Language:',
                            font=('Segoe UI', 10),
                            fg=self.colors['text_light'],
                            bg=self.colors['background'])
        lang_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.gui_lang_var = tk.StringVar(value=self.current_lang)
        self.gui_lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.gui_lang_var,
            values=['ja - 日本語', 'en - English', 'zh - 中文', 'ko - 한국어'],
            font=('Segoe UI', 10),
            style='Modern.TCombobox',
            state='readonly',
            width=15
        )
        self.gui_lang_combo.set(f"{self.current_lang} - {['日本語', 'English', '中文', '한국어'][['ja', 'en', 'zh', 'ko'].index(self.current_lang)]}")
        self.gui_lang_combo.pack(side=tk.LEFT)
        self.gui_lang_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
    def on_language_change(self, event=None):
        """Handle GUI language change"""
        selection = self.gui_lang_combo.get()
        new_lang = selection.split(' - ')[0]
        if new_lang != self.current_lang:
            self.current_lang = new_lang
            self.save_language_preference()
            self.update_all_texts()
            
    def update_all_texts(self):
        """Update all GUI texts to current language"""
        # Update window title
        self.root.title(self.get_text('window_title'))
        
        # Update all stored GUI components
        if hasattr(self, 'title_label'):
            self.title_label.config(text=self.get_text('main_title'))
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.config(text=self.get_text('subtitle'))
        if hasattr(self, 'topic_label'):
            self.topic_label.config(text=self.get_text('keyword_label'))
        if hasattr(self, 'language_label'):
            self.language_label.config(text=self.get_text('language_label'))
        if hasattr(self, 'start_button'):
            self.start_button.config(text=self.get_text('start_button'))
        if hasattr(self, 'stop_button'):
            self.stop_button.config(text=self.get_text('stop_button'))
        if hasattr(self, 'floating_toggle_button'):
            if self.floating_subtitle and self.floating_subtitle.is_visible:
                self.floating_toggle_button.config(text=self.get_text('floating_button_hide'))
            else:
                self.floating_toggle_button.config(text=self.get_text('floating_button'))
        if hasattr(self, 'status_title'):
            self.status_title.config(text=self.get_text('system_status'))
        if hasattr(self, 'level_label'):
            self.level_label.config(text=self.get_text('audio_level'))
        if hasattr(self, 'subtitle_frame'):
            self.subtitle_frame.config(text=self.get_text('subtitle_display'))
        if hasattr(self, 'debug_frame'):
            self.debug_frame.config(text=self.get_text('system_info'))
            
        # Update status label based on current state
        if hasattr(self, 'status_label'):
            if self.is_recording:
                self.status_label.config(text=self.get_text('recording_status'))
            elif hasattr(self, '_stopped') and self._stopped:
                self.status_label.config(text=self.get_text('stopped_status'))
            else:
                self.status_label.config(text=self.get_text('waiting_status'))
                
        # Update debug info
        if hasattr(self, 'debug_info'):
            if not self.is_recording:
                self.debug_info.set(self.get_text('system_idle'))
        
    def create_header(self, parent):
        """ヘッダーセクション作成 / Create application header section"""
        header_frame = tk.Frame(parent, bg=self.colors['background'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # メインタイトル / Main title
        self.title_label = tk.Label(header_frame, 
                              text=self.get_text('main_title'),
                              font=('Yu Gothic', 24, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        self.title_label.pack()
        
        # サブタイトル / Subtitle
        self.subtitle_label = tk.Label(header_frame,
                                 text=self.get_text('subtitle'),
                                 font=('Segoe UI', 12),
                                 fg=self.colors['text_light'],
                                 bg=self.colors['background'])
        self.subtitle_label.pack(pady=(5, 0))
        
    def create_topic_section(self, parent):
        """キーワード入力セクション作成 / Create keyword input section"""
        topic_frame = tk.Frame(parent, bg=self.colors['surface'], relief='solid', bd=1)
        topic_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 内部パディングフレーム / Internal padding frame
        topic_inner = tk.Frame(topic_frame, bg=self.colors['surface'])
        topic_inner.pack(fill=tk.X, padx=20, pady=20)
        
        # ラベル: キーワード入力 / First row: keyword label
        self.topic_label = tk.Label(topic_inner, 
                              text=self.get_text('keyword_label'),
                              font=('Yu Gothic', 14, 'bold'),
                              fg=self.colors['text'],
                              bg=self.colors['surface'])
        self.topic_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.topic_entry = ttk.Entry(topic_inner, 
                                    font=('Yu Gothic', 12),
                                    style='Modern.TEntry')
        self.topic_entry.pack(fill=tk.X, pady=(0, 15))
        
        # ラベル: 言語選択 / Second row: language selection label
        self.language_label = tk.Label(topic_inner, 
                                 text=self.get_text('language_label'),
                                 font=('Yu Gothic', 14, 'bold'),
                                 fg=self.colors['text'],
                                 bg=self.colors['surface'])
        self.language_label.pack(anchor=tk.W, pady=(0, 8))
        
        # 言語選択コンボボックス / Language selection combobox
        self.language_var = tk.StringVar(value="ja")
        self.language_combo = ttk.Combobox(
            topic_inner,
            textvariable=self.language_var,
            values=[
                ("ja", "日本語 (Japanese)"),
                ("en", "English"),
                ("zh", "中文 (Chinese)"),
                ("ko", "한국어 (Korean)"),
                ("es", "Español"),
                ("fr", "Français"),
                ("de", "Deutsch"),
                ("ru", "Русский"),
                ("auto", "自動検出 (Auto-detect)")
            ],
            font=('Yu Gothic', 12),
            style='Modern.TCombobox',
            state="readonly",
            width=30
        )
        
        # 表示形式設定 / Set display format
        language_options = [
            "ja - 日本語 (Japanese)",
            "en - English", 
            "zh - 中文 (Chinese)",
            "ko - 한국어 (Korean)",
            "es - Español",
            "fr - Français", 
            "de - Deutsch",
            "ru - Русский",
            "auto - 自動検出 (Auto-detect)"
        ]
        self.language_combo['values'] = language_options
        self.language_combo.set("ja - 日本語 (Japanese)")
        self.language_combo.pack(fill=tk.X)
        
    def create_control_section(self, parent):
        """録音制御ボタンセクション作成 / Create recording control button section"""
        control_frame = tk.Frame(parent, bg=self.colors['background'])
        control_frame.pack(pady=20)
        
        button_frame = tk.Frame(control_frame, bg=self.colors['background'])
        button_frame.pack()
        
        self.start_button = ttk.Button(
            button_frame, 
            text=self.get_text('start_button'),
            command=self.start_recording,
            style='Success.TButton'
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_button = ttk.Button(
            button_frame, 
            text=self.get_text('stop_button'),
            command=self.stop_recording,
            state=tk.DISABLED,
            style='Danger.TButton'
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # 浮動字幕制御ボタン / Floating subtitle control button
        self.floating_toggle_button = ttk.Button(
            button_frame,
            text=self.get_text('floating_button'),
            command=self.toggle_floating_subtitle,
            style='Primary.TButton'
        )
        self.floating_toggle_button.pack(side=tk.LEFT)
        
    def create_status_section(self, parent):
        """ステータスとオーディオレベル表示セクション作成 / Create status and audio level display section"""
        status_frame = tk.Frame(parent, bg=self.colors['surface'], relief='solid', bd=1)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 内部パディングフレーム / Internal padding frame
        status_inner = tk.Frame(status_frame, bg=self.colors['surface'])
        status_inner.pack(fill=tk.X, padx=20, pady=15)
        
        # ステータス表示 / Status display
        status_row = tk.Frame(status_inner, bg=self.colors['surface'])
        status_row.pack(fill=tk.X, pady=(0, 15))
        
        self.status_title = tk.Label(status_row, 
                               text=self.get_text('system_status'),
                               font=('Yu Gothic', 12, 'bold'),
                               fg=self.colors['text'],
                               bg=self.colors['surface'])
        self.status_title.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(status_row, 
                                    text=self.get_text('waiting_status'),
                                    font=('Yu Gothic', 12),
                                    fg=self.colors['accent'],
                                    bg=self.colors['surface'])
        self.status_label.pack(side=tk.RIGHT)
        
        # オーディオレベル表示 / Audio level display
        level_row = tk.Frame(status_inner, bg=self.colors['surface'])
        level_row.pack(fill=tk.X)
        
        self.level_label = tk.Label(level_row, 
                                   text=self.get_text('audio_level'),
                                   font=('Yu Gothic', 12, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['surface'])
        self.level_label.pack(side=tk.LEFT)
        
        self.level_bar = ttk.Progressbar(
            level_row, 
            length=200, 
            mode='determinate',
            style='Modern.Horizontal.TProgressbar'
        )
        self.level_bar.pack(side=tk.RIGHT)
        
    def create_subtitle_section(self, parent):
        """字幕表示セクション作成 / Create subtitle display section"""
        self.subtitle_frame = ttk.LabelFrame(parent, 
                                       text=self.get_text('subtitle_display'),
                                       style='Modern.TLabelframe',
                                       padding=20)
        self.subtitle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # カスタムスクロールバー付きテキストウィジェット / Text widget with custom scrollbar
        text_frame = tk.Frame(self.subtitle_frame, bg=self.colors['surface'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.subtitle_text = tk.Text(
            text_frame,
            font=('Yu Gothic', 12),
            bg=self.colors['surface'],
            fg=self.colors['text'],
            wrap=tk.WORD,
            relief='flat',
            selectbackground=self.colors['accent'],
            selectforeground='white',
            padx=15,
            pady=15,
            spacing1=5,
            spacing3=0  # 字幕間の余白をなくす / Remove space between subtitles
        )
        
        # カスタムスクロールバー / Custom scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.subtitle_text.yview)
        self.subtitle_text.configure(yscrollcommand=scrollbar.set)
        
        self.subtitle_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_debug_section(self, parent):
        """デバッグ情報セクション作成 / Create debug information section"""
        self.debug_frame = ttk.LabelFrame(parent, 
                                    text=self.get_text('system_info'),
                                    style='Modern.TLabelframe',
                                    padding=15)
        self.debug_frame.pack(fill=tk.X)
        
        self.debug_info = tk.StringVar()
        self.debug_info.set(self.get_text('system_idle'))
        
        debug_label = tk.Label(self.debug_frame, 
                              textvariable=self.debug_info,
                              font=('Consolas', 10),
                              fg=self.colors['text_light'],
                              bg=self.colors['surface'],
                              justify=tk.LEFT)
        debug_label.pack(anchor=tk.W)
        
    def toggle_floating_subtitle(self):
        """浮動字幕表示を切り替え / Toggle floating subtitle display"""
        if self.floating_subtitle.is_visible:
            self.floating_subtitle.hide()
            self.floating_toggle_button.configure(text=self.get_text('floating_button'))
        else:
            self.floating_subtitle.show()
            self.floating_toggle_button.configure(text=self.get_text('floating_button_hide'))
            
    def on_closing(self):
        """ウィンドウ閉じるイベント処理 / Handle window closing event"""
        self.stop_recording()
        if self.floating_subtitle:
            self.floating_subtitle.destroy()
        self.root.destroy()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """オーディオストリームコールバック / Audio stream callback"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def start_recording(self):
        """録音開始 / Start recording"""
        # 録音開始前にキーワードを取得 / Get keyword before starting recording
        self.meeting_topic = self.topic_entry.get().strip()
        
        self.is_recording = True
        self._stopped = False
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=self.get_text('recording_status'), fg=self.colors['success'])
        
        # オーディオストリームを開く / Open audio stream
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )
        
        # スレッド起動 / Start processing and transcription threads
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.context_history.clear()
        
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()
        
        self.transcription_thread = threading.Thread(target=self.transcribe_audio, daemon=True)
        self.transcription_thread.start()
        
        # GUI更新ループ開始 / Start GUI update loop
        self.update_gui()
        
    def stop_recording(self):
        """録音停止 / Stop recording"""
        self.is_recording = False
        self._stopped = True
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text=self.get_text('stopped_status'), fg=self.colors['danger'])
        
        # オーディオストリームを閉じる / Close audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # バッファをクリア / Clear buffers
        self.audio_buffer = []
        self.overlap_buffer = []
        self.context_history.clear()
        
    def process_audio(self):
        """オーディオデータを処理し、チャンクを転写キューに投入 / Process audio data and enqueue chunks for transcription"""
        chunk_samples = int(self.RATE * self.CHUNK_DURATION)
        overlap_samples = int(self.RATE * self.OVERLAP_DURATION)
        
        while self.is_recording:
            try:
                audio_data = self.audio_queue.get(timeout=0.1)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # オーディオレベルを計算し、プログレスバーを更新 / Calculate audio level and update progress bar
                audio_level = np.abs(audio_array).mean() / 32768.0
                self.root.after(0, self.update_audio_level, audio_level)
                
                # バッファに追加 / Add to buffer
                self.audio_buffer.extend(audio_array)
                
                # チャンクサイズに到達したか確認 / Check if buffer has reached chunk size
                if len(self.audio_buffer) >= chunk_samples:
                    chunk = self.audio_buffer[:chunk_samples]
                    
                    # overlap_bufferがあれば結合 / If overlap_buffer exists, concatenate
                    if self.overlap_buffer:
                        full_chunk = np.concatenate([self.overlap_buffer, chunk])
                    else:
                        full_chunk = chunk
                    
                    # 次回用に最後のoverlap部分を保存 / Save last overlap portion for next iteration
                    self.overlap_buffer = chunk[-overlap_samples:]
                    
                    # 処理済みデータをバッファから削除 / Remove processed data from buffer
                    self.audio_buffer = self.audio_buffer[chunk_samples:]
                    
                    # チャンクを転写キューに追加 / Enqueue the full_chunk for transcription
                    self.transcription_queue.put(full_chunk)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"音声処理エラー / Audio processing error: {e}")
                
    def transcribe_audio(self):
        """音声を文字起こし（gpt-4o-transcribeを使用） / Transcribe audio using gpt-4o-transcribe"""
        first_request = True  # 最初のリクエストかどうかを判定 / Flag to mark first API request
        while self.is_recording:
            try:
                audio_chunk = self.transcription_queue.get(timeout=0.1)
                
                # WAV形式に変換 / Convert to WAV format
                wav_data = self.numpy_to_wav(audio_chunk)
                
                # コンテキストプロンプトを構築 / Build context prompt
                if first_request and self.meeting_topic:
                    if self.current_lang == 'ja':
                        prompt = f"以下の音声は「{self.meeting_topic}」というキーワードに関連しています。このキーワードを念頭に置いて、正確に文字起こししてください。"
                    elif self.current_lang == 'en':
                        prompt = f"The following audio is related to the keyword '{self.meeting_topic}'. Please transcribe accurately while keeping this keyword in mind."
                    elif self.current_lang == 'zh':
                        prompt = f"以下音频与关键词{self.meeting_topic}相关。请在记住此关键词的同时准确转录。"
                    elif self.current_lang == 'ko':
                        prompt = f"다음 오디오는 '{self.meeting_topic}' 키워드와 관련이 있습니다. 이 키워드를 염두에 두고 정확하게 전사해 주세요."
                    first_request = False
                else:
                    prompt = self.build_context_prompt()
                
                # API呼び出し / Call API for transcription
                start_time = time.time()
                transcription = self.call_transcription_api(wav_data, prompt)
                latency = int((time.time() - start_time) * 1000)
                
                if transcription:
                    # コンテキスト履歴を更新 / Update context history
                    self.context_history.append(transcription)
                    
                    # GUIに字幕を表示 / Display subtitle in GUI
                    self.root.after(0, self.display_subtitle, transcription)
                    
                    # デバッグ情報を更新 / Update debug info
                    debug_text = f"{self.get_text('response_time')}: {latency}ms | {self.get_text('prompt_length')}: {len(prompt)} | {self.get_text('buffer_length')}: {len(self.audio_buffer)/self.RATE:.1f}s"
                    self.root.after(0, self.debug_info.set, debug_text)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"文字起こしエラー / Transcription error: {e}")
                
    def numpy_to_wav(self, audio_array):
        """NumPy配列をWAVに変換し、BytesIOバッファを返す / Convert NumPy array to WAV and return BytesIO buffer"""
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wav_file.setframerate(self.RATE)
            wav_file.writeframes(audio_array.astype(np.int16).tobytes())
        buffer.seek(0)
        return buffer
        
    def build_context_prompt(self):
        """コンテキストプロンプトを構築: 直近の文字起こし結果を結合 / Build context prompt by joining recent transcriptions"""
        if not self.context_history:
            return ""
        context_text = " ".join(self.context_history)
        
        if self.current_lang == 'ja':
            return f"これは音声の続きです。前の文脈：{context_text}"
        elif self.current_lang == 'en':
            return f"This is a continuation of audio. Previous context: {context_text}"
        elif self.current_lang == 'zh':
            return f"这是音频的延续。之前的上下文：{context_text}"
        elif self.current_lang == 'ko':
            return f"이것은 오디오의 연속입니다. 이전 컨텍스트: {context_text}"
        
    def call_transcription_api(self, wav_data, prompt):
        """文字起こしAPIを呼び出し（gpt-4o-transcribeを使用） / Call transcription API (using gpt-4o-transcribe)"""
        try:
            # 選択された言語コードを取得 / Get selected language code
            selected_language = self.get_selected_language()
            
            files = {
                'file': ('audio.wav', wav_data, 'audio/wav')
            }
            data = {
                'model': 'gpt-4o-transcribe',
                'response_format': 'json'
            }
            
            # 自動検出モードでない場合のみ言語を指定 / Specify language only if not auto-detect
            if selected_language != 'auto':
                data['language'] = selected_language
                
            if prompt:
                data['prompt'] = prompt
            
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '').strip()
            else:
                print(f"APIエラー / API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"API呼び出しに失敗しました / Failed to call API: {e}")
            return None
            
    def get_selected_language(self):
        """現在選択されている言語コードを取得 / Get currently selected language code"""
        try:
            selection = self.language_combo.get()
            # 選択から言語コードを抽出（例 "ja - 日本語 (Japanese)" -> "ja"） / Extract language code from selection (e.g., "ja - 日本語 (Japanese)" -> "ja")
            language_code = selection.split(' - ')[0]
            return language_code
        except:
            return 'ja'  # デフォルトで日本語を返す / Default to Japanese
            
    def update_audio_level(self, level):
        """オーディオレベル表示を更新 / Update audio level display"""
        self.level_bar['value'] = min(level * 500, 100)
        
    def display_subtitle(self, text):
        """GUIに字幕を表示 / Display subtitle in GUI"""
        if text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            # メインウィンドウにタイムスタンプ付き字幕を表示 / Show timestamped subtitle in main window
            self.subtitle_text.insert(tk.END, f"[{timestamp}] {text}\n")
            self.subtitle_text.see(tk.END)
            
            # 浮動ウィンドウにタイムスタンプなしの字幕を表示 / Show subtitle without timestamp in floating window
            self.floating_subtitle.update_subtitle(text)
            
    def update_gui(self):
        """GUIを定期更新（プログレスバーアニメーション維持） / Periodically update GUI (keep progress bar animated)"""
        if self.is_recording:
            self.root.after(100, self.update_gui)
            
    def run(self):
        """メインループ実行 / Run main loop"""
        self.root.mainloop()
        
        # 終了時にリソースをクリーンアップ / Clean up resources on exit
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


class RealtimeTranscriberServer:
    """サーバー側実装（オプション） / Server-side implementation (optional) - WebSocket for better real-time"""
    def __init__(self, api_key, websocket_port=8765):
        self.api_key = api_key
        self.websocket_port = websocket_port
        # WebSocketサーバーのロジックをここに拡張可能 / You can extend WebSocket server logic here
        pass


if __name__ == "__main__":
    # API_Key.txtからAPIキーを読み込む / Read API key from API_Key.txt
    api_key_path = "API_Key.txt"
    if not os.path.exists(api_key_path):
        print("API_Key.txt ファイルが見つかりません。同じディレクトリにファイルが存在し、正しい API Key が含まれていることを確認してください。 / API_Key.txt file not found. Ensure it exists in the same directory with a valid API Key.")
        exit(1)
    try:
        with open(api_key_path, "r", encoding="utf-8") as f:
            API_KEY = f.read().strip()
    except Exception as e:
        print(f"API_Key.txt の読み込みに失敗しました: {e} / Failed to read API_Key.txt: {e}")
        exit(1)

    if not API_KEY:
        print("読み込まれた API Key が空です。API_Key.txt の内容を確認してください。 / Loaded API Key is empty. Check the contents of API_Key.txt.")
        exit(1)

    # 転写器を作成して実行 / Create and run transcriber
    transcriber = RealtimeJapaneseTranscriber(API_KEY)
    try:
        transcriber.run()
    except KeyboardInterrupt:
        print("\nプログラムが終了しました / Program terminated")
    except Exception as e:
        print(f"プログラムエラー / Program error: {e}")