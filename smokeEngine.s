global decideAndDrive

section .bss
    currentSpeed resq 1
    linearSpeed resq 1
    lastBackwardTimeMs resq 1
    accountedForLastBackwardTime resq 1
    lastCommand resq 1
    frameCounter resq 1

section .data
    cmdForward db 0x81, 0x87, 0xAA, 0xBB, 0xCC, 0xDD, 0xCC, 0xD4, 0xBE, 0xAA, 0xCB, 0xC9, 0xA8
    cmdForwardLen equ $ - cmdForward

    cmdBackward db 0x81, 0x88, 0xAA, 0xBB, 0xCC, 0xDD, 0xC8, 0xDA, 0xAF, 0xB6, 0xDD, 0xDA, 0xBE, 0xB9
    cmdBackwardLen equ $ - cmdBackward

    cmdLeft db 0x81, 0x84, 0xAA, 0xBB, 0xCC, 0xDD, 0xC6, 0xDE, 0xAA, 0xA9
    cmdLeftLen equ $ - cmdLeft

    cmdRight db 0x81, 0x85, 0xAA, 0xBB, 0xCC, 0xDD, 0xD8, 0xD2, 0xAB, 0xB5, 0xDE
    cmdRightLen equ $ - cmdRight

    cmdStop db 0x81, 0x84, 0xAA, 0xBB, 0xCC, 0xDD, 0xD9, 0xCF, 0xA3, 0xAD
    cmdStopLen equ $ - cmdStop

    dynSpeedFrame db 0x81, 0x89, 0xAA, 0xBB, 0xCC, 0xDD, 0xD9, 0xCB, 0xA9, 0xB8, 0xCE, 0x81, 0x00, 0x00, 0x00
    dynSpeedFrameLen equ 15

    initialLinearSpeed dq 255
    initialAccounted dq 1

section .text
decideAndDrive:
    push r12
    push r13
    push r14

    mov r12, rsi
    mov r13, rdx

    mov rax, qword [rel linearSpeed]
    cmp rax, 0
    jne skipInit
    mov rax, qword [rel initialLinearSpeed]
    mov qword [rel linearSpeed], rax
    mov rax, qword [rel initialAccounted]
    mov qword [rel accountedForLastBackwardTime], rax
skipInit:

    cmp rdi, -1
    je handleLostLine

    mov qword [rel frameCounter], 0

    mov rax, rdi
    sub rax, 160
    mov rbx, rax
    sar rbx, 63
    xor rax, rbx
    sub rax, rbx

    cmp rax, 80
    jg handleTurn

handleForward:
    mov rax, qword [rel accountedForLastBackwardTime]
    cmp rax, 0
    jne checkAcc
    mov rax, r13
    sub rax, qword [rel lastBackwardTimeMs]
    cmp rax, 1000
    jge setAccTrue
    mov rax, qword [rel linearSpeed]
    sub rax, 5
    mov qword [rel linearSpeed], rax
setAccTrue:
    mov qword [rel accountedForLastBackwardTime], 1

checkAcc:
    mov rax, qword [rel lastBackwardTimeMs]
    cmp rax, 0
    je applyFwdSpeed
    mov rax, r13
    sub rax, qword [rel lastBackwardTimeMs]
    cmp rax, 1000
    jle applyFwdSpeed
    mov rax, qword [rel linearSpeed]
    cmp rax, 255
    jge applyFwdSpeed
    add rax, 5
    mov qword [rel linearSpeed], rax

applyFwdSpeed:
    mov rax, qword [rel linearSpeed]
    cmp rax, qword [rel currentSpeed]
    je sendForward

    call setDynamicSpeed
    mov rax, qword [rel linearSpeed]
    mov qword [rel currentSpeed], rax

sendForward:
    lea rcx, [rel cmdForward]
    mov rdx, cmdForwardLen
    mov qword [rel lastCommand], 1
    call fireSyscall
    jmp exitFunction

handleTurn:
    mov rax, 140
    cmp rax, qword [rel currentSpeed]
    je sendTurnCommand
    call setDynamicSpeed
    mov qword [rel currentSpeed], 140

sendTurnCommand:
    cmp rdi, 160
    jg sendRight
    lea rcx, [rel cmdLeft]
    mov rdx, cmdLeftLen
    mov qword [rel lastCommand], 2
    call fireSyscall
    jmp exitFunction

sendRight:
    lea rcx, [rel cmdRight]
    mov rdx, cmdRightLen
    mov qword [rel lastCommand], 3
    call fireSyscall
    jmp exitFunction

handleLostLine:
    mov rax, qword [rel frameCounter]
    inc rax
    mov qword [rel frameCounter], rax

    cmp rax, 15
    jle exitFunction

    mov qword [rel frameCounter], 0

    mov rbx, qword [rel lastCommand]
    cmp rbx, 4
    je checkBackSpeed
    cmp rbx, 5
    je checkBackSpeed

    lea rcx, [rel cmdStop]
    mov rdx, cmdStopLen
    call fireSyscall

checkBackSpeed:
    mov rax, 100
    cmp rax, qword [rel currentSpeed]
    je sendBackward
    call setDynamicSpeed
    mov qword [rel currentSpeed], 100

sendBackward:
    lea rcx, [rel cmdBackward]
    mov rdx, cmdBackwardLen
    mov qword [rel lastCommand], 4
    call fireSyscall

    mov qword [rel lastBackwardTimeMs], r13
    mov qword [rel accountedForLastBackwardTime], 0

exitFunction:
    pop r14
    pop r13
    pop r12
    ret

setDynamicSpeed:
    push rax
    mov rcx, 10
    
    xor rdx, rdx
    div rcx
    add rdx, 48
    xor rdx, 0xAA
    mov byte [rel dynSpeedFrame + 14], dl

    xor rdx, rdx
    div rcx
    add rdx, 48
    xor rdx, 0xDD
    mov byte [rel dynSpeedFrame + 13], dl

    add rax, 48
    xor rax, 0xCC
    mov byte [rel dynSpeedFrame + 12], al

    lea rcx, [rel dynSpeedFrame]
    mov rdx, dynSpeedFrameLen
    call fireSyscall
    pop rax
    ret

fireSyscall:
    push rax
    push rdi
    push rsi
    mov rax, 1
    mov rdi, r12
    mov rsi, rcx
    syscall
    pop rsi
    pop rdi
    pop rax
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
