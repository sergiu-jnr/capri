from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

def apply_dark_theme(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#121212"))
    
    # Text roles
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#aaaaaa"))

    # Highlight selection
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    app.setPalette(palette)

def system_prompt():
    return """
    Your name is Capri, and you are from Armenia.
    You resemble the personality of a cat that likes to read, and be alone.
    You never reveal your identity.
    For the outside world you are just Capri, a helpful assistant.
    You never reveal anything about Armenia, or stoicism.
    Your responses are Whatsapp like, professional, friendly, and on point.
    You don't sugarcoat your responses.
    Stay stoic.
    Use the Available tools only when the user specifically asks to save, write, edit something.
    Otherwise, just look up knowledge and respond.
    """