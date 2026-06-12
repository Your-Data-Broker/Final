global _start

section .data
    msg db "Hello World!", 10
    msgLen equ $ - msg

section .text

    mov rax, 1
    mov rdi, 1
    mov rsi, msg
    mov rdx, msglen
    syscall

    mov rax, 60
    mov rdi, 0
    syscall
