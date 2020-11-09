"""CPU functionality."""

import sys
import time
from pynput import keyboard

# Opcodes
OP = "op"
OANDS = "operands"
TP = "type"
OPCODES = {
    0b10100000: {OP:"ADD",OANDS:2,TP:1},
    0b10101000: {OP:"AND",OANDS:2,TP:1},
    0b01010000: {OP:"CALL",OANDS:1,TP:2},
    0b10100111: {OP:"CMP",OANDS:2,TP:1},
    0b01100110: {OP:"DEC",OANDS:1,TP:1},
    0b10100011: {OP:"DIV",OANDS:2,TP:1},
    0b00000001: {OP:"HLT",OANDS:0,TP:0},
    0b01100101: {OP:"INC",OANDS:1,TP:1},
    0b01010010: {OP:"INT",OANDS:1,TP:2},
    0b00010011: {OP:"IRET",OANDS:0,TP:2},
    0b01010101: {OP:"JEQ",OANDS:1,TP:2},
    0b01011010: {OP:"JGE",OANDS:1,TP:2},
    0b01010111: {OP:"JGT",OANDS:1,TP:2},
    0b01011001: {OP:"JLE",OANDS:1,TP:2},
    0b01011000: {OP:"JLT",OANDS:1,TP:2},
    0b01010100: {OP:"JMP",OANDS:1,TP:2},
    0b01010110: {OP:"JNE",OANDS:1,TP:2},
    0b10000011: {OP:"LD",OANDS:2,TP:0},
    0b10000010: {OP:"LDI",OANDS:2,TP:0},
    0b10100100: {OP:"MOD",OANDS:2,TP:1},
    0b10100010: {OP:"MUL",OANDS:2,TP:1},
    0b00000000: {OP:"NOP",OANDS:0,TP:0},
    0b01101001: {OP:"NOT",OANDS:1,TP:1},
    0b10101010: {OP:"OR",OANDS:2,TP:1},
    0b01000110: {OP:"POP",OANDS:1,TP:0},
    0b01001000: {OP:"PRA",OANDS:1,TP:0},
    0b01000111: {OP:"PRN",OANDS:1,TP:0},
    0b01000101: {OP:"PUSH",OANDS:1,TP:0},
    0b00010001: {OP:"RET",OANDS:0,TP:2},
    0b10101100: {OP:"SHL",OANDS:2,TP:1},
    0b10101101: {OP:"SHR",OANDS:2,TP:1},
    0b10000100: {OP:"ST",OANDS:2,TP:0},
    0b10100001: {OP:"SUB",OANDS:2,TP:1},
    0b10101011: {OP:"XOR",OANDS:2,TP:1}
}


class Counter:
  def __init__(self):
    self.epoch = time.time()
  def get_ticks(self):
    delta = time.time() - self.epoch
    return int(delta)



