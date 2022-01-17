def signed_from_bin(sir_binar, bits):
    y = 0
    if sir_binar[0] == '1':
        y = -1 * pow(2, bits - 1)
    for n, bit in enumerate(sir_binar[1:]):
        if bit == '1':
            y += pow(2, bits - n - 2)
    return y


def instruction_fetch(PC):
    instructiune_32 = [bin(int(x))[2:].zfill(8) for x in cod_b[PC:PC + 4]]  # 4 bytes -> 32 bits
    instructiune_32 = "".join(instructiune_32)
    return instructiune_32


def get_input(file_name):
    f_in = open(file_name, 'r')
    lines = f_in.readlines()
    cod = []
    data = []
    data_offset = -1
    start_address = 0x80000000      # default start address
    index = 0
    sectiune = 1  # .text
    for i, line in enumerate(lines[1:]):
        if sectiune:  # .text
            if line[-2] != ":":  # linie de cod, sectiunea text
                index += 4
                l = [x.strip(" \n\t") for x in line.split(':')]
                cod.append((int(l[1], 16) & 0xFF000000) >> 24)
                cod.append((int(l[1], 16) & 0x00FF0000) >> 16)
                cod.append((int(l[1], 16) & 0x0000FF00) >> 8)
                cod.append(int(l[1], 16) & 0x000000FF)
            else:
                if "userstart" in line:
                    start_address = line.split()[0].strip(" \n\t")
                    pc_offset = index
                if line[-6:] == "data:\n":
                    sectiune = 0  # .data
        else:  # .data
            if line[-2] != ":":
                l = [x.strip(" \n\t") for x in line.split(':')]
                if len(l[1]) == 4:  # 2 bytes
                    data.append((int(l[1], 16) & 0x0000FF00) >> 8)
                    data.append(int(l[1], 16) & 0x000000FF)
                elif len(l[1]) == 8:  # 4 bytes
                    data.append((int(l[1], 16) & 0xFF000000) >> 24)
                    data.append((int(l[1], 16) & 0x00FF0000) >> 16)
                    data.append((int(l[1], 16) & 0x0000FF00) >> 8)
                    data.append(int(l[1], 16) & 0x000000FF)
                else:  # 1 byte
                    data.append(int(l[1], 16))
                if data_offset == -1:
                    data_offset = int(l[0], 16)
    if data_offset != -1:
        data_offset = data_offset - int(start_address, 16) + pc_offset  # ramane -1 daca nu exista .data
    cod_b = bytearray(cod)
    data_b = bytearray(data)
    return cod_b, data_b, data_offset


