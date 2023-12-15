import cv2


def main():
    # file_name = "docs/models/donut/data/key/invoice_0.json"
    # for i in range(2, 250):
    #     with open(file_name, "r") as file:
    #         # create new file name
    #         new_file_name = file_name.replace("invoice_0", f"invoice_{i}")
    #         # open new file
    #         with open(new_file_name, "w") as outfile:
    #             # write to new file
    #             outfile.write(file.read())

    file_name = "docs/models/donut/data/img/test/invoice_1.jpg"
    img = cv2.imread(file_name)
    for i in range(250, 500):
        new_file_name = file_name.replace("invoice_1", f"invoice_{i}")
        cv2.imwrite(new_file_name, img)

if __name__ == '__main__':
    main()