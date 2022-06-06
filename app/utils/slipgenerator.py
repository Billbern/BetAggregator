from app.utils.slipstructure import SlipStruct


class SlipGenerator:
    
    def __init__(self) -> None:
        self.tree = SlipStruct()
        self.__populateTree()
    
    def __populateTree(self):
        __addons =  ['1', '2', '3', '4', '5', '6', '7', '8', '9', "A", "B", "C", "D", "E", "F", "G", "H","J","K", "L", "M", "N","P","Q","R","S","T","U","V","W","X","Y","Z"]
        for char in __addons:
            self.tree.populate(char)
    
    def generateSlip(self, slip, n):
        bin = [slip]
        while len(bin) < n:
            initialSlip = bin[-1]
            if initialSlip[-1] == "Z":
                count = -1
                while initialSlip[count] == "Z":
                    if initialSlip[count-1] != "Z":
                        if count == -1:
                            initialSlip = initialSlip[:count-1] + self.tree.getNext(initialSlip[count-1]) + self.tree.getNext(initialSlip[count])
                        else:
                            initialSlip = initialSlip[:count-1] + self.tree.getNext(initialSlip[count-1]) + self.tree.getNext(initialSlip[count]) + initialSlip[count+1:]
                        break
                    else:
                        if count == -1:
                            initialSlip = initialSlip[:count] + self.tree.getNext(initialSlip[count])
                        else:
                            initialSlip = initialSlip[:count] + self.tree.getNext(initialSlip[count]) + initialSlip[count+1:]
                        count -= 1
                bin.append(initialSlip)
            else:
                initialSlip = initialSlip[:-1] + self.tree.getNext(initialSlip[-1])
                bin.append(initialSlip)
        return bin