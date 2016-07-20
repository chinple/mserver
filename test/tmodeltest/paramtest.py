'''

@author: chinple
'''
from tmodel.model.paramgen import GroupCombSpace
gp = GroupCombSpace({'order': True, 'degree': [4, 2]})
orderNum = 0
t = gp.getTotalNum()
while t > 0:
    t -= 1
    print(orderNum, gp.getGroupCombNum(0, orderNum))
    orderNum = gp.getNextPureOrderNum(orderNum)

