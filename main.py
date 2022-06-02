from module.dispatch_module import dispatch_module_main

'''
원하는 날짜 선택 
승객 증가 비율 선택 (장애인 이동율 0.04)
승객의 dispatch time 조절 가능 
'''

date = "20220215"
fake_ratio = 0
fail_time = 30

dispatch_module_main(date, fake_ratio, fail_time)