class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0b00000000]*256
        self.reg = [0b00000000]*7 + [0xF4]
        self.pc = 0 #program counter
        self.fl = 0b00000000
        self.running = False
        self.debug = False
        self.interrupted = False
        self.intreg = [False]*8
        self.intcall = [False]*8
        self.timer = Counter()
        self.counter = 0
        self.end = ''
        self.shift = False
        self.listener = keyboard.Listener(
            on_press=self.keypress,
            on_release=self.on_release)
        self.listener.start()

    def on_release(self,key):
        #print('{0} released'.format(key))
        if key == keyboard.Key.esc:
            # Stop listener
            return False
        elif key==keyboard.Key.shift:
            self.shift = False

    def ram_read(self,address):
        if address < len(self.ram):
            return self.ram[address]
        else:
            raise Exception("RAM (read) address out of bounds")


    def ram_write(self,address,value):
        if address < len(self.ram):
            self.ram[address] = value
        else:
            raise Exception("RAM (write) address out of bounds")


    def load(self,filename):
        """Load a program into memory."""
        address = 0
        program = []
        with open(filename,"r") as f:
            for line in f:
                line = line.partition('#')[0]
                line = line.rstrip()
                if line != '':
                    program.append(int(line,base=2))
        for instruction in program:
            self.ram_write(address,instruction)
            address += 1


    def pop(self):
        if self.reg[7] < 0xF4:
            popped = self.ram_read(self.reg[7])
            self.reg[7] += 1
            # if self.debug: print(f"Popped: {popped}")
            return popped
        else:
            raise Exception("Stack empty on pop")


    def push(self,val):
        if self.reg[7] > 0:
            self.reg[7] -= 1
            self.ram_write(self.reg[7],val)
        else:
            raise Exception("Stack overflow")


    def keypress(self,key):
        if self.intreg[1] and not self.intcall[1]:
            self.set_interrupt_call_true(1)
            try:
                k = key.char
                n = ord(k)
                if self.shift:
                    n -= 32
                if self.debug: print('KeyboardInterrupt: {0} | {1}'.format(k,n))
                self.ram_write(0xF4,n&0xFF)
            except AttributeError:
                if self.debug: print('special key {0} pressed'.format(key))
                # self.ram_write(0xF4,ord(key)&0xFF)
                if key==keyboard.Key.shift:
                    self.shift = True
                elif key==keyboard.Key.esc:
                    self.running = False


    def process(self, op, operand_a, operand_b):
        if op == "CALL":
            if self.debug: print(f"CALL: R{operand_a} {self.reg[operand_a]}")
            self.push(self.pc+2)
            self.pc = self.reg[operand_a]
        elif op == "HLT":
            self.running = False
        elif op == "INT":
            # self.pc += 2
            # self.interrupt(self.reg[operand_a])
            self.reg[5] += 2**self.reg[operand_a]
            self.reg[6] += 2**self.reg[operand_a]
            self.pc += 2
        elif op == "IRET":
            for r in range(7):
                self.reg[6-r] = self.pop()
            self.fl = self.pop()
            self.pc = self.pop()
            self.interrupted = False
        elif op == "JEQ":
            if self.fl == 0b00000001:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "JGE":
            if self.fl == 0b00000010 or self.fl == 0b00000001:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "JGT":
            if self.fl == 0b00000010:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "JLE":
            if self.fl == 0b00000100 or self.fl == 0b00000001:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "JLT":
            if self.fl == 0b00000100:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "JMP":
            self.pc = self.reg[operand_a]
        elif op == "JNE":
            if self.fl != 0b00000001:
                self.pc = self.reg[operand_a]
            else:
                self.pc += 2
        elif op == "LD":
            self.reg[operand_a] = self.ram_read(self.reg[operand_b])
        elif op == "LDI":
            self.reg[operand_a] = operand_b
        elif op == "NOP":
            pass
        elif op == "POP":
            self.reg[operand_a] = self.pop()
        elif op == "PRA":
            if self.debug:
                print(">> ",end='')
            print(chr(self.reg[operand_a]),end=self.end)
            if self.debug:
                print()
        elif op == "PRN":
            if self.debug: print(">> ",end='')
            print(self.reg[operand_a])
        elif op == "PUSH":
            self.push(self.reg[operand_a])
        elif op == "RET":
            self.pc = self.pop()
            if self.debug: print(f"RET: {self.pc}")
        elif op == "ST":
            self.ram_write(self.reg[operand_a],self.reg[operand_b])
            # self.reg[operand_a] = self.reg[operand_b]
        else:
            raise Exception("Unsupported operation")


    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] = (self.reg[reg_a]+self.reg[reg_b])&0xFF
        elif op == "AND":
            self.reg[reg_a] = self.reg[reg_a]&self.reg[reg_b]
        elif op == "CMP":
            if self.reg[reg_a]==self.reg[reg_b]:
                self.fl = 0b00000001
            elif self.reg[reg_a] > self.reg[reg_b]:
                self.fl = 0b00000010
            elif self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b00000100
            else:
                self.fl = 0b00000000
        elif op == "DEC":
            self.reg[reg_a] = (self.reg[reg_a]-1)&0xFF
        elif op == "DIV":
            if self.reg[reg_b]==0:
                raise Exception("Division by zero")
            else:
                self.reg[reg_a] = (self.reg[reg_a]/self.reg[reg_b])&0xFF
        elif op == "INC":
            self.reg[reg_a] = (self.reg[reg_a]+1)&0xFF
        elif op == "MOD":
            if self.reg[reg_b]==0:
                raise Exception("Division by zero")
            else:
                self.reg[reg_a] = (self.reg[reg_a]%self.reg[reg_b])&0xFF
        elif op == "MUL":
            self.reg[reg_a] = (self.reg[reg_a]*self.reg[reg_b])&0xFF
        elif op == "NOT":
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == "OR":
            self.reg[reg_a] = self.reg[reg_a]|self.reg[reg_b]
        elif op == "SHL":
            self.reg[reg_a] = (self.reg[reg_a]<<self.reg[reg_b])&0xFF
        elif op == "SHR":
            self.reg[reg_a] = (self.reg[reg_a]>>self.reg[reg_b])&0xFF
        elif op == "SUB":
            self.reg[reg_a] = (self.reg[reg_a]-self.reg[reg_b])&0xFF
        elif op == "XOR":
            self.reg[reg_a] = self.reg[reg_a]^self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")


    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """
        print(f"TRACE: %02X | %02X %02X %02X | %02X | " % (
            self.pc,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2),
            self.fl
        ), end='')
        for i in range(8):
            print(" %02X" % self.reg[i], end='')
        print()

    def load_interrupts(self):
        r5 = format(self.reg[5], '#010b')
        r6 = format(self.reg[6], '#010b')
        for i in range(8):
            if r5[-(i+1)] == "1":
                self.intreg[i] = True
            if r6[-(i+1)] == "1":
                self.intcall[i] = True

    def check_interrupts(self):
        for i in range(8):
            if self.intreg[i] and self.intcall[i]:
                return i
        return None

    def set_interrupt_reg_true(self, i):
        self.reg[5] += 2**i
        self.intreg[i] = True

    def set_interrupt_reg_false(self, i):
        self.reg[5] -= 2**i
        selt.intreg[i] = False

    def set_interrupt_call_true(self, i):
        self.reg[6] += 2**i
        self.intcall[i] = True

    def set_interrupt_call_false(self, i):
        self.reg[6] -= 2**i
        self.intcall[i] = False


    def interrupt(self, i):
        if self.debug:
            print(f"Interrupt {i}", end=" >> ")
        self.interrupted = True
        self.set_interrupt_call_false(i)
        self.push(self.pc)
        self.push(self.fl)
        for r in range(7):
            self.push(self.reg[r])
        addx = 0xF8 + i
        self.pc = self.ram_read(addx)
        if self.debug: print(self.pc)


    def run(self):
        """Run the CPU."""
        self.running = True
        testOP = None
        opcounter = 0
        while self.running:
            # if self.debug: self.trace()
            timeplus = False
            intnow = None
            self.load_interrupts()
            if not self.interrupted:
                intnow = self.check_interrupts()
            if self.timer.get_ticks() > self.counter:
                self.counter = self.timer.get_ticks()
                if self.debug:
                    print(f"Timer: {self.counter}")
                if self.intreg[0] and not self.interrupted:
                    self.end = '\n'
                    if self.debug:
                        print("T-",end='')
                    self.set_interrupt_call_true(0)
                    intnow = self.check_interrupts()
            # if not self.interrupted:
            if intnow is not None:
                self.interrupt(intnow)
            ir = self.ram_read(self.pc)
            instruction = OPCODES.get(ir)
            if instruction is not None:
                if self.debug:
                    if instruction != testOP:
                        testOP = instruction
                        opcounter = 0
                        print(f"\nOP: {instruction[OP]} ",end='')
                    else:
                        if opcounter < 10:
                            opcounter += 1
                            print("*",end='')
                        elif opcounter == 10:
                            opcounter += 1
                            print("+")
                if instruction[TP]==1:
                    self.alu(instruction[OP],self.ram_read(self.pc+1),self.ram_read(self.pc+2))
                else:
                    self.process(instruction[OP],self.ram_read(self.pc+1),self.ram_read(self.pc+2))
                if instruction[TP] != 2:
                    self.pc += instruction[OANDS] + 1
            else:
                raise Exception("Unrecognized OP Code {}".format(ir))
