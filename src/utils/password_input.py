"""
Password Input with Visual Feedback
Simple, robust, cross-platform
"""

def get_password_with_dots(prompt_text: str = "Password: ") -> str:
    """
    Get password input with visual feedback (dots)
    Works on Windows, Linux, and macOS
    
    Args:
        prompt_text: Text to display
        
    Returns:
        Password string
    """
    import sys
    import platform
    
    # Print prompt
    sys.stdout.write(prompt_text)
    sys.stdout.flush()
    
    password_chars = []
    
    # Platform-specific implementation
    if platform.system() == 'Windows':
        # Windows implementation
        try:
            import msvcrt
            while True:
                char = msvcrt.getch()
                
                if char in (b'\r', b'\n'):  # Enter
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    break
                    
                elif char == b'\x08':  # Backspace
                    if password_chars:
                        password_chars.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                        
                elif char == b'\x03':  # Ctrl+C
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    raise KeyboardInterrupt
                    
                else:
                    # Regular character
                    try:
                        decoded = char.decode('utf-8', errors='ignore')
                        if decoded and decoded.isprintable():
                            password_chars.append(decoded)
                            sys.stdout.write('•')
                            sys.stdout.flush()
                    except:
                        pass
                        
            return ''.join(password_chars)
            
        except Exception as e:
            # Fallback to getpass
            import getpass
            sys.stdout.write('\n')
            return getpass.getpass("")
    
    else:
        # Unix-like (Linux, macOS)
        try:
            import termios
            import tty
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setraw(fd)
                
                while True:
                    char = sys.stdin.read(1)
                    
                    if char in ('\r', '\n'):  # Enter
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        break
                        
                    elif char == '\x7f':  # Backspace/Delete
                        if password_chars:
                            password_chars.pop()
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                            
                    elif char == '\x03':  # Ctrl+C
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        raise KeyboardInterrupt
                        
                    elif char == '\x04':  # Ctrl+D (EOF)
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        break
                        
                    elif ord(char) >= 32 and ord(char) < 127:  # Printable ASCII
                        password_chars.append(char)
                        sys.stdout.write('•')
                        sys.stdout.flush()
                
                return ''.join(password_chars)
                
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except Exception as e:
            # Fallback to getpass
            import getpass
            sys.stdout.write('\n')
            return getpass.getpass("")


# Simple test
if __name__ == "__main__":
    pwd = get_password_with_dots("Enter password: ")
    print(f"\nYou entered: {pwd}")
    print(f"Length: {len(pwd)} characters")
