import tkinter as tk
from tkinter import ttk
from localizer import _
from ui.tab_base import BaseTab


class AboutTab(BaseTab):
    """
    “关于”选项卡 UI。
    """
    def __init__(self, master):
        super().__init__(master, padding='10 10 10 10')

        self.label_about = ttk.Label(self, text='About tab')
        self.label_about.pack(pady=20, padx=20)