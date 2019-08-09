'''
Parallel Algorithms exercise implementing Carry-Lookahead algorithm for adding two N-bits numbers. 
Results from comparing the parallel and sequentian algorithm are also provided.
'''

from bitarray import bitarray # Data structure for efficient storing of the individual bits
import multiprocessing as mp # For parallelizing
from multiprocessing import Process, Lock
from math import log2

def isBinaryString(string) :
    ''' Checking if a string is binary'''
    p = set(string) 
    s = {'0','1'}
    if s == p or p == {'0'} or p == {'1'} :
        return True
    else:
        return False

def getInput(size) :
    '''Getting input from user and error checking'''
    error_message_size = "Invalid size. Size must be as previously declared!"
    error_message_binary_string = "Invalid type. Input must be binary number!"
    success_message = "Succesfull nunber insertion!"
    while True:
        bitString = input("What is the number? ")
        if len(bitString) != size :
            print(error_message_size)
        if not isBinaryString(bitString) :
            print(error_message_binary_string)
        if len(bitString) == size and isBinaryString(bitString) :
            break
    print(success_message)
    return(bitString)

def sequentialBinaryAdder(bitArrayA, bitArrayB) :
    '''Function for sequentially adding two binary numbmers. Assumes same length of bit arrays as this is always the case for this program. Inputs are two bitArrays and an integer
    variable for the number of steps that were needed to complete the adition to be stored. A and B are the bit arrays that will be added. In the i-th position there must be 
    the i-th bit of the number. A bit array with the result is returned in the same output which means that in the i-th position there is the result of adding the i-th bit of 
    array A with the i-th bit of array B.'''

    bitArrayResult = bitarray()
    carry_flag = False 

    for x,y in zip(bitArrayA,bitArrayB) :
        if carry_flag :
            bitArrayResult.append(not(x ^ y)) #Adding if there is carry
            carry_flag = x or y #If there is a carry and at least one bit is 1, carry will be generated again. Otherwise carry_flag is set to False

        else :
            bitArrayResult.append(x ^ y) #Adding with no carry
            carry_flag = x and y #Generating carry only in the case that both bits are 1

    
    
    if carry_flag : #If last addition generates carry one bit is added with value 1 as msb
        bitArrayResult.append(True)

    return bitArrayResult


def identifySubAdditionCarry(bitA, bitB) :
    '''Function which identifies if subaddition stop (s), propagate (p), or generate (g) a carry.'''
    if bitA == True :
        if bitB == True :
            return 'g' #generate carry
        else :
            return 'p' #propagate carry
    else :
        if bitB == True :
            return 'p' #propagate carry
        else :
            return 's' #stop carry

def setInternalNode(nodeA,nodeB) :
    '''Function for returning the correct value for the internal node, given the 2 child nodes. Node A is the left and B the right node.''' 
    if nodeB != 'p' :
        return nodeB
    else :
        return nodeA


def transformLeave(leaf) :
    '''Transforms s ang g values to 0 and 1'''
    if leaf == 's':
        return 0
    else :
        return 1

def noCarryAdder(a,b,c) :
    '''Adding three numbers without taking into consideration carries'''
    return a^b^c  




if __name__ == "__main__" :
    N = int(input("What is the bit size of the numbers that will be added? "))
    bitStringA = getInput(N)
    bitStringB = getInput(N)

    bitArrayA = bitarray(bitStringA)
    bitArrayB = bitarray(bitStringB)

    # Reversing bits so in the first position of each array there will be the lsb etc...
    #In position i of each array we have the i-th bit of each number
    bitArrayA.reverse()  
    bitArrayB.reverse()

#  ___________________________________----END OF PARSING----___________________________________




# ____________________----CALCULATING RESULT USING SEQUENTIAL ALGORITHM----____________________

bitArrayResult = sequentialBinaryAdder(bitArrayA,bitArrayB) #Output of function
bitArrayResult.reverse() #Output of function with bits reversed so they will be printed properly
sequentialResult = bitArrayResult.to01()

sequentialSteps = len(sequentialResult) #Bit-steps are always N or N+1 in sequential algorithm 


#___________________________----END OF SEQUENTIAL PART OF PROGRAM----___________________________











# ___________________---CALCULATING RESULT USING CARRY-LOOKAHEAD ALGORITHM---_________________


parallelAlgSteps = 0 #Real bit-steps needed
parallelAlgStepsIdeal = 0 #Bit-steps needed assuming number of processors same with the size of the numbers given to add

# Numbers should have even bits length for the algorithm to work
if N % 2 == 1 :
    # Adding a dummy bit (value 0) as msb so that the size will be an even number
    bitArrayA.append(False)
    bitArrayB.append(False)
    N += 1

#Calculating height of binary tree
if log2(N) == int(log2(N)) :
    height = int(log2(N)) + 1 # plus 1 because of the initial level
else :
    height = int(log2(N)) + 1 + 1 # plus 2 because of the initial level and to round up to integer
