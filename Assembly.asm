.CODE

; void IntAddLoop(UINT64 iterations)
IntAddLoop PROC
push rbx
xor rax, rax
xor rbx, rbx
xor rdx, rdx
xor r8, r8
align 16
@@loop:
add rax, rbx
add rbx, rdx
add rdx, r8
add r8, rax
add rax, rbx
add rbx, rdx
add rdx, r8
add r8, rax
sub rcx, 1
jnz @@loop
pop rbx
ret
IntAddLoop ENDP

FloatAddLoop PROC
mov rax, 3F800000h ; 1.0f as raw bits
movd xmm0, eax
movd xmm1, eax
movd xmm2, eax
movd xmm3, eax
align 16
@@loop:
addss xmm0, xmm1 ; scalar float adds
addss xmm1, xmm2
addss xmm2, xmm3
addss xmm3, xmm0
addss xmm0, xmm1
addss xmm1, xmm2
addss xmm2, xmm3
addss xmm3, xmm0
sub rcx, 1
jnz @@loop
ret
FloatAddLoop ENDP

END 
