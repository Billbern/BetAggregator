class Node:
    def __init__(self, val):
        self.value = val
        self.next = None

class SlipStruct:
    
    def __init__(self):
        self.head = None
    
    def populate(self, val):
        newNode = Node(val)
        if not self.head:
            self.head = newNode
            self.head.next = self.head
            return
        else:
            currentNode = self.head
            while currentNode.next != self.head:
                currentNode = currentNode.next
            currentNode.next = newNode
            currentNode.next.next = self.head
    
    def getNext(self, val):
        temp = self.head
        while val.upper() != temp.value:
            temp = temp.next
        return temp.next.value
    
    def displayTree(self):
        temp = self.head
        if self.head != None:
            while True: 
                print(f"{temp.value} --> ", end=" ")
                temp = temp.next
                if temp == self.head:
                    break