def instruction_execute(parametri):
    opcode, imm, rd, rs1, rs2, funct3, funct7 = parametri
    if opcode == "0110011":  # R type
        if funct3 == "000":  # add sau sub
            if funct7 == "0000000":
                # add rd,rs1, rs2 ; rd <- rs1 + rs2
                registries[rd] = registries[rs1] + registries[rs2]
                if registries[rd] > 2147483647:
                    registries[rd] -= 2147483648
            elif funct7 == "0100000":
                # sub rd,rs1, rs2 ; rd <- rs1 - rs2
                registries[rd] = registries[rs1] - registries[rs2]
                if registries[rd] < -2147483648:
                    registries[rd] = 4294967296 + registries[rd]
            elif funct7 == "0000001":
                # mul
                registries[rd] = registries[rs1] * registries[rs2]
                if registries[rd] > 0:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[(len(binary_repr) - 32):]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)
                elif registries[rd] < -2147483648:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[(len(binary_repr) - 32):]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)

        elif funct3 == "001":
            if funct7 == "0000000":
                # todo
                # sll = logical shift left
                shift_left_by = registries[rs2][-5:]
                registries[rd] = registries[rs1] << shift_left_by
            elif funct7 == "0000001":
                # mulh- THE UPPER 32 BITS OF SIGNED*SIGNED
                registries[rd] = registries[rs1] * registries[rs2]
                if registries[rd] > 0:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)
                elif registries[rd] < -2147483648:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)

        elif funct3 == "010":
            if funct7 == "0000000":
                # slt
                if registries[rs1] < registries[rs2]:
                    registries[rd] = 1
                else:
                    registries[rd] = 0
            elif funct7 == "0000001":
                # mulhsu - upper 32 bits - signed * unsigned - res2 e unsigned
                if registries[rs2] < 0:
                    registries[rd] = registries[rs1] * (4294967296 + registries[rs2])
                if registries[rd] > 0:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)
                elif registries[rd] < -2147483648:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)

        elif funct3 == "011":
            if funct7 == "0000000":
                # sltu
                if registries[rs1] < 0:
                    # tb sa fac in complement fata de 2
                    unsigned_r1 = 4294967296 + registries[rs1]
                if registries[rs2] < 0:
                    # tb sa fac in complement fata de 2
                    unsigned_r2 = 4294967296 + registries[rs2]

                if unsigned_r1 < unsigned_r2 and registries[rs2] != 0:
                    registries[rd] = 1
                else:
                    registries[rd] = 0
            elif funct7 == "0000001":
                # mulhu - 32 upper bits - unsigned* unsigned
                if registries[rs1] < 0:
                    unsigned_rs1 = 4294967296 + registries[rs1]
                if registries[rs2] < 0:
                    unsigned_rs2 = 4294967296 + registries[rs2]
                else:
                    unsigned_rs1 = registries[rs1]
                    unsigned_rs2 = registries[rs2]
                registries[rd] = unsigned_rs1 * unsigned_rs2

                if registries[rd] > 0:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)
                elif registries[rd] < -2147483648:
                    binary_repr = bin(registries[rd])[2:]
                    binary_repr = binary_repr[:32]
                    if binary_repr[0] == "1":
                        registries[rd] = -(pow(2, 31) - int(binary_repr[1:], 2))
                    else:
                        registries[rd] = int(binary_repr, 2)

        elif funct3 == "101":
            if funct7 == "0000000":
                # srl
                shift_right_by = registries[rs2] & 0x0000001F
                if shift_right_by > 0:
                    if registries[rs1] < 0:
                        registries[rd] = (registries[rs1] + 0x100000000) >> shift_right_by
                    else:
                        registries[rd] = registries[rs1] >> shift_right_by
                else:
                    registries[rd] = registries[rs1]

            elif funct7 == "0100000":
                # sra
                shift_right_by = registries[rs2][-5:]
                registries[rd] = registries[rs1] >> shift_right_by
            elif funct7 == "0000001":
                # divu
                if registries[rs2] == 0:
                    registries[rd] = 4294967296 - 1
                elif registries[rs1] == -2147483648 and registries[rs2] == -1:
                    # todo
                    raise OverflowError("Division cannot occur")
                else:
                    if registries[rs1] * registries[rs2] < 0:
                        if registries[rs1] < 0:
                            registries[rd] = (2147483648 + registries[rs1]) // registries[rs2]
                        elif registries[rs1] < 0:
                            registries[rd] = registries[rs1] // (2147483648 + registries[rs2])
                    else:
                        registries[rd] = registries[rs1] // registries[rs2]

        elif funct3 == "100":
            if funct7 == "0000000":
                # xor
                registries[rd] = registries[rs1] ^ registries[rs2]
            elif funct7 == "0000001":
                # div
                if registries[rs2] == 0:
                    registries[rd] = -1
                elif registries[rs1] == -2147483648 and registries[rs2] == -1:
                    registries[rd] = -2147483648
                else:
                    registries[rd] = registries[rs1] // registries[rs2]

        elif funct3 == "110":
            if funct7 == "0000000":
                # or
                registries[rd] = registries[rs1] | registries[rs2]
            elif funct7 == "0000001":
                # rem
                if registries[rs2] == 0:
                    registries[rd] = registries[rs1]
                elif registries[rs1] == -2147483648 and (registries[rs2] == -1 or registries[rs2] == 1):
                    registries[rd] = 0
                else:
                    registries[rd] = registries[rs1] % registries[rs2]
                    if registries[rs1] < 0 and registries[rs2] > 0:
                        registries[rd] -= registries[rs2]
                    if registries[rs1] >= 0 and registries[rs2] < 0:
                        registries[rd] += registries[rs2]*-1


        elif funct3 == "111":
            if funct7 == "0000000":
                registries[rd] = registries[rs1] & registries[rs2]
            elif funct7 == "0000001":
                # remu
                if registries[rs2] == 0:
                    registries[rd] = registries[rs1]
                elif registries[rs1] == -2147483648 and registries[rs2] == -1:
                    raise OverflowError("Division cannot occur")
                else:
                    if registries[rs1] * registries[rs2] < 0:
                        if registries[rs1] < 0:
                            registries[rd] = (2147483648 + registries[rs1]) % registries[rs2]
                        elif registries[rs1] < 0:
                            registries[rd] = registries[rs1] % (2147483648 + registries[rs2])
                    else:
                        registries[rd] = registries[rs1] % registries[rs2]

    elif opcode == "0010011":  # I type
        if funct3 == "000":  # ADDI
            registries[rd] = registries[rs1] + signed_from_bin(imm, 12)  # adauga overflow check
            if registries[rd] > 0x7FFFFFFF:
                registries[rd] -= 0x100000000
            if registries[rd] < -0x80000000:
                registries[rd] += 0x100000000
        if funct3 == "001":  # SLLI
            shamt = int(imm[7:12], 2)
            registries[rd] = registries[rs1] << shamt
        if funct3 == "010":  # SLTI
            registries[rd] = registries[rs1] < signed_from_bin(imm, 12)
        if funct3 == "011":  # SLTIU
            if imm[0] == '1':
                imm = int(imm, 2) + 0xFFFFF000  # sign extend
            registries[rd] = registries[rs1] < int(imm, 2)
        if funct3 == "100":  # XORI
            registries[rd] = registries[rs1] ^ signed_from_bin(imm, 12)
        if funct3 == "101":
            shamt = int(imm[7:12], 2)
            if imm[1] == '0':  # SRLI
                if registries[rs1] < 0:
                    registries[rd] = (registries[rs1] + 0x100000000) >> shamt
                else:
                    registries[rd] = registries[rs1] >> shamt
            else:  # SRAI
                registries[rd] = registries[rs1] >> shamt
        if funct3 == "110":  # ORI
            registries[rd] = registries[rs1] | signed_from_bin(imm, 12)
        if funct3 == "111":  # ANDI
            registries[rd] = registries[rs1] & signed_from_bin(imm, 12)
    elif opcode == "0100011":  # S type
        address = registries[rs1] + signed_from_bin(imm, 12) - data_offset
        if funct3 == "000":  # SB
            data_b[address] = registries[rs2] & 0x000000FF
        if funct3 == "001":  # SH
            data_b[address] = (registries[rs2] & 0x0000FF00) >> 8
            data_b[address + 1] = registries[rs2] & 0x000000FF
        if funct3 == "010":  # SW
            data_b[address] = (registries[rs2] & 0xFF000000) >> 24
            data_b[address + 1] = (registries[rs2] & 0x00FF0000) >> 16
            data_b[address + 2] = (registries[rs2] & 0x0000FF00) >> 8
            data_b[address + 3] = registries[rs2] & 0x000000FF
    elif opcode == "0000011":  # Load instruction
        address = registries[rs1] + signed_from_bin(imm, 12)
        if funct3 == "000":  # LB
            registries[rd] = int.from_bytes(data_b[address - data_offset], byteorder="big")
            if registries[rd] >= 0x80:
                registries[rd] -= 0x100
        if funct3 == "001":  # LH
            registries[rd] = int.from_bytes(data_b[address - data_offset:address - data_offset + 2], byteorder="big")
            if registries[rd] >= 0x8000:
                registries[rd] -= 0x10000
        if funct3 == "010":  # LW
            registries[rd] = int.from_bytes(data_b[address - data_offset:address - data_offset + 4], byteorder="big")
            if registries[rd] >= 0x80000000:
                registries[rd] -= 0x100000000
        if funct3 == "100":  # LBU
            registries[rd] = int.from_bytes(data_b[address - data_offset], byteorder="big")
        if funct3 == "101":  # LHU
            if data_b[address - data_offset] >= 0:
                registries[rd] = int.from_bytes(data_b[address - data_offset:address - data_offset + 2], byteorder="big")
    elif opcode == "1100011":  # B type
        if funct3 == "000":  # beq
            if registries[rs1] == registries[rs2]:
                registries[32] += signed_from_bin(imm, 12)*2
                return
        if funct3 == "001":  # bne
            if registries[rs1] != registries[rs2]:
                registries[32] += signed_from_bin(imm, 12)*2
                return
        if funct3 == "100":  # blt
            if registries[rs1] < registries[rs2]:
                registries[32] += signed_from_bin(imm, 12)*2
                return
        if funct3 == "101":  # bge
            if registries[rs1] >= registries[rs2]:
                registries[32] += signed_from_bin(imm, 12)*2
                return
        if funct3 == "110":  # bltu
            rs1_unsigned = registries[rs1]
            rs2_unsigned = registries[rs2]
            if registries[rs1] < 0:
                rs1_unsigned = registries[rs1] + 0x100000000
            if registries[rs2] < 0:
                rs2_unsigned = registries[rs2] + 0x100000000
            if rs1_unsigned < rs2_unsigned:
                registries[32] += signed_from_bin(imm, 12)*2
                return
        if funct3 == "111":  # bgeu
            rs1_unsigned = registries[rs1]
            rs2_unsigned = registries[rs2]
            if registries[rs1] < 0:
                rs1_unsigned = registries[rs1] + 0x100000000
            if registries[rs2] < 0:
                rs2_unsigned = registries[rs2] + 0x100000000
            if rs1_unsigned >= rs2_unsigned:
                registries[32] += signed_from_bin(imm, 12)*2
                return
    elif opcode == "0010111":  # AUIPC
        registries[rd] = int((imm + "000000000000"), 2) + registries[32]
    elif opcode == "0110111":  # LUI
        registries[rd] = int((imm + "000000000000"), 2) & 0xFFFFFFFF
        if registries[rd] > 0x7FFFFFFF:
            registries[rd] -= 0x100000000
    elif opcode == "1101111":  # JAL
        registries[rd] = registries[32] + 4
        registries[32] += signed_from_bin(imm, 20) * 2
        return
    elif opcode == "1100111":  # JALR
        registries[rd] = registries[32] + 4
        registries[32] = signed_from_bin(imm, 12) + registries[rs1]
        if registries[32] % 2 == 1:
            registries[32] -= 1  # then setting the least-significant bit of the result to zero
        return
    elif opcode == "1110011":  # ECALL
        global interrupt
        interrupt = 1
        print("pass")
    registries[32] += 4
    return


