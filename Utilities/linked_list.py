class node:
    def __init__(self,dataval=None):
        self.dataval=dataval
        self.next=None
        self.previous=None

class linked_list:
	
    def __init__(self):
        self.headval=None
        self.tail=None

    def listprint(self):
        printval = self.headval
        while printval is not None:
            print (printval.dataval)
            printval = printval.next
    
    #insert at the beggining 
    def push_front(self,value):
        new_start=node(value)
        second=self.headval
        self.headval=new_start
        self.headval.next=second
        self.tail=second
        self.tail.previous=self.headval
    
    #insert at the end
    def push_back(self,value):
        new_end=node(value)  #create a new node
        end=self.tail       #the old end node
        end.next=new_end
        self.tail=new_end #set the tail to the new end node
        self.tail.previous=end
    
    def begin(self):
        return self.headval
    
    def end(self):
        return self.tail
        
        
#some test code for the linked list and node class 
if __name__ == '__main__':
    test=linked_list()
    test.headval=node(2)
    test.push_front(1)
    test.push_back(3)
    test.push_back(4)
    test.listprint()
    
    
