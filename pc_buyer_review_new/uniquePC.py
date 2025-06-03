import csv

unique = set()
with open("/home/ec2-user/ucsd/pc_buyer_review_new/PC_Buyer_Assignments - Copy(Buyer Review).csv","r") as f:
    dictReader = csv.DictReader(f)
    for row in dictReader:
        unique.add(row["Purchasing Category"])

print(f"{unique}")