def instruction_decode(instructiune_32):
    opcode = instructiune_32[25:]
    rd = int(instructiune_32[20:25], 2)
    funct3 = instructiune_32[17:20]
    rs1 = int(instructiune_32[12:17], 2)
    rs2 = int(instructiune_32[7:12], 2)
    funct7 = instructiune_32[:7]
    if opcode == "0110011":  # R type
        return opcode, -1, rd, rs1, rs2, funct3, funct7
    elif opcode == "0010011" or opcode == "0000011":  # I type
        imm = instructiune_32[0:12]
        return opcode, imm, rd, rs1, -1, funct3, -1
    elif opcode == "0100011":  # S type
        imm = instructiune_32[:7] + instructiune_32[20:25]
        return opcode, imm, -1, rs1, rs2, funct3, -1
    elif opcode == "1100011":  # B type
        imm = instructiune_32[0] + instructiune_32[24] + instructiune_32[1:7] + instructiune_32[20:24]  # *2 la calcul
        return opcode, imm, -1, rs1, rs2, funct3, -1
    elif opcode == "0010111" or opcode == "0110111":  # AUIPC, LUI
        imm = instructiune_32[:20]
        return opcode, imm, rd, -1, -1, -1, -1
    elif opcode == "1101111":  # JAL
        imm = instructiune_32[0] + instructiune_32[12:20] + instructiune_32[11] + instructiune_32[1:11]
        return opcode, imm, rd, -1, -1, -1, -1
    elif opcode == "1100111":  # JALR
        imm = instructiune_32[:12]
        return opcode, imm, rd, rs1, -1, 0, -1
    elif opcode == "1110011":   # ECALL
        return opcode, -1, -1, -1, -1, -1, -1
    # opcode, imm, rd, rs1, rs2, funct3, funct7


files = ['risc-v code/rv32ui-v-addi.mc',
         'risc-v code/rv32ui-v-beq.mc',
         'risc-v code/rv32ui-v-srl.mc',
         'risc-v code/rv32ui-v-sw.mc',
         'risc-v code/rv32ui-v-xor.mc',
         'risc-v code/rv32um-v-rem.mc',
         'risc-v code/rv32ui-v-lw.mc', ]
for file in files:
    print(file)
    registries = [0] * 33  # registries[32] = PC
    interrupt = False
    cod_b, data_b, data_offset = get_input(file)
    while True:  # codul executat se termina la ECALL
        instructiune_32 = instruction_fetch(registries[32])  # instructiune sub forma unui string de 32 de biti
        parametri = instruction_decode(instructiune_32)
        instruction_execute(parametri)
        registries[0] = 0   # x0 = 0
        if interrupt:
            break