level = [[] for x in range(height)] #List where each level will be saved to

# Generating s,p,g values
pool = mp.Pool(mp.cpu_count()) #Initiallizing pool of processes --As many processes as the cpu can handle at once
level[0] = [pool.apply(identifySubAdditionCarry, args=(x,y)) for x,y in zip(bitArrayA,bitArrayB)] #This will be level 0 of our binary tree
pool.close() # Closing pool when finished

if N % mp.cpu_count() == 0 and N > mp.cpu_count() : 
    parallelAlgSteps += N // mp.cpu_count() #Bit steps are calculated by dividing number of function calls with number of processes cpu can handle at once
else :
    parallelAlgSteps += N // mp.cpu_count() + 1 #Bit steps are calculated by dividing number of function calls with number of processes cpu can handle at once plus 1
parallelAlgStepsIdeal += 1


for k in range(1,height) :
    pool = mp.Pool(mp.cpu_count())
    level[k] = [pool.apply(setInternalNode, args=(level[k-1][x],level[k-1][x+1])) for x in range(0,len(level[k-1]) - 1,2)]
    pool.close()
    if len(level[k]) % 2 == 1 and k != height-1 :
        level[k].append('p') #Making the size an even number

    #Calculating steps as before
    if (len(level[k-1]) / 2) % mp.cpu_count() == 0 and len(level[k-1]) / 2 > mp.cpu_count() :
        parallelAlgSteps += len(level[k-1]) // mp.cpu_count()
    else :
        parallelAlgSteps += len(level[k-1]) // mp.cpu_count() + 1 
    parallelAlgStepsIdeal += 1


root_output = level[height-1][0] #Root value will be output 
level[height - 1][0] = 's' #Setting root value to 's'

#For loop should have been parallelized and added to the setInternalNode function.  
for k in range(0,height-1) :
    for y in range(1,len(level[k]),2) :
        level[k][y] = level[k][y-1]
        level[k][y-1] = 'x'
    #Calculating steps assuming parallel execution    
    if (len(level[k]) / 2) % mp.cpu_count() == 0 and len(level[k]) / 2 > mp.cpu_count():
        parallelAlgSteps += len(level[k]) // mp.cpu_count()
    else :
        parallelAlgSteps += len(level[k]) // mp.cpu_count() + 1  
    parallelAlgStepsIdeal += 1

#for k in range(0,height) :
#    print(*level[k])



#Searching for the first non p value for the ancestor of each leaf and assigning leaf appropriate value. Should have been running parallel.
parallelAlgSteps_lastPhase = 0
for k in range(0,len(level[0])):
    if level[0][k] == 'p' or level[0][k] == 'x' :
        father_index = k // 2
        for p in range(1,height):
            parallelAlgSteps_lastPhase += 1
            if level[p][father_index] != 'p' and level[p][father_index] != 'x' :
                level[0][k] = level[p][father_index]
                break
            else:
                father_index = father_index // 2

#Adjusting steps to simulate parallel execution
parallelAlgSteps_lastPhase_Fixed = parallelAlgSteps_lastPhase // mp.cpu_count()
parallelAlgSteps += parallelAlgSteps_lastPhase_Fixed
parallelAlgStepsIdeal += 1


#Transforming 's' and 'g' to 0 and 1 
pool = mp.Pool(mp.cpu_count())
level[0] = [pool.apply(transformLeave, args=(leaf)) for leaf in level[0]]
pool.close()

#Steps are not counted because g and s values are already calculated
'''if len(level[0]) % mp.cpu_count() == 0:
    parallelAlgSteps += len([level][0]) // mp.cpu_count() #Updating steps needed 
else:
    parallelAlgSteps += len([level][0]) // mp.cpu_count() + 1 #Upating steps needed'''


#Final step
pool = mp.Pool(mp.cpu_count())
ArrayResult2 = [pool.apply(noCarryAdder, args=(bitArrayA[x],bitArrayB[x],level[0][x])) for x in range(0,len(bitArrayA))]
pool.close()

parallelAlgSteps += len(bitArrayA) // mp.cpu_count() 
parallelAlgStepsIdeal += 1

ArrayResult2.append(transformLeave(root_output)) #Adding already calculated carry of overall sum
bitArrayResult2 = bitarray(ArrayResult2)
bitArrayResult2.reverse()
parallelResult = bitArrayResult2.to01()


print(parallelResult)


#___________________________FINISHED IMMPLEMENTING CARRY-LOOKAHEAD ALGORITHM_________________________







#_____PRINTING RESULTS_____

print("Result of sequential algorithm is: " + sequentialResult)
print("Bit steps needed for the sequential algorithm to finish were: " + str(sequentialSteps))
print()
print("Result of parallel algorithm is: " + parallelResult)
print("Bit-steps needed for the parallel algorithm to finish were: " + str(parallelAlgSteps))
print("If computer had at least as many processors as the size of the numbers added then the steps would have been: " + str(parallelAlgStepsIdeal))