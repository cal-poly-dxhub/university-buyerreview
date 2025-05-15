from PyPDF2 import PdfReader

reader = PdfReader("/home/ec2-user/ucsd/data/checklist/Source Selection & Price Reasonabless (SSPR)/SSPR Example #1.pdf")
fields = reader.get_fields()

for field_name, field_info in fields.items():
    print(f"{field_name}: {field_info.get('/V')}") 