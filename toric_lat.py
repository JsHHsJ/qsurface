import os
import sys
import time
import datetime
import random
import toric_plot2 as tp
import blossom5.pyMatch as pm
import peeling as pel
import graph_objects as GO


class lattice:

    def __init__(self, size=10, plot_load=True):

        '''
        :param size:
        :param plot_load:

         We define the unit cell, which contains two qubits, a star operator and plaquette operator.

            |       |
        - Star  -  Q_0 -     also top (T) qubit
            |       |
        -  Q_1  - Plaq  -    also down (D) qubit
            |       |

        By doing so, we can define arrays the star and plaquette operators, where their index value define their position
          on the qubit lattice. For the qubit array, there is an extra dimension to store the two qubits per unit cell.

        self.array stores the qubit values and has dimension [XZ_error{0,1}, Top_down{0,1}, size, size]
        Qubit values are either 0 or 1, which is analogous to the -1, and 1 state, respectively
        '''
        self.size = size
        self.plot_load = plot_load
        self.time = time.time()

        random.seed(self.time)
        # random.seed(10)

        # self.array = [[[[True for _ in range(self.size)] for _ in range(self.size)] for _ in range(2)] for _ in range(2)]

        self.num_stab = self.size * self.size * 2
        self.num_qubit = self.num_stab * 2
        self.array = [True for _ in range(self.num_qubit)]

        if not os.path.exists("./errors/"):
            os.makedirs("./errors/")


    def init_data(self):
        '''
        Initializes a tuple (edge_data) which contains information of every qubit on lattice (primary and secundary)

        The qubits on the X and Z lattices are defined by the unit cell:
            X:     Z:
                    _
            _|     |

        Each qubit (depected by an edge) has 2 connected anyons and 6 neighbor qubits:
        - for each qubit _, the neigbors are  _|_|_
                                               | |

                                               _|_
        - for each qubit |, the neighbors are  _|_
                                                |

        v1-v3 and v4-v6 are neighbors located at opposite sides of the qubit (loc A and loc B)

        The tuple stores the information in the following order:
            0   error type (primary or secundary)
            1   y location of unit cell
            2   x location of unit cell
            3   td, top or down qubit/edge in the unit cell
            4   number of neighbor qubits in loc A
            5   tuple of qID's of neighbors in loc A (qID0, qID1...)
            6   number of neighbor qubits in loc B
            7   tuple of qID's of neighbors in loc B (qID0, qID1...)
            8   sID of anyon 1
            9   sID of anyon 2
        The y and x position of anyon 0 are within the same unit cell of the qubit, and are defined in 2 and 3 already
        '''

        qubit_list = []
        stab_list = []

        qubitlist = []

        self.G = GO.Graph(None,None,None)

        for ertype in range(2):
            for y in range(self.size):
                for x in range(self.size):
                    stab_list.append([ertype, y, x])

                    self.G.add_vertex((ertype, y, x))

                    for td in range(2):
                        qubit_list.append([ertype, y, x, td])

                        qubitlist.append((ertype, y, x, td))

        neighbor_list = []
        qubit_stab_list = []


        for (ertype, y, x, td) in qubitlist:
            qID = (ertype, y, x, td)
            if ertype == 0 and td == 0:
                VL_sID = (ertype, y, x)
                VR_sID = (ertype, y, (x + 1) % self.size)
                self.G.add_edge(qID, VL_sID, VR_sID, 'H')
            elif ertype == 1 and td == 1:
                VL_sID = (ertype, y, (x - 1) % self.size)
                VR_sID = (ertype, y, x)
                self.G.add_edge(qID, VL_sID, VR_sID, 'H')
            elif ertype == 0 and td == 1:
                VU_sID = (ertype, y, x)
                VD_sID = (ertype, (y + 1) % self.size, x)
                self.G.add_edge(qID, VU_sID, VD_sID, 'V')
            elif ertype == 1 and td == 0:
                VU_sID = (ertype, (y - 1) % self.size, x)
                VD_sID = (ertype, y, x)
                self.G.add_edge(qID, VU_sID, VD_sID, 'V')





        for (ertype, y, x, td) in qubit_list:

            if ertype == 0:
                v1 = qubit_list.index([0, y, x, 1 - td])
                v2 = qubit_list.index([0, (y + 1) % self.size, x, 0])
                v3 = qubit_list.index([0, y, (x + 1) % self.size, 1])
                v4 = qubit_list.index([0, (y - 1 + td) % self.size, (x - td) % self.size, 0])
                v5 = qubit_list.index([0, (y - 1 + td) % self.size, (x - td) % self.size, 1])
                v6 = qubit_list.index([0, (y - 1 + 2*td) % self.size, (x + 1 - 2*td) % self.size, 1 - td])
            else:
                v1 = qubit_list.index([1, y, x, 1 - td])
                v2 = qubit_list.index([1, y, (x - 1) % self.size, 0])
                v3 = qubit_list.index([1, (y - 1) % self.size, x, 1])
                v4 = qubit_list.index([1, (y + td) % self.size, (x + 1 - td) % self.size, 0])
                v5 = qubit_list.index([1, (y + td) % self.size, (x + 1 - td) % self.size, 1])
                v6 = qubit_list.index([1, (y - 1 + 2*td) % self.size, (x + 1 - 2*td) % self.size, 1 - td])

            neighbor_list.append([3, (v1, v2, v3), 3, (v4, v5, v6)])

            s1 = stab_list.index([ertype, y, x])
            s2 = stab_list.index([ertype, (y + td + ertype - 1) % self.size, (x - td + ertype) % self.size])
            qubit_stab_list.append([s1, s2])

        edge_data = []

        for (qubit, neighbor, stab) in zip(qubit_list, neighbor_list, qubit_stab_list):
            edge_data.append(tuple(qubit + neighbor + stab))

        self.edge_data = tuple(edge_data)

        '''
        Also, for each possible stabilizer, there are 4 or 3 (only planar) connected qubits
            |
          - o -
            |
        We call each of these qubis the North (qN), South (qS), East (qE) and West (qW) qubits, in that order
        Store the connected qubits to a tuple in the following order:
            0   error type (primary or secundary)
            1   y location of unit cell
            2   x location of unit cell
            3   tuple of neighbor anyons (sN, sS, sE, sW)
            4   tuple of connected qubit id (qN, qS, qE, qW)
        '''

        stab_qubit_list = []

        for (ertype, y, x) in stab_list:

            sN = stab_list.index([ertype, (y - 1) % self.size, x])
            sS = stab_list.index([ertype, (y + 1) % self.size, x])
            sE = stab_list.index([ertype, y, (x - 1) % self.size])
            sW = stab_list.index([ertype, y, (x + 1) % self.size])

            if ertype == 0:
                qN = qubit_list.index([0, y, x, 0])
                qS = qubit_list.index([0, (y + 1) % self.size, x, 0])
                qE = qubit_list.index([0, y, x, 1])
                qW = qubit_list.index([0, y, (x + 1) % self.size, 1])
            if ertype == 1:
                qN = qubit_list.index([1, (y - 1) % self.size, x, 1])
                qS = qubit_list.index([1, y, x, 1])
                qE = qubit_list.index([1, y, (x - 1) % self.size, 0])
                qW = qubit_list.index([1, y, x, 0])

            stab_qubit_list.append([(sN, sS, sE, sW), (qN, qS, qE, qW)])

        stab_data = []

        for (stab, qubit) in zip(stab_list, stab_qubit_list):
            stab_data.append(tuple(stab + qubit))

        self.stab_data = tuple(stab_data)

        '''
        Get edge qubits for the detection of logical errors
        '''

        lx0 = [2*q for q in range(self.size)]
        lx1 = [1 + 2*q*self.size for q in range(self.size)]
        lz0 = [self.num_stab + 2*(self.size - 1)*self.size + 1 + 2*q for q in range(self.size)]
        lz1 = [self.num_stab + 2*(self.size - 1) + 2*q*self.size for q in range(self.size)]

        self.log_data = (tuple(lx0), tuple(lx1), tuple(lz0), tuple(lz1))

        # for i,a in enumerate(self.edge_data): print(i,a)
        # for i,a in enumerate(self.stab_data): print(i,a)
        # print(self.log_data)

        return (self.edge_data, self.stab_data, self.log_data)

    def load_data(self, edge_data, stab_data, log_data):
        '''
        loads the data structures initialezed in init_edge_data
        '''
        self.edge_data = edge_data
        self.stab_data = stab_data
        self.log_data = log_data

    def init_plots(self):
        # Initiate plot
        if self.plot_load:
            self.LP = tp.lattice_plot(self.size, self.edge_data, self.stab_data)
            self.LP.plot_lattice()


    '''
    Main functions
    '''

    def print_errors(self, array, type, p):
        '''
        :param array        error list of size 2*L*L
        :param type         string indicating the error type
        :param p            the error probability of the current error type

        Prints the given error array to an easy to read format, which can be altered by the user, and reused later.
        '''

        st = datetime.datetime.fromtimestamp(self.time).strftime('%Y-%m-%d_%H-%M-%S')
        st2 = datetime.datetime.fromtimestamp(self.time).strftime('%Y-%m-%d %H-%M-%S')
        name = "./errors/" + st + "_L_" + str(self.size) + "_" + type + ".txt"

        f = open(name, "w")

        f.write(type + " error file created on " + st2 + "\n")
        f.write("Seed = " + str(self.time) + "\n")
        f.write("P = " + str(p) + "\n")
        f.write("L = " + str(self.size) + "\n\n")

        for line in range(self.size):
            f.write("  ")
            for qubit in range(self.size):
                f.write(str(int(array[line*self.size*2 + qubit*2])) + "   ")
            f.write("\n")
            for qubit in range(self.size):
                f.write(str(int(array[line*self.size*2 + qubit*2 + 1])) + "   ")
            f.write('\n')

        f.close()

    def read_errors(self, type, filetimestamp):
        '''
        :param ertype           string indicating the error type
        :param filetimestamp    timestamp of error file: YYYY-MM-DD_hh_mm

        Loads the error array given the filetimestamp
        '''

        filename = "./errors/" + filetimestamp + "_L_" + str(self.size) + "_" + type + ".txt"

        try:
            f = open(filename, "r")
        except FileNotFoundError:
            sys.exit("Error file not found")

        array = []

        for ln, line in enumerate(f.readlines()):
            if ln > 4:
                if ln % 2 == 1:
                    l1 = []
                    for char in range(self.size):
                        l1.append(int(line[2 + char*4]))
                else:
                    for char in range(self.size):
                        array.append(l1[char])
                        array.append(int(line[char*4]))

        return array

    def init_erasure(self, pE=0.05, savefile=True, filetimestamp=None):

        '''
        :param pE:                      probability of erasure error
        :param new_errors: if true:     new array is generated with errors; if false; previous array is used (txt file)
        :param write_error: if true:    writes the generated array with pauli errors to txt files
        :param array_file:              name for the txt file
        '''

        self.pE = pE

        if filetimestamp is None:

            # Generate erasure errors
            erasures = [1 if random.random() < self.pE else 0 for _ in range(self.num_stab)]

            # Increase error size, make blob
            for id in [id for id, erasure in enumerate(erasures) if erasure == 1]:
                for qA in self.edge_data[id][5]:
                    erasures[qA] = 1
                for qB in self.edge_data[id][7]:
                    erasures[qB] = 1


            # Uniform I, X, Y, Z
            for id in [id for id, erasure in enumerate(erasures) if erasure == 1]:
                rand = random.random()
                if rand < 0.25:
                    erasures[id] = 2
                elif rand >= 0.25 and rand < 0.5:
                    erasures[id] = 3
                elif rand >= 0.5 and rand < 0.75:
                    erasures[id] = 4

            if savefile:
                self.print_errors(erasures, "Erasure", pE)

        else:
            erasures = self.read_errors("Erasure", filetimestamp)

        # if self.plot_load:   self.LP.plot_erasures(self.erasures)

        self.er_loc = []
        # Apply erasure errors to array
        for id, erasure in enumerate(erasures):
            if erasure != 0:
                self.er_loc.append(id)
                self.er_loc.append(id + self.num_stab)

            if erasure in [2, 4]:
                self.array[id] = not self.array[id]
            if erasure in [3, 4]:
                self.array[id + self.num_stab] = not self.array[id + self.num_stab]

        self.er_loc = tuple(self.er_loc)



    def init_pauli(self, pX=0.1, pZ=0.1, savefile=True, filetimestamp=None):

        '''
        :param pX:                      probability of X error
        :param pZ:                      probability of Z error
        :param new_errors: if true:     new array is generated with errors; if false; previous array is used (txt file)
        :param write_error: if true:    writes the generated array with pauli errors to txt files
        :param array_file:              name for the txt file
        '''

        self.pX = pX
        self.pZ = pZ

        if filetimestamp is None:
            eX = [True if random.random() < self.pX else False for _ in range(self.num_stab)]
            eZ = [True if random.random() < self.pZ else False for _ in range(self.num_stab)]
            if savefile:
                self.print_errors(eX, "Pauli-X", pX)
                self.print_errors(eZ, "Pauli-Z", pZ)
        else:
            eX = self.read_errors("Pauli-X", filetimestamp)
            eZ = self.read_errors("Pauli-Z", filetimestamp)

        # Apply pauli errors to array
        for id, iX in enumerate(eX):
            if iX:
                self.array[id] = not self.array[id]
        for id, iZ in enumerate(eZ):
            if iZ:
                self.array[id + self.num_stab] = not self.array[id + self.num_stab]


        if self.plot_load:
            self.LP.plot_errors(self.array)

    def measure_stab(self):
        '''
        self.stab is an array that stores the measurement outcomes for the stabilizer measurements
            It has dimension [XZ{0,1}, size, size]
            Measurements outcomes are either 0 or 1, analogous to -1 and 1 states
            The 0 values are the quasiparticles
        '''

        stab_measurement = [True for _ in range(self.num_stab)]

        # Measure plaquettes and stars
        for sID, stabilizer in enumerate(self.stab_data):

            # Flip value of stabilizer measurement
            for qID in stabilizer[4]:
                if not self.array[qID]:
                    stab_measurement[sID] = not stab_measurement[sID]

        self.qua_loc = tuple([sID for sID, stab in enumerate(stab_measurement) if not stab])

        if self.plot_load:
            self.LP.plot_anyons(self.qua_loc)

    def get_matching_peeling(self):
        '''
        Uses the Peeling algorithm to get the matchings
        Optionally, edge_data can be inputted here, which is useful in multiple iteration simulations
        '''

        PL = pel.toric(self)
        PL.find_clusters()
        PL.grow_clusters()
        PL.init_trees()
        PL.peel_trees()
        matching = PL.return_matching()


        for id in matching:

            self.array[id] = not self.array[id]

        if self.plot_load:
            self.LP.plot_final(matching, self.array)

    def get_matching_MWPM(self):
        '''
        Uses the MWPM algorithm to get the matchings
        A list of combinations of all the anyons and their respective weights are feeded to the blossom5 algorithm
        '''

        qua_loc = (tuple([qua for qua in self.qua_loc if qua < self.size**2]), tuple([qua for qua in self.qua_loc if qua >= self.size**2]))
        N_qua = (len(qua_loc[0]), len(qua_loc[1]))

        self.results = []
        self.flips = []

        for ertype in range(2):

            # edges given to MWPM algorithm [[v0, v1, distance],...]
            edges = []

            # Get all possible strings - connections between the quasiparticles and their weights
            for i0, v0 in enumerate(qua_loc[ertype][:-1]):

                (y0, x0) = self.stab_data[v0][1:3]

                for i1, v1 in enumerate(qua_loc[ertype][i0 + 1:]):

                    (y1, x1) = self.stab_data[v1][1:3]
                    wy = (y0 - y1) % (self.size)
                    wx = (x0 - x1) % (self.size)
                    weight = min([wy, self.size - wy]) + min([wx, self.size - wx])
                    edges.append([i0, i1 + i0 + 1, weight])

            # Apply BlossomV algorithm if there are quasiparticles
            output = pm.getMatching(N_qua[ertype], edges) if N_qua[ertype] != 0 else []

            # Save results to same format as self.syn_inf
            matching_pairs = [[i, output[i]] for i in range(N_qua[ertype]) if output[i] > i]

            '''
            Finds the qubits that needs to be flipped in order to correct the errors
            '''

            result = []

            for pair in matching_pairs:

                v0 = qua_loc[ertype][pair[0]]
                v1 = qua_loc[ertype][pair[1]]
                result.append((v0, v1))

                (y0, x0) = self.stab_data[v0][1:3]
                (y1, x1) = self.stab_data[v1][1:3]

                # Get distance between endpoints, take modulo to find min distance
                dy0 = (y0 - y1) % self.size
                dx0 = (x0 - x1) % self.size
                dy1 = (y1 - y0) % self.size
                dx1 = (x1 - x0) % self.size

                if dy0 < dy1:
                    dy = dy0
                    yd = 0
                else:
                    dy = dy1
                    yd = 1

                if dx0 < dx1:
                    dx = dx0
                    xd = 3
                else:
                    dx = dx1
                    xd = 2

                ynext = v0
                for y in range(dy):
                    self.flips.append(self.stab_data[ynext][4][yd])
                    ynext = self.stab_data[ynext][3][yd]

                xnext = v1
                for x in range(dx):
                    self.flips.append(self.stab_data[xnext][4][xd])
                    xnext = self.stab_data[xnext][3][xd]


            self.results.append(result)

        # Apply flips on qubits
        for id in self.flips:
            self.array[id] = not self.array[id]


        if self.plot_load:
            self.LP.plot_lines(self.results)
        if self.plot_load:
            self.LP.plot_final(self.flips, self.array)

    def logical_error(self):

        # logical error in [Xvertical, Xhorizontal, Zvertical, Zhorizontal]
        logical_error = [False, False, False, False]

        # Check number of flips around borders
        for i, error in enumerate(self.log_data):
            for qubit in error:
                if self.array[qubit] == False:
                    logical_error[i] = not logical_error[i]

        return logical_error


    def print_array(self):
        '''
        used to print the qubit array at any moment
        '''

        Ername = ["X", "Z"]
        for ertype in range(2):
            for y in range(self.size):
                line1 = "  "
                line2 = ""
                for x in range(self.size):
                    str1 = "O" if self.array[ertype*self.num_stab + y*self.size*2 + x*2] else Ername[ertype]
                    str2 = "O" if self.array[ertype*self.num_stab + y*self.size*2 + x*2 + 1] else Ername[ertype]
                    line1 += str1 + "   "
                    line2 += str2 + "   "
                print(line1)
                print(line2)
            print("")

    def print_LL2(self, LL2_array):
        '''
        print a LxLx2 array (stab, error) in a way that is nice to read
        '''

        base = 0
        for ertype in range(2):
            for y in range(self.size):
                print([0 if x in [False, 0] else 1 for x in LL2_array[base: base + self.size]])
                base += self.size


'''
Helper functions
'''
