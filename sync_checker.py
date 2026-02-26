import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from PyQt6.QtCore import QCoreApplication
from company_manager import CompanyManager

def test_shared_signals():
    app = QCoreApplication(sys.argv)
    
    # 1. Create one manager (like MainWindow does)
    manager = CompanyManager()
    
    # 2. Add multiple listeners (like MainWindow and other components)
    update_count = 0
    
    def on_change():
        nonlocal update_count
        update_count += 1
        print(f"Listener notified! Total updates: {update_count}")

    manager.company_changed.connect(on_change)
    
    # 3. Modify something using THAT instance
    print("Emitting signal from manager...")
    manager.company_changed.emit()
    
    # 4. Check if notified
    if update_count == 1:
        print("SUCCESS: Signal correctly propagated.")
    else:
        print(f"FAILURE: Expected 1 update, got {update_count}.")

    # 5. Check if using a shared instance in another class works
    class OtherComponent:
        def __init__(self, shared_manager):
            self.manager = shared_manager
            self.manager.company_changed.connect(self.on_data_changed)
            self.notified = False
            
        def on_data_changed(self):
            self.notified = True
            print("OtherComponent notified!")

    other = OtherComponent(manager)
    manager.company_changed.emit()
    
    if other.notified and update_count == 2:
        print("SUCCESS: Shared instance works across different objects.")
    else:
        print("FAILURE: Shared instance sync failed.")

if __name__ == "__main__":
    test_shared_signals()