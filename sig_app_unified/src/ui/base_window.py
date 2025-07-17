
"""
Ventana base para todas las interfaces de la aplicación SIG.
Proporciona funcionalidad común y estilo consistente.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from src.core.config import UI_COLORS, UI_FONTS, logger

class BaseWindow:
    """Clase base para todas las ventanas de la aplicación."""
    
    def __init__(self, title: str, width: int = 800, height: int = 600, 
                 resizable: bool = True, parent: Optional[tk.Tk] = None):
        """
        Inicializa la ventana base.
        
        Args:
            title: Título de la ventana
            width: Ancho inicial
            height: Alto inicial
            resizable: Si la ventana es redimensionable
            parent: Ventana padre (opcional)
        """
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title(title)
        self.root.configure(bg=UI_COLORS["bg_primary"])
        self.root.resizable(resizable, resizable)
        
        # Configurar tamaño y posición
        self._center_window(width, height)
        
        # Variables de estado
        self.is_processing = False
        self.status_var = tk.StringVar()
        
        # Configurar estilo
        self._setup_styles()
        
        # Crear frame principal
        self.main_frame = tk.Frame(self.root, bg=UI_COLORS["bg_primary"])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Callback para cerrar ventana
        self.on_close_callback: Optional[Callable] = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self, width: int, height: int):
        """Centra la ventana en la pantalla."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_styles(self):
        """Configura estilos personalizados."""
        self.style = ttk.Style()
        
        # Configurar tema
        self.style.theme_use('clam')
        
        # Estilo para botones principales
        self.style.configure(
            "Primary.TButton",
            background=UI_COLORS["accent_primary"],
            foreground="white",
            font=UI_FONTS["button"],
            padding=(15, 8)
        )
        
        self.style.map(
            "Primary.TButton",
            background=[('active', UI_COLORS["accent_hover"]),
                       ('pressed', UI_COLORS["accent_dark"])]
        )
        
        # Estilo para botones secundarios
        self.style.configure(
            "Secondary.TButton",
            background=UI_COLORS["text_secondary"],
            foreground="white",
            font=UI_FONTS["body"],
            padding=(10, 6)
        )
    
    def create_title(self, text: str, row: int = 0) -> tk.Label:
        """
        Crea un título principal.
        
        Args:
            text: Texto del título
            row: Fila donde colocar el título
            
        Returns:
            Widget Label creado
        """
        title_label = tk.Label(
            self.main_frame,
            text=text,
            font=UI_FONTS["title"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_primary"]
        )
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        return title_label
    
    def create_file_selector(self, label_text: str, row: int, 
                           file_types: list, command: Callable,
                           variable: tk.StringVar) -> tuple:
        """
        Crea un selector de archivos con etiqueta, entrada y botón.
        
        Args:
            label_text: Texto de la etiqueta
            row: Fila donde colocar el selector
            file_types: Tipos de archivo para el diálogo
            command: Comando para el botón examinar
            variable: Variable para el campo de entrada
            
        Returns:
            Tupla (label, entry, button)
        """
        # Etiqueta
        label = tk.Label(
            self.main_frame,
            text=label_text,
            font=UI_FONTS["body"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_primary"]
        )
        label.grid(row=row, column=0, sticky="w", pady=5)
        
        # Campo de entrada
        entry = tk.Entry(
            self.main_frame,
            textvariable=variable,
            font=UI_FONTS["body"],
            width=50,
            bg="white",
            fg=UI_COLORS["text_primary"],
            relief="solid",
            bd=1
        )
        entry.grid(row=row, column=1, padx=(10, 5), pady=5, sticky="ew")
        
        # Botón examinar
        button = tk.Button(
            self.main_frame,
            text="Examinar",
            command=command,
            bg=UI_COLORS["accent_primary"],
            fg="white",
            font=UI_FONTS["body"],
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        button.grid(row=row, column=2, padx=5, pady=5)
        
        # Efectos hover
        self._add_hover_effects(button)
        
        return label, entry, button
    
    def create_action_button(self, text: str, command: Callable, 
                           row: int, column: int = 1, 
                           style: str = "primary") -> tk.Button:
        """
        Crea un botón de acción.
        
        Args:
            text: Texto del botón
            command: Comando a ejecutar
            row: Fila donde colocar el botón
            column: Columna donde colocar el botón
            style: Estilo del botón ('primary' o 'secondary')
            
        Returns:
            Widget Button creado
        """
        if style == "primary":
            bg_color = UI_COLORS["accent_primary"]
            hover_color = UI_COLORS["accent_hover"]
            font = UI_FONTS["button"]
        else:
            bg_color = UI_COLORS["text_secondary"]
            hover_color = UI_COLORS["text_primary"]
            font = UI_FONTS["body"]
        
        button = tk.Button(
            self.main_frame,
            text=text,
            command=command,
            bg=bg_color,
            fg="white",
            font=font,
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        button.grid(row=row, column=column, pady=15, padx=5)
        
        # Efectos hover
        self._add_hover_effects(button, hover_color)
        
        return button
    
    def create_status_label(self, row: int) -> tk.Label:
        """
        Crea una etiqueta de estado.
        
        Args:
            row: Fila donde colocar la etiqueta
            
        Returns:
            Widget Label creado
        """
        status_label = tk.Label(
            self.main_frame,
            textvariable=self.status_var,
            font=UI_FONTS["body"],
            bg=UI_COLORS["bg_primary"],
            fg=UI_COLORS["text_secondary"],
            wraplength=600
        )
        status_label.grid(row=row, column=0, columnspan=3, pady=10)
        return status_label
    
    def _add_hover_effects(self, button: tk.Button, hover_color: str = None):
        """Agrega efectos hover a un botón."""
        if hover_color is None:
            hover_color = UI_COLORS["accent_hover"]
        
        original_color = button.cget("background")
        
        def on_enter(e):
            button.configure(background=hover_color)
        
        def on_leave(e):
            button.configure(background=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def show_success(self, message: str):
        """Muestra mensaje de éxito."""
        self.status_var.set(message)
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["success"]))
        messagebox.showinfo("Éxito", message)
    
    def show_error(self, message: str):
        """Muestra mensaje de error."""
        self.status_var.set(f"Error: {message}")
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["error"]))
        messagebox.showerror("Error", message)
    
    def show_warning(self, message: str):
        """Muestra mensaje de advertencia."""
        self.status_var.set(f"Advertencia: {message}")
        self.root.after(100, lambda: self._update_status_color(UI_COLORS["warning"]))
        messagebox.showwarning("Advertencia", message)
    
    def set_processing(self, is_processing: bool, message: str = ""):
        """
        Establece el estado de procesamiento.
        
        Args:
            is_processing: Si está procesando
            message: Mensaje a mostrar
        """
        self.is_processing = is_processing
        
        if is_processing:
            self.status_var.set(f"Procesando... {message}")
            self._update_status_color(UI_COLORS["accent_primary"])
            self.root.configure(cursor="wait")
        else:
            self.root.configure(cursor="")
            if not message:
                self.status_var.set("")
    
    def _update_status_color(self, color: str):
        """Actualiza el color de la etiqueta de estado."""
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(self.status_var):
                widget.configure(fg=color)
                break
    
    def set_close_callback(self, callback: Callable):
        """Establece callback para cerrar ventana."""
        self.on_close_callback = callback
    
    def _on_close(self):
        """Maneja el cierre de la ventana."""
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.root.destroy()
    
    def show(self):
        """Muestra la ventana."""
        self.root.mainloop()
    
    def close(self):
        """Cierra la ventana."""
        self.root.destroy()
    
    def configure_grid_weights(self):
        """Configura pesos de las columnas del grid."""
        self.main_frame.grid_columnconfigure(1, weight=1)
