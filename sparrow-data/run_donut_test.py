from tools.donut.dataset_tester import DonutDatasetTester

def main():
    dataset_tester = DonutDatasetTester()
    dataset_tester.test("katanaml-org/invoices-donut-data-v1")

if __name__ == '__main__':
    main()