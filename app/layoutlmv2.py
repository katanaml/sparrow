import datetime


def process_document():
    a = datetime.datetime.now()
    print('LayoutLMv2 started')

    print('LayoutLMv2 completed')
    b = datetime.datetime.now()
    print(b - a)