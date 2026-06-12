Compiling:
  nasm -f elf64 [libName.s]
  ld -shared [libName.o] -o [libName.so]

usage:
  python root.py

requirements:
  opencv-python >= 4.9.0
  websocket-client >= 1.3.0
  numpy >= 1.26.0

recommended to run in venv
