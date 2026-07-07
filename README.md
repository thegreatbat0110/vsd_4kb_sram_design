# 4kb_sram_design
---------------------------------------------------------------------------------------------
Week 1 
-------
This project focuses on the understanding and recreating the circuit-level design flow of an SRAM memory block using open-source EDA tools such as Xschem, Magic, ngspice, and OpenRAM. The main emphasis is on the 6T SRAM bitcell architecture and its associated peripheral circuits.
The goal is to study how a single SRAM cell stores data, how read and write operations work, and how peripheral blocks support array-level memory operation.

SRAM Background
--------------

Static Random Access Memory (SRAM) is a volatile memory technology that stores data using bistable latch structures. Unlike DRAM, SRAM does not require periodic refresh because the stored value is maintained as long as power is applied.

SRAM is widely used in cache memories, register files, and other high-speed memory applications because of its fast access time and low latency.

###6T SRAM Bitcell
----------------

The basic SRAM storage element is the **6-transistor (6T) bitcell**. It is built from:

- Two cross-coupled CMOS inverters.
- Two access NMOS transistors connected to the complementary bitlines BL and BLB.
- A word line (WL) that enables access to the cell.

The cross-coupled inverters form a latch that stores one bit of information. The access transistors connect the internal storage nodes to the bitlines during read and write operations when WL is asserted.

Internal Nodes
----------------

The 6T cell has two internal nodes:

- Node Q.
- Node QB.

These nodes always store complementary logic values. If Q = 1, then QB = 0, and vice versa.

## Working Principle
----------------------

### Hold Mode

When WL is low, the access transistors remain OFF. The cell is isolated from the bitlines, and the cross-coupled inverters preserve the stored state.

### Read Operation

During read, the bitlines are typically precharged high. When WL goes high, the access transistors connect the internal nodes to BL and BLB. The bitline connected to the stored 0 discharges slightly, creating a small differential voltage that can be detected by a sense amplifier.

A proper read must not disturb the stored data inside the cell. This requirement is closely related to the cell’s read stability.

### Write Operation

During write, the write driver forces BL and BLB to complementary values. When WL is asserted, the stronger bitline driver overpowers the previous state of the latch and flips the cell to the new value.

Write ability depends on the relative strength of the access transistors and the pull-up / pull-down devices in the cell.

## Peripheral Circuits
------------------------

A practical SRAM is not just a memory cell. It also needs supporting peripheral circuits to enable reliable read and write operations.

### Precharge Circuit

The precharge circuit consists of 3 PMOS transistors that equalize and charge BL and BLB before a read cycle. This helps ensure fast sensing and proper bitline initialization.

### Sense Amplifier

The sense amplifier detects the small voltage difference that develops on the bitlines during a read operation and amplifies it to a full logic level.

### Write Driver

The write driver provides strong complementary signals to BL and BLB during write operations so that the selected cell can be overwritten.

### Row Decoder

The row decoder selects one word line from many possible word lines based on the input address. This activates only the desired memory row.

### Column Decoder

The column decoder selects the correct bitline pair or output path from the memory array. It helps organize larger SRAM banks efficiently.

### Wordline Driver

The wordline driver boosts the decoded row signal and drives the selected word line across the memory array.

## SRAM Read and Write Flow

A typical SRAM access sequence is:

1. Precharge the bitlines.
2. Decode the row and column address.
3. Activate the selected word line.
4. Perform read through the sense amplifier or write through the write driver.
5. Deassert WL and return the bitlines to precharge state.

## Design Flow Using Open-Source Tools

### Xschem

Xschem is used for schematic capture of the 6T cell and peripheral circuits.

### ngspice

ngspice is used for simulation of transient behavior, read/write operation, and basic circuit verification.

### Magic

Magic is used for layout design, placement, routing, and DRC/LVS-related implementation tasks.

### OpenRAM

OpenRAM is used for SRAM compiler-based generation and exploration of memory macros, helping connect the theoretical design with practical memory architecture.

## Key Design Concerns

Important SRAM design metrics include:

- Static noise margin.
- Read stability.
- Write ability.
- Access time.
- Power consumption.
- Cell area.
- Bitline delay.
