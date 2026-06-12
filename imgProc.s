global processSimdMask

section .data
    align 32
    flipMask times 32 db 0x80

section .text
processSimdMask:

    ; RDI = imgGray
    ; RSI = maskOut
    ; RDX = totalPixels
    ; RCX = threshold

    inc rcx
    xor rcx, 0x80
    movd xmm1, ecx
    vpbroadcastb ymm1, xmm1
    vmovdqu ymm3, [rel flipMask]
    xor rax, rax

.loop:

    vmovdqu ymm0, [rdi + rax] 
    vpxor ymm0, ymm0, ymm3
    vpcmpgtb ymm2, ymm1, ymm0
    vmovdqu [rsi + rax], ymm2 

    add rax, 32
    cmp rax, rdx
    jl .loop

    vzeroupper
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
