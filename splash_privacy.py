import tkinter as tk
from tkinter import messagebox
import time

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, tax_accountant_name="", tax_office_name="", tax_accountant_phone="", tax_accountant_email="", tax_branch_name=""):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)  # Remove window decorations
        self.grab_set()  # Make it modal during its display
        
        # Center the splash screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 400
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.configure(bg="white")

        # Tax Accountant Info
        display_office_name = tax_office_name if tax_office_name else "세무회계사무소"
        if tax_branch_name:
            tk.Label(self, text=f"{display_office_name} ({tax_branch_name})", font=("맑은 고딕", 18, "bold"), bg="white").pack(pady=(50, 5))
        else:
            tk.Label(self, text=display_office_name, font=("맑은 고딕", 18, "bold"), bg="white").pack(pady=(50, 5))
        tk.Label(self, text=f"세무사/사무장 {tax_accountant_name}", font=("맑은 고딕", 14), bg="white").pack(pady=2)
        tk.Label(self, text=f"연락처: {tax_accountant_phone}", font=("맑은 고딕", 12), bg="white").pack(pady=2)
        tk.Label(self, text=f"Email: {tax_accountant_email}", font=("맑은 고딕", 12), bg="white").pack(pady=2)
        
        # Warning
        warning_text = f"""
        본 소프트웨어는 '{display_office_name}'의 독점적 자산입니다.
        저작권법 및 관련 법령에 의거하여 무단 복제, 배포, 수정, 
        역설계 및 상업적 이용을 엄격히 금합니다.
        개발 또는 기능 개선에 대한 문의는 세무사 {tax_accountant_name}에게 직접 문의하여 주시기 바랍니다.
        위반 시 법적 책임이 따를 수 있습니다.
        """
        tk.Label(self, text=warning_text, font=("맑은 고딕", 10, "bold"), fg="red", bg="white", wraplength=window_width-40, justify=tk.CENTER).pack(pady=(30, 10))
        
        tk.Label(self, text="로딩 중...", font=("맑은 고딕", 10), bg="white").pack(pady=10)
        
import tkinter as tk
from tkinter import messagebox, ttk # Import ttk
import time

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, tax_accountant_name="", tax_office_name="", tax_accountant_phone="", tax_accountant_email="", tax_branch_name=""):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)  # Remove window decorations
        self.grab_set()  # Make it modal during its display
        
        # Center the splash screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 450 # Increased height for better aesthetics
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.configure(bg="#F0F0F0") # Lighter background color

        # --- Company/Office Info ---
        display_office_name = tax_office_name if tax_office_name else "세무회계사무소"
        
        if tax_branch_name:
            ttk.Label(self, text=f"{display_office_name} ({tax_branch_name})", font=("맑은 고딕", 22, "bold"), background="#F0F0F0").pack(pady=(40, 5))
        else:
            ttk.Label(self, text=display_office_name, font=("맑은 고딕", 22, "bold"), background="#F0F0F0").pack(pady=(40, 5))
        
        ttk.Label(self, text=f"세무사 {tax_accountant_name}", font=("맑은 고딕", 16, "bold"), background="#F0F0F0").pack(pady=5)
        ttk.Label(self, text=f"연락처: {tax_accountant_phone}", font=("맑은 고딕", 12), background="#F0F0F0").pack(pady=2)
        ttk.Label(self, text=f"Email: {tax_accountant_email}", font=("맑은 고딕", 12), background="#F0F0F0").pack(pady=2)
        
        # --- Warning ---
        warning_text = f"""
        본 소프트웨어는 '{display_office_name}'의 독점적 자산입니다.
        저작권법 및 관련 법령에 의거하여 무단 복제, 배포, 수정, 
        역설계 및 상업적 이용을 엄격히 금합니다.
        개발 또는 기능 개선에 대한 문의는 세무사 {tax_accountant_name}에게 직접 문의하여 주시기 바랍니다.
        위반 시 법적 책임이 따를 수 있습니다.
        """
        ttk.Label(self, text=warning_text, font=("맑은 고딕", 10, "bold"), foreground="red", background="#F0F0F0", wraplength=window_width-40, justify=tk.CENTER).pack(pady=(25, 10))
        
        # --- Loading Indicator ---
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start(10) # Start animating the progress bar
        
        ttk.Label(self, text="데이터 로딩 중...", font=("맑은 고딕", 11, "italic"), foreground="gray", background="#F0F0F0").pack(pady=5)
        
        # Schedule destruction after 10 seconds
        self.after(10000, self.destroy_splash)

    def destroy_splash(self):
        self.progress.stop() # Stop animating
        self.grab_release()
        self.destroy()
        self.parent.event_generate("<<SplashScreenClosed>>") # Notify parent

class PrivacyConsentDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("개인정보 처리 방침 동의")
        self.grab_set()  # Make it modal
        self.result = False # To store consent result

        # Center the dialog
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 500
        window_height = 350 # Increased height
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        ttk.Label(self, text="""
        본 프로그램은 개인정보보호법을 준수하여 
        사용자의 개인정보를 처리하며, 어떠한 개인정보도 
        외부로 전송하거나 공유하지 않습니다.
        """, font=("맑은 고딕", 10), wraplength=window_width-40).pack(pady=20)

        ttk.Label(self, text="""
        상기 내용에 동의하십니까?
        """, font=("맑은 고딕", 10, "bold")).pack(pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="동의", command=self.on_agree, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="취소", command=self.on_cancel, width=10).pack(side=tk.RIGHT, padx=10)

        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_agree(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        messagebox.showinfo("안내", "동의하지 않으시면 프로그램을 종료합니다.")
        self.destroy()
        self.parent.quit() # Exit the main application if not agreed

class PrivacyConsentDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("개인정보 처리 방침 동의")
        self.grab_set()  # Make it modal
        self.result = False # To store consent result

        # Center the dialog
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 500
        window_height = 300
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        tk.Label(self, text="""
        본 프로그램은 개인정보보호법을 준수하여 
        사용자의 개인정보를 처리하며, 어떠한 개인정보도 
        외부로 전송하거나 공유하지 않습니다.
        """, font=("맑은 고딕", 10), wraplength=window_width-40).pack(pady=20)

        tk.Label(self, text="""
        상기 내용에 동의하십니까?
        """, font=("맑은 고딕", 10, "bold")).pack(pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="동의", command=self.on_agree, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="취소", command=self.on_cancel, width=10).pack(side=tk.RIGHT, padx=10)

        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_agree(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        messagebox.showinfo("안내", "동의하지 않으시면 프로그램을 종료합니다.")
        self.destroy()
        self.parent.quit() # Exit the main application if not agreed
