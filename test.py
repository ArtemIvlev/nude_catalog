import ctypes

# Загрузка библиотеки cuDNN
libcudnn = ctypes.CDLL('libcudnn.so')

# Определение типа возвращаемого значения функции cudnnGetVersion
libcudnn.cudnnGetVersion.restype = ctypes.c_char_p

# Вызов функции и вывод версии
version = libcudnn.cudnnGetVersion()
print(f"Версия cuDNN: {version.decode('utf-8')}")
