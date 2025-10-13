import serial
import threading

class SerialComm:
    def __init__(self, port='COM5', baudrate=115200, on_message=None):
        """
        Serial communication handler.
        :param port: COM port (e.g. 'COM5')
        :param baudrate: Baud rate (default 115200)
        :param on_message: callback function(msg) for received messages
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.thread = None
        self.on_message = on_message
        self.buffer = b""  # For building messages ending with '\n'

    def connect(self):
        """Open serial port and start background reading."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.01)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.close()

    def _read_loop(self):
        """Continuously read bytes and handle messages."""
        while self.running and self.ser and self.ser.is_open:
            try:
                data = self.ser.read(1)  # read one byte at a time
                if data:
                    # If it's a newline, treat the buffer as a complete message
                    if data in [b'\n', b'\r']:
                        if self.buffer:
                            try:
                                message = self.buffer.decode('utf-8').strip()
                                if self.on_message and message:
                                    self.on_message(message)
                            except UnicodeDecodeError:
                                print("Received non-UTF-8 data")
                            self.buffer = b""  # reset buffer
                    else:
                        # Append to buffer in case it's part of a longer message
                        self.buffer += data
            except serial.SerialException:
                break

    def send(self, message: str):
        """Send a message to STM32."""
        if self.ser and self.ser.is_open:
            self.ser.write(message.encode('utf-8') + b'\n')
            print(f"Sent: {message}")
        else:
            print("Serial port not open")

    def close(self):
        """Stop reading and close serial port."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial port closed.")
        if self.thread and self.thread.is_alive():
            self.thread.join()
