# ASC-proiect-0x01
# **Echipa 5 din 7**


<p >

Am uitat să adăugăm în cod fail check-ul.
Liniile 381-384 din <b> asc-0x01_fixed.py </b> ar trebui înlocuite cu :

    elif opcode == "1110011":  # ECALL
        global interrupt
        interrupt = 1
        if registries[10] == 1:
            print("pass")
        else:
            print(f"failed test: {int((registries[10]-1)/2)}")
</p>
