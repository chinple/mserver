'''

@author: chinple
'''
from tmodel.model.paramgen import CombSpace
d1, d2, d3 = 5, 3, 7
a = CombSpace(d1, d2, d3)

print "Comb Total: %s * %s * %s = %s" % (d1, d2, d3, a.__spaceSize__)
print "Comb Base:  %s " % a.__orderNumCombBase__
print "Number < %s is valid:" % a.__spaceSize__
for i in [0, 1, 10, 20, a.__spaceSize__ - 2, a.__spaceSize__ - 1]:
    print "\t%s = %s" % (i, a.getCombNum(i))

print "Number >= %s is invalid:" % a.__spaceSize__
for i in [ a.__spaceSize__, a.__spaceSize__ + 1, 100 * int((a.__spaceSize__ + 100) / 100)]:
    print "\t%s = %s" % (i, a.getCombNum(i))

# from tmodel.model.paramgen import GroupCombSpace
# gp = GroupCombSpace({'order': True, 'degree': [4, 2]})
# orderNum = 0
# t = gp.getTotalNum()
# while t > 0:
#     t -= 1
#     print(orderNum, gp.getGroupCombNum(0, orderNum))
#     orderNum = gp.getNextPureOrderNum(orderNum)

