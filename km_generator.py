# import random
#
# chars = 'QWERTYUIOPASDFGHJKLZXCVBNNM'
# numbers = '123456789'
#
# used_sn = []
# mc_list = []
#
# for i in range(1000):
#     sn = None
#     while True:
#         sn = ''.join(random.sample(''.join(random.sample(chars, 5)) + ''.join(random.sample(numbers, 8)), 13))
#         if sn not in used_sn:
#             break
#     mc = f'010460219301283721{sn}91EE0692MPZk59qku/oUlN5T5ejan67uY4d6l3GhWJNy0FQgIqQ='
#     mc_list.append(mc)
#
# with open('mark_code.txt', 'w') as f:
#     f.write('\n'.join(mc_list))

test = ['Борисов', 'Петр', 'Петрович']

result = f'{test[0]} {" ".join([f"{i[0]}." for i in test[1:]])}'

print(